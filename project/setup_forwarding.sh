iptables-legacy -t nat -A POSTROUTING -o wlan0 -j MASQUERADE &&

iptables-legacy -A FORWARD -i wlan0 -o LongG -m state --state RELATED,ESTABLISHED -j ACCEPT &&
iptables-legacy -A FORWARD -i LongG -o wlan0 -j ACCEPT
