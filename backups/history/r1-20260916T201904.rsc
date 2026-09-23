# 2026-09-16 20:19:00 by RouterOS 7.19.4
# system id = GWVYAJfO2ZO
#
/interface ethernet
set [ find default-name=ether1 ] disable-running-check=no
/port
set 0 name=serial0
/ip dhcp-client
add interface=ether1
/system identity
set name=r1-lab-demo
