from src.net.netmap import *
from src.logging.eventsCenter import *
from modules.actives.nmapExplorer import *
import time

ev_center = EventsCenter()
netmap = Netmap(event_center=ev_center)

# Instantiating modules

nmapexplo = AModNmapExplorer(params=None, netmap=netmap)

# Before any mod exec

print(netmap.detail_str(level=3))

# Launching modules
print("#### Launching scanning modules ####")
nmapexplo.launch()

# After

time.sleep(10)
print("#### Netmap after mods exec ####")
print(netmap.detail_str(level=3))

