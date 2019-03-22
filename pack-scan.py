#!/usr/bin/env python3

import socketserver
import socket
import threading
import time

SERVER_PROXY_PORT = 7850
PUBLIC_PORT = 7777
PUBLIC_PORT_BYTES = PUBLIC_PORT.to_bytes(2, byteorder='little')
SAMP_SERVER_ADDRESS = "-INSERT PUBLIC IP HERE"
SAMP_SERVER_ADDRESS_BYTES = socket.inet_aton(SAMP_SERVER_ADDRESS)

class UDPProxy:
  def __init__(self, bind_address, target_address, internal_host = "127.0.0.1", num_ports = 1000, timeout = 4.0): #ulimit?
    self.target_address = target_address
    self.timeout = timeout

    self.server = socketserver.UDPServer(bind_address, create_handler(self.handle_external_packet))

    self.internal_servers = []
    for i in range(num_ports):
      internal_server = socketserver.UDPServer((internal_host, 0), create_handler(self.handle_internal_packet))

      internal_server.client_address = None
      internal_server.last_used = None

      self.internal_servers.append(internal_server)

  def start(self):
    for internal_server in self.internal_servers:
      thread = threading.Thread(target = internal_server.serve_forever)
      thread.daemon = True
      thread.start()

    self.server.serve_forever()

  def stop(self):
    self.server.shutdown()

  def filter(self, payload, client_address): 
  #perhaps add some mechanism that filters the packages so that one IP can only request once ever x ms. 
  #This would be very beneficial for the query mechanism to avoid having to respond to everything.
   
    if len(payload) <4: #because the packet size varies - can't really determine the defaults here.
      return False
      # if payload[2:3] != b't':
      #   print("Too short %r" % (payload,))
      #   return False  
      # else:
      #   return True

    if payload[0:4] != b'SAMP': #mainly interested in these packages and not the other ones..
      #print("Not SAMP")
      return False

    if payload[4:8] != SAMP_SERVER_ADDRESS_BYTES:
      #print("Unknown host %r %r" % (socket.inet_ntoa(payload[4:8]), SAMP_SERVER_ADDRESS))
      return False 

    if payload[10] not in b'pirdc': #opcodes defined here: https://wiki.sa-mp.com/wiki/Query/Request#Opcodes
     # print("Wrong opcode %r" % (payload[10]))
      return False  
    return True

  def handle_external_packet(self, handler):
    (payload, socket) = handler.request
    client_address = handler.client_address
    #print("Got external packet %r from %r on %r len: %r" % (payload, client_address, socket.getsockname(), len(payload)))
    if not self.filter(payload, client_address):
      #print("debug 1 filter")
      return
    internal_socket = self.get_internal_socket(client_address)
    internal_socket.sendto(payload, self.target_address)

   def handle_internal_packet(self, handler):
    (payload, socket) = handler.request
    #print("internal pack")
    client_address = handler.client_address
    if client_address != self.target_address:
      return

    server_port = socket.getsockname()[1]

    #print("Got internal packet %r from %r on %r" % (payload, client_address, socket.getsockname()))

    external_client_address = self.get_client_address(server_port)
    self.server.socket.sendto(payload, external_client_address)
    #print("Sent internal packet further; %r to %r" % (payload, external_client_address))
  def get_internal_socket(self, client_address): #find free socket internally
    now = time.time()
    #print("internal socket check")
    for internal_server in self.internal_servers:
      if internal_server.client_address is not None and internal_server.client_address == client_address:
        internal_server.last_used = now
        return internal_server.socket

    for internal_server in self.internal_servers:
      if internal_server.client_address is None or internal_server.last_used is None or now - internal_server.last_used > self.timeout:
        internal_server.client_address = client_address
        internal_server.last_used = now
        return internal_server.socket

    raise Exception('No available internal socket')

  def get_client_address(self, internal_port):
    for internal_server in self.internal_servers:
      if internal_server.server_address[1] == internal_port:
        return internal_server.client_address

    raise Exception('Got response on unused internal socket')

def create_handler(func):
  class Handler(socketserver.BaseRequestHandler):
    def handle(self):
      try:
        func(self)
      except Exception as e:
        print("An error occured: %s" % (e,))
  return Handler

if __name__ == '__main__':
  bind_address = ("0.0.0.0", PUBLIC_PORT) 
  target_address = ("127.0.0.1", SERVER_PROXY_PORT)
  proxy = UDPProxy(bind_address, target_address)
  proxy.start()
  # UDPProxy.start(proxy)
