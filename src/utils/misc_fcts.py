
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
    return f"{lim}\n{str_to_frame}\n{lim}"


def str_multiframe(str_to_frame):
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
    return '\n'.join([top] + adjusted + [bot])


if __name__ == '__main__':
    print(str_frame("simple|frame"))
    print(str_frame("test with \n carriage"))
    print("\n-----------------\n")
    print(str_multiframe("with one | only | line"))
    print(str_multiframe("str\nstr a bit longer\nmark|here"))