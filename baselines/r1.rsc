# 2026-09-16 20:56:58 by RouterOS 7.19.4
# system id = TGd4MuJNbgD
#
/interface ethernet
set [ find default-name=ether1 ] disable-running-check=no
/port
set 0 name=serial0
/ip dhcp-client
add interface=ether1
