from src.logging.logger_setup import *
from src.net.netmap import *


def fill_center(center):
    center.register_threat("mymodule", 3, "netmapVI_id", "Alert raised by module!")
    center.register_modif("instance MAC field", "virt_inst", "myinst_id", "scanmodule", "unknown", "1C:39:47:12:AA:B3")
    center.register_threat("second_module", 5, "target_mapid", "Very SERIOUS alert!")
    center.register_threat("mymodule", 1, "target_mapid", "Same module raised easy alert")
    center.register_modif("'target' module parameter", "module", None, "app user", "192.168/16", "10.102/16")
    center.register_modif("VI hostname field", obj_type='virt_inst', obj_id='target_mapid', modificator='user',
                          old_state='old_hostname', new_state='NEW_HOSTNAME')


l = CustomLoggerSetup()
center = EventsCenter(logging.getLogger("debug"))
fill_center(center)
print(center)
print("\n\n##### all event ordered ####\n")
for event in center.get_ordered_events():
    print(event)


# Testing cooperation with network map
netmap = Netmap(event_center=center)
netmap.create_VI(mapid='target_mapid', ip='192.168.0.1', user_created=True)

threats = netmap.get_threats_for_vi(mapid='target_mapid')
modifs = netmap.get_modifs_for_vi(mapid='target_mapid')
all_events = netmap.get_events_for_vi(mapid='target_mapid')
print("\n##### Found registered threats for an iv mapid ('target_mapid') #####\n")
for threat in threats:
    print(threat)

print("\n##### Found registered modifs for an iv mapid ('target_mapid')#####\n")
for modif in modifs:
    print(modif)


print("\n##### All events for an iv mapid ('target_mapid') #####\n")
for event in all_events:
    print(event)