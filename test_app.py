import logging, time
from flask import Flask, request
from flask_cors import CORS

from ps4.actions import Action, Command, OnOff
from ps4.config import ConfigMixin
from ps4.tools import PS4Tool, DiscoveryTool, GoogleHomeDiscoveryTool
from ps4.packets import CipherModule, KeyExchangePacket, HelloPacket, PacketManager, MultiFunctionPacket

import threading

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
    cred = config.config['DEFAULT']['credential']

    # action = Action.map(raw=data)
    action = OnOff()
    action.state = True
    action.command = Command.ON_OFF

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

    iv = data[20:36]
    crypto = CipherModule(iv)
    manager.set_cipher_module(crypto)

    kex_packet = manager.init_keyex_packet()

    ps4_tool.send(kex_packet.buffer)
    logger.debug("exchanged key with playstation")

    login_packet = manager.init_login_packet(credentials=bytes(cred,'utf-8'))

    ps4_tool.send(login_packet.cipher_text)
    data = ps4_tool.receive()
    logger.debug("logged into playstation")

    if action.command == Command.ON_OFF:
        if not action.state:
            shutdown_packet = manager.init_shutdown_packet()
            ps4_tool.send(shutdown_packet.cipher_text)
            data = ps4_tool.receive()
            return

    if action.command == Command.APP_SELECT:
        status = manager.init_status_packet()
        packet = manager.init_launch_packet(action.get_application())
        logger.debug("launching %s on playstation", action.application)
        ps4_tool.send(status.cipher_text)
        ps4_tool.send(packet.cipher_text)
        data = ps4_tool.receive()


@app.route('/process', methods=['POST'])
def action():
    thread_action = threading.Thread(target=execute_action, kwargs={'data': request.data})
    thread_action.start()
    return "success"


if __name__ == '__main__':
    # home = GoogleHomeDiscoveryTool()
    ##home.daemon = True
    # home.start()
    execute_action()
    # app.run(port=8081, host='0.0.0.0')
