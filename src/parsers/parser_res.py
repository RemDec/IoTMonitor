
spec_cmds =  "There are some commands callable everywhere (not menu choices relative), to prefix with a '$':\n" \
             "   -main : brings back to main menu, aborting current action\n" \
             "   -exit : shut down the application and this interactive CLI\n" \
             "   -help [menuid] : print help page for given menu (current one if not specified)\n" \
             "   -choices [menuid] : print available choices for the current or any given menu with detail level" \
             " depending on print lvl\n" \
             "   -output : interact with output view if it exists (launched from an app controller)\n" \
             "      + level [new_level] : print or set detail level of the resources displayed in the view\n" \
             "                  L 0 for less details, 10 is maximum level\n" \
             "      + view [resource] : print or set current app resource displayed in the output view\n" \
             "                  L 'any' to display possible code values for available resources\n" \
             "   -set : change a general parameter value or print all currents one if no argument given\n" \
             "      + level [new level] print or set detail level for printing information in this terminal\n" \
             "   -cmds : display above special commands description"
CLIparser = {
    'main_help': "This interactive CLI works as a menus navigation system where typing one of the proposed choice\n"
                 "redirect in the corresponding menu (if no ambiguity first choice letters suffice)(if defined,\n"
                 "default choice is < > surrounded and selected pressing enter). Each menu is identified by an id.\n\n"
                 + spec_cmds,
    'create_help': "Build diverse elements to append in the application environment : virtual instance, module, etc.\n"
                   "Redirect to an interactive form taking parameters for the new element instance, or defaults.",
    'remove_help': "Remove an element already present in the application, like a routine or a virtual instance.\n"
                   "The target is specified by id, either a setid for the routine or a mapid for a VI.",
    'clear_help': "Clear (meaning empty) target container in the app, or all of them. All objects in target and their\n"
                  " information/job will be dropped and cancelled without possible return.",
    'show_help': "Print in this console the current state of selected resource considering the current detail level\n"
                 " level (settable with $set level [0<= int <= 10]).",
    'save_help': "Write a file in a predefined structured format to save an application resource state or config.\n"
                 "Targetable resources are routine and netmap and general app config file (indicating their paths)",
    'pause_help': "Control the routine execution state, pause the panel kill all working background processes and \n"
                  "pause the queue suspends its timer so no more module working thread will be launched. Pause the\n"
                  "entire routine is equivalent to pause both.",
    'resume_help': "Control routine execution state, starting or restarting it. Start panel equals to call launch()\n"
                   "on every module sitting in (spawning two threads managing underlying cmd subprocess), start queue\n"
                   "rerun its timer that will decrement every expiration time of modules (spawning a thread at this\n"
                   "moment running underlying scanning program).",
    'cmds_help': spec_cmds
}



def get_res_CLI(resource, dflt=None):
    if dflt is None:
        dflt = "No entry in CLIparser for resource " + str(resource)
    return CLIparser.get(resource, dflt)
