from ipaddress import ip_address
import re

IPv4_addr = r'(((25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|\d).){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|\d))'


def is_ipv4(target):
    try:
        if re.fullmatch(IPv4_addr, target) is None:
            return False
        ip_address(target)
        return True
    except ValueError:
        return False


class IpParser:

    def __init__(self, txt):
        self.txt = txt

    def find_IPs(self, duplicates=True):
        matches = [group[0] for group in re.findall(IPv4_addr, self.txt)]
        return matches if duplicates else list(dict.fromkeys(matches))

    def isolate_IPs(self, target=None):
        slices = []
        ind = 0
        for ipmatch in re.finditer(IPv4_addr if target is None else target, self.txt):
            start, end = ipmatch.span()
            if ind == start:  # avoid empty slice when ip starts string
                slices.append((True, self.txt[start:end]))
                ind = end
                continue
            slices.append((False, self.txt[ind:start]))
            slices.append((True, self.txt[start:end]))
            ind = end
        if ind < len(self.txt):
            slices.append((False, self.txt[ind:]))
        return slices


if __name__ == '__main__':
    p = IpParser('mymodem (192.168.1.1)         : [0], 84 bytes, 4.08 ms (4.08 avg, 0% loss)')
    p2 = IpParser('ICMP Host Unreachable from 192.168.1.50 for ICMP Echo sent to 192.168.1.24 (192.168.1.24)')
    print(p.find_IPs())
    print(p2.find_IPs(duplicates=False))

    print(p.isolate_IPs())
    print(p2.isolate_IPs('192.168.1.24'))
