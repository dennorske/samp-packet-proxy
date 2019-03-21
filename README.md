# samp-packet-proxy
A proxy that will throttle / filter UDP packages by reading the payload and frequency of them, before passing them over to the SA-MP server.

## Requirements for the system running it;
1. You need to be able to run python scripts on your host. That means; on your host system.
2. You need python 3(.7) installed

## How to use
1. Edit your server.cfg and set `port 7850`. This is what the proxy binds to the server with. Can be changed by altering `SERVER_PROXY_PORT` in the code.
2. also add: `bind 127.0.0.1` in server.cfg.
3. Make sure `PUBLIC_PORT`in the code matches the port you are using for your server. Set to 7777 by default.
4. Run the **pack-scan.py** file using `python3 pack-scan.py & bg`. Proxy is enabled.
5. Run the samp server (make sure it's bound to the right port)
6. Packets should now pass through servers internet-interface --> proxy server --> samp
7. They will also return through the proxy back to the client. TTL for the UDP server are 4s atm, can be adjusted down..



## To-do: 
*(Can someone do this? SA-MP master list is suffering and I am out of knowledge and time right now..)*
1. Create a rate limiter under the filter function - filter the packets from IP's and let them only request certain OP-codes with certain X miliseconds rate.
2. Get the packet filtering to work with all packets sent through. It should only filter SAMP packets 
3. Repack the packet going out from the proxy (to the server) so it contains the IP from the origin. Why? Because else all IP's ingame will show 127.0.0.1 and banning won't work. Please have a look at this: https://scapy.net/

## Known issues:
- If the python script returns an error: "Too many open files" 
      - Raise the ULIMIT on your linux distro - each UDP server in this code creates 1 open "file". If you get 2k packets per second, you can basically only have `timeout`in the code as 0.5 seconds. Default ULIMIT value on linux is usually 1024.
- Havent tested this in full scale yet so unaware of performance issues. Please report back.

## other
Please contribute as you wish, I will check for pull requests and so.
Big thanks to my community (xSF) and H20, Lilkaapa, Akira, Frxstrem for their amazing help and me bothering them so much.
Thanks to mum.


