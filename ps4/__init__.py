import logging
import socket
import time

from ps4.encryption import CipherModule

from ps4.actions import Action, Command

from ps4.packets import PacketManager
from ps4.tools import Socket, Protocol

logger = logging.getLogger()


class PS4(Socket):
    def __init__(self, ip: str, port: int, credentials: bytes):
        Socket.__init__(self)
        self.ip = ip
        self.port = port

        self.credentials = credentials
        self.is_discovered = False
        self.is_logged_in = False

        self.manager = PacketManager()

    def discover(self, auto_wakeup=True):
        while not self.is_discovered:
            try:
                self.is_discovered = self.send_search()
                self.send_wakeup()
                time.sleep(1)
                if auto_wakeup:
                    self.send_launch()
            except Exception as e:
                logger.exception(e)

    def login(self) -> bool:
        self.discover()

        self.connect(self.ip, self.port)
        logger.debug("connected to playstation on {ip: %s, port: %s}", self.ip, self.port)

        hello_packet = self.manager.init_hello_packet()
        self.send(hello_packet.buffer)
        logger.debug("sent client hello to playstation")
        data = self.receive()
        logger.debug("response: %s", data)
        iv = data[20:36]
        crypto = CipherModule(iv)
        self.manager.set_cipher_module(crypto)

        kex_packet = self.manager.init_keyex_packet()

        self.send(kex_packet.buffer)
        #data = self.receive()
        #response = kex_packet.aes_decrypt(data)
        #logger.debug("data: %s", data)
        #logger.debug("response: %s", response)
        logger.debug("exchanged key with playstation")

        login_packet = self.manager.init_login_packet(credentials=self.credentials)
        self.send(login_packet.cipher_text)
        data = self.receive()
        response = login_packet.decrypt(data)
        logger.debug("response: %s", response)
        logger.debug("logged into playstation")
        # TODO: actually check response?
        self.is_logged_in = True
        return True

    def shutdown(self) -> bool:
        if self.is_logged_in:
            shutdown_packet = self.manager.init_shutdown_packet()
            self.send(shutdown_packet.cipher_text)
            data = self.receive()
            #logger.debug("response: %s", response)
            return True
        raise RuntimeError('not logged in: unable to shutdown')

    def run_application(self, action: Action):
        status = self.manager.init_status_packet()
        packet = self.manager.init_app_launch_packet(action.get_application())
        logger.debug("launching %s on playstation", action.application)
        self.send(status.cipher_text)
        self.send(packet.cipher_text)
        data = self.receive()
        #response = packet.aes_decrypt(data)
        #logger.debug("response: %s", response)

    def execute(self, action: Action):
        if action.command == Command.ON_OFF:
            if not action.state:
                self.shutdown()

        if action.command == Command.APP_SELECT:
            self.run_application(action=action)

    def send_search(self):
        is_discovered = False
        sock = self.get_socket(protocol=Protocol.UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = self.manager.init_udp_search_packet()
        logger.debug("sending search packet: '%s'", msg)

        try:
            sock.sendto(msg.buffer, (self.BROADCAST_IP, self.MCAST_PORT))
            sock.settimeout(5)
            (data, ip) = sock.recvfrom(300)
            logger.debug("search response: %s", data)

            # TODO map to a proper object
            if 'Ok' in data.decode('utf-8'):
                is_discovered = True
        except Exception as e:
            logger.error("error sending search packet")
            raise e
        finally:
            sock.close()
            return is_discovered

    def send_wakeup(self):
        sock = self.get_socket(protocol=Protocol.UDP)
        msg = self.manager.init_udp_wakeup_packet(credentials=self.credentials)
        logger.debug("sending wake packet: '%s'", msg)

        try:
            sock.sendto(msg.buffer, (self.ip, self.DDP_PORT))
        except Exception as e:
            logger.exception("error sending wake packet")
            raise e
        finally:
            sock.close()

    def send_launch(self):
        sock = self.get_socket(protocol=Protocol.UDP)
        msg = self.manager.init_udp_launch_packet(
            credentials=self.credentials)
        logger.debug("sending launch packet: '%s'", msg)

        try:
            sock.sendto(msg.buffer, (self.ip, self.MCAST_PORT))
        except Exception as e:
            logger.exception("error sending launch packet")
            raise e
        finally:
            sock.close()
