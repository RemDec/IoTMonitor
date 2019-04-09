
def has_method(obj, name):
    return callable(getattr(obj, name, None))


def str_frame(str_to_frame):
    """Nice formatting for a given string (framing it).

    For str returns
    +-----+
    | str |
    +-----+
    """
    str_to_frame = f"| {str_to_frame} |"
    lim = str_to_frame.replace('|', '+')
    lim = "".join(["-" if c != "+" else c for c in lim])
    return f"{lim}\n{str_to_frame}\n{lim}"
