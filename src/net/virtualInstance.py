div_fields = {'manufacturer': "",
              'model': "", 'firmware': "",
              'ports': PortTable()
              }


class VirtualInstance:

    def __init__(self, mac=None, ip=None, hostname=None, div=None):
        self.mac = mac
        self.ip = ip
        self.hostname = hostname
        self.div = div if div is not None else div_fields

    def detail_str(self, level=0):
        pass

    def __str__(self):
        pass


class PortTable:

    # NumPort : (service, protocol, state)

    def __init__(self, table=None):
        self.table = table if table is not None else {}

    def set_port(self, num, values=('unknown', 'unknown', 'unknown')):
        self.table[num] = values

    def list_ports(self, only_open):
