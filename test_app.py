import logging, time, sys
from flask import Flask, request
from flask_cors import CORS
from ps4.actions import AppSelection, Application

from ps4 import PS4
from ps4.actions import Action, Command, OnOff
from ps4.config import ConfigMixin

import argparse
import threading

parser = argparse.ArgumentParser(description='Command PS4 from Google')
parser.add_argument('--register', dest='is_register', action='store_true', help='initiate registration with PS4')

args = parser.parse_args()

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
CORS(app)


def execute_action():
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])
    credentials = config.config['DEFAULT']['credential']

    # action = Action.map(raw=data)
    #action = OnOff()
    #action.state = False
    #action.command = Command.ON_OFF
    action = AppSelection()
    action.command = Command.APP_SELECT
    action.application = Application.NETFLIX

    ps4 = PS4(ip=ip, port=port, credentials=bytes(credentials, 'utf-8'))
    ps4.login()

    ps4.execute(action=action)

def register(pin):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])
    #credentials = config.config['DEFAULT']['credential']

    # action = Action.map(raw=data)
    action = OnOff()
    action.state = False
    action.command = Command.ON_OFF
    #action = AppSelection()
    #action.command = Command.APP_SELECT
    #action.application = Application.AMAZON

    ps4 = PS4(ip=ip, port=port, credentials=bytes(pin, 'utf-8'))
    ps4.login()

    #ps4.execute(action=action)

'''def register(pin):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])
    cred = config.config['DEFAULT']['credential']

    discovery_tool = DiscoveryTool(ip=ip, cred=cred)
    ps4_tool = PS4Tool()

    is_ok = False
    while not is_ok:
        try:
            is_ok = discovery_tool.search()
            discovery_tool.wake()
            time.sleep(1)
        except Exception as e:
            logger.exception(e)

    manager = PacketManager()

    ps4_tool.connect(ip, port)
    logger.debug("connected to playstation on {ip: %s, port: %s}", ip, port)

    hello_packet = manager.init_hello_packet()
    ps4_tool.send(hello_packet.buffer)
    logger.debug("sent client hello to playstation")
    data = ps4_tool.receive()
    # logger.debug("response: %s", data)
    iv = data[20:36]
    crypto = CipherModule(iv)
    manager.set_cipher_module(crypto)

    kex_packet = manager.init_keyex_packet()

    ps4_tool.send(kex_packet.buffer)
    logger.debug("exchanged key with playstation")

    login_packet = manager.init_login_packet(credentials=bytes(cred, 'utf-8'))

    ps4_tool.send(login_packet.cipher_text)
    data = ps4_tool.receive()

    login_packet = manager.init_login_packet(credentials=bytes(cred, 'utf-8'), pin=bytes(pin, 'utf-8'))
    ps4_tool.send(login_packet.cipher_text)
    data = ps4_tool.receive()
'''

@app.route('/process', methods=['POST'])
def action():
    thread_action = threading.Thread(target=execute_action, kwargs={'data': request.data})
    thread_action.start()
    return "success"


if __name__ == '__main__':
    if args.is_register:
        pin = input("Pin: ")
        register(pin)
        sys.exit(0)
    # home = GoogleHomeDiscoveryTool()
    ##home.daemon = True
    # home.start()
    execute_action()
    # app.run(port=8081, host='0.0.0.0')
