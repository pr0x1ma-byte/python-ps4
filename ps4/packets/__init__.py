from __future__ import annotations
from ps4.encryption import RSAMixin, AESMixin, CipherModule

from enum import Enum


class PacketType(Enum):
    CLIENT_HELLO = 1
    CLIENT_LOGIN = 2
    CLIENT_STATUS = 3
    CLIENT_SHUTDOWN = 4
    CLIENT_KEYEXCHNG = 5
    CLIENT_APPLAUNCH = 6

    DEVICE_SEARCH = 7
    DEVICE_LAUNCH = 8
    DEVICE_WAKEUP = 9


class Packet:
    def __init__(self, packet_type: PacketType = None):
        self.nop = b'\x00'
        self.buffer = b''
        self.cipher_text = None
        self.packet_type = packet_type

    def write_int(self, value: int, max_bytes=4, endian='little') -> Packet:
        self._write(int(value).to_bytes(2, endian), max_bytes)
        return self

    def write_bytes(self, bytz: bytes, max_bytes=4) -> Packet:
        self._write(bytz, max_bytes)
        return self

    def _write(self, bytz: bytes, max_bytes: int) -> Packet:
        padding = 0
        size_bytes = len(bytz)

        if max_bytes != 0:

            if size_bytes > max_bytes:
                raise RuntimeError('Invalid length of bytes')

            padding = max_bytes - size_bytes

        self.buffer += (bytz + (self.nop * padding))
        return self


class RSAPacket(Packet, RSAMixin):
    def __init__(self, packet_type:PacketType, cipher_module: CipherModule):
        super().__init__(packet_type=packet_type)
        self.cipher_module = cipher_module

    def write_key(self) -> RSAPacket:
        self.encrypt_key()
        self.write_bytes(self.cipher_text, max_bytes=256)
        return self


class AESPacket(Packet, AESMixin):

    def __init__(self, packet_type:PacketType, cipher_module: CipherModule):
        super().__init__(packet_type=packet_type)
        self.cipher_module = cipher_module


class PacketManager:
    def __init__(self):
        self.cipher_module = None

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

    def init_shutdown_packet(self) -> AESPacket:
        packet = AESPacket(packet_type=PacketType.CLIENT_SHUTDOWN, cipher_module=self.cipher_module) \
            .write_int(8, max_bytes=4) \
            .write_int(26, max_bytes=4) \
            .write_bytes(b'', max_bytes=8)
        packet.encrypt()
        return packet

    def init_hello_packet(self) -> Packet:
        return Packet(packet_type=PacketType.CLIENT_HELLO) \
            .write_int(28, max_bytes=4) \
            .write_bytes(b'pcco', max_bytes=5) \
            .write_int(512, max_bytes=4) \
            .write_bytes(b'', max_bytes=15)

    def init_keyex_packet(self) -> RSAPacket:
        return RSAPacket(packet_type=PacketType.CLIENT_KEYEXCHNG, cipher_module=self.cipher_module) \
            .write_int(280, max_bytes=4) \
            .write_int(32, max_bytes=4) \
            .write_key() \
            .write_bytes(self.cipher_module.iv, max_bytes=16)

    def init_login_packet(self, credentials: bytes, pin: bytes = b'') -> AESPacket:
        packet = AESPacket(packet_type=PacketType.CLIENT_LOGIN, cipher_module=self.cipher_module) \
            .write_int(value=384) \
            .write_int(value=30) \
            .write_bytes(b'', max_bytes=4) \
            .write_int(513) \
            .write_bytes(credentials, max_bytes=64) \
            .write_bytes(b'Python App', max_bytes=256) \
            .write_bytes(b'4.4', max_bytes=16) \
            .write_bytes(b'RPI', max_bytes=16) \
            .write_bytes(pin, max_bytes=16)
        packet.encrypt()

        return packet

    def init_status_packet(self) -> AESPacket:
        packet = AESPacket(packet_type=PacketType.CLIENT_STATUS, cipher_module=self.cipher_module) \
            .write_int(12, max_bytes=4) \
            .write_int(20, max_bytes=4) \
            .write_bytes(b'', max_bytes=8)
        packet.encrypt()
        return packet

    def init_app_launch_packet(self, id: bytes) -> AESPacket:
        packet = AESPacket(packet_type=PacketType.CLIENT_APPLAUNCH, cipher_module=self.cipher_module) \
            .write_int(24, max_bytes=4) \
            .write_int(10, max_bytes=4) \
            .write_bytes(id, max_bytes=16) \
            .write_bytes(b'', max_bytes=8)
        packet.encrypt()
        return packet

    def set_cipher_module(self, cipher_module: CipherModule):
        self.cipher_module = cipher_module
