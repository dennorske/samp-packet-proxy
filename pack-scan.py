#!/usr/bin/env python3


#
#    iptables -t nat -A PREROUTING -p udp --dport 7777 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7778
#    iptables -I INPUT -p udp --dport 7778 -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP
#    
#
#    make sure ports above match ports below
#    
#    Basicly all query packets get directed to this script, and sync packets are left untouched
#


import array
import socket
import socketserver
import threading
import time

####################### MUST BE CONFIGURED ##########################
SERVER_PORT = 7777 #Assuming your samp server runs on this port
PROXY_PORT = 7778 #Assuming no other servers are running on this one, as it will be taken by the code.
SAMP_SERVER_ADDRESS = "YOUR SERVER IP" #Public ip
#####################################################################

SAMP_SERVER_LOCALHOST = "127.0.0.1" #Edit this if you run this on a different server than the samp server
SAMP_SERVER_ADDRESS_BYTES = socket.inet_aton(SAMP_SERVER_ADDRESS)

info = " "
rules = " "
clients = " "
detail = " "
isonline = False


iplogpos = 0
iplog = []


class UDPServer:
  def __init__(self, bind_address, target_address, internal_host = "127.0.0.1", timeout = 0.1): #ulimit?
    self.target_address = target_address
    self.timeout = timeout

    self.server = socketserver.UDPServer(bind_address, create_handler(self.handle_external_packet))

  def querythread(self):

    global info
    global rules
    global clients
    global detail
    global isonline

    socket.setdefaulttimeout(1)
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
      
      if self.ping():

        packet = self.assemblePacket("i")
        self.sock.sendto(packet.encode(), (SAMP_SERVER_LOCALHOST, SERVER_PORT))
        info = self.sock.recv(1024)[11:]


        packet = self.assemblePacket("r")
        self.sock.sendto(packet.encode(), (SAMP_SERVER_LOCALHOST, SERVER_PORT))
        rules = self.sock.recv(1024)[11:]


        packet = self.assemblePacket("d")
        self.sock.sendto(packet.encode(), (SAMP_SERVER_LOCALHOST, SERVER_PORT))
        detail = self.sock.recv(1024)[11:]

        packet = self.assemblePacket("c")
        self.sock.sendto(packet.encode(), (SAMP_SERVER_LOCALHOST, SERVER_PORT))
        clients = self.sock.recv(1024)[11:]

        isonline = True

      else:
        isonline = False
        print("Server unable to be reached")
      time.sleep(2)

  def ping(self):

    pack = self.assemblePacket("p0101")
    self.sock.sendto(pack.encode(), (SAMP_SERVER_LOCALHOST, SERVER_PORT))
    try:
      reply = self.sock.recv(1024)[10:]
      if reply == b'p0101':
        return True
      else:
        return False
    except socket.timeout:
      return False
      
  def assemblePacket(self, type):
    ipSplit = str.split(SAMP_SERVER_LOCALHOST, '.')

    packet = 'SAMP'
    packet += chr(int(ipSplit[0]))
    packet += chr(int(ipSplit[1]))
    packet += chr(int(ipSplit[2]))
    packet += chr(int(ipSplit[3]))
    packet += chr(SERVER_PORT & 0xFF)
    packet += chr(SERVER_PORT >> 8 & 0xFF)
    packet += type

    return packet

  def start(self):
    q = threading.Thread(target=self.querythread)
    q.daemon = True
    q.start()
    self.server.serve_forever()
    self.server.settimeout(0.1)


  def stop(self):
    self.server.shutdown()

  def handle_external_packet(self, handler):
    (payload, socket) = handler.request
    client_address = handler.client_address

    if isonline == False: #server is offline
      return False

    if payload[4:8] != SAMP_SERVER_ADDRESS_BYTES: #Payload with IP bytes are not matching your public IP
      print("Unknown host %r %r" % (socket.inet_ntoa(payload[4:8]), SAMP_SERVER_ADDRESS))
      return False 
    
    if payload[10] not in b'pirdc': #opcodes defined here: https://wiki.sa-mp.com/wiki/Query/Request#Opcodes
      print("Wrong opcode %r" % (payload[10]))
      return False 

    if payload[10] in b'p': #Ping packets are just sent back to the client 
      client_address = handler.client_address
      self.server.socket.sendto(payload, client_address)
      return True

    elif payload[10] in b'i':

      client_address = handler.client_address
      self.server.socket.sendto(payload+info, client_address)
      return True
      

    elif payload[10] in b'r': 
      #print(rules)
      client_address = handler.client_address
      self.server.socket.sendto(payload+rules, client_address)
      return True
      

    elif payload[10] in b'd':
      #print(detail)
      client_address = handler.client_address
      self.server.socket.sendto(payload+detail, client_address)
      return True
      

    elif payload[10] in b'c':
      #print(clients)
      client_address = handler.client_address
      self.server.socket.sendto(payload+clients, client_address)
      return True 
    return

def create_handler(func):
  class Handler(socketserver.BaseRequestHandler):
    def handle(self):
      try:
        func(self)
      except Exception as e:
        print("An error occured: %s" % (e,))
  return Handler

if __name__ == '__main__':
  print("Listening on port", PROXY_PORT, "for server",SAMP_SERVER_ADDRESS,"on port",SERVER_PORT)
  bind_address = ("0.0.0.0", PROXY_PORT) 
  target_address = ("127.0.0.1", SERVER_PORT)
  proxy = UDPServer(bind_address, target_address)
  proxy.start()
