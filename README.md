# samp-packet-proxy
A proxy that querys and runs along side a sa:mp server, caches the result, then when clients query the server, it sends the cached results. Prevents SA-MP servers being overwhelmed by UDP floods and appear offline.
![Infographic](https://pics.ducky.rocks/images/2020/04/20/Untitled-Diagram-2.png)

## What does it do?
1. It does increases the rate at which the query mechanism can respond, by accelerating the responses.
2. Iptables makes sure to limit the rate at which the host responds to 10/sec.
3. It hides the server behind the proxy, so only the proxy can ask "hey what is your status" - and then the proxy spreads this information to the clients when they ask for information.
4. It does this only at the server public port (e.g. 7777)
5. Avoids the single-threaded workload being too high on the sa-mp server

## What does it not do?
1. It does not protect you against DDOS attacks.
2. It does not protect any other thing than the query mechanism of SA-MP, meaning it can't protect against malicious traffic on other ports on the server
3. It does not block the traffic, as UDP packets are extremely easily spoofed

## Requirements for the system running it
1. You need to be able to run python scripts on your host. That means; on your host system. If you don't have a VPS or a self managed host there is no need to continue. 
2. You need python 3(.7) installed
3. You need iptables / similar software for windows.

## How to use
This part implies that your server port is `7777`, and your proxy port is `7778` and that your a somewhat familiar with python. If not, *change* the values below to your values.
1. Edit pack-scan.py and change `SAMP_SERVER_ADDRESS = "YOUR SERVER IP"` to your servers public ip
2. Edit `SERVER_PORT = 7777` to match your servers public port
3. Edit `PROXY_PORT = 7778` to whatever non used port you want. Used for step "3" in the inforgraphic.
4. Apply following iptable rules. Make sure to edit ports accordingly.
    `iptables -t nat -A PREROUTING -p udp --dport 7777 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7778` This rule routes all query packets on port 7777, to port 7778.
    `iptables -I INPUT -p udp --dport 7778 -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP` This firewall rule is a rate liming rule that limits querys per second. No need to respond to more than this.
5. `iptables -t nat -A PREROUTING -p udp --dport 7777 -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port 7777` This rule make sure that internal packets find their way between the server and proxy. (Returning from samp server) 
6. Run the proxy with `python3 pack-scan.py`
7. Profit?


## To-do: 
- Create a Server plugin that could handle this easier for people without VPS's. 

## Known issues:
- Under load, script tends to stop working after approximately a week. You can set up a simple bash script to restart it automatically
- game-state and SACNR monitor queries are not responded correctly, causing graphs to not show or show incorrectly.
- 100+ players causes issues

## Credits and praise
Please contribute as you wish, pull requests are preffered from separate branches.
Big thanks to my community (xSF) and H20, Lilkaapa, Akira, Frxstrem for their amazing help and me bothering them so much.


