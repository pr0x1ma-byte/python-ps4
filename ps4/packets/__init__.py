from __future__ import annotations
from ps4.encryption import RSAMixin, AESMixin, CipherModule

'''
bye = 4
newByePacket() {
        return this.create(8)
            .writeInt(PacketType.Bye);
    }

    newCHelloPacket() {
        return this.create(28)
            .writeInt(PacketType.ClientHello)
            .writeInt(VERSION)
            .writeInt(0);
    }
'''


class Packet:
    def __init__(self):
        self.nop = b'\x00'
        self.buffer = b''
        self.cipher_text = None

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


class EndPacket(Packet):
    def __init__(self):
        super().__init__()


class HelloPacket(Packet):
    def __init__(self):
        super().__init__()


class KeyExchangePacket(Packet, RSAMixin):
    def __init__(self, cipher_module: CipherModule):
        super().__init__()
        self.cipher_module = cipher_module

    def write_key(self) -> KeyExchangePacket:
        self.encrypt_key()
        self.write_bytes(self.cipher_text, max_bytes=256)
        return self


class MultiFunctionPacket(Packet, AESMixin):

    def __init__(self, cipher_module: CipherModule):
        super().__init__()
        self.cipher_module = cipher_module


class PacketManager:
    def __init__(self):
        self.cipher_module = None

    def init_shutdown_packet(self) -> MultiFunctionPacket:
        packet = MultiFunctionPacket(self.cipher_module) \
            .write_int(8, max_bytes=4) \
            .write_int(26, max_bytes=12) \
            .write_bytes(b'', max_bytes=8)
        packet.encrypt()
        return packet

    def init_hello_packet(self) -> HelloPacket:
        return HelloPacket() \
            .write_int(28, max_bytes=4) \
            .write_bytes(b'pcco', max_bytes=5) \
            .write_int(512, max_bytes=4) \
            .write_bytes(b'', max_bytes=15)

    def init_keyex_packet(self) -> KeyExchangePacket:
        return KeyExchangePacket(self.cipher_module) \
            .write_int(280, max_bytes=4) \
            .write_int(32, max_bytes=4) \
            .write_key() \
            .write_bytes(self.cipher_module.iv, max_bytes=16)

    def init_login_packet(self, credentials : bytes) -> MultiFunctionPacket:
        packet = MultiFunctionPacket(self.cipher_module) \
            .write_int(value=384) \
            .write_int(value=30) \
            .write_bytes(b'', max_bytes=4) \
            .write_int(513) \
            .write_bytes(credentials, max_bytes=64) \
            .write_bytes(b'Python App', max_bytes=256) \
            .write_bytes(b'4.4', max_bytes=16) \
            .write_bytes(b'PS4 IOT', max_bytes=16) \
            .write_bytes(b'', max_bytes=16)
        packet.encrypt()

        return packet

    def init_status_packet(self) -> MultiFunctionPacket:
        packet = MultiFunctionPacket(self.cipher_module) \
            .write_int(12, max_bytes=4) \
            .write_int(20, max_bytes=4) \
            .write_bytes(b'', max_bytes=8)
        packet.encrypt()
        return packet

    def init_launch_packet(self, id: bytes) -> MultiFunctionPacket:
        packet = MultiFunctionPacket(self.cipher_module) \
            .write_int(24, max_bytes=4) \
            .write_int(10, max_bytes=4) \
            .write_bytes(id, max_bytes=16) \
            .write_bytes(b'', max_bytes=8)
        packet.encrypt()
        return packet

    def set_cipher_module(self, cipher_module: CipherModule):
        self.cipher_module = cipher_module
