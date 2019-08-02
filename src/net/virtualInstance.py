from src.utils.misc_fcts import str_lines_frame
from src.parsers.ipOutputParser import IPv4_addr
import re

div_fields = {'manufacturer': "",
              'model': "", 'firmware': ""
              }


re_MAC = r'([\dA-F]{2}(?:[-:][\dA-F]{2}){5})'
re_IPv4 = IPv4_addr


class FieldFormatError(Exception):

    def __init__(self, field, corr_format):
        super().__init__(f"Wrong format for field {field} that accepts only values given by {corr_format}")


def assess_formats(fields):
    if fields.get('mac') is not None:
        if re.match(re_MAC, fields['mac']) is None:
            raise FieldFormatError('MAC address', 'Regex :' + re_MAC)
    if fields.get('ip') is not None:
        if re.match(re_IPv4, fields['ip']) is None:
            raise FieldFormatError('IP address', 'Regex :' + re_IPv4)


class VirtualInstance:
    """Object standing for a virtual representation in the application of a real/artificial network host

    A network equipment can be summarised using common notions for networks, valid in all classical use cases : namely
    its MAC address, IP address and hostname. We call those information VI fields, they are strings formatted depending
    their nature. A VI maintains values for those fields, trying to represent as well as possible the real equipment
    characteristics. Another main 'field' is the table of used ports, an entire PortTable object is dedicated to it in
    order to handle all ports and services relative information. Additional information are considered as 'diverse' :
    manufacturer, model, etc. are represented by an arbitrary string value indexed in the div dictionary.
    A connection state is also associated with each VI, describing its availability in the network.
    A VI can be created either automatically by a module either manually by the user who craft it. If a VI is user
    created, non empty field values are not replaced whenever a new different value is given.
    """

    def __init__(self, mac=None, ip=None, hostname=None, div=None, ports=None, user_created=False):
        assess_formats({'mac': mac, 'ip': ip})
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
        """Fill fields values with ones given, where None means no modification

        If a field is already non empty, its value is replaced by the given one if VI is not user created
        Args:
            mac:
            ip:
            hostname:
            div(dict): a dictionary of diverse arbitrary fields, indexed by field name and whose values are fields
            values. If a field name is not yet present in div dict of VI, the entry is added to it, else normal
            rules with user crafted applies.

        Returns:
            changed(bool): whether one field took the corresponding given value
        """
        assess_formats({'mac': mac, 'ip': ip})
        changed = False
        if mac is not None and mac != self.mac:
            if self.mac is None or not self.user_created:
                self.mac = mac
                changed = True
        if ip is not None and ip != self.ip:
            if self.ip is None or not self.user_created:
                self.ip = ip
                changed = True
        if hostname is not None and hostname != self.hostname:
            if self.hostname is None or not self.user_created:
                self.hostname = hostname
                changed = True
        for field, val in div.items():
            # Set field value if non existing or if it exists, set it if not created by user (consider as prior info)
            curr_field = self.div.get(field)
            if val != curr_field and (curr_field is None or not self.user_created):
                self.div[field] = val
                changed = True
        return changed

    def complete_fields_from_dict(self, fields_dict):
        """Shortcut for complete field from one dict without passing each value as individual parameter

        Args:
            fields_dict(dict): combination of div dict and main fields indexed by 'mac', 'ip', 'hostname'. Other key
            in dict will be considered as div fields, those are extracted to retrieve their values

        Returns:
            changed(bool): whether one field took the corresponding given value
        """
        assess_formats(fields_dict)
        given_div = dict([(key, val) for key, val in fields_dict.items() if key not in ['mac', 'ip', 'hostname']])
        return self.complete_fields(mac=fields_dict.get('mac'), ip=fields_dict.get('ip'),
                                    hostname=fields_dict.get('hostname'), div=given_div)

    def complete_ports_table(self, new_vals_dict, replacing=True):
        """Complete the PortTable instance associated to this VI with new ports information

        Args:
            new_vals_dict:
            replacing:

        Returns:

        """
        changed = False
        for portnum, new_port_info in new_vals_dict.items():
            if self.ports_table.complete_portinfos(portnum, new_port_info, replacing):
                changed = True
        return changed

    def used_fields(self):
        used = {}
        if self.mac is not None:
            used['mac'] = self.mac
        if self.ip is not None:
            used['ip'] = self.ip
        if self.hostname is not None:
            used['hostname'] = self.hostname
        return used

    def used_div_fields(self):
        used = {}
        for field, value in self.div.items():
            if value != "" and value is not None:
                used[field] = value
        return used

    def unused_div_fields(self):
        return [field for field in self.div if self.div.get(field) is not None]

    def repr_same_device(self, mac=None, ip=None, hostname=None, div={}):
        """Decision function determining if there exist a consistent match between given parameters and VI field values

        This is an arbitrary decision process based on the good sense, ordered in that way (return True if one matches):
            - MAC addresses match
            - IPs match and hostnames also if given one is not None
            - Hostnames match and every field value given in div also
        Args:
            mac:
            ip:
            hostname:
            div:

        Returns:
            match(bool) : whether given values can be considered as ones belonging to the same real equipment
        """
        if mac is not None and self.mac is not None:
            return self.mac == mac
        elif ip is not None and self.ip is not None:
            if self.ip == ip:
                if hostname is not None and self.hostname is not None:
                    return self.hostname == hostname
                return True
        elif hostname is not None and self.hostname is not None:
            if self.hostname == hostname:
                for div_field, val in div.items():
                    if self.div[div_field] != val:
                        return False
                return True
        return False

    def set_state(self, new_state):
        """Set the network state of the VI

        Args:
            new_state(str): a constant amongst 'up', 'down', 'unknown'
        """
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

    def get_divfields(self):
        return self.div

    def get_ports_table(self):
        return self.ports_table

    def get_state(self):
        return self.state

    def str_state(self):
        if self.state == 'unknown':
            return '?'
        elif self.state == 'up':
            return 'up'
        elif self.state == 'down':
            return 'down'

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
            s += self.ports_table.detail_str(level=level)
            s += f" |--Other divers fields :\n"
            for field, value in self.div.items():
                s += f" | {field} = {value if value != '' else '<empty>'}\n"
            return s

    def __str__(self):
        return self.detail_str()


class PortTable:
    """

    The PortTable aims to provide a list of used ports on an equipment and information relative to each port like the
    service running on. Other useful common details are the transport protocol and the current state of the port.
    As for VI, diverse other fields are possible like service version, confidence level in the port information, ...
    The table is indexed by port numbers (int) and presents the following scheme :
     NumPort : {'service': srv_name, 'protocol': netw_protocol, 'state': up|closed|filtered, 'div': {other_fields}}
    """

    def __init__(self, table=None):
        """

        Args:
            table(dict):
        """
        self.dflt_entry = {'service': 'unknown',
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
        """Format an entry given in tuple format in an indexable dict in the PortTable

        Args:
            infos_tuple(str tuple): values tuple formatted like (service, protocol, state, div_dict), or shorter (any
            missing value will be set to 'unknown')

        Returns:
            dictinfos(dict) : a dictionary as could be indexed by a port number in the table.
        """
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
        """Index a new entry from the given port information, replace the current values if port was already referenced

        Args:
            num(int): the concerned port number
            new_infos(dict): can also be a tuple formatted as (service, protocol, state, div_dict). Given values will
            replace current ones
        """
        if isinstance(new_infos, tuple):
            new_entry = self.tupleinfo_to_dict(new_infos)
        else:
            new_entry = self.dflt_entry.copy()
            for field, val in new_infos.items():
                if field in new_entry:
                    # Main values
                    new_entry[field] = val
                else:
                    # Value set in diverse dict
                    new_entry['div'][field] = val
        self.table[num] = new_entry

    def complete_portinfos(self, num, infos, creating=True, replacing=True):
        """Fill the values for a given port or create a new entry in the table from port information

        Args:
            num(int): the concerned port number
            infos(dict): a dict with key that are field value names, either in 'service', 'protocol', 'state' for main
            fields or any other key that will be placed in div dict with its value
            creating(bool): whether should create an entry in the port table if port was not already referenced
            replacing(bool): whether if a field value is already present, the new one should replace it

        Returns:
            changed(bool) : whether at least on field value has been modified/created
        """
        entry = self.table.get(num)
        if entry is None:
            if creating:
                self.set_port(num, infos)
            return True
        changed = False
        if isinstance(infos, tuple):
            infos = self.tupleinfo_to_dict(infos)
        for field, val in infos.items():
            if isinstance(field, str) and field in entry:
                # Main field (field key already present in dict but maybe empty value)
                if val != entry.get(field) and (replacing or entry[field] in ['', 'unknown', {}, None]):
                    entry[field] = val
                    changed = True
            else:
                # Diverse info to place in div dict
                if field in self.get_divinfos(num):
                    if replacing and val != self.get_divinfos(num).get(field):
                        self.set_divinfo(num, field, val)
                        changed = True
                else:
                    self.set_divinfo(num, field, val)
                    changed = True
        return changed

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

    def get_infos(self, num, as_dicts=False):
        if self.table.get(num) is None:
            return None
        if as_dicts:
            return self.get_maininfos(num, as_dict=True), self.get_divinfos(num)
        return self.get_maininfos(num) + (self.get_divinfos(num), )

    def get_divinfos(self, num):
        return self.table[num]['div'] if num in self.table else None

    def get_maininfos(self, num, as_dict=False):
        entry = self.table.get(num)
        if entry is None:
            return None
        if as_dict:
            c = entry.copy()
            c.pop('div')
            return c
        return entry['service'], entry['protocol'], entry['state']

    def is_empty(self):
        return self.table == {}

    def str_ports_list(self, header=None, empty_str="Empty ports table\n", fct_per_port=None):
        if self.is_empty():
            return empty_str
        s = "Registered ports with <service, protocol, state>\n" if header is None else header
        ports = sorted(self.table.keys())
        for port in ports:
            if fct_per_port is None:
                (service, prot, state) = self.get_maininfos(port)
                has_div = ' [+]' if self.get_divinfos(port) else ''
                s += f" | {port} : < {service}, {prot}, {state} >{has_div}\n"
            else:
                s += fct_per_port(port)
        return s

    def detail_str(self, level=0):
        if self.is_empty():
            return "Empty ports table\n"
        if level == 0:
            return f"Registered ports in table : {', '.join(map(str,self.list_ports()))}"
        elif level == 1:
            return self.str_ports_list()
        elif level == 2:
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
        else:
            def fct_per_port(port):
                service, prot, state, div = self.get_infos(num=port)
                s = f" | {port} : < {service}, {prot}, {state} >\n"
                if len(div) == 0:
                    s = s[:-1] + " (no other div field)\n"
                else:
                    div = div.copy()
                    for cpe_part in ['App', 'Hw', 'Os']:
                        cpe_val = div.pop(cpe_part, False)
                        if cpe_val:
                            s += f" |   +- CPE {cpe_part}: {cpe_val}\n"
                    while len(div) > 0:
                        others = ''
                        for divkey in sorted(div.keys()):
                            others += f"{divkey}:{div.pop(divkey, 'unknown')}, "
                            if len(others) > 300:
                                break
                        s += f" |    +- divs: {others[:-2]}\n"
                return s
            return self.str_ports_list(header="Registered ports with <service, protocol, state> and diverse fields\n",
                                       fct_per_port=fct_per_port)

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
