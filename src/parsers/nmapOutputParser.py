from lxml import etree


class NmapParser:

    def __init__(self, xml_source):
        self.tree = etree.parse(xml_source)
        self.root = self.tree.getroot()

    def get_root(self):
        return self.root

    def get_hosts(self, filter_host_fct=lambda host: True):
        return list(filter(filter_host_fct, self.root.findall('host')))

    def get_hosts_fields(self, fields=(), filter_host_fct=lambda host: True, keep_empty=True):
        h = self.get_hosts(filter_host_fct)
        pairs = []
        for host in h:
            found_fields = {}
            for field in fields:
                fields_elmts = list(host.iterdescendants(field))
                found_fields[field] = fields_elmts
            if keep_empty:
                pairs.append((host, found_fields))
            else:
                if len(found_fields) > 0:
                    pairs.append((host, found_fields))
        return pairs

    def get_attr_dict_from_elmt(self, elmt, attrs=(), max_val_lgth=-1):
        kept_attrs = {}
        for attr_key, attr_val in dict(elmt.attrib).items():
            if attr_key in attrs:
                if max_val_lgth > 0 and len(attr_val) <= max_val_lgth:
                    kept_attrs[attr_key] = attr_val
                else:
                    kept_attrs[attr_key] = attr_val
        return kept_attrs

    def addr_from_host(self, host_elmt, add_info_fct=lambda addr_elmt: []):
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
        return ip, mac, others
