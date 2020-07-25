import logging
import socket
import time

from ps4.encryption import EncryptionModule, DecryptionModule

from ps4.actions import Action, Command, AppSelection, OnOff

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
        self.iv = None
        self.encryption_module = None
        self.decryption_module = None

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

    def _init_encryption(self, iv):
        self.iv = iv
        self.encryption_module = EncryptionModule(self.iv)
        self.decryption_module = DecryptionModule(self.iv)
        self.manager.set_encryption_module(self.encryption_module)

    def decrypt(self, enc_bytes: bytes) -> bytes:
        return self.decryption_module.aes_decrypt(enc_bytes)

    def login(self) -> bool:

        # search and wakeup
        self.discover()

        self.connect(self.ip, self.port)
        logger.debug("connected to playstation on {ip: %s, port: %s}", self.ip, self.port)

        # client hello
        hello_packet = self.manager.init_hello_packet()
        self.send(hello_packet.buffer)
        logger.debug("sent client hello")
        data = self.receive()
        logger.debug("response: %s", data)

        # initialize encryption objects
        iv = data[20:36]
        self._init_encryption(iv=iv)

        # exchange aes encryption key
        kex_packet = self.manager.init_keyex_packet()
        self.send(kex_packet.buffer)
        data = self.receive()
        data = self.decrypt(data)
        logger.debug("exchanged aes key")
        logger.debug("response: %s", data)

        # send login request
        login_packet = self.manager.init_login_packet(credentials=self.credentials)
        self.send(login_packet.cipher_text)
        data = self.receive()
        data = self.decrypt(data)
        logger.debug("login successful")
        logger.debug("response: %s", data)

        # TODO: actually check response value
        if data[4] == 0x07:
            self.is_logged_in = True
        return self.is_logged_in

    def shutdown(self) -> bool:
        if self.is_logged_in:
            shutdown_packet = self.manager.init_shutdown_packet()
            logger.debug("shutting down playstation")
            self.send(shutdown_packet.cipher_text)
            data = self.receive()
            data = self.decrypt(data)
            logger.debug("response: %s", data)
            return True
        raise RuntimeError('not logged in: unable to shutdown')

    def run_application(self, action: AppSelection):
        status_packet = self.manager.init_status_packet()
        launch_packet = self.manager.init_app_launch_packet(action.get_application())
        logger.debug("launching %s on playstation", action.application)
        self.send(status_packet.cipher_text)
        self.send(launch_packet.cipher_text)
        data = self.receive()
        data = self.decrypt(data)
        logger.debug("response: %s", data)

    def execute(self, action: Action):
        if isinstance(action, OnOff):
            if not action.state:
                self.shutdown()

        if isinstance(action, AppSelection):
            self.run_application(action=action)

    def send_search(self):
        is_discovered = False
        sock = self.get_socket(protocol=Protocol.UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = self.manager.init_udp_search_packet()
        logger.debug("sending search packet: '%s'", msg.buffer)

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
        logger.debug("sending wake packet: '%s'", msg.buffer)

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
        logger.debug("sending launch packet: '%s'", msg.buffer)

        try:
            sock.sendto(msg.buffer, (self.ip, self.MCAST_PORT))
        except Exception as e:
            logger.exception("error sending launch packet")
            raise e
        finally:
            sock.close()
