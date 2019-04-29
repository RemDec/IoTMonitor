from src.net.virtualInstance import *


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
        vi = self.get_VI(mapid)
        if self.event_center is None or vi is None:
            return None
        find_fct = lambda threat_event: threat_event.rel_to_vi() == mapid
        corresp_threats = self.event_center.get_threat_events(filter_fct=find_fct)
        return corresp_threats

    def get_modifs_for_vi(self, mapid):
        return self.get_events_for_vi(mapid, target='modifs')

    def get_VI(self, mapid):
        return self.map.get(mapid)

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

    def __str__(self):
        pass