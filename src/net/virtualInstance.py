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

    def complete_fields(self, mac=None, ip=None, hostname=None, div={}):
        self.mac = self.mac if mac is None or (self.user_created and self.mac is not None) else mac
        self.ip = self.ip if ip is None or (self.user_created and self.ip is not None) else ip
        self.hostname = self.hostname if hostname is None or (self.user_created and self.hostname is not None) \
                                      else hostname
        for field, val in div.items():
            curr_field = self.div.get(field)
            self.div[field] = val if curr_field is None or (self.user_created and curr_field is not None) else val

    def complete_ports_table(self, new_vals_dict, replacing=True):
        for portnum, new_port_info in new_vals_dict.items():
            self.ports_table.complete_portinfos(portnum, new_port_info, replacing)

    def used_div_fields(self, keep_val=False):
        used = []
        for field, value in self.div.items():
            if value != "" and value is not None:
                used.append((field, value) if keep_val else field)
        return used

    def unused_div_fields(self):
        return [field for field in self.div if self.div.get(field) is not None]

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

    def relevant_field(self):
        if self.mac is not None:
            return self.mac
        elif self.ip is not None:
            return self.ip
        elif self.hostname is not None:
            return self.hostname

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
        s = f"Virtual Instance (state:{self.state}) {manual}: {self.relevant_field()}\n"
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

    # NumPort : {'service': srv_name, 'protocol': netw_protocol, 'state': up|closed|filtered, 'div': {other_fields}}

    def __init__(self, table=None):
        self.dflt_entry = {'serive': 'unknown',
                           'protocol': 'unknown',
                           'state': 'unknown', 'div': {}}
        self.table = {}
        if table is not None:
            self.arrange_table(table)

    def arrange_table(self, table):
        for port_num, portinfos in table.items():
            num = port_num if isinstance(port_num, int) else int(port_num)
            if isinstance(portinfos, tuple):
                self.set_maininfos(num, portinfos[:3])
                if len(portinfos) > 3:
                    self.set_divinfos(num, portinfos[3])
            elif isinstance(portinfos, dict):
                self.set_port(num, portinfos)

    def tupleinfo_to_dict(self, infos_tuple):
        dictinfos = {}
        if len(infos_tuple) < 3:
            infos_tuple += ('unknown', )*(3-len(infos_tuple))
        for i, main_field in enumerate(['service', 'protocol', 'state']):
            dictinfos[main_field] = infos_tuple[i]
        if len(infos_tuple) >= 4 and isinstance(infos_tuple[3], dict):
            dictinfos['div'] = infos_tuple[3]
        else:
            dictinfos['div'] = {}
        return dictinfos

    def set_port(self, num, new_infos):
        if isinstance(new_infos, tuple):
            new_entry = self.tupleinfo_to_dict(new_infos)
        else:
            new_entry = self.dflt_entry.copy()
            for field, val in new_infos.items():
                if field in new_entry:
                    new_entry[field] = val
                else:
                    new_entry['div'][field] = val
        self.table[num] = new_entry

    def complete_portinfos(self, num, infos, creating=True, replacing=True):
        entry = self.table.get(num)
        if entry is None:
            if creating:
                self.set_port(num, infos)
            return
        for field, val in infos.items():
            if field in entry:
                # Main field
                if replacing:
                    entry[field] = val
                elif entry[field] in ['unknown', {}]:
                    entry[field] = val
            else:
                # Diverse info in div dict
                if field in self.get_divinfos(num):
                    if replacing:
                        self.set_divinfo(num, field, val)
                else:
                    self.set_divinfo(num, field, val)

    def list_ports(self, only_open=False):
        if not only_open:
            return self.table.keys()
        return [port for port in self.table.keys() if self.table[port]['state'] not in ['unknown', 'closed', 'filtered']]

    def set_divinfo(self, num, field, value):
        if self.table.get(num) is not None:
            self.table[num]['div'][field] = value

    def set_divinfos(self, num, field_dict):
        if self.table.get(num) is not None:
            self.table[num]['div'] = field_dict

    def set_maininfos(self, num, infos_tuple):
        if self.table.get(num) is None:
            self.table[num] = self.dflt_entry.copy()
        if len(infos_tuple) < 3:
            infos_tuple += ('unknown', )*(3-len(infos_tuple))
        for i, main_field in enumerate(['service', 'protocol', 'state']):
            self.table[num][main_field] = infos_tuple[i]

    def get_infos(self, num):
        if self.table.get(num) is None:
            return None
        return self.get_maininfos(num) + (self.get_divinfos(num), )

    def get_divinfos(self, num):
        return self.table[num]['div'] if num in self.table else None

    def get_maininfos(self, num):
        entry = self.table.get(num)
        if entry is None:
            return None
        return entry['service'], entry['protocol'], entry['state']

    def is_empty(self):
        return self.table == {}

    def str_ports_list(self, header=None, empty_str="Empty ports table\n"):
        if self.is_empty():
            return empty_str
        s = "Registered ports with <service, protocol, state>\n" if header is None else header
        ports = sorted(self.table.keys())
        for port in ports:
            (service, prot, state) = self.get_maininfos(port)
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
                (service, prot, state) = self.get_maininfos(port)
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


class PortTableOld:

    # NumPort : (service, protocol, state, divers_fields={field_name: field_value})

    def __init__(self, table=None):
        self.table = table if table is not None else {}

    def set_port(self, num, infos=('unknown', 'unknown', 'unknown', {})):
        if isinstance(infos, dict):
            self.table[num] = (infos.get('service', 'unknown'),
                               infos.get('protocol', 'unknown'),
                               infos.get('state', 'unknown'),
                               infos.get('div', {}))
        elif isinstance(infos, tuple):
            if len(infos) == 4:
                self.table[num] = infos
            else:
                final_infos = ['unknown', 'unknown', 'unknown', {}]
                for i, val in enumerate(infos):
                    final_infos[i] = val
                self.table[num] = tuple(final_infos)

    def complete_portinfos(self, num, infos, replacing=True):
        values = self.table.get(num)
        if values is None:
            return
        for info_key, info_val in infos.items():
            curr_val = self.get_info(num, info_key)
            ind = self.get_ind_info(info_key)
            if ind != -1 and (curr_val == 'unknown' or replacing):
                self.replace_val(num, ind, info_val)
            if ind == -1 and ((values[3].get(info_key) in [None, 'unknown']) or replacing):
                values[3][info_key] = info_val

    def replace_val(self, num, ind, newval):
        values = self.table.get(num)
        new_t = ()
        for i in range(values):
            if i == ind:
                new_t += (newval, )
            else:
                new_t += (values[i], )
        self.table[num] = new_t

    def list_ports(self, only_open=False):
        if not only_open:
            return self.table.keys()
        return [port for port in self.table.keys() if self.table[port][2] not in ['unknown', 'closed']]

    def get_ind_info(self, target):
        if target == 'service':
            return 0
        elif target == 'protocol':
            return 1
        elif target == 'state':
            return 2
        elif target == 'div':
            return 3
        return -1

    def get_info(self, num, target):
        infos = self.table.get(num)
        if infos is None:
            return None
        ind = self.get_ind_info(target)
        if ind != -1:
            return infos[ind]
        return infos[self.get_ind_info('div')].get(target)

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
    table.set_maininfos(631, ("ipp", "TCP", "closed"))
    print(table.detail_str(level=2))

    vi = VirtualInstance(mac="50:B7:C3:4F:BE:8C", ip="192.168.1.1", hostname="testvi", ports=ports, user_created=True)
    print("\n ### print lvl 0 ###\n", vi.detail_str(level=0))
    print("\n ### print lvl 1 ###\n", vi.detail_str(level=1))
    print("\n ### print lvl 2 ###\n", vi.detail_str(level=2))
