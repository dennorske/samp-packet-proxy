#!/usr/bin/env python3
import logging
import socket
import socketserver
import threading
import time
from enum import Enum


#    The current settings assume your server is running on port 7777
#
#    iptables -t nat -A PREROUTING -p udp --dport 7777 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7778  # noqa
#    iptables -I INPUT -p udp --dport 7778 -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP  # noqa
#
#
#    make sure ports above match ports below in the variables.
#
#    Basicly all query packets get directed to this script,
#    and sync packets are left untouched
#


####################### MUST BE CONFIGURED #####################  # noqa
SERVER_PORT = 7777  # Assuming your samp server runs on this port
PROXY_PORT = 7778  # This script will take this port.
SAMP_SERVER_ADDRESS = "123.123.123.123"  # Public ip for your server SAMP srv

# Edit the below if you run this on a different server than the samp server
# Useful if you have this script running on a separate server.
SAMP_SERVER_LOCALHOST = "127.0.0.1"

# Do not touch code below this line.
#####################################################################
SAMP_SERVER_ADDRESS_BYTES = socket.inet_aton(SAMP_SERVER_ADDRESS)
SHORT_SLEEP_DURATION = 1
RETRY_SLEEP_DURATION = 2
QUERY_TIMEOUT = 4


class StatusType(Enum):
    info = "i"
    rules = "r"
    clients = "c"
    details = "d"


class ServerStatus:
    """ServerStatus represents the current status and information returned from
    internal query packets.
    """

    def __init__(self) -> None:
        self.info: bytes = b""
        self.rules: bytes = b""
        self.clients: bytes = b""
        self.detail: bytes = b""
        self.isonline = False


server = ServerStatus()


class UDPServer:
    def __init__(
        self,
        bind_address,
        target_address,
        internal_host="127.0.0.1",
        timeout=0.5,
    ):
        # ulimit?
        self.target_address = target_address
        self.timeout = timeout
        self.server = socketserver.UDPServer(
            bind_address, create_handler(self.handle_external_packet)
        )
        self.stop_thread = False

    def send_server_query(self, query: StatusType) -> bytes:
        """Send internal opcode and return the data it gives."""
        packet = self.assemblePacket(query.value)
        answer = b""
        try:
            self.sock.sendto(packet, (SAMP_SERVER_ADDRESS, SERVER_PORT))
            answer = self.sock.recv(1024)[11:]
        except socket.timeout:
            logging.error(f"Timed out getting info for opcode '{query.value}'")
        return answer

    def querythread(self) -> None:
        """Fetch data from the SA-MP server and feed it to clients via the
        proxy.

        PS: Runs indefinitely unless the `stop_thread` attribute is set to
        True.
        """
        socket.setdefaulttimeout(QUERY_TIMEOUT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stop_thread = False  # To control the loop from outside

        status_order: list[tuple[StatusType, str]] = [
            (StatusType.info, "info"),
            (StatusType.rules, "rules"),
            (StatusType.details, "detail"),
            (StatusType.clients, "clients"),
        ]

        while not self.stop_thread:
            if self.ping():
                for status, attribute in status_order:
                    setattr(server, attribute, self.send_server_query(status))
                    time.sleep(SHORT_SLEEP_DURATION)
            else:
                logging.error(
                    "Packet-proxy could not reach the samp server.. "
                    + "Trying again.."
                )
                time.sleep(RETRY_SLEEP_DURATION)

    def ping(self):
        pack = self.assemblePacket("p0101")
        self.sock.sendto(pack, (SAMP_SERVER_ADDRESS, SERVER_PORT))
        try:
            reply = self.sock.recv(1024)[10:]
            server.isonline = reply == b"p0101"
            return server.isonline
        except socket.timeout:
            return False

    def assemblePacket(self, type):
        PUBLIC_PORT_BYTES = SERVER_PORT.to_bytes(2, byteorder="little")
        packet = b"SAMP"
        packet += SAMP_SERVER_ADDRESS_BYTES
        packet += PUBLIC_PORT_BYTES
        packet += bytes(type, "utf-8")
        return packet

    def start(self):
        self.server.socket.settimeout(self.timeout)
        q = threading.Thread(target=self.querythread)
        q.daemon = True
        q.start()
        self.server.serve_forever()

    def stop(self):
        self.server.stop_thread = True
        # self.server.shutdown()

    def handle_external_packet(
        self, handler, sampserver: ServerStatus = server
    ):
        """When external clients query the server, this method is called.
        Depending on which data is requested, the reply is generated.
        """
        payload, _ = handler.request

        if not sampserver.isonline:
            logging.debug("Server is offline")
            return False
        if payload[4:8] != SAMP_SERVER_ADDRESS_BYTES:
            logging.debug("Server address does not match")
            return False
        if payload[10] not in b"pirdc":
            logging.debug("Invalid opcode received")
            return False

        data_lookup = {
            b"p": None,
            b"i": sampserver.info,
            b"r": sampserver.rules,
            b"d": sampserver.detail,
            b"c": sampserver.clients,
        }

        response_data = data_lookup.get(payload[10:11])
        if response_data is not None:
            self._send_packet(handler, payload, response_data)
            return True
        logging.debug("Ping packet received")
        return False

    def _send_packet(self, handler, payload, data):
        """Generate packet based on payload and data and send it to client."""
        client_address = handler.client_address
        if data is not None:
            packet = payload + data
        else:  # for ping packets
            packet = payload
        self.server.socket.sendto(packet, client_address)


def create_handler(func):
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                func(self)
            except Exception as e:
                print("An error occurred: %s" % (e,))
            func(self)

    return Handler


if __name__ == "__main__":
    print(
        "Proxy is listening on port",
        PROXY_PORT,
        "for SAMP server",
        SAMP_SERVER_ADDRESS,
        "using port",
        SERVER_PORT,
    )
    bind_address = (SAMP_SERVER_ADDRESS, PROXY_PORT)
    target_address = (SAMP_SERVER_LOCALHOST, SERVER_PORT)
    proxy = UDPServer(bind_address, target_address)
    proxy.start()
