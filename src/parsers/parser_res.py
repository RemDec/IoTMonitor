CLIparser = {
    'main_help': "This interactive CLI works as a menus navigation system where typing one of the proposed choice\n"
                 "redirect in the corresponding menu (if no ambiguity first choice letters suffice)(if defined,\n"
                 "default choice is < > surrounded and selected pressing enter). Each menu is identified by an id.\n"
                 "There are some commands callable everywhere (not menu choices relative), to prefix with a '$' :\n"
                 "   -main : brings back to main menu, aborting current action\n"
                 "   -exit : shut down the application and this interactive CLI\n"
                 "   -help [menuid] : print help page for given menu (current one if not specified)\n"
                 "   -choices [menuid] : print available choices for a menu with detail level depending on print lvl"
}


def get_res_CLI(resource, dflt=None):
    if dflt is None:
        dflt = "No entry in CLIparser for resource " + str(resource)
    return CLIparser.get(resource, dflt)
