import socket, struct
import threading
import logging

logger = logging.getLogger().getChild(__name__)


class SocketBase:
    def __init__(self):
        self.DDP_VERSION = '00020020'
        self.DDP_PORT = 987
        self.REQ_PORT = 997
        self.MCAST_PORT = self.DDP_PORT
        self.BROADCAST_IP = '255.255.255.255'
        self.BROADCAST_PORT = self.DDP_PORT
        self.wake_packet = "WAKEUP * HTTP/1.1\nclient-type:i\nauth-type:C\nuser-credential:{}\n\device-discovery-protocol-version:00020020\r\n\r\n"
        self.srch_packet = "SRCH * HTTP/1.1\r\ndevice-discovery-protocol-version:00020020\r\n\r\n"
        self.launch_packet = "LAUNCH * HTTP/1.1\nclient-type:i\nauth-type:C\nuser-credential:{}\n\device-discovery-protocol-version:00020020\r\n\r\n"


class PS4Tool:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        logger.debug("connecting to {ip: %s, port: %s}", host, port)
        self.sock.connect((host, port))

    def send(self, msg):
        sent = self.sock.send(msg)
        if sent == 0:
            raise RuntimeError("socket connection broken")

    def receive(self):
        return self.sock.recv(300)


class DiscoveryTool(SocketBase):
    def __init__(self, cred=None, ip=None):
        super().__init__()
        self.ip = ip
        self.cred = cred

    def search(self):
        is_ok = False
        search_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        search_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            logger.debug("sending search packet to ps4")
            search_sock.sendto(bytes(self.srch_packet, 'utf-8'), (self.BROADCAST_IP, self.MCAST_PORT))
            search_sock.settimeout(5)
            (data, ip) = search_sock.recvfrom(300)
            logger.debug("recieved <%s> from ps4", data)
            if 'Ok' in data.decode('utf-8'):
                is_ok = True
        except Exception as e:
            logger.error("error searching for ps4")
            raise e
        finally:
            search_sock.close()
            return is_ok

    def wake(self):
        msg = self.wake_packet.format(self.cred)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.debug("sending wake packet to ps4")
        sock.sendto(bytes(msg, 'utf-8'), (self.ip, self.DDP_PORT))
        try:
            self._launch()
        except Exception as e:
            logger.exception("error waking the ps4")
            raise e
        finally:
            sock.close()

    def _launch(self):
        logger.debug("sending launch packet to ps4")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msg = self.launch_packet.format(self.cred)
        sock.sendto(bytes(msg, 'utf-8'), (self.ip, self.MCAST_PORT))
        sock.close()


class GoogleHomeDiscoveryTool(threading.Thread):
    def __init__(self):
        super().__init__()
        self.MCAST_PORT = 3311
        self.MCAST_GRP = '224.1.1.1'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind(('', self.MCAST_PORT))
        multicast_req = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_req)
        self.quit = False

    def run(self):
        while not self.quit:
            (bytze, addr) = self.sock.recvfrom(10240)
            self.handle(addr, bytze)

    def handle(self, addr, bytze):
        msg = b'HelloFromPS4'
        (ip, port) = addr
        logger.debug('received discovery payload<%s> from: {address: %s, port: %s}', bytze, ip, port)
        self.sock.sendto(msg, addr)
        logger.debug('sent discovery response<%s> to: {address: %s, port: %s}', msg, ip, port)
