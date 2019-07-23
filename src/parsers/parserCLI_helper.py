
spec_cmds =  "There are some commands callable everywhere (not menu choices relative), to prefix with a '$':\n" \
             "   -main : brings back to main menu, aborting current action\n" \
             "   -previous : backward to the previous menu\n" \
             "   -exit : shut down the application and this interactive CLI\n" \
             "   -help [menuid] : print help page for given menu (current one if not specified)\n" \
             "   -choices [menuid] : print available choices for the current or any given menu with detail level" \
             " depending on print lvl\n" \
             "   -output : interact with output view if it exists (launched from an app controller)\n" \
             "      + level [new_level] : print or set detail level of the resources displayed in the view\n" \
             "                  L 0 for less details, 10 is maximum level\n" \
             "      + view [resource] : print or set current app resource displayed in the output view\n" \
             "                  L 'any' to display possible code values for available resources\n" \
             "      + mode [viewmode] : switch or display the current view mode to [noout|outpiped|outscreen]\n" \
             "      + stop : stop to update the view and terminate linked processes\n" \
             "      + reset : restore the view considering current mode (restart it if already working)\n" \
             "   -set : change a general parameter value or print all currents one if no argument given\n" \
             "      + level [new level] print or set detail level for printing information in this terminal\n" \
             "   -cmds : display above special commands description"

help_pages = {0: "This interactive CLI works as a menus navigation system where typing one of the proposed choice\n"
                 "redirect in the corresponding menu. If no ambiguity first choice letters suffice, others terminal\n"
                 "facilities as autocompletion are available. Each menu is identified by an unique id.\n"
                 "A guide is available through some help pages, accessible typing $help [page_nbr].\n",
              1: "Help pages summary :\n"
                 "    0: Introduction\n"
                 "    1: Summary\n"
                 "    2: Special commands ($ prefixed)\n"
                 "    3: General application concepts (1/2)\n"
                 "    4: General application concepts (2/2)\n"
                 "    5: Getting started\n"
                 "    6: New Module integration (programmers)\n",
              2: spec_cmds,
              3: "# Modules\n"
                 "An object manipulable in the app that abstracts a real program utilisation (so installed in the\n"
                 "system as nmap). Each Module has an unique id amongst all available Modules in the application.\n"
                 "It is an overlayer for the underlying program and defines a scheme for the parameters it can take."
                 "When a module is 'launched', it starts an execution of the program in a new process\n"
                 "as if it was called from a CLI with some given flags + arguments. The building of this\n"
                 "command is transparent for the user and done from parameters scheme, with values the user\n"
                 "passed to the Module instance. A Module can be of two archetypes depending its execution :\n"
                 "  - Active : as a script, the program do its task and ends up printing on its standard output the\n"
                 "             results of its work.\n"
                 "  - Passive : similar to a fingerprinting/traffic analysis tool, the program do not ends up itself\n"
                 "              but continuously runs printing information on its output as of some stuff is analyzed\n"
                 "Available Modules are referenced in the Module Library, with a description of their utility and the\n"
                 "parameters defined in the associated scheme.\n\n"
                 "# Routine\n"
                 "A purpose of this application is the automation of several programs usages to monitor and protect\n"
                 "the network. The Routine is the component handling automation feature throughout manipulation of\n"
                 "Modules. Basically, the Routine can be fulfilled with the desired Module instances and executes\n"
                 "them automatically once its running state is triggered. Parsed results of Modules execution are\n"
                 "treated to rise security alerts or fill the network representation (see Netmap further).\n"
                 "The Routine consists of 2 subsets according to Module archetype it accepts, and has a 'running'\n"
                 "state (Routine is running if at least one subset is running):\n"
                 "  - Panel (passive) : Module instances in this set, once launched, run as long as they're stopped.\n"
                 "                      Once Panel running state is triggered, all Modules in are launched.\n"
                 "  - Queue (active) : an expiration timer is associated with each Module instance. At 0, the Module\n"
                 "                     is launched and the timer is reinitialized. Running state for Queue means all\n"
                 "                     timers of Module instances it contains are decremented each second.\n",
              4: "# Virtual Instances & Netmap\n"
                 "Through the parsing of the outputs handled by the Modules, some information are retrieved about the\n"
                 "hosts up in the analyzed network. Such information (IP, MAC, ...) are summarized in what\n"
                 "stands for the virtual representation of a network equipment, called Virtual Instance. It maintains\n"
                 "those values in indexed by name fields like IP -> 192.168.1.1. There are the main fields : IP, MAC,\n"
                 "hostname present for every VI and arbitrary diverse fields containing any value, for example\n"
                 "manufacturer -> Samsung. A table of ports maintaining information about used ones is also\n"
                 "referenced in each VI.\n"
                 "The Netmap is the set of VIs representing the current network globally. It indexes each VI with an\n"
                 "unique mapid. Each network host should be represented by a VI in the Netmap. The Netmap also keeps\n"
                 "a trace of processed modifications on those VI, from which Module it has been done, etc. A VI can\n"
                 "also be created from scratch by the user and its fields fulfilled manually.\n\n"
                 "# Events\n"
                 "We distinguish 2 types of Events instantiated by the application : Threats and Modifs.\n"
                 "Threats are discovered by the Modules underlying programs and parsed to be integrable in the app\n"
                 "environment. They content an arbitrary description and a dangerosity level ranging from 1 to 10 is\n"
                 "attributed to each. "
              }


CLIparser = {
    'main_help': help_pages[0] + spec_cmds,
    'create_help': "Build diverse elements to append in the application environment : virtual instance, module, etc.\n"
                   "Redirect to an interactive form taking parameters for the new element instance, or defaults.",
    'edit_help': "Change some parameter/fields value of various in-app elements (this editing will be permanent)\n",
    'rename_help': "Some elements in app are uniquely identified by an id, namely setid for module entries and mapid \n"
                   "for virtual instances. Edit this name, if new given name already exists the current so named will\n"
                   "be automatically renamed with an increment counter at its end",
    'remove_help': "Remove an element already present in the application, like a routine or a virtual instance.\n"
                   "The target is specified by id, either a setid for the routine or a mapid for a VI.",
    'clear_help': "Clear (meaning empty) target container in the app, or all of them. All objects in target and their\n"
                  " information/job will be dropped and cancelled without possible return.",
    'show_help': "Print in this console the current state of selected resource considering the current detail level\n"
                 " level (settable with $set level [0<= int <= 10]). To start you should try to show library content\n"
                 "from which Module instantiation can be done to build Routine automation system.",
    'save_help': "Write a file in a predefined structured format to save an application resource state or config.\n"
                 "Targetable resources are routine and netmap and general app config file (indicating their paths)",
    'pause_help': "Control the routine execution state, pause the panel kill all working background processes and \n"
                  "pause the queue suspends its timer so no more module working thread will be launched. Pause the\n"
                  "entire routine is equivalent to pause both.",
    'resume_help': "Control routine execution state, starting or restarting it. Start panel equals to call launch()\n"
                   "on every module sitting in (spawning two threads managing underlying cmd subprocess), start queue\n"
                   "rerun its timer that will decrement every expiration time of modules (spawning a thread at this\n"
                   "moment running underlying scanning program).",
    'integrate_help': "New Module integration to the app. environment. Supply the corresponding python module name \n"
                      "ie. the name of the file where the new Module class is defined (should be located in either\n"
                      "modules/passives either modules/actives). If the Module is correctly written, it will be added\n"
                      "to the Library and instantiable in the app from here.",
    'cmds_help': spec_cmds
}


def get_res_CLI(resource, dflt=None):
    if dflt is None:
        dflt = "No entry in CLIparser for resource " + str(resource)
    if isinstance(resource, int):
        return help_pages.get(resource, dflt)
    return CLIparser.get(resource, dflt)
