from src.utils.misc_fcts import str_lines_frame


div_fields = {'manufacturer': "",
              'model': "", 'firmware': ""
              }


class VirtualInstance:

    def __init__(self, mac=None, ip=None, hostname=None, div=None, ports=None, user_created=False):
        self.mac = mac
        self.ip = ip
        self.hostname = hostname
        self.div = div if div is not None else div_fields
        self.ports_table = ports if isinstance(ports, PortTable) else PortTable(ports)
        self.user_created = user_created
        self.STATES = ['unknown', 'up', 'down']
        self.state = 'unknown'

    def add_divinfo(self, key, value):
        self.div[key] = value

    def used_div_fields(self, keep_val=False):
        used = []
        for field, value in self.div.items():
            if value != "" and value is not None:
                used.append((field, value) if keep_val else field)
        return used

    def unused_div_fields(self):
        return [field for field in self.div if self.div.get(field) is not None]

    def revelant_field(self):
        if self.mac is not None:
            return self.mac
        elif self.ip is not None:
            return self.ip
        elif self.hostname is not None:
            return self.hostname

    def repr_same_device(self, mac=None, ip=None, hostname=None, div={}):
        if mac is not None:
            return self.mac == mac
        elif ip is not None:
            if self.ip == ip:
                if hostname is not None:
                    return self.hostname == hostname
                return True
        elif hostname is not None:
            if self.hostname == hostname:
                for div_field, val in div.items():
                    if self.div[div_field] != val:
                        return False
                return True
        return False

    def set_state(self, new_state):
        if new_state in self.STATES:
            self.state = new_state
            return True
        return False

    # --- Misc ---

    def get_mac(self, dflt="< empty >"):
        return dflt if self.mac is None else self.mac

    def get_ip(self, dflt="< empty >"):
        return dflt if self.ip is None else self.ip

    def get_hostname(self, dflt="< empty >"):
        return dflt if self.hostname is None else self.hostname

    def get_ports_table(self):
        return self.ports_table

    def str_state(self):
        if self.state == 'unknown':
            return '?'
        elif self.state == 'up':
            return 'v'
        elif self.state == 'down':
            return 'n'

    def get_defined_fields(self):
        s = f"{'' if self.mac is None else 'MAC, '}" \
            f"{'' if self.ip is None else 'IP, '}" \
            f"{'' if self.hostname is None else 'hostname, '}" \
            f"{', '.join(self.used_div_fields())}"
        return s

    def detail_str(self, level=0):
        manual = 'created manually' if self.user_created else ''
        s = f"Virtual Instance (state:{self.state}) {manual}: {self.revelant_field()}\n"
        if level == 0:
            defined = f" | fields: {self.get_defined_fields()}\n"
            return s + defined
        elif level == 1:
            s += f" | MAC: {self.mac} - IP: {self.ip} - hostname: {self.hostname}\n"
            s += f" | Other available fields : {', '.join(self.used_div_fields())}\n"
            s += self.ports_table.detail_str(level=1)
            return s
        else:
            s += f" |--Main fields :\n" \
                 f" | MAC : {self.mac}\n" \
                 f" | IP : {self.ip}\n" \
                 f" | Hostname : {self.hostname}\n" \
                 f" |--Registered ports table :\n"
            s += self.ports_table.detail_str(level=2)
            s += f" |--Other divers fields :\n"
            for field, value in self.div.items():
                s += f" | {field} = {value if value != '' else '<empty>'}\n"
            return s

    def __str__(self):
        return self.detail_str()


class PortTable:

    # NumPort : (service, protocol, state)

    def __init__(self, table=None):
        self.table = table if table is not None else {}

    def set_port(self, num, infos=('unknown', 'unknown', 'unknown')):
        self.table[num] = infos

    def list_ports(self, only_open=False):
        if not only_open:
            return self.table.keys()
        return [port for port in self.table.keys() if self.table[port][2] not in ['unknown', 'closed']]

    def is_empty(self):
        return self.table == {}

    def str_ports_list(self, header=None, empty_str="Empty ports table\n"):
        if self.is_empty():
            return empty_str
        s = "Registered ports with <service, protocol, state>\n" if header is None else header
        ports = sorted(self.table.keys())
        for port in ports:
            (service, prot, state) = self.table[port]
            s += f" | {port} : < {service}, {prot}, {state} >\n"
        return s

    def detail_str(self, level=0):
        if self.is_empty():
            return "Empty ports table\n"
        if level == 0:
            return f"Registered ports in table : {', '.join(map(str,self.list_ports()))}"
        elif level == 1:
            return self.str_ports_list()
        else:
            ports = sorted(self.table.keys())
            services, prots, states = [], [], []
            headers = [" Ports nbr ", " services ", " protocols ", " states "]
            lgth_port = max(len(str(max(ports))), len(headers[0]))
            lgth_serv, lgth_prot, lgth_sta = [len(h) for h in headers[1:]]
            for port in ports:
                (service, prot, state) = self.table[port]
                services.append(service)
                lgth_serv = max(len(service), lgth_serv)
                prots.append(prot)
                lgth_prot = max(len(prot), lgth_prot)
                states.append(state)
                lgth_sta = max(len(state), lgth_sta)
            s = "|".join(headers) + '\n'
            s += len(s) * '=' + '\n'
            for i, port in enumerate(ports):
                s_port = str(port) + ' ' * (lgth_port-len(str(port)))
                s_serv = services[i] + ' ' * (lgth_serv-len(services[i]))
                s_prot = prots[i] + ' ' * (lgth_prot-len(prots[i]))
                s_state = states[i] + ' ' * (lgth_sta-len(states[i]))
                s += '|'.join([s_port, s_serv, s_prot, s_state])
                if i != len(ports)-1:
                    s += '\n'
            return str_lines_frame(s)

    def __str__(self):
        return self.detail_str(1)


if __name__ == '__main__':
    ports = {80: ("HTTP", "TCP", "open")}
    table = PortTable(ports)
    table.set_port(631, ("ipp", "TCP", "closed"))
    print(table.detail_str(level=2))

    vi = VirtualInstance(mac="50:B7:C3:4F:BE:8C", ip="192.168.1.1", hostname="testvi", ports=ports, user_created=True)
    print("\n ### print lvl 0 ###\n", vi.detail_str(level=0))
    print("\n ### print lvl 1 ###\n", vi.detail_str(level=1))
    print("\n ### print lvl 2 ###\n", vi.detail_str(level=2))
