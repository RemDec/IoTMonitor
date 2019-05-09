from src.net.netmap import *
from src.logging.eventsCenter import *
from modules.actives.nmapExplorer import *
from modules.actives.nmapPortDiscovery import *
import time

ev_center = EventsCenter()
netmap = Netmap(event_center=ev_center)

# Instantiating modules

nmapexplo = AModNmapExplorer(params=None, netmap=netmap)
nmap_ports = AModNmapPortDisc(params=None, netmap=netmap)
mods = [nmapexplo, nmap_ports]

# Before any mod exec

print(netmap.detail_str(level=3))

# Launching modules
print("#### Launching scanning modules ####")
for mod in mods:
    mod.launch()

# After

for mod in mods:
    while mod.get_nbr_running() > 0:
        time.sleep(5)

print("#### Netmap after mods exec ####")
print(netmap.detail_str(level=3))

