import logging, time
from flask import Flask, request
from flask_cors import CORS

from ps4.actions import Action, Command
from ps4.config import ConfigMixin
from ps4.tools import PS4Tool, DiscoveryTool, GoogleHomeDiscoveryTool
from ps4.packets import CipherModule, KeyExchangePacket, HelloPacket, PacketManager, MultiFunctionPacket

import threading

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
CORS(app)


def execute_action(data):
    config = ConfigMixin()
    config.load()
    ip = config.config['DEFAULT']['ip']
    port = int(config.config['DEFAULT']['port'])
    cred = config.config['DEFAULT']['credential']

    action = Action.map(raw=data)

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

    ps4_tool.connect(ip, port)
    logger.debug("connected to playstation on {ip: %s, port: %s}", ip, port)
    hello_packet = HelloPacket() \
        .write_int(28, max_bytes=4) \
        .write_bytes(b'pcco', max_bytes=5) \
        .write_int(512, max_bytes=4) \
        .write_bytes(b'', max_bytes=15)

    ps4_tool.send(hello_packet.buffer)
    logger.debug("sent client hello to playstation")
    data = ps4_tool.receive()

    iv = data[20:36]
    crypto = CipherModule(iv)

    kex_packet = KeyExchangePacket(crypto)
    kex_packet.write_int(280, max_bytes=4) \
        .write_int(32, max_bytes=4) \
        .write_key() \
        .write_bytes(iv, max_bytes=16)

    ps4_tool.send(kex_packet.buffer)
    logger.debug("exchanged key with playstation")

    login_packet = MultiFunctionPacket(crypto) \
        .write_int(value=384) \
        .write_int(value=30) \
        .write_bytes(b'', max_bytes=4) \
        .write_int(513) \
        .write_bytes(bytes(cred, 'utf-8'), max_bytes=64) \
        .write_bytes(b'Python App', max_bytes=256) \
        .write_bytes(b'4.4', max_bytes=16) \
        .write_bytes(b'PS4 IOT', max_bytes=16) \
        .write_bytes(b'', max_bytes=16) \
        .encrypt()

    ps4_tool.send(login_packet.cipher_text)
    data = ps4_tool.receive()
    logger.debug("logged into playstation")
    status = MultiFunctionPacket(crypto) \
        .write_int(12, max_bytes=4) \
        .write_int(20, max_bytes=4) \
        .write_bytes(b'', max_bytes=8)
    status.encrypt()

    if action.command == Command.ON_OFF:
        manager = PacketManager()
        manager.set_cipher_module(crypto)
        if not action.state:
            shutdown_packet = manager.init_shutdown_packet()
            ps4_tool.send(shutdown_packet.cipher_text)
            data = ps4_tool.receive()
            return

    if action.command == Command.APP_SELECT:
        manager = PacketManager()
        manager.set_cipher_module(crypto)
        status = MultiFunctionPacket(crypto) \
            .write_int(12, max_bytes=4) \
            .write_int(20, max_bytes=4) \
            .write_bytes(b'', max_bytes=8)
        status.encrypt()

        packet = manager.init_launch_packet(action.get_application())
        logger.debug("launching %s on playstation", action.application)
        ps4_tool.send(status.cipher_text)
        ps4_tool.send(packet.cipher_text)
        data = ps4_tool.receive()


@app.route('/action', methods=['POST'])
def action():
    thread_action = threading.Thread(target=execute_action, kwargs={'data': request.data})
    thread_action.start()
    return "success"


if __name__ == '__main__':
    home = GoogleHomeDiscoveryTool()
    home.daemon = True
    home.start()

    app.run(port=8081, host='0.0.0.0')
