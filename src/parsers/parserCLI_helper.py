
spec_cmds = "There are some commands callable everywhere (not menu choices relative), to prefix with a '$':\n" \
            "   -main : brings back to main menu, aborting current action\n" \
            "   -previous : backward to the previous menu\n" \
            "   -exit : shut down the application and this interactive CLI\n" \
            "   -help [menuid] : print help page for given menu (current one if not specified)\n" \
            "   -choices [menuid] : print available choices for the current or any given menu with detail level" \
            " depending on print lvl\n" \
            "   -output : interact with output view if it exists (launched from an app controller, see $help 6)\n" \
            "      + level [new_level] : print or set detail level of the resources displayed in the view\n" \
            "                  L 0 for less details, 10 is maximum level\n" \
            "      + view [resource] : print or set current app resource displayed in the output view\n" \
            "                  L 'any' to display possible code values for available resources\n" \
            "      + mode [viewmode] [args] : switch or display the current view mode to [noout|outpiped|outscreen]\n" \
            "                          L params to Output constructor, terminal for outscreen for ex. (see $help 6)\n" \
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
                 "    6: Interact with the View\n"
                 "    7: New Module integration (programmers)\n",
              2: spec_cmds,
              3: "# Modules\n"
                 "An object manipulable in the app that abstracts a real program utilisation (so installed in the\n"
                 "system as nmap). Each Module has an unique id amongst all available Modules in the application.\n"
                 "It is an overlayer for the underlying program and defines a scheme for the parameters it can take.\n"
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
                 "Events are objects instantiated in the application to keep a trace of important happenings in it.\n"
                 "They are registered in the EventCenter from which can be later filtered, sorted and retrieved.\n"
                 "We distinguish 2 types of Events instantiated by the application : Threats and Modifs.\n"
                 "Threats are discovered by the Modules underlying programs and parsed to be integrable in the app\n"
                 "environment. They content an arbitrary description and a dangerosity level ranging from 1 to 10 is\n"
                 "attributed to each, eventually some vulnerability patching possibility.\n"
                 "Modifications represent a totally arbitrary modification of a element resource value in the app.\n"
                 "For example, the value of a VI field changed by a module. It contains an old and a new value\n"
                 "description, the name of modified resource, the type of the element (VI, Module instance,...).",
              5: "Getting started\n"
                 "  1. Check available Modules\n"
                 "All Modules descriptions are available in the Library. To display it, access the 'show' menu from\n"
                 "the main menu by typing it and pressing enter. In show menu, select 'library', all usable Module\n"
                 "descriptors appear, each titled with an unique mod_id. A description of the parameters scheme is\n"
                 "also provided, notice that some values may dynamically recomputed at instantiation.\n\n"
                 "  2. Fill the Routine\n"
                 "To instantiate a Module and place it in the Routine, back to the main menu with $main and go to the\n"
                 "'create' menu, where select choice 'module'. Then all available Module ids are displayed. Once this\n"
                 "choice is entered, an interactive dialog appear to configure the instance.\n"
                 "  - Use default parameters : whether the default values of non optional parameters shouldn't be\n"
                 "    used but specified in place (given by user or let default)\n"
                 "  - Specific VI : some Modules may be configured to have their execution relative to an already\n"
                 "    existing VI in the application. For ex., if Module take IPs in parameters, it will take ones of\n"
                 "    specified VIs if there are\n"
                 "  - Timer value : differ whether Module is active or not : if it does, the timer is the expiration\n"
                 "    time in the Queue before each launching. If passive it is the reading timer, the time between\n"
                 "    readings of the underlying program outputs\n"
                 "  - Add the Module instance in the Routine : if not, it will be added in the independent set where\n"
                 "    its execution will be launched once, not automated in the Routine\n"
                 "  - Give a setid : this id identify the Module instance in the Routine, if not provided it will be\n"
                 "    the Module id.\n\n"
                 "  3. Manipulate the Routine\n"
                 "Once all desired Modules are present in the Routine, trigger its launching by going 'resume' menu.\n"
                 "The Panel or the Queue can be launched individually, consider that Routine running state is the\n"
                 "result of OR between both Panel and Queue states. Then the executions are automated until stopping\n"
                 "the Routine and results/events should appear in the feedback of the View, the Netmap filled up.\n\n"
                 "  4. Inspect the Netmap\n"
                 "Once Module executions automatically instantiated some VI corresponding to analyzed hosts in the\n"
                 "network, some details about them can be retrieved from the Netmap. Do not forget that each VI is\n"
                 "identified in the Netmap by an unique id called mapid, useful when you desire indicate which\n"
                 "equipment you want to select in menus. A pretty presentation of the current network map can be\n"
                 "displayed from show menu by setting the display level to 2 ($set lvl 2), summarizing most of\n"
                 "available information. Note those symbols significations :\n"
                 "  - /!\\ stands for threats discovered and associated with the VI\n"
                 "  - -o- stands for modifications done on the VIs, like its fields value changes (IP, MAC, etc.)\n"
                 "Details of these Events can be displayed increasing the display details level. If you gave an email\n"
                 "at the application launching, some recap mails should have been sent about discovered threats.\n\n"
                 "  5. Explore others menus\n"
                 "Of course, once instantiated some living objects in the application can be edited, renamed, etc. To\n"
                 "get help about it, typing '$help' in any of those menus will display the related help page.",
              6: "Interact with the View\n\n"
                 "    Even if all app. elements can be displayed in this CLI using the 'show' menu, keeping vision\n"
                 "on current application state continuously would be convenient. That's the role of the View, that\n"
                 "displays each second the current state of a target element. This target is identified by a string,\n"
                 "like 'app', 'netmap', 'routine',etc. Each choice in the show menu can also be displayed in the View\n"
                 "using '$o view [resource]' with a detail level settable by '$o lvl [int]'. The View has different\n"
                 "modes, current one is settable by '$o mode [code_mode] [args]' :\n"
                 "  - noout : no View handled\n"
                 "  - outpiped : displayed stuff is fed in a pipe, readable by the user using external programs\n"
                 "  - outscreen [term] : a terminal emulator is spawned besides this CLI, displaying an updated view\n"
                 "                       of the element each second. The used terminal can be set passing its code as\n"
                 "                       argument amongst 'auto', 'xterm', 'gnome', 'konsole'\n"
                 "Flow control of the View subprocess can be manipulated with '$o reset|stop'.\n",
              7: "New Module integration\n\n"
                 "    Since this application can be transparently used as a tool, it provides also a framework for an\n"
                 "easy integration of new arbitrary underlying programs. As explained in the code doc, this is done\n"
                 "writing new Modules as python classes inheriting already written superclasses facilities. Once done\n"
                 "the Module should be integrated in the app environment, meaning the Library. The easiest way is\n"
                 "using this CLI, going the 'integrate' menu from $main. If all is correctly written following the\n"
                 "framework, integration should be as simple as give the python module name where is the class Module\n"
                 "code.\n"
              }


CLIparser = {
    'main_help': help_pages[0] + spec_cmds,
    'create_help': "Build diverse elements to append in the application environment : virtual instance, module, etc.\n"
                   "Redirect to an interactive form taking parameters for the new element instance, or defaults.",
    'edit_help': "Change some parameter/fields value of various in-app elements (this editing will be permanent)\n",
    'rename_help': "Some elements in app are uniquely identified by an id, namely setid for module entries and mapid \n"
                   "for virtual instances. Edit this name, if new given name already exists the current so named will\n"
                   "be automatically renamed with an increment counter at its end so the desired element get the\n"
                   "right name.",
    'remove_help': "Remove an element already present in the application, like a Module or a Virtual Instance.\n"
                   "The target is specified by id, either a setid for the routine or a mapid for a VI.",
    'clear_help': "Clear (meaning empty) target container in the app, or all of them. All objects in target and their\n"
                  "information/job will be dropped and terminated without possible cancellation.",
    'show_help': "Print in this console the current state of selected resource considering the current detail level\n"
                 "(settable with $set level [0<= int <= 10]). To start you should try to show library content\n"
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
