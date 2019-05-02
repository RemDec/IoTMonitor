from src.net.virtualInstance import *
from src.utils.misc_fcts import str_multiframe


class Netmap:

    def __init__(self, map=None, event_center=None):
        self.map = {} if map is None else map
        self.event_center = event_center

    def add_VI(self, vi, given_mapid=None):
        mapid = self.get_unique_id(given_mapid)
        self.map[mapid] = vi

    def remove_VI(self, mapid):
        self.map.pop(mapid)

    def create_VI(self, mapid=None, append_netmap=True,
                  mac=None, ip=None, hostname=None, div=None, ports=None, user_created=False):
        vi = VirtualInstance(mac=mac, ip=ip, hostname=hostname, div=div, ports=ports, user_created=user_created)
        if append_netmap:
            self.add_VI(vi, given_mapid=mapid)
        return mapid, vi

    def get_events_for_vi(self, mapid, target='all'):
        vi = self.get_VI(mapid)
        if self.event_center is None or vi is None:
            return None
        find_fct = lambda event: event.rel_to_vi() == mapid
        corresp_threats = self.event_center.filter_events(target=target, filter_fct=find_fct)
        return corresp_threats

    def get_threats_for_vi(self, mapid):
        return self.get_events_for_vi(mapid, target='threats')

    def get_modifs_for_vi(self, mapid):
        return self.get_events_for_vi(mapid, target='modifs')

    def get_VI(self, mapid):
        return self.map.get(mapid)

    def get_VI_mapids(self, filter_fct=lambda vi_inst: True):
        ids = []
        for mapid in self.map:
            if filter_fct(self.get_VI(mapid)):
               ids.append(mapid)
        return ids

    def get_similar_VI(self, mac=None, ip=None, hostname=None, div={}):
        for mapid in self.map:
            vi = self.map[mapid]
            if vi.repr_same_device(mac, ip, hostname, div):
                return mapid

    def check_unique_id(self, mapid):
        return not(mapid in self.map)

    def get_unique_id(self, mapid=None):
        mapid = mapid if mapid is not None else f"device{len(self.map)}"
        if self.check_unique_id(mapid):
            return mapid
        i = 2
        new_mapid = mapid + str(i)
        while not self.check_unique_id(new_mapid):
            i += 1
            new_mapid = mapid + str(i)
        return new_mapid

    def vi_frame_str(self, mapid, max_char=25):
        vi = self.get_VI(mapid)
        header = f" {mapid} [state] "
        l = max(max_char, len(header))
        cut = lambda s:s if len(s)<l else s[:l]
        s = header + '\n' + '='*l + '\n'
        s += cut(f" MAC: {vi.get_mac()}") + '\n'
        s += cut(f" IP: {vi.get_ip()}") + '\n'
        s += cut(f" Hostname:{vi.get_hostname()}") + '\n'
        ports = vi.get_ports_table().str_ports_list("Ports table:\n").split('\n')
        if len(ports) == 0:
            s += f"  < empty ports table >\n"
        s += '\n'.join([cut(portline) for portline in ports])
        for field, val in vi.used_div_fields(keep_val=True):
            s += cut(f" {field}: {val}") + '\n'
        return str_lines_frame(s[:-1] if s[-1] == '\n' else s)

    def detail_str(self, level=0):
        s = f"Netmap maintaining {len(self.map)} virtual instances" \
            f"{'' if self.event_center is None else 'and ref to an EventCenter'}\n"
        if level == 0:
            return s + ', '.join(self.get_VI_mapids()) + '\n'
        elif level == 1:
            for mapid, vi in self.map.items():
                s += f"   <<<[{mapid}]>>>\n{vi.detail_str(1)}"
            return s
        else:
            vi_frames = [self.vi_frame_str(mapid) for mapid in self.get_VI_mapids()]
            return s + str_multiframe(vi_frames)

    def __str__(self):
        return self.detail_str()


if __name__ == '__main__':
    ports = {80: ("HTTP", "TCP", "open")}
    table = PortTable(ports)
    table.set_port(631, ("ipp", "TCP", "closed"))
    div_fields = {'manufacturer': "Cisco", 'model': "IPSecCam_HX-8655-001.69", 'other': "Mean trafic rate:500kbps"}
    vi = VirtualInstance(mac="50:B7:C3:4F:BE:8C", ip="192.168.1.1", hostname="hostnamevi",
                         ports=ports, user_created=True, div=div_fields)

    vi2 = VirtualInstance(mac="86:EE:EE:12:B2:6A", hostname="router")
    netmap = Netmap()
    netmap.add_VI(vi, given_mapid="testdevice")
    netmap.add_VI(vi, given_mapid="testdevice2")
    netmap.add_VI(vi2)
    #print(netmap.vi_frame_str("testdevice"))
    print(netmap.detail_str(level=2))