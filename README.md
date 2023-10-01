# SA-MP query proxy/cache

This repository houses the SA-MP (San Andreas Multiplayer) query cache script, designed to act as a mediator between SA-MP Clients and the SA-MP Server. The main purpose is to filter, manage, and forward client requests, optimizing the interaction for safety, efficiency, and performance. SA-MP's query mechanism is single threaded, and when overloaded (due to attacks), it shows offline for clients. This cache will utilize python to help accelerate the rate at which the packets are returned, helping servers appear online again.

## Diagram

```
+-----------------------+     +-------------------+     +-----------------------+
|                       |     |                   |     |                       |
|     SA-MP Client      |<--->|    UDP Proxy      |<--->|     SA-MP Server      |
| (Game/Query Client)   |     | (pack-scan.py)    |     | (Game/Query Server)   |
|                       |     |                   |     |                       |
+-----------------------+     +-------------------+     +-----------------------+
          |                             |                          |
          |                             |                          |
          v                             v                          v
     Sends Game/                   Filters and                 Accepts/
    Query Requests               Forwards Requests          Sends Responses
```

## What does it do?
1. It does increases the rate at which the query mechanism can respond, by accelerating the responses.
2. It hides the server behind the proxy, so only the proxy can ask "hey what is your status" - and then the proxy spreads this information to the clients when they ask for information. The proxy can do this much much quicker than the SA-MP server is capable of.
3. It does this only at the server public port (e.g. 7777)
4. Avoids the single-threaded workload being too high on the sa-mp server

## What does it **not** do?
1. It does not protect you against DDoS attacks, it just "accelerates" the responses.
2. It does not protect anything but the query mechanism of SA-MP.
3. It does not block the traffic, as UDP packets can easily be spoofed, depending on ISP.

## Requirements
1. You need to be able to run python scripts on your host. If you don't have a VPS or a self managed host, you can not run this. 
2. You need python 3.7 (or above) installed.
3. You need iptables (or similar software for windows), because you need to redirect all traffic to the proxy, and then back to the client.
4. You need more than 1 processor thread on the host. We have been maxing out 1 thread on a intel 8700k with 3.5k pps.

## How to set up / start the proxy
Remember to change the values to your needs.
1. Edit `pack_scan.py` and change `SAMP_SERVER_ADDRESS = "123.123.123.123"` to your servers public ip
2. Edit `SERVER_PORT = 7777` to match your servers public port. Yes, the port you are currently using
3. Edit `PROXY_PORT = 7778` to use a free port on the host. The `pack_scan.py` will take this port.
4. Apply the following iptable rules. **Make sure to enter ports.** Replace "SERVER_PORT_HERE" and "PROXY_PORT_HERE" with the ports you use.

    ```bash
    iptables -t nat -A PREROUTING -p udp --dport SERVER_PORT_HERE -m string --algo bm --string 'SAMP' -j REDIRECT --to-port PROXY_PORT_HERE
    # This rule will route all incoming SAMP query packets meant for your SA-MP server to the port where the proxy script will reply.
    # Replace SERVER_PORT_HERE with your SA-MP server's port number and PROXY_PORT_HERE with the port number the proxy script will listen on.
    ```
        
    ```bash
    iptables -I INPUT -p udp --dport PROXY_PORT_HERE -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 3/sec --hashlimit-burst 7/sec --hashlimit-mode srcip --hashlimit-name query -j DROP
    # Replace PROXY_PORT_HERE with the port number the proxy script will listen on.
    # This rule ensures no individual IP can flood your server with excessive query requests.
    ```
    Please note that these rules are not permanent. If your host restarts, these rules needs to be applied again.
5. Run the proxy with `python3 pack_scan.py` - Alternatively, set up a systemd service.
 
## Removing IPTABLES rules:
Please replace `-A` (or `-I`) with `-D`. `-D` means "delete". Look at examples below. The ports has to match your setup! Replace "SERVER_PORT_HERE" and "PROXY_PORT_HERE". If you are unsure, you can also check what your existing rules are by checking `iptables-save` output in your terminal.
- `iptables -t nat -D PREROUTING -p udp --dport SERVER_PORT_HERE -m string --algo bm --string 'SAMP' -j REDIRECT --to-port PROXY_PORT_HERE`
- `iptables -D INPUT -p udp --dport PROXY_PORT_HERE -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP`
- `iptables -t nat -D PREROUTING -p udp --dport SERVER_PORT_HERE -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port SERVER_PORT_HERE` 

## Known issues:
Game-state and SACNR monitor queries are not responded correctly, causing graphs to not show or show incorrectly.

## Feedback and Contributions
If you have feedback, issues, or want to contribute to this project, please open an issue or submit a pull request. All contributions are welcome!