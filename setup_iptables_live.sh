#!/bin/sh

iptables -t nat -A PREROUTING -p udp --dport $LIVE_SERVER_PORT -m string --algo bm --string 'SAMP' -j REDIRECT --to-port $LIVE_PROXY_PORT
iptables -I INPUT -p udp --dport $LIVE_PROXY_PORT -m string --algo bm --string 'SAMP' -m hashlimit ! --hashlimit-upto 10/sec --hashlimit-burst 15/sec --hashlimit-mode srcip --hashlimit-name query -j DROP
iptables -t nat -A PREROUTING -p udp --dport $LIVE_SERVER_PORT -s 127.0.0.1 -m string --algo bm --string 'SAMP' -j REDIRECT --to-port $LIVE_SERVER_PORT