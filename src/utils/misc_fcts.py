

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


def log_feedback_available(msg, logitin='info', lvl=20):
    import logging
    if has_method(logging, 'log_feedback'):
        logging.log_feedback(msg, logitin=logitin, lvl=lvl)
    else:
        if isinstance(lvl, str):
            lvl = lvl.upper()
            map_lvl = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING,
                       'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
            lvl = map_lvl.get(lvl, logging.DEBUG)
        logging.getLogger(logitin).log(level=lvl, msg=msg)


def obj_str(obj, level=0):
    if has_method(obj, 'detail_str'):
        return obj.detail_str(level=level)
    else:
        return obj.__str__()


def get_infoname_py(fun):
    """Return tuple (fun_name, mod_name) if fun defined in python module mod_name

    """
    full = fun.__module__
    ind = full.rfind('.')
    modname = full[ind+1:] if ind > -1 else full
    return fun.__name__, modname


def get_available_modules(stringnames=True):
    from pkgutil import iter_modules
    import modules.actives as actpackage
    import modules.passives as paspackage
    actives, passives = [], []
    for _, modname, ispkg in iter_modules(actpackage.__path__):
        if not ispkg:
            actives.append(modname)
    for _, modname, ispkg in iter_modules(paspackage.__path__):
        if not ispkg:
            passives.append(modname)
    return passives, actives


def write_modlib(file_dest=None):
    from modules.actives import arbitraryCmd, nmapExplorer, nmapPortDiscovery, nmapVulners
    from modules.passives import arbitraryCmdBg, pingTarget
    from src.utils.moduleManager import ModManager
    from src.utils.filesManager import get_dflt_entry

    if file_dest is None:
        file_dest = get_dflt_entry('dflt_lib')
    actives = [arbitraryCmd.AModArbitraryCmd(), nmapExplorer.AModNmapExplorer(), nmapPortDiscovery.AModNmapPortDisc(),
               nmapVulners.AModNmapVulners()]
    passives = [arbitraryCmdBg.PModArbitraryCmdBg(), pingTarget.PModPing()]
    mod_instances = actives + passives
    ModManager(str(file_dest)).create_modlib(mod_instances)


def is_program_callable(prog):
    """Check whether prog is on PATH or existing file and marked as executable."""
    from shutil import which
    if which(prog) is not None:
        return True
    import os
    return os.access(prog, os.F_OK or os.X_OK)


class NonExecutableError(Exception):

    def __init__(self, tried_prog_call):
        super().__init__(f"The program called by command '{tried_prog_call}' does not exist in PATH or the file is not"
                         f" marked as executable.")


def verify_program(prog):
    """Raise an exception if the command is not in path or an existing file marked as executable"""
    if not is_program_callable(prog):
        raise NonExecutableError(prog)


def str_param_comp(current, defaults, descriptions={}, prefix=''):
    """Illustrate which value would be given for each param

    """
    s = ""
    for code, (defval, mand, pref) in defaults.items():
        mand = "T" if mand else "F"
        defval = "[empty default value]" if defval == "" else defval
        desc = descriptions.get(code)
        if desc is not None:
            s += f"{prefix}~{code} (mandatory:{mand}): {desc}\n"
            s += f"{prefix} -dflt prefixed val : {pref + ' ' if pref is not None else ''}{defval}"
        else:
            s += f"{prefix}~{code}({mand}): {pref + ' ' if pref is not None else ''}{defval}"
        repl = current.get(code)
        if repl is not None:
            s += f" but current value {repl}"
        s += '\n'
    for other in [code for code in current if defaults.get(code) is None]:
        s += f"{prefix}!unref value in default for {other} : {current.get(other)}\n"
    return s


def pretty_str_curr_param(current, defaults, descriptions={}, prefix=''):
    s = ""
    for code, (defval, mand, _) in defaults.items():
        m = "mandatory" if mand else "optional"
        s += f"{prefix}~{code}   {descriptions.get(code, '(no description provided)')}\n"
        s += f"{prefix} - value ({m}) : {current.get(code, defval)}\n"
    return s


def treat_params(scheme_params, given_params):
    final_par = {}
    for par, val in scheme_params.items():
        if given_params.get(par):
            # Parameter is given as is
            final_par[par] = given_params[par]
        elif val[1]:
            # Not given parameter but mandatory -> take default
            final_par[par] = val[0]
    return final_par


def get_sep_modparams(modinstance):
    _, PARAMS, _ = modinstance.get_params()
    mandatory = [param_code for param_code in PARAMS if PARAMS[param_code][1]]
    optional = [param_code for param_code in PARAMS if not PARAMS[param_code][1]]
    return mandatory, optional


def replace_in_dicts(dic, key, apply_fct):
    """Replace values for a key in multilevel dict, applying a function on elements indexed by key

    """
    for k in dic:
        if k == key:
            apply_fct(dic[k])
        elif isinstance(dic[k], dict):
            replace_in_dicts(dic[k], key, apply_fct)


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


def str_multiframe(strlist, by_pack_of=3, add_interspace=True):
    """Nice formatting for several multilines str at the same level

    Adjust multilines strings on same horizontal basis
    For [str1, str2] where str1="+-----+\n+| str    |\n..." etc. returns
    +--------+  +--------+
    | str    |  | str2   |
    | longer |  | same l |
    +--------+  +--------+
    """

    sep = '  ' if add_interspace else ''  # horizontal space between frames
    final = ""
    pack = 0
    while pack < len(strlist):
        pack_to = min(pack+by_pack_of, len(strlist))
        frames = [s.split('\n') for s in strlist[pack:pack_to]]
        frames = list(map(lambda frame: list(filter(lambda str: str != '', frame)), frames))
        deepest = max(map(len, frames))  # longer (with most \n) frame in the pack to adjust others with blanklines
        for frame in frames:
            if len(frame) < deepest:
                frame_wide = max(map(len, frame))
                frame.extend([' '*frame_wide]*(deepest-len(frame)))
        for level in range(deepest):
            linesep = '\n'
            if level == deepest-1 and add_interspace:
                linesep = '\n\n'  # vertical space between lines of packed frames
            final += sep.join([lvl_str[level] for lvl_str in frames]) + linesep
        pack += by_pack_of
    return final


def get_root_path():
    """Get absolute path root for this project in the system

    """
    from pathlib import Path
    return Path(__file__).parent.parent.parent


if __name__ == '__main__':
    print(str_frame("simple|frame"))
    print(str_frame("test with \n carriage"))
    print("\n-----------------\n")
    print(str_lines_frame("with one | only | line"))
    print(str_lines_frame("str\nstr a bit longer\nmark|here"))

    write_modlib()