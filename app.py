import logging
from flask import Flask, request
from flask_cors import CORS

from ps4 import PS4, Action
from ps4.config import ConfigMixin
from ps4.tools import GoogleHomeDiscoveryTool
import setproctitle
import threading, argparse, sys

setproctitle.setproctitle('python-ps4')
parser = argparse.ArgumentParser(description='Command PS4 from Google')
parser.add_argument('--register', dest='is_register', action='store_true', help='initiate registration with PS4')

args = parser.parse_args()
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)


def execute_action(data):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])
    credentials = config.config['DEFAULT']['credential']
    log_level = config.config['DEFAULT']['log_level']
    logger.setLevel(logging.getLevelName(log_level))

    action = Action.map(raw=data)
    ps4 = PS4(ip=ip, port=port, credentials=bytes(credentials, 'utf-8'))
    ps4.login()
    ps4.execute(action=action)


def register(pin):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])

    ps4 = PS4(ip=ip, port=port, credentials=bytes(pin, 'utf-8'))
    ps4.login()
    ps4.execute(action=action)


@app.route('/action', methods=['POST'])
def action():
    thread_action = threading.Thread(target=execute_action, kwargs={'data': request.data})
    thread_action.start()
    return "success"


if __name__ == '__main__':

    if args.is_register:
        pin = input("Pin: ")
        register(pin)
        sys.exit(0)

    home = GoogleHomeDiscoveryTool()
    home.daemon = True
    home.start()

    app.run(port=8081, host='0.0.0.0')
