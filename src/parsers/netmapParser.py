from lxml import etree
from lxml.builder import E
from src.net.netmap import Netmap
from src.net.virtualInstance import VirtualInstance, PortTable
from src.parsers.eventParser import event_to_XML, XML_to_event
from src.utils.filesManager import get_dflt_entry


# --- Translating netmap components to XML and writing it ---

def vi_to_XML(virt_inst, mapid):
    main = E.mainfields(virt_inst.used_fields())
    div = E.divfields(virt_inst.used_div_fields())
    ports = E.portstable()
    table = virt_inst.get_ports_table()
    ports_elmts = []
    for portnum in table.list_ports():
        maininfos, divinfos = table.get_infos(portnum, as_dicts=True)
        ports_elmts.append(E.port(E.maininfos(maininfos), E.divportinfos(divinfos), portnum=str(portnum)))
    ports.extend(ports_elmts)
    return E.virtinst(main, div, ports, mapid=mapid, usercreated=str(virt_inst.user_created))


def saved_events_to_XML(svd_events):
    svd_elmt = E.savedevents()
    for mapid, event_list in svd_events.items():
        events_elmt = E.vievents(mapid=mapid)
        events_elmt.extend([event_to_XML(event) for event in event_list])
        svd_elmt.append(events_elmt)
    return svd_elmt


def netmap_to_XML(netmap):
    # Computing XML elements from VI instances
    vi_elmts = []
    inst_elmt = E.instances()
    for mapid, vi in netmap.map.items():
        vi_elmts.append(vi_to_XML(vi, mapid))
    inst_elmt.extend(vi_elmts)
    # Retrieving events associated with VI and getting their XML element repr.
    svdevents_elmt = saved_events_to_XML(netmap.svd_events)
    # Aggregating both in one super netmap element
    netmap_elmt = E.netmap(inst_elmt, svdevents_elmt)
    return netmap_elmt


def write_netmap_XML(netmap, filepath=None):
    if filepath is None:
        filepath = get_dflt_entry('last_netmap')
    tree = etree.ElementTree(E.xmlsave(netmap_to_XML(netmap)))
    tree.write(filepath, pretty_print=True, xml_declaration=True)


# --- Parse XML files to build netmap elements instances ---

def XML_to_vi(vi_elmt):
    mapid = vi_elmt.get('mapid')
    user_created = bool(vi_elmt.get('usercreated', False))
    mainfields = vi_elmt.find('mainfields')
    mac, ip, hostname = mainfields.get('mac'), mainfields.get('ip'), mainfields.get('hostname')
    div = vi_elmt.find('divfields').attrib
    table = PortTable()
    for port_elmt in vi_elmt.find('portstable').findall('port'):
        portnum = int(port_elmt.get('portnum'))
        port_infos = port_elmt.find('maininfos').attrib
        port_div_infos = port_elmt.find('divportinfos').attrib
        port_infos.update(port_div_infos)
        table.set_port(portnum, port_infos)
    new_vi = VirtualInstance(mac=mac, ip=ip, hostname=hostname, div=div, ports=table, user_created=user_created)
    return mapid, new_vi


def XML_to_saved_events(svd_events_elmt):
    svd_events = {}
    for events_elmt in svd_events_elmt.findall('vievents'):
        mapid = events_elmt.get('mapid')
        events_for_vi = []
        for event_elmt in events_elmt.getchildren():
            events_for_vi.append(XML_to_event(event_elmt))
        svd_events[mapid] = events_for_vi
    return svd_events


def XML_to_netmap(netmap_elmt, event_center=None):
    netmap = Netmap(event_center=event_center)
    instances_elmt = netmap_elmt.find('instances')
    saved_events_elmt = netmap_elmt.find('savedevents')
    for vi_elmt in instances_elmt.findall('virtinst'):
        mapid, vi = XML_to_vi(vi_elmt)
        netmap.add_VI(vi, given_mapid=mapid)
    netmap.svd_events = XML_to_saved_events(saved_events_elmt)
    return netmap


def parse_netmap_XML(filepath=None, event_center=None):
    if filepath is None:
        filepath = get_dflt_entry('last_netmap')
    with open(filepath, 'r') as f:
        tree = etree.parse(f)
        netmap = XML_to_netmap(tree.getroot().find('netmap'), event_center=event_center)
        return netmap


if __name__ == '__main__':
    from src.logging.eventsCenter import EventsCenter
    netmap = Netmap(event_center=EventsCenter())

    netmap.create_VI(mapid='VirtInst1', mac='B6-E3-5E-7A-C1-D6', ip='192.168.0.3', hostname='wifiCam')
    netmap.create_VI(mapid='VirtInst2', mac='BB-E5-BA-6F-7E-2A', ip='192.168.0.4', user_created=True)
    netmap.create_VI(mapid='VirtInst3', mac='31-E7-FA-9C-6C-FC', ip='192.168.0.5',
                     div={'uptime': '1245s', 'rate': '500kbps'})
    ports = PortTable({53: ('domain', 'TCP', 'open'), 80: ('http', 'TCP', 'open'),
                       5060: ('sip', 'TCP', 'open'), 49152: ('unknwown', 'UDP', 'open')})
    netmap.create_VI(mapid='homemodem', mac='5A-82-CB-48-47-C6', ip='192.168.0.100', user_created=True,
                     div={'clients': 'VirtInst1 VirtInst2'}, ports=ports)

    netmap.register_threat('scanmodule1', mapid='VirtInst1', msg='exploit detected for this device :CVE-15559.56.23')
    netmap.register_threat('scanmodule1', level=4, mapid='VirtInst2',
                           msg='Several exploitx detected for this device :CVE-40000.10.10, CVE-40000.21.3',
                           patch='Look at update from manufacturer : https://www.samsung.com/be_fr/')
    netmap.register_modif('IP field', obj_type='virt_inst', obj_id='VirtInst1', modificator='scanmodule2',
                          old_state='192.168.0.3', new_state='192.168.0.9')
    netmap.register_modif('ports table', obj_type='virt_inst', obj_id='homemodem', modificator='scanmodule2',
                          new_state='+ entry 9000: (cslistener, TCP, open)')

    print("### Netmap to write as XML ###")
    print(netmap.detail_str(level=2))
    print("### Converting to XML ###")
    print(etree.tostring(netmap_to_XML(netmap), pretty_print=True).decode())
    write_netmap_XML(netmap, filepath=get_dflt_entry('div_outputs', suffix='testNetmapXML.xml'))
    print("### netmap written in tests/test_outputs/testNetmap.xml ###")

    print("### reloading netmap from file ###")
    new_netmap = parse_netmap_XML(filepath=get_dflt_entry('div_outputs', suffix='testNetmapXML.xml'))
    print(new_netmap.detail_str(level=2))
    print("### compared to original ###")
    print(netmap.detail_str(level=2))