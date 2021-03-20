# SA:MP Packet Proxy
A proxy that querys and runs along side a SA:MP server, caches the result, then when clients query the server, it sends the cached results. Prevents SA-MP servers being overwhelmed by UDP floods and appear offline, because they can't respond quick enough.
![Infographic](https://pics.ducky.rocks/images/2020/04/20/Untitled-Diagram-2.png)

## What does it do?
1. It does increases the rate at which the query mechanism can respond, by accelerating the responses.
2. It hides the server behind the proxy, so only the proxy can ask "hey what is your status" - and then the proxy spreads this information to the clients when they ask for information. The proxy can do this much much quicker than the SA-MP server is capable of.
3. It does this only at the server public port (e.g. 7777)
4. Avoids the single-threaded workload being too high on the sa-mp server

## What does it not do?
1. It does not protect you against DDOS attacks, it just "Accelerates" the responses.
2. It does not protect any other thing than the query mechanism of SA-MP, meaning it can't protect against malicious traffic on other ports on the server
3. It does not block the traffic, as UDP packets are extremely easily spoofed.

## Requirements for the system running it
1. You need to be able to run python scripts on your host. That means; on your host system. If you don't have a VPS or a self managed host there is no need to continue. 
2. You need python 3(.7) installed
3. You need iptables / similar software for windows, because we need to redirect all traffic to the proxy, and then back to the client.
4. You need more than 1 processor thread on the host. We have been maxing out 1 thread on a 8700k with 3.5k packets per second.

## How to set up / start the proxy
PSST: Remember to change values to your needs.
1. Edit `pack-scan.py` and change `SAMP_SERVER_ADDRESS = "YOUR SERVER IP"` to your servers public ip
2. Edit `SERVER_PORT = 7777` to match your servers public port. Yes, the port you are currently using
3. Edit `PROXY_PORT = 7778` to whatever non used port you want. It has to be an unused port. Used for step "3" in the inforgraphic, and will be taken by the script.
4. Apply following iptable rules. Make sure to edit ports accordingly. Replace "SERVER_PORT_HERE" and "PROXY_PORT_HERE" with the ports you use.
    `iptables -t nat -A PREROUTING -p udp --dport SERVER_PORT_HERE -m string --algo bm --string 'SAMP' -j REDIRECT --to-port PROXY_PORT_HERE` 
    This rule routes all query packets on port 7777, to port 7778, where the script will do the filtering.
    `iptables -I INPUT -p udp --dport PROXY_PORT_HERE -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP` This firewall rule is a rate liming rule that limits querys per second. No need to respond to more than this per client.
5. `iptables -t nat -A PREROUTING -p udp --dport SERVER_PORT_HERE -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port SERVER_PORT_HERE` 
    This rule make sure that internal packets find their way between the server and proxy. (Returning from samp server). Do not replace `'SAMP'` - because, this is actually something we are looking for inside a packet. If you change that, the rule will fail.
6. Run the proxy with `python3 pack-scan.py`
6a. Set up systemd service if you want to easily stop and start the proxy. (Update coming soon to show how this can be done) 
7. Profit?
 
## Removing IPTABLES rules:
Please _replace_ `-A` (or `-I`) with `-D`. -D means "delete". Look at examples. The ports has to match your setup! Replace "SERVER_PORT_HERE" and "PROXY_PORT_HERE". You can also check what your existing rules are by checking `iptables-save` output in terminal.
- `iptables -t nat -D PREROUTING -p udp --dport SERVER_PORT_HERE -m string --algo bm --string 'SAMP' -j REDIRECT --to-port PROXY_PORT_HERE`
- `iptables -D INPUT -p udp --dport PROXY_PORT_HERE -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP`
- `iptables -t nat -D PREROUTING -p udp --dport SERVER_PORT_HERE -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port SERVER_PORT_HERE` 

## Known issues:
- ~Under load, script tends to stop working after approximately a week. You can set up a simple bash script to restart it automatically~ (Fixed March 19th 2021)
- game-state and SACNR monitor queries are not responded correctly, causing graphs to not show or show incorrectly.
- ~100+ players causes issues~ (Fixed March 19th 2021)

## Credits and praise
Please contribute as you wish, pull requests are preffered from separate branches.
Big thanks to my community (xSF) and H20, Lilkaapa, Akira, Frxstrem for their amazing help and me bothering them so much.


