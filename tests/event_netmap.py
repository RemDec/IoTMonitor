from src.logging.logger_setup import *
from src.net.netmap import *


def fill_netmap(netmap):
    netmap.create_vi(mapid='VirtInst1', mac='B6-E3-5E-7A-C1-D6', ip='192.168.0.3', hostname='wifiCam')
    netmap.create_vi(mapid='VirtInst2', mac='BB-E5-BA-6F-7E-2A', ip='192.168.0.4', user_created=True)
    netmap.create_vi(mapid='VirtInst3', mac='31-E7-FA-9C-6C-FC', ip='192.168.0.5',
                     div={'uptime': '1245s', 'rate': '500kbps'})
    ports = PortTable({53: ('domain', 'TCP', 'open'), 80: ('http', 'TCP', 'open'),
                       5060: ('sip', 'TCP', 'open'), 49152: ('unknwown', 'UDP', 'open')})
    netmap.create_vi(mapid='homemodem', mac='5A-82-CB-48-47-C6', ip='192.168.0.100', user_created=True,
                     div={'clients': 'VirtInst1 VirtInst2'}, ports=ports)


def register_events(netmap):
    netmap.register_threat('scanmodule1', mapid='VirtInst1', msg='exploit detected for this device :CVE-15559.56.23')
    netmap.register_threat('scanmodule1', level=4, mapid='VirtInst2',
                           msg='Several exploitx detected for this device :CVE-40000.10.10, CVE-40000.21.3',
                           patch='Look at update from manufacturer : https://www.samsung.com/be_fr/')
    netmap.register_modif('IP field', elmt_type='virt_inst', elmt_id='VirtInst1', modificator='scanmodule2',
                          old_state='192.168.0.3', new_state='192.168.0.9')
    netmap.register_modif('ports table', elmt_type='virt_inst', elmt_id='homemodem', modificator='scanmodule2',
                          new_state='+ entry 9000: (cslistener, TCP, open)')


log_setup = CustomLoggerSetup()
center = log_setup.get_event_center()
netmap = Netmap(event_center=center)
fill_netmap(netmap)
print("### After filling netmap ###\n", netmap.detail_str(level=1))
register_events(netmap)
print("### After registering events ###\n", netmap.detail_str(level=2))
events_vi1 = netmap.get_all_events_for_vi('VirtInst1')

print("### Retrieving saved events for 1 virtual instance ###\n\n")
for event in events_vi1:
    print("##Event:\n", event.detail_str(level=2))

