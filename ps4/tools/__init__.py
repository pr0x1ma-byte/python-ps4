import socket, struct
import threading
import logging

from ps4.packets import PacketManager

logger = logging.getLogger().getChild(__name__)

from enum import Enum


class Protocol(Enum):
    TCP = 1
    UDP = 2


class Socket:
    def __init__(self, sock=None, protocol: Protocol = None):
        if sock is None and protocol is None:
            self.sock = self.get_socket(protocol=Protocol.TCP)
        elif sock:
            self.sock = sock
        elif protocol:
            self.sock = self.get_socket(protocol)

        self.DDP_VERSION = '00020020'
        self.DDP_PORT = 987
        self.REQ_PORT = 997
        self.MCAST_PORT = self.DDP_PORT
        self.BROADCAST_IP = '255.255.255.255'
        self.BROADCAST_PORT = self.DDP_PORT

        self.DISCOVERY_MCAST_PORT = 3311
        self.DISCOVERY_MCAST_GRP = '224.1.1.1'

    def connect(self, host, port):
        logger.debug("connecting to {ip: %s, port: %s}", host, port)
        self.sock.connect((host, port))

    def send(self, msg):
        sent = self.sock.send(msg)
        if sent == 0:
            raise RuntimeError("socket connection broken")

    def receive(self):
        return self.sock.recv(1024)

    @staticmethod
    def get_socket(protocol: Protocol = Protocol.TCP):
        sock = None
        if protocol == Protocol.TCP:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if protocol == Protocol.UDP:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return sock


class GoogleHomeDiscoveryTool(threading.Thread, Socket):
    def __init__(self):
        threading.Thread.__init__(self)
        Socket.__init__(self, protocol=Protocol.UDP)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(('', self.DISCOVERY_MCAST_PORT))
        multicast_req = struct.pack("4sl", socket.inet_aton(self.DISCOVERY_MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_req)
        self.quit = False

    def run(self):
        while not self.quit:
            (raw_bytes, address) = self.sock.recvfrom(10240)
            self.handle(address, raw_bytes)

    def handle(self, address, raw_bytes: bytes):
        msg = b'HelloFromPythonPS4'
        (ip, port) = address
        logger.debug('received discovery payload<%s> from: {address: %s, port: %s}', raw_bytes, ip, port)
        self.sock.sendto(msg, address)
        logger.debug('sent discovery response<%s> to: {address: %s, port: %s}', msg, ip, port)


class TCPSockServer(threading.Thread, Socket):
    def __init__(self):
        threading.Thread.__init__(self)
        Socket.__init__(self, protocol=Protocol.TCP)
        self.sock.bind(('0.0.0.0', self.DDP_PORT))
        self.quit = False

    def run(self):
        self.sock.listen(1)
        while not self.quit:
            try:
                (csock, address) = self.sock.accept()
                (raw_bytes, address) = csock.recvfrom(10240)
                logger.debug(raw_bytes)
                #print(raw_bytes)
            except Exception as e:
                logger.exception(e)

    def stop(self):
        self.quit = True
        self.sock.close()


class CredentialCaptureTool(Socket):
    def __init__(self):
        Socket.__init__(self, protocol=Protocol.UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(('', self.MCAST_PORT))
        multicast_req = struct.pack("4sl", socket.inet_aton(self.DISCOVERY_MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_req)
        self.quit = False

        self.sock2 = TCPSockServer()

    def run(self):
        self.sock2.start()

        while not self.quit:
            (raw_bytes, address) = self.sock.recvfrom(10240)
            self.handle(address, raw_bytes)

    def stop(self):
        self.quit = True

    def handle(self, address, raw_bytes):
        msg = PacketManager().init_udp_standby_packet()
        (ip, port) = address
        logger.debug('received discovery payload<%s> from: {address: %s, port: %s}', raw_bytes, ip, port)
        self.sock.sendto(msg.buffer, address)
        logger.debug('sent discovery response<%s> to: {address: %s, port: %s}', msg.buffer, ip, port)
