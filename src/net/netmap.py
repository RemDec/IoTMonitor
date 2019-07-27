from src.net.virtualInstance import *
from src.logging.modifEvent import *
from src.logging.threatEvent import *
from src.logging.eventsCenter import EventsCenter
from src.utils.misc_fcts import str_multiframe
import src.logging.modifEvent as modif_event


class Netmap:
    """The Netmap is the object representing the network and its hosts, a set of Virtual Instances

    In this set, each VI is identified by an unique id (mapid) which can be used to retrieve the VI and its fields.
    A Netmap also manages Events : it maintains a reference to an EventCenter (meaning 'events for this network') and
    can be used as a bridge to feed it with new events. Additionally, as events in EventCenter are limited in number,
    Netmap can retain indefinitely desired events for each VI (especially threats that are important to keep in memory).
    A set of event is associated with each VI, indexed by mapid.
    """

    def __init__(self, map=None, event_center=None):
        self.map = {} if map is None else map
        self.event_center = event_center if event_center is not None else EventsCenter()
        self.svd_events = {}

    # ----- Interactions with the network map maintaining Virtual Instances -----

    def add_vi(self, vi, given_mapid=None):
        """Append a new VI to the current set with an unused mapid

        Args:
            vi(VirtualInstance): the VI object to index in the Netmap
            given_mapid(str): desired mapid, if already exists the given mapid is extended by an increasing digit until
            result is unique. If None, the base mapid is 'device'.

        Returns:
            The final mapid used to index the VI
        """
        mapid = self.get_unique_id(given_mapid)
        self.map[mapid] = vi
        return mapid

    def remove_vi(self, mapid):
        """Remove an indexed VI by its mapid if exists"""
        if mapid in self.map:
            self.map.pop(mapid)

    def clear(self):
        """Empty netmap and saved events"""
        self.map = {}
        self.svd_events = {}

    def create_vi(self, mapid=None, append_netmap=True, create_event=False, creator='unknown',
                  mac=None, ip=None, hostname=None, div=None, ports=None, user_created=False):
        """Instantiate a VI from given parameters, append it in netmap and register creation event (as a modification)

        Args:
            mapid(str): desired mapid for the created VI index in netmap
            append_netmap(bool): whether the VI instance should be indexed in netmap
            create_event(bool): whether a ModifEvent should be instantiated and registered for the VI creation
            creator(str): arbitrary string naming the agent who created the VI (likely a Module so its modid)
            mac(str): host MAC address used to fill the corresponding VI field
            ip(str): host IP address used to fill the corresponding VI field
            hostname(str): hostname of the host used to fill the corresponding VI field
            div(dict): others diverse fields associated with the VI, formatted as specified by VirtualInstance usage
            ports(PortTable): table of ports used by the host, as specified by PortTable usage
            user_created(bool): whether this VI were created from scratch by the user himself

        Returns:
            infos(tuple) : first element is the final mapid used for indexing the created VI, second one is the VI
                           instance
        """
        vi = VirtualInstance(mac=mac, ip=ip, hostname=hostname, div=div, ports=ports, user_created=user_created)
        if append_netmap:
            mapid = self.add_vi(vi, given_mapid=mapid)
            if create_event:
                self.register_modif('VI ' + mapid, elmt_type='virt_inst', elmt_id=mapid, modificator=creator,
                                    old_state="Non-existing VI", new_state="Registered VI in netmap", logit_with_lvl=20)
        return mapid, vi

    def rename_vi(self, oldmapid, newmapid):
        """Replace an existing mapid by a new one. If newmapid already present, it is renamed before to free it."""
        if newmapid != '' and oldmapid in self.map:
            vi_to_rename = self.map.pop(oldmapid)
            if newmapid in self.map:
                self.map[self.get_unique_id(newmapid)] = self.get_vi(newmapid)
            self.map[newmapid] = vi_to_rename

    def get_vi(self, mapid):
        return self.map.get(mapid)

    def vi_present(self, mapid):
        if isinstance(mapid, str):
            return mapid in self.map

    def get_vi_mapids(self, subset_mapids=None, sorted=True, filter_fct=lambda vi_inst: True):
        """Get mapids of some filtered VIs amongst all indexed or a subset

        Args:
            subset_mapids(str list): list of mapids to consider for the filtering
            sorted(bool): whether VIs should be grouped and sorted by their current state (up, down, unknown)
            filter_fct(function): an arbitrary function taking one parameter (the VI instance) returning a bool

        Returns:
            ids(list) : mapids of so indexed VIs for which filter_fct returns true
        """
        up, down, unkown = [], [], []
        for mapid in self.map if subset_mapids is None else subset_mapids:
            if self.vi_present(mapid) and filter_fct(self.get_vi(mapid)):
                if not sorted:
                    up.append(mapid)
                else:
                    vi_state = self.get_vi(mapid).get_state()
                    if vi_state == 'up':
                        up.append(mapid)
                    elif vi_state == 'down':
                        down.append(mapid)
                    else:
                        unkown.append(mapid)
        return up + down + unkown

    def get_vis_from_mapids(self, mapids_list):
        return [self.get_vi(mapid) for mapid in mapids_list if self.get_vi(mapid) is not None]

    def get_similar_vi(self, mac=None, ip=None, hostname=None, div={}):
        """Find the best matching in indexed IVs, given some VI fields

        Args:
            mac(str): MAC address to match
            ip(str): IP address to match
            hostname(str): hostname to match
            div(dict): diverse fields values

        Returns:
            mapid(str) : the index of a matching VI based on given field values or None if no VI corresponds. Matching
            rules are defined in VirtualInstance class doc.
        """
        for mapid in self.map:
            vi = self.map[mapid]
            if vi.repr_same_device(mac, ip, hostname, div):
                return mapid

    def map_fct_on_vis(self, mapids, fct, purge=False):
        applied = list(map(fct, self.get_vis_from_mapids(mapids)))
        if not purge:
            return applied
        return [info for info in applied if info is not None]

    def get_IPs_from_mapids(self, mapids):
        return self.map_fct_on_vis(mapids, lambda vi: vi.get_ip(), purge=True)

    # ----- Events interactions (saved for VI and logged in event center) -----

    # -- from saved events in this netmap instance --

    def get_saved_events_for_vi(self, mapid, target='all'):
        """Retrieve permanent events stocked in this netmap and indexed by the given mapid

        Args:
            mapid(str): index of the target VI
            target(str): 'all' for modifications and threats, 'threats' for only threats, 'modifs' or any for modifs

        Returns:
            events(list): the list of events with first element as the most recent event
        """
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
        """Check if an event is already present in the list indexed by the corresponding VI mapid

        Args:
            tomatch(Event): the Event instance to check presence
        Returns:
            present(bool): whether tomatch is already registered in event list corresponding to given mapid in the event
        """
        mapid = tomatch.rel_to_vi()
        if mapid:
            events = self.get_saved_events_for_vi(mapid)
            for event in events:
                if event == tomatch:
                    return True
        return False

    # -- from events in eventcenter memory --

    def get_events_for_vi(self, mapid, target='all'):
        """Retrieve Events currently registered in the netmap EventCenter concerning a given mapid

        Args:
            mapid(str): mapid of the VI
            target(str): 'all' for modifications and threats, 'threats' for only threats, 'modifs' or any for modifs
        Returns:
            events(list): the list of events with first element as the most recent event
        """
        vi = self.get_vi(mapid)
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
                        logit_with_lvl=-1, target_logger="threats",
                        save_vi_event=True, avoid_duplicate=True):
        """Instantiate and register a Threat Event through the Event Center and may index it in netmap if mapid provided

        Args:
            from_module(str): id of module raising the threat
            level(int): dangerosity level of the threat (ranges from 0 to 10)
            mapid(str): mapid indexing the VI the threat is relaticve to
            msg(str): description of the threat
            patch(str): possible patch to correct the problem
            logit_with_lvl(int): whether the threat alert should be logged in a normal way (not just registered in
            center). A level < 0 means no such logging, other value meanings are as defined in logging standard library
            target_logger(str): name of the target logger, 'threats' by default as defined in default loggers config.
            save_vi_event(bool): whether the event should be indexed in the netmap with the concerned mapid
            avoid_duplicate(bool): whether should verify if event already saved in netmap before indexing it

        Returns:
            event(ThreatEvent) : the event instance if saved in netmap (None if duplicate)
        """
        if self.event_center is None:
            return None
        event = self.event_center.register_threat(from_module, level, mapid, msg, patch,
                                                  logit_with_lvl, target_logger)
        if save_vi_event:
            if not self.event_already_saved(event):
                self.register_threat_event(event)
                return event
            else:
                if not avoid_duplicate:
                    self.register_threat_event(event)
                    return event

    def register_modif(self, modified_res, elmt_type=modif_event.VI, elmt_id=None, modificator='app',
                       old_state=None, new_state=None,
                       logit_with_lvl=-1, target_logger="modifs",
                       save_vi_event=True, avoid_duplicate=True):
        """Instantiate and register a Modif Event through the Event Center and may index it in netmap if mapid provided

        Args:
            modified_res(str): description of the modified resource
            elmt_type(str): type of the element whose resource has been modified
            elmt_id(str): element id in the app
            modificator(str): agent that modified the resource
            old_state(str): representation of the old resource state
            new_state(str): representation of the new resource state
            logit_with_lvl(int): whether the modif event should be logged in a normal way (not just registered in
            center). A level < 0 means no such logging, other value meanings are as defined in logging standard library
            target_logger(str): name of the target logger, 'modifs' by default as defined in default loggers config.
            save_vi_event(bool): whether the event should be indexed in the netmap with the concerned mapid
            avoid_duplicate(bool): whether should verify if event already saved in netmap before indexing it

        Returns:
            event(ModifEvent) : the event instance if saved in netmap (None if duplicate)
        """
        if self.event_center is None:
            return None
        event = self.event_center.register_modif(modified_res, elmt_type, elmt_id, modificator,
                                                 old_state, new_state,
                                                 logit_with_lvl, target_logger)
        if save_vi_event:
            if not self.event_already_saved(event):
                self.register_modif_event(event)
                return event
            else:
                if not avoid_duplicate:
                    self.register_modif_event(event)
                    return event

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
        state = self.get_vi(mapid).str_state()
        return f"[{state}]    {nbr_threats} /!\\  {nbr_modifs} -o-"

    def vi_frame_str(self, mapid, max_char=25):
        vi = self.get_vi(mapid)
        header = f" {mapid} {self.vi_icons(mapid)} "
        l = max(max_char, len(header))
        cut = lambda s: s if len(s) < l else s[:l]
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
            slcted_vis = self.get_vi_mapids()
        vi_frames = [self.vi_frame_str(mapid) for mapid in slcted_vis]
        return str_multiframe(vi_frames)

    def detail_str(self, level=0, vi_by_pack_of=3, max_char_per_vi=25):
        s = f"Netmap maintaining {len(self.map)} virtual instances" \
            f"{'' if self.event_center is None else ' and ref to an EventCenter'}\n"
        if level == 0:
            vis_state = [f"{mapid}[{self.get_vi(mapid).str_state()}]" for mapid in self.get_vi_mapids()]
            return s + ', '.join(vis_state) + '\n'
        elif level <= 2:
            vi_frames = [self.vi_frame_str(mapid, max_char=max_char_per_vi) for mapid in self.get_vi_mapids()]
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
    netmap.add_vi(vi, given_mapid="testdevice")
    netmap.add_vi(vi, given_mapid="testdevice2")
    netmap.add_vi(vi2)
    #print(netmap.vi_frame_str("testdevice"))
    print(netmap.detail_str(level=2))