#!/usr/bin/env python3


#    The current settings assume your server is running on port 7777
#
#    iptables -t nat -A PREROUTING -p udp --dport 7777 -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7777
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
import binascii
####################### MUST BE CONFIGURED ##########################
SERVER_PORT = os.getenv('LIVE_SERVER_PORT', 7777) #Assuming your samp server runs on this port
PROXY_PORT = os.getenv('LIVE_PROXY_PORT', 7778) #Assuming no other servers are running on this one, as it will be taken by the code.
SAMP_SERVER_ADDRESS = os.getenv('LIVE_SAMP_SERVER_ADDRESS', "68.183.239.18") #Public ip set this to the ip you using in bind in your server.cfg
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
  def __init__(self, bind_address, target_address, internal_host = "127.0.0.1", timeout = 0.3): #ulimit?
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
        self.sock.sendto(packet, (SAMP_SERVER_ADDRESS, SERVER_PORT))
        info = self.sock.recv(1024)[11:]

        packet = self.assemblePacket("r")
        self.sock.sendto(packet, (SAMP_SERVER_ADDRESS, SERVER_PORT))
        rules = self.sock.recv(1024)[11:]

        packet = self.assemblePacket("d")
        self.sock.sendto(packet, (SAMP_SERVER_ADDRESS, SERVER_PORT))
        detail = self.sock.recv(1024)[11:]

        packet = self.assemblePacket("c")
        self.sock.sendto(packet, (SAMP_SERVER_ADDRESS, SERVER_PORT))
        clients = self.sock.recv(1024)[11:]

        isonline = True

        time.sleep(2)
      else:
        isonline = False
        print("Server unable to be reached...")

  def ping(self):

    pack = self.assemblePacket("p0101")
    self.sock.sendto(pack, (SAMP_SERVER_ADDRESS, SERVER_PORT))
    try:
      reply = self.sock.recv(1024)[10:]
      if reply == b'p0101':
        return True
      else:
        return False
    except socket.timeout:
      return False
      
  def assemblePacket(self, type):
    PUBLIC_PORT_BYTES = SERVER_PORT.to_bytes(2, byteorder='little')
    packet = b'SAMP'
    packet += SAMP_SERVER_ADDRESS_BYTES
    packet += PUBLIC_PORT_BYTES
    packet += bytes(type, 'utf-8')
    return packet



  def start(self):
    q = threading.Thread(target=self.querythread)
    q.daemon = True
    q.start()
    self.server.serve_forever()
    self.server.socket.settimeout(self.timeout)


  def stop(self):
    self.server.shutdown()

  def handle_external_packet(self, handler):
    (payload, socket) = handler.request
    client_address = handler.client_address
    if(isonline == False):
      return
    if payload[4:8] != SAMP_SERVER_ADDRESS_BYTES: #Payload with IP bytes are not matching your public IP
      return False 
    
    if payload[10] not in b'pirdc': #opcodes defined here: https://wiki.sa-mp.com/wiki/Query/Request#Opcodes
      return False 

    if payload[10] in b'p': #Ping packets are just sent back to the client 
      client_address = handler.client_address
      self.server.socket.sendto(payload, client_address)
      return True

    elif payload[10] in b'i':

      client_address = handler.client_address
      argument = payload+info
      self.server.socket.sendto(argument, client_address)
      return True
      

    elif payload[10] in b'r': 
      client_address = handler.client_address
      argument = payload+rules
      self.server.socket.sendto(argument, client_address)
      #print(binascii.hexlify(payload+rules))
      return True
      

    elif payload[10] in b'd':
      client_address = handler.client_address
      argument = payload+detail
      self.server.socket.sendto(argument, client_address)
      return True
      

    elif payload[10] in b'c':
      client_address = handler.client_address
      argument = payload+clients
      self.server.socket.sendto(argument, client_address)
      #thebytes=payload+clients
      #print(len(payload+clients))
      return True 
    return

def create_handler(func):
  class Handler(socketserver.BaseRequestHandler):
    def handle(self):
      try:
        func(self)
      except Exception as e:
        print("An error occurred: %s" % (e,))
      func(self)
  return Handler

if __name__ == '__main__':
  print("Listening on port", PROXY_PORT, "for server",SAMP_SERVER_ADDRESS,"on port",SERVER_PORT)
  bind_address = (SAMP_SERVER_ADDRESS, PROXY_PORT) 
  target_address = ("127.0.0.1", SERVER_PORT)
  proxy = UDPServer(bind_address, target_address)
  proxy.start()
