from src.net.virtualInstance import *


class Netmap:

    def __init__(self, map=None):
        self.map = {} if map is None else map

    def add_VI(self, vi, given_mapid=None):
        mapid = self.get_unique_id(given_mapid)
        self.map[mapid] = vi

    def remove_VI(self, mapid):
        self.map.pop(mapid)

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
        if self.check_unique_id():
            return mapid
        i = 2
        new_mapid = mapid + str(i)
        while not self.check_unique_id(new_mapid):
            i += 1
            new_mapid = mapid + str(i)
        return new_mapid

    def __str__(self):
        pass