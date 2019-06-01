from lxml import etree


class NmapParser:

    def __init__(self, xml_source):
        self.tree = etree.parse(xml_source)
        self.root = self.tree.getroot()

    def get_root(self):
        return self.root

    def get_scan_infos(self):
        nmaprun = dict(self.root.attrib)
        nmaprun.update(dict(self.root.find('scaninfo').attrib))
        return nmaprun

    def get_hosts(self, filter_host_fct=lambda host: True):
        """Retrieve all host elements from the tree with a filter function

        Args:
            filter_host_fct: a filtering function taking host XML element as first parameter

        Returns:
            list: a list of host elements validating the filter
        """
        return list(filter(filter_host_fct, self.root.findall('host')))

    def get_hosts_fields(self, fields=(), filter_host_fct=lambda host: True, keep_empty=True):
        """Getting some children of host elements, selected by passing desired tags in fields

        Args:
            fields: tags of children to keep
            filter_host_fct: preprocess filtering function on hosts
            keep_empty: keep the pair even if no corresponding children were found for the host

        Returns:
            list of pairs: one entry per host, associated with a dict where keys are tag names provided in fields
                           and values are lists or children elements with this tag for each host
                           pairs looks like [(host1, {field1: [elmt1, elmt2], field2: [elmt1], ... }), (host2, ...)]
        """
        h = self.get_hosts(filter_host_fct)
        pairs = []
        for host in h:
            found_fields = self.get_host_fields(host, fields, keep_empty=keep_empty)
            if keep_empty or len(found_fields) > 0:
                pairs.append((host, found_fields))
        return pairs

    def get_host_fields(self, host, fields=(), keep_empty=True):
        """Get children elements named with each tag in fields

        Args:
            host: XML host element
            fields: strings that are tags of host children elements to retrieve

        Returns:
            found_fields: a dict which looks like {field1:[elmtWithTagfield1, elmtWithTagfield1], field2: ...}
        """
        found_fields = {}
        for field in fields:
            fields_elmts = list(host.iterdescendants(field))
            if len(fields_elmts) > 0 or keep_empty:
                found_fields[field] = fields_elmts
        return found_fields

    def get_attr_dict_from_elmt(self, elmt, attrs=(), max_val_lgth=-1):
        """Select a subset of attributes of a XML element, with a max length on those string values

        Args:
            elmt: a XML element
            attrs: an iterable of strings corresponding to attributes to keep
            max_val_lgth: maximum length of attributes values (not selected if too long, -1 mean no condition)

        Returns:
            A dict with keys original attribute names and values the corresponding string values
        """
        kept_attrs = {}
        for attr_key, attr_val in dict(elmt.attrib).items():
            if attr_key in attrs:
                if max_val_lgth > 0 and len(attr_val) <= max_val_lgth:
                    kept_attrs[attr_key] = attr_val
                else:
                    kept_attrs[attr_key] = attr_val
        return kept_attrs

    def addr_from_host(self, host_elmt, add_info_fct=lambda addr_elmt: []):
        """From an host element, retrieve infos about network adresses and infos linked with present in this element

        Args:
            host_elmt: XML host element
            add_info_fct: function taking an address element (child of host elmt) and returning a list of pairs
            key/values used to build dict other

        Returns:
            (ip, mac, others): a tuple where ip and mac are respectively strings for MAC and IP addresses and others
                               is a dict of others retrieved infos from function add_info_fct()
        """
        ip, mac, others = None, None, {}
        for addr in host_elmt.findall('address'):
            ad, adtype = addr.get('addr'), addr.get('addrtype')
            if adtype == 'ipv4':
                ip = ad
            elif adtype == 'mac':
                mac = ad
            list_pairs = add_info_fct(addr)
            for key, got_val in list_pairs:
                others[key] = got_val
        return mac, ip, others

    def hostname_from_host(self, host_elmt, list_all=False):
        """From an host element, retrieve its found hostname(s)

        Args:
            host_elmt: xXML host element
            list_all (bool): should return not only first hostname but the list of all

        Returns:
            names : a list of string hostnames or the first one by default
        """
        names_elmt = self.get_host_fields(host_elmt, fields=('hostname',))['hostname']
        names = [name_elmt.get('name') for name_elmt in names_elmt if 'name' in name_elmt.attrib]
        if list_all:
            return names
        if len(names) > 0:
            return names[0]

    def state_from_host(self, host_elmt):
        return host_elmt.find('status').get('state')

    def portlist_from_host(self, host_elmt):
        return self.get_host_fields(host_elmt, fields=('port',))['port']

    def maininfos_from_port(self, port_elmt):
        service_elmt = port_elmt.find('service')
        service = service_elmt.get('name') if service_elmt is not None else 'unknown'
        state_elmt = port_elmt.find('state')
        state = state_elmt.get('state') if state_elmt is not None else 'unknown'
        return port_elmt.get('portid', 0), service, port_elmt.get('protocol', 'unknown'), state


def cpes_to_dict(cpes):
    """Given one or multiple Common Platform Enumeration (CPE), determine which type or resource it is

    Args:
        cpe_string: a list or single string of CPE url, or XML elements containing it as text
                    following syntax 'cpe:/<part>:<vendor>:<product>:<version>:<update>:<edition>:<language>'

    Returns:
        cpes_typed(dict): a prettier dict indexing these CPEs with their type (+ a counter if CPEs of same
                          types in the list)
    """
    cpes_typed = {}
    name = lambda part: 'App' if part == 'a' else ('Hw' if part == 'h' else 'Os')
    keyit = lambda cpe: name(cpe[5] if cpe.startswith('cpe:/') else 'Unknown')
    if not(isinstance(cpes, list)):
        cpes = [cpes]
    cpe_strings = [cpe.text if isinstance(cpe, etree._Element) else cpe for cpe in cpes]
    for cpe in cpe_strings:
        if not(cpe in cpes_typed.values()):
            cpe_index = keyit(cpe)
            i = 2
            while cpe_index in cpes_typed:
                cpe_index = cpe_index + str(i)
                i += 1
            cpes_typed[cpe_index] = cpe
    return cpes_typed


if __name__ == '__main__':
    cpe1 = 'cpe:/a:lighttpd:lighttpd'
    cpe2 = 'cpe:/a:samba:samba:3'
    cpe3 = etree.Element('cpe')
    cpe3.text = "cpe:/h:tp-link:td-w8968"
    cpe4 = 'cpe:/o:linux:linux_kernel'
    cpe5 = etree.Element('cpe')
    cpe5.text = "cpe:/h:tp-link:td-w8968"
    print(cpes_to_dict([cpe1, cpe2, cpe3, cpe4, cpe5]))
