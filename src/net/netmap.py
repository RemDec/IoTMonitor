from src.net.virtualInstance import *
from src.logging.modifEvent import *
from src.logging.threatEvent import *
from src.logging.eventsCenter import EventsCenter
from src.utils.misc_fcts import str_multiframe


class Netmap:

    def __init__(self, map=None, event_center=None):
        self.map = {} if map is None else map
        self.event_center = event_center if event_center is not None else EventsCenter()
        self.svd_events = {}

    # ----- Interactions with the network map maintaining Virtual Instances -----

    def add_VI(self, vi, given_mapid=None):
        mapid = self.get_unique_id(given_mapid)
        self.map[mapid] = vi
        return mapid

    def remove_VI(self, mapid):
        self.map.pop(mapid)

    def clear(self):
        self.map = {}
        self.svd_events = {}

    def create_VI(self, mapid=None, append_netmap=True, create_event=False,
                  mac=None, ip=None, hostname=None, div=None, ports=None, user_created=False):
        vi = VirtualInstance(mac=mac, ip=ip, hostname=hostname, div=div, ports=ports, user_created=user_created)
        if append_netmap:
            mapid = self.add_VI(vi, given_mapid=mapid)
            if create_event:
                self.register_modif('VI '+mapid, obj_type='virt_inst', obj_id=mapid, old_state="Non-existing VI",
                                    new_state="Registered VI in netmap", logit_with_lvl=20)
        return str(mapid), vi

    def rename_VI(self, oldmapid, newmapid):
        if newmapid != '' and oldmapid in self.map:
            vi_to_rename = self.map.pop(oldmapid)
            if newmapid in self.map:
                self.map[self.get_unique_id(newmapid)] = self.get_VI(newmapid)
            self.map[newmapid] = vi_to_rename

    def get_VI(self, mapid):
        return self.map.get(mapid)

    def vi_present(self, mapid):
        if isinstance(mapid, str):
            return mapid in self.map

    def get_VI_mapids(self, subset_mapids=None, filter_fct=lambda vi_inst: True):
        ids = []
        for mapid in self.map if subset_mapids is None else subset_mapids:
            if filter_fct(self.get_VI(mapid)):
               ids.append(mapid)
        return ids

    def get_VIs_from_mapids(self, mapids_list):
        return [self.get_VI(mapid) for mapid in mapids_list if self.get_VI(mapid) is not None]

    def get_similar_VI(self, mac=None, ip=None, hostname=None, div={}):
        for mapid in self.map:
            vi = self.map[mapid]
            if vi.repr_same_device(mac, ip, hostname, div):
                return mapid

    def map_fct_on_VIs(self, mapids, fct, purge=False):
        applied = list(map(fct, self.get_VIs_from_mapids(mapids)))
        if not purge:
            return applied
        return [info for info in applied if info is not None]

    def get_IPs_from_mapids(self, mapids):
        return self.map_fct_on_VIs(mapids, lambda vi: vi.get_ip(), purge=True)

    # ----- Events interactions (saved for VI and logged in event center) -----

    # -- from saved events in this netmap instance --

    def get_saved_events_for_vi(self, mapid, target='all'):
        events = self.svd_events.get(mapid, [])
        if target == 'all':
            return events
        elif target == 'threats':
            return [threat for threat in events if isinstance(threat, ThreatEvent)]
        else:
            return [modif for modif in events if isinstance(modif, ModifEvent)]

    def get_saved_threats_for_vi(self, mapid):
        return self.get_saved_events_for_vi(mapid, 'threats')

    def get_saved_modifs_for_vi(self, mapid):
        return self.get_saved_events_for_vi(mapid, 'modifs')

    def event_already_saved(self, tomatch):
        mapid = tomatch.rel_to_vi()
        if mapid:
            events = self.get_saved_events_for_vi(mapid)
            for event in events:
                if event == tomatch:
                    return True
        return False

    # -- from events in eventcenter memory --

    def get_events_for_vi(self, mapid, target='all'):
        vi = self.get_VI(mapid)
        if self.event_center is None or vi is None:
            return None
        find_fct = lambda event: event.rel_to_vi() == mapid
        corresp_events = self.event_center.filter_events(target=target, filter_fct=find_fct)
        return corresp_events

    def get_threats_for_vi(self, mapid):
        return self.get_events_for_vi(mapid, target='threats')

    def get_modifs_for_vi(self, mapid):
        return self.get_events_for_vi(mapid, target='modifs')

    # -- from both simultaneously --

    def get_all_events_for_vi(self, mapid, target='all'):
        return self.get_events_for_vi(mapid, target) + self.get_saved_events_for_vi(mapid, target)

    def event_already_reported(self, tomatch):
        return self.event_already_saved(tomatch) or self.event_center.event_already_exists(tomatch)

    # ----- Registering events through this map -----

    def add_vi_event(self, mapid, event):
        vi_ev_list = self.svd_events.get(mapid)
        if vi_ev_list is None:
            self.svd_events[mapid] = [event]
        else:
            vi_ev_list.insert(0, event)

    def register_threat(self, from_module, level=1, mapid=None, msg=None, patch=None,
                        logit_with_lvl=-1, target_logger="threat",
                        save_vi_event=True, avoid_duplicate=True):

        if self.event_center is None:
            return None
        event = self.event_center.register_threat(from_module, level, mapid, msg, patch,
                                                  logit_with_lvl, target_logger)
        if save_vi_event:
            if not self.event_already_saved(event):
                self.register_threat_event(event)
            else:
                if not avoid_duplicate:
                    self.register_threat_event(event)
        return event

    def register_modif(self, modified_res, obj_type='app_res', obj_id=None, modificator='app',
                       old_state=None, new_state=None,
                       logit_with_lvl=-1, target_logger="modifs",
                       save_vi_event=True):

        if self.event_center is None:
            return None
        event = self.event_center.register_modif(modified_res, obj_type, obj_id, modificator,
                                                 old_state, new_state,
                                                 logit_with_lvl, target_logger)
        if save_vi_event:
            self.register_modif_event(event)

    def register_event(self, event):
        vi_relative = event.rel_to_vi()
        if vi_relative and self.vi_present(vi_relative):
            self.add_vi_event(vi_relative, event)
            return True
        return False

    def register_threat_event(self, threat_event):
        self.register_event(threat_event)

    def register_modif_event(self, modif_event):
        self.register_event(modif_event)

    # ----- Misc and printing -----

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

    def vi_icons(self, mapid):
        nbr_threats = len(self.get_saved_threats_for_vi(mapid))
        nbr_modifs = len(self.get_saved_modifs_for_vi(mapid))
        state = self.get_VI(mapid).str_state()
        return f"[{state}]    {nbr_threats} /!\\  {nbr_modifs} -o-"

    def vi_frame_str(self, mapid, max_char=25):
        vi = self.get_VI(mapid)
        header = f" {mapid} {self.vi_icons(mapid)} "
        l = max(max_char, len(header))
        cut = lambda s: s if len(s)<l else s[:l]
        s = header + '\n' + '='*l + '\n'
        s += cut(f" MAC: {vi.get_mac()}") + '\n'
        s += cut(f" IP: {vi.get_ip()}") + '\n'
        s += cut(f" Hostname:{vi.get_hostname()}") + '\n'
        ports = vi.get_ports_table().str_ports_list("Ports table:\n").split('\n')
        s += '\n'.join([cut(portline) for portline in ports])
        for field, val in vi.used_div_fields().items():
            s += cut(f" {field}: {val}") + '\n'
        return str_lines_frame(s[:-1] if s[-1] == '\n' else s)

    def vi_frames(self, slcted_vis=None):
        if slcted_vis is None:
            slcted_vis = self.get_VI_mapids()
        vi_frames = [self.vi_frame_str(mapid) for mapid in slcted_vis]
        return str_multiframe(vi_frames)

    def detail_str(self, level=0, vi_by_pack_of=3, max_char_per_vi=25):
        s = f"Netmap maintaining {len(self.map)} virtual instances" \
            f"{'' if self.event_center is None else ' and ref to an EventCenter'}\n"
        if level == 0:
            return s + ', '.join(self.get_VI_mapids()) + '\n'
        elif level == 1:
            for mapid, vi in self.map.items():
                s += f"      <<<[{mapid}]>>>\n{vi.detail_str(1)}"
            return s
        elif level == 2:
            vi_frames = [self.vi_frame_str(mapid, max_char=max_char_per_vi) for mapid in self.get_VI_mapids()]
            return s + str_multiframe(vi_frames, by_pack_of=vi_by_pack_of)
        else:
            for mapid, vi in self.map.items():
                s += f"\n      <<<[{mapid}]>>>\n{vi.detail_str(2)}"
                saved_events = self.get_saved_events_for_vi(mapid)
                if len(saved_events) > 0:
                    s += "  +-Saved events attached to this VI\n"
                    for event in saved_events:
                        s += "  |" + event.detail_str(level=0)
            return s

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