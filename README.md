# samp-packet-proxy
~~A proxy that will throttle / filter UDP packages by reading the payload and frequency of them, before passing them over to the SA-MP server.~~
A proxy that querys and runs along side a sa:mp server, caches the result, then when clients query the server, it sends the cached results. Amazing.


## Requirements for the system running it;
1. You need to be able to run python scripts on your host. That means; on your host system.
2. You need python 3(.7) installed
3. You need iptables
4. You need not to ask nick or denNorske how to run this 37 million times

## How to use
This how too implies that your server port is `7777`, and your proxy port is `7778` and that your a somewhat familiar with python
1. Edit pack-scan.py and change `SAMP_SERVER_ADDRESS = "YOUR SERVER IP"` to your servers public ip
2. Edit `SERVER_PORT = 7777` to match your servers public port
3. Edit `PROXY_PORT = 7778` to whatever non used port you want
4. Apply following iptable rules. Make sure to edit ports accordingly.
    `iptables -t nat -A PREROUTING -p udp --dport 7777 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7778` This rule routes all query packets on port 7777, to port 7778.
    `iptables -I INPUT -p udp --dport 7778 -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP` This firewall rule is a rate liming rule that limits querys per second to prevent other bad things from happening
5. Run the proxy with `python3 pack-scan.py`
6. Profit?




## To-do: 
*(Can someone do this? SA-MP master list is suffering and I am out of knowledge and time right now..)*
1. Create a rate limiter under the filter function - filter the packets from IP's and let them only request certain OP-codes with certain X miliseconds rate.
2. Get the packet filtering to work with all packets sent through. It should only filter SAMP packets 
3. Repack the packet going out from the proxy (to the server) so it contains the IP from the origin. Why? Because else all IP's ingame will show 127.0.0.1 and banning won't work. Please have a look at this: https://scapy.net/

## Known issues:
- If the python script returns an error: "Too many open files" 
      - Raise the ULIMIT on your linux distro - each UDP server in this code creates 1 open "file". If you get 2k packets per second, you can basically only have `timeout`in the code as 0.5 seconds. Default ULIMIT value on linux is usually 1024.
- ~~Havent tested this in full scale yet so unaware of performance issues. Please report back.~~ It works

## other
Please contribute as you wish, I will check for pull requests and so.
Big thanks to my community (xSF) and H20, Lilkaapa, Akira, Frxstrem for their amazing help and me bothering them so much.
Thanks to mum.
Thanks sweet baby jesus for the doritos and mountain dew that helped me make this possible. Hallelujah brutha, amen!


