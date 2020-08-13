import logging
from logging.handlers import SysLogHandler
import platform
from flask import Flask, request
from flask_cors import CORS

from ps4 import PS4, Action
from ps4.config import ConfigMixin
from ps4.tools import GoogleHomeDiscoveryTool, CredentialCaptureTool
import setproctitle
import threading, argparse, sys

setproctitle.setproctitle('python-ps4')
parser = argparse.ArgumentParser(description='Command PS4 from Google')
parser.add_argument('--discover-id', dest='discover_id', action='store_true', help='discover the client id from PS4 Second Screen app')
parser.add_argument('--register', dest='is_register', action='store_true', help='initiate registration with PS4')
parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='enable debug output')

args = parser.parse_args()
logger = logging.getLogger()

if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

address='/dev/log'
if platform.system() == 'Darwin':
    address='/var/run/syslog'

logger.addHandler(SysLogHandler(address=address))
logger.addHandler(logging.StreamHandler())
app = Flask(__name__)
CORS(app)


def execute_action(data):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])
    credentials = config.config['DEFAULT']['credential']

    action = Action.map(raw=data)
    logger.debug("recieved automation request: %s", action)
    retry_count = 0
    while True:
        try:
            ps4 = PS4(ip=ip, port=port, credentials=bytes(credentials, 'utf-8'), action=action)
            ps4.login()
            ps4.execute()
            break
        except ConnectionRefusedError as cre:
            if retry_count > 2:
                logger.error("failed to login on %s attempts!", retry_count)
                raise cre
            logger.debug("retrying login....")
            retry_count += 1
            continue
        except Exception as e:
            raise e


def register(pin):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])

    ps4 = PS4(ip=ip, port=port, credentials=bytes(pin, 'utf-8'))
    ps4.login()


@app.route('/action', methods=['POST'])
def action():
    thread_action = threading.Thread(target=execute_action, kwargs={'data': request.data})
    thread_action.start()
    return "success"


if __name__ == '__main__':

    if args.discover_id:
        CredentialCaptureTool().run()

    if args.is_register:
        pin = input("Pin: ")
        register(pin)
        sys.exit(0)

    home = GoogleHomeDiscoveryTool()
    home.daemon = True
    home.start()

    app.run(port=8081, host='0.0.0.0')
