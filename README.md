# samp-packet-proxy
A proxy that querys and runs along side a sa:mp server, caches the result, then when clients query the server, it sends the cached results. Prevents SA-MP servers being overwhelmed by UDP floods and appear offline.
![Infographic](http://i.imgur.com/D3Uzmri.png)

## Requirements for the system running it
1. You need to be able to run python scripts on your host. That means; on your host system. If you don't have a VPS there is no need to continue. 
2. You need python 3(.7) installed
3. You need iptables
4. You need not to ask nick or denNorske how to run this 37 million times

## How to use
This how too implies that your server port is `7777`, and your proxy port is `7778` and that your a somewhat familiar with python. If not, *change this* accordingly.
1. Edit pack-scan.py and change `SAMP_SERVER_ADDRESS = "YOUR SERVER IP"` to your servers public ip
2. Edit `SERVER_PORT = 7777` to match your servers public port
3. Edit `PROXY_PORT = 7778` to whatever non used port you want
4. Apply following iptable rules. Make sure to edit ports accordingly.
    `iptables -t nat -A PREROUTING -p udp --dport 7777 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7778` This rule routes all query packets on port 7777, to port 7778.
    `iptables -I INPUT -p udp --dport 7778 -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP` This firewall rule is a rate liming rule that limits querys per second to prevent other bad things from happening
5. `iptables -t nat -A PREROUTING -p udp --dport 7777 -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7777` This rule make sure that internal packets find their way between the server and proxy. 
6. Run the proxy with `python3 pack-scan.py`
7. Profit?


## To-do: 
- Create a Server plugin that could handle this easier for people without VPS's. 

## Known issues:
It works, tested on multiple servers already

## Credits and praise
Please contribute as you wish, pull requests are preffered from separate branches.
Big thanks to my community (xSF) and H20, Lilkaapa, Akira, Frxstrem for their amazing help and me bothering them so much.
Thanks to mum.

Thanks sweet baby jesus for the doritos and mountain dew that helped me make this possible. Hallelujah brutha, amen!


