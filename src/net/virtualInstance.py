from src.utils.misc_fcts import str_multiframe


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

    def used_div_fields(self):
        used = []
        for field, value in self.div.items():
            if value != "" and value is not None:
                used.append(field)
        return used

    def revelant_field(self):
        if self.mac is not None:
            return self.mac
        elif self.ip is not None:
            return self.ip
        elif self.hostname is not None:
            return self.hostname

    def add_divinfo(self, key, value):
        self.div[key] = value

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

    def detail_str(self, level=0):
        s = f"Virtual Instance {'created manually' if self.user_created else ''}: {self.revelant_field()}\n"
        if level == 0:
            return s
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
        pass


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

    def detail_str(self, level=0):
        if level == 0:
            return f"Registered ports in table : {', '.join(map(str,self.list_ports()))}"
        elif level == 1:
            s = "Registered ports with <service, protocol, state>\n"
            ports = sorted(self.table.keys())
            for port in ports:
                (service, prot, state) = self.table[port]
                s += f" | {port} : < {service}, {prot}, {state} >\n"
            return s
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
            return str_multiframe(s)

    def __str__(self):
        return self.detail_str(1)


if __name__ == '__main__':
    ports = {80: ("HTTP", "TCP", "open")}
    table = PortTable(ports)
    table.set_port(631, ("ipp", "TCP", "closed"))
    print(table.detail_str(level=2))

    vi = VirtualInstance(mac="50:B7:C3:4F:BE:8C", ip="192.168.1.1", hostname="testvi", ports=ports, user_created=True)
    print(vi.detail_str(level=2))
