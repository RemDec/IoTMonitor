

def get_ip(dflt_ip='127.0.0.1', mask=None):
    """Get current IP on LAN (NAT internal) and mask off if subnetwork is required

    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = dflt_ip
    finally:
        s.close()
    return ip if mask is None else ip + '/' + str(mask)


def has_method(obj, name):
    """Look if obj contains a definition for function name

    """
    return callable(getattr(obj, name, None))


def get_infoname_py(fun):
    """Return tuple (fun_name, mod_name) if fun defined in python module mod_name

    """
    full = fun.__module__
    ind = full.rfind('.')
    modname = full[ind+1:] if ind > -1 else full
    return fun.__name__, modname


def str_param_comp(defaults, current):
    """Illustrate which value would be given for each param

    """
    s = ""
    for code, (defval, mand, pref) in defaults.items():
        mand = "T" if mand else "F"
        defval = "[empty default value]" if defval == "" else defval
        if pref != "":
            s += f"~{code}({mand}): {pref} {defval}"
        else:
            s += f"~{code}({mand}): {defval}"
        repl = current.get(code)
        if repl is not None:
            s += f" but current value {repl}"
        s += '\n'
    for other in [code for code in current if defaults.get(code) is None]:
        s += f"!unref value in default for {other} : {current.get(other)}\n"
    return s


def replace_in_dicts(dic, key, newval):
    """Replace values for a key in multilevel dict

    """
    for k in dic:
        if k == key:
            dic[k] = newval
        elif isinstance(dic[k], dict):
            replace_in_dicts(dic[k], key, newval)


def bound_frame(s):
    s = s.replace('|', '+')
    return "".join(["-" if c != "+" else c for c in s])


def str_frame(str_to_frame):
    """Nice formatting for a given string (framing it).

    For str returns
    +-----+
    | str |
    +-----+
    """
    str_to_frame = f"| {str_to_frame} |"
    lim = bound_frame(str_to_frame)
    return f"{lim}\n{str_to_frame}\n{lim}\n"


def str_lines_frame(str_to_frame):
    """Nice formatting for a given multiline string (framing it).

    For str\nlonger returns
    +--------+
    | str    |
    | longer |
    +--------+
    """
    sep = str_to_frame.split('\n')
    max_l = max([len(line) for line in sep])
    adjusted = [f"| {line}{' '*(max_l-len(line))} |" for line in sep]
    top = bound_frame(adjusted[0])
    bot = bound_frame(adjusted[-1])
    return '\n'.join([top] + adjusted + [bot]) + '\n'


def str_multiframe(strlist, by_pack_of=3):
    """Nice formatting for several multilines str at the same level

    Adjust multilines strings on same horizontal basis
    For [str1, str2] where str1="+-----+\n+| str    |\n..." etc. returns
    +--------+  +--------+
    | str    |  | str2   |
    | longer |  | same l |
    +--------+  +--------+
    """
    final = ""
    pack = 0
    while pack < len(strlist):
        pack_to = min(pack+by_pack_of, len(strlist))
        frames = [s.split('\n') for s in strlist[pack:pack_to]]
        deepest = max(list(map(len, frames)))
        for frame in frames:
            frame.remove('')
            if len(frame) < deepest:
                frame_wide = max(list(map(len, frame)))
                frame.extend([' '*frame_wide]*(deepest-len(frame)))
        for level in range(deepest):
            final += '  '.join([lvl_str[level] for lvl_str in frames]) + '\n'
        pack += by_pack_of
    return final


def get_root_path():
    """Get absolute path root for this project in the system

    """
    from pathlib import Path
    return Path(__file__).parent.parent.parent


def write_modlib(file_dest=None):
    from modules.actives import arbitraryCmd, nmapExplorer, nmapPortDiscovery
    from modules.passives import arbitraryCmdBg, pingTarget
    from src.utils.moduleManager import ModManager
    from src.utils.filesManager import get_dflt_entry

    if file_dest is None:
        file_dest = get_dflt_entry('lib')
    actives = [arbitraryCmd.AModArbitraryCmd(), nmapExplorer.AModNmapExplorer(), nmapPortDiscovery.AModNmapPortDisc()]
    passives = [arbitraryCmdBg.PModArbitraryCmdBg(), pingTarget.PModPing()]
    mod_instances = actives + passives
    ModManager(str(file_dest)).create_modlib(mod_instances)


if __name__ == '__main__':
    print(str_frame("simple|frame"))
    print(str_frame("test with \n carriage"))
    print("\n-----------------\n")
    print(str_lines_frame("with one | only | line"))
    print(str_lines_frame("str\nstr a bit longer\nmark|here"))

    a = {0: 1, 1: {}, 2: {0: "b", 1: "c"}, 3: {0: {}}}
    replace_in_dicts(a, 0, "a")
    print("\n\nAfter replacing 0 keys with value 'a'\n", a)
    default = {'par1': ("par1val", True, ""), 'par2': ("par2val", False, ""), 'par3': ("par3val", False, "")}
    given = {'par1':"new_val1", 'par3': "new_val3", 'unknown': "val"}
    print("\n\nSee used parameters\n", str_param_comp(default, given))

    write_modlib()