from __future__ import annotations
from ps4.encryption import EncryptionModule, DecryptionModule

from enum import Enum


class PacketType(Enum):
    CLIENT_HELLO = 1
    CLIENT_LOGIN = 2
    CLIENT_STATUS = 3
    CLIENT_SHUTDOWN = 4
    CLIENT_KEYEXCHNG = 5
    CLIENT_APPLAUNCH = 6

    SERVER_HELLO_RSP = 7
    SERVER_LOGIN_RSP = 8
    SERVER_SHUTDOWN_RSP = 9
    SERVER_KEYEXCHNG_RSP = 10
    SERVER_APPLAUNCH_RSP = 11

    DEVICE_SEARCH = 12
    DEVICE_LAUNCH = 13
    DEVICE_WAKEUP = 14
    DEVICE_DISCOVERY = 15


class Packet:
    def __init__(self, packet_type: PacketType = None):
        self.nop = b'\x00'
        self.buffer = b''
        self.cipher_text = None
        self.packet_type = packet_type

    def write_int(self, value: int, max_bytes=4, endian='little') -> Packet:
        self._write(int(value).to_bytes(2, endian), max_bytes)
        return self

    def write_bytes(self, raw_bytes: bytes, max_bytes=4) -> Packet:
        self._write(raw_bytes, max_bytes)
        return self

    def _write(self, raw_bytes: bytes, max_bytes: int) -> Packet:
        padding = 0
        size_bytes = len(raw_bytes)

        if max_bytes != 0:

            if size_bytes > max_bytes:
                raise RuntimeError('Invalid length of bytes')

            padding = max_bytes - size_bytes

        self.buffer += (raw_bytes + (self.nop * padding))
        return self


class Response:
    def __init__(self, packet_type: PacketType = None):
        self.status = None
        self.raw_bytes = None
        self.packet_type = packet_type


class PacketManager:
    def __init__(self):
        self.encryption_module = None
        self.decryption_module = None

    def init_udp_standby_packet(self, protocol_version: bytes = b'00020020',
                                  system_version: bytes = b'07510001') -> Packet:
        packet = Packet(packet_type=PacketType.DEVICE_DISCOVERY) \
            .write_bytes(b'HTTP/1.1 620 Server Standby\n', max_bytes=0) \
            .write_bytes(b'host-id:F8461C8E7D59\n', max_bytes=0) \
            .write_bytes(b'host-type:PS4\n', max_bytes=0) \
            .write_bytes(b'host-name:Py-PS4\n', max_bytes=0) \
            .write_bytes(b'host-request-port:997\n', max_bytes=0) \
            .write_bytes(b'device-discovery-protocol-version:', max_bytes=0) \
            .write_bytes(protocol_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0) \
            .write_bytes(b'system-version:', max_bytes=0) \
            .write_bytes(system_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0)
        return packet

    def init_udp_discovery_packet(self, protocol_version: bytes = b'00020020',
                                  system_version: bytes = b'07510001') -> Packet:
        packet = Packet(packet_type=PacketType.DEVICE_DISCOVERY) \
            .write_bytes(b'HTTP/1.1 200 Ok\n', max_bytes=0) \
            .write_bytes(b'host-id:F8461C8E7D59\n', max_bytes=0) \
            .write_bytes(b'host-type:PS4\n', max_bytes=0) \
            .write_bytes(b'host-name:Py-PS4\n', max_bytes=0) \
            .write_bytes(b'host-request-port:997\n', max_bytes=0) \
            .write_bytes(b'device-discovery-protocol-version:', max_bytes=0) \
            .write_bytes(protocol_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0) \
            .write_bytes(b'system-version:', max_bytes=0) \
            .write_bytes(system_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0)
        return packet

    def init_udp_launch_packet(self, credentials: bytes = b'', protocol_version: bytes = b'00020020') -> Packet:
        if credentials == b'':
            raise RuntimeError('must supply device credential')

        packet = Packet(packet_type=PacketType.DEVICE_LAUNCH) \
            .write_bytes(b'LAUNCH * HTTP/1.1\n', max_bytes=0) \
            .write_bytes(b'client-type:i\n', max_bytes=0) \
            .write_bytes(b'auth-type:C\n', max_bytes=0) \
            .write_bytes(b'user-credential:', max_bytes=0) \
            .write_bytes(credentials, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0) \
            .write_bytes(b'device-discovery-protocol-version:', max_bytes=0) \
            .write_bytes(protocol_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0)

        return packet

    def init_udp_wakeup_packet(self, credentials: bytes = b'', protocol_version: bytes = b'00020020') -> Packet:
        if credentials == b'':
            raise RuntimeError('must supply device credential')

        packet = Packet(packet_type=PacketType.DEVICE_WAKEUP) \
            .write_bytes(b'WAKEUP * HTTP/1.1\n', max_bytes=0) \
            .write_bytes(b'client-type:i\n', max_bytes=0) \
            .write_bytes(b'auth-type:C\n', max_bytes=0) \
            .write_bytes(b'user-credential:', max_bytes=0) \
            .write_bytes(credentials, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0) \
            .write_bytes(b'device-discovery-protocol-version:', max_bytes=0) \
            .write_bytes(protocol_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0)

        return packet

    def init_udp_search_packet(self, protocol_version: bytes = b'00020020') -> Packet:
        packet = Packet(packet_type=PacketType.DEVICE_SEARCH) \
            .write_bytes(b'SRCH * HTTP/1.1\r\n', max_bytes=0) \
            .write_bytes(b'device-discovery-protocol-version:', max_bytes=0) \
            .write_bytes(protocol_version, max_bytes=0) \
            .write_bytes(b'\n', max_bytes=0)

        return packet

    def init_shutdown_packet(self) -> Packet:
        packet = Packet(packet_type=PacketType.CLIENT_SHUTDOWN) \
            .write_int(8, max_bytes=4) \
            .write_int(26, max_bytes=4) \
            .write_bytes(b'', max_bytes=8)
        packet.cipher_text = self.encryption_module.aes_encrypt(packet.buffer)
        return packet

    def init_hello_packet(self) -> Packet:
        return Packet(packet_type=PacketType.CLIENT_HELLO) \
            .write_int(28, max_bytes=4) \
            .write_bytes(b'pcco', max_bytes=5) \
            .write_int(512, max_bytes=4) \
            .write_bytes(b'', max_bytes=15)

    def init_keyex_packet(self) -> Packet:
        encrypted_aes_key = self.encryption_module.get_encrypted_aes_key()
        packet = Packet(packet_type=PacketType.CLIENT_KEYEXCHNG) \
            .write_int(280, max_bytes=4) \
            .write_int(32, max_bytes=4) \
            .write_bytes(encrypted_aes_key, max_bytes=256) \
            .write_bytes(self.encryption_module.iv, max_bytes=16)
        return packet

    def init_login_packet(self, credentials: bytes, pin: bytes = b'') -> Packet:
        packet = Packet(packet_type=PacketType.CLIENT_LOGIN) \
            .write_int(value=384) \
            .write_int(value=30) \
            .write_bytes(b'', max_bytes=4) \
            .write_int(513) \
            .write_bytes(credentials, max_bytes=64) \
            .write_bytes(b'Python App', max_bytes=256) \
            .write_bytes(b'4.4', max_bytes=16) \
            .write_bytes(b'RPI', max_bytes=16) \
            .write_bytes(pin, max_bytes=16)
        packet.cipher_text = self.encryption_module.aes_encrypt(packet.buffer)

        return packet

    def init_status_packet(self) -> Packet:
        packet = Packet(packet_type=PacketType.CLIENT_STATUS) \
            .write_int(12, max_bytes=4) \
            .write_int(20, max_bytes=4) \
            .write_bytes(b'', max_bytes=8)
        packet.cipher_text = self.encryption_module.aes_encrypt(packet.buffer)
        return packet

    def init_app_launch_packet(self, id: bytes) -> Packet:
        packet = Packet(packet_type=PacketType.CLIENT_APPLAUNCH) \
            .write_int(24, max_bytes=4) \
            .write_int(10, max_bytes=4) \
            .write_bytes(id, max_bytes=16) \
            .write_bytes(b'', max_bytes=8)
        packet.cipher_text = self.encryption_module.aes_encrypt(packet.buffer)
        return packet

    def init_login_rsp_packet(self, raw_bytes: bytes):
        # packet = Packet(packet_type=PacketType.SERVER_LOGIN_RSP)
        # return packet
        pass

    def set_encryption_module(self, encryption_module: EncryptionModule):
        self.encryption_module = encryption_module

    def set_decryption_module(self, decryption_module: DecryptionModule):
        self.decryption_module = decryption_module
