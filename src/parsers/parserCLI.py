from src.appcore import *
from src.net.virtualInstance import *
from src.utils.misc_fcts import str_lines_frame
from src.parsers.parser_res import get_res_CLI
import readline
import os


class CLIparser:

    def __init__(self, core, core_controller=None):
        self.core_ctrl = core_controller
        self.core = core
        self.setup_menus()
        self.get_input = False
        self.curr_menu = {}
        self.curr_choices = []
        self.reserved = {'main': self.back_main_menu, 'exit': self.exit,
                         'help': self.ask_help, 'choices': self.ask_choices, 'cmds': self.ask_cmds,
                         'output': self.ctrl_output, 'set': self.set_cfg_param}
        self.display_header = True
        self.clear_cls = True

        self.curr_display_lvl = 1 if self.core_ctrl is None else self.core_ctrl.get_level()

        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)

    def complete(self, text, state):
        return (self.match_input_to_choice(text) + [None])[state]

    # ----- Parsing execution flow -----

    def start_parsing(self):
        self.get_input = True
        self.curr_menu = self.main_menu
        self.loop_parsing()

    def stop_parsing(self):
        self.get_input = False

    def loop_parsing(self):
        while self.get_input:
            # Entering current menu, compute available choices from corresponding menu dict, wait for an input choice
            self.curr_choices = self.compute_curr_choices()
            header = self.header_from_menu(include_header=self.display_header)
            user_in = input(header)
            self.display_header = True
            if user_in.startswith('$'):
                # Handling special command invokable from everywhere (all prefixed by $)
                self.handle_reserved_kw(user_in[1:])
            else:
                # Handling regular input, try to match to an available current choice or taking default value if defined
                if user_in == "" and self.curr_menu.get('dflt_choice', False):
                    user_in = self.curr_menu['dflt_choice']
                # Select choice if no ambiguity with given letters
                completed_in = self.match_input_to_choice(user_in)
                if len(completed_in) == 0:
                    print(f"No corresponding choice for this menu [id:{self.get_currmenu_index()}]"
                          f" (type $choices or $help)")
                    self.no_wipe_next()
                elif len(completed_in) > 1:
                    print("Ambiguous choice between", ', '.join(completed_in))
                    self.no_wipe_next()
                else:
                    # Correct choice, call corresponding menu function on the choice value, do process in it
                    user_in = completed_in[0]
                    self.curr_menu['fct_choice'](user_in)
                self.clear_console()
                self.clear_cls = True

    # ----- Internal utilities functions -----

    def compute_curr_choices(self):
        # Transform current menu 'choices' arbitrary value (function, dict, list) into regular format
        return self.compute_choices(self.curr_menu)

    def compute_choices(self, menu):
        choices = menu['choices']
        # treated choices format [[ch1, ch2, ..], [ch3, ch4, ..], ...] (1 list per newline)
        if callable(choices):
            return choices()
        if isinstance(choices, dict):
            return [choices.keys()]
        return choices

    def str_curr_choices(self):
        # Get string to display for current formatted choices
        return self.str_choices(self.curr_menu, 0)

    def str_choices(self, menu, detail_lvl=None):
        # Pretty display formatting for available choices of a given menu
        detail_lvl = self.curr_display_lvl if detail_lvl is None else detail_lvl
        s = ""
        dflt_choice = menu.get('dflt_choice', None)
        if detail_lvl == 0:
            # Simply display choices codes and which is the default
            for choice_line in self.compute_choices(menu):
                with_indic_dflt = [choice if choice != dflt_choice else f"< {choice} >" for choice in choice_line]
                s += ' | '.join(with_indic_dflt) + '\n'
        else:
            # Search for each choice if it corresponds to another menu and try to pull it's description
            for choice_list in self.compute_choices(menu):
                for choice in choice_list:
                    s += f"{choice if choice != dflt_choice else '<' + choice + '>'} : "
                    if not(isinstance(menu['choices'], dict)) or menu['choices'].get(choice) is None:
                        s += "generated choice without description\n"
                    else:
                        choice_code = menu['choices'][choice]
                        corresp_menu = self.index_menus.get(choice_code)
                        if corresp_menu is not None and corresp_menu.get('desc', "") != "":
                            s += corresp_menu['desc'] + '\n'
                        else:
                            s += f"undefined description in menu [{choice_code}]\n"
        return s

    def header_from_menu(self, include_header=True):
        disp_desc = self.curr_menu.get('disp_desc', True)
        disp_choice = self.curr_menu.get('disp_choice', True)
        marker = self.curr_menu.get('marker', ">>>")
        s = ""
        if include_header:
            if disp_desc and self.curr_menu['desc'] != "":
                s = str_lines_frame(f"[{self.get_currmenu_index()}] {self.curr_menu['desc']}")
            if disp_choice:
                s += "Following commands/choices are available :\n" + self.str_curr_choices()
        s += '\n' + marker
        return s

    def match_input_to_choice(self, user_in):
        matches = []
        for choice_line in self.curr_choices:
            for choice in choice_line:
                if choice == user_in:
                    # exact match, consider only this choice as unambiguous
                    return [choice]
                if choice.startswith(user_in):
                    matches.append(choice)
        return matches

    def check_reserved_kw(self, user_input, handle_it=True):
        if user_input.startswith('$'):
            if handle_it:
                self.handle_reserved_kw(user_input[:1])
            else:
                return True
        return False

    def handle_reserved_kw(self, keyword_cmd):
        # keyword is whole command without the '$' prefix. command[0] indicates which function to call on remaining args
        cmd = list(filter(None, keyword_cmd.split(' ')))
        tocall = cmd.pop(0)
        corresp = [cmd_ok for cmd_ok in self.reserved if cmd_ok.startswith(tocall)]
        if len(corresp) == 0:
            print(f"No special command starting with {tocall}\n")
            self.no_wipe_next()
        elif len(corresp) == 1:
            self.reserved[corresp[0]](args=cmd)
        else:
            print("Ambiguous special command amongs : ", ', '.join(corresp))
            self.no_wipe_next()

    def get_user_confirm(self, marker=None, val=('y', 'o', 'yes', 'oui', 'ok'), empty_ok=True):
        if marker is None:
            marker = "Confirm ? (Y/n) " if empty_ok else "Confirm ? (y/N) "
        res = input(marker)
        return res.lower() in val + ('',) if empty_ok else val

    def get_user_in_or_dflt(self, default, marker=">>>"):
        user_in = input(marker)
        return default if user_in == "" else user_in

    def no_wipe_next(self):
        self.display_header = False
        self.clear_cls = False

    def clear_console(self):
        if self.clear_cls:
            os.system('cls' if os.name == 'nt' else 'clear')

    # ----- Functions related to reserved keywords (called when entered) -----

    def back_main_menu(self, args=[]):
        self.clear_console()
        self.clear_cls = True
        self.curr_menu = self.main_menu

    def exit(self, kill_app=True, args=[]):
        if self.core_ctrl is not None:
            # exiting app delegated to controller
            self.core_ctrl.stop_app()
            return
        self.stop_parsing()
        if kill_app:
            self.core.quit()

    def ask_help(self, args=[]):
        # help for current menu by default (no menu id given)
        target_menu = self.curr_menu
        if len(args) >= 1:
            target_menu = self.index_menus.get(args[0])
        if target_menu is None:
            print("Invalid target menu\n")
            return
        if target_menu.get('help', False):
            print(f"help[{self.get_menu_index(target_menu)}]\n {target_menu['help']}")
        elif target_menu.get('desc', "") != "":
            print(f"[{self.get_menu_index(target_menu)}]description (no help available)\n {target_menu['desc']}")
        else:
            print(f"No help provided for this menu ([{self.get_menu_index(target_menu)}])\n")
        self.no_wipe_next()

    def ask_choices(self, args=[]):
        target_menu = self.curr_menu
        if len(args) >= 1:
            target_menu = self.index_menus.get(args[0])
        if target_menu is None:
            print("Invalid target menu\n")
            return
        if target_menu.get('choices') is not None:
            str_choices = self.str_choices(target_menu)
            print(f"List of available choices/command for menu [{self.get_menu_index(target_menu)}] :\n\n{str_choices}")
        else:
            print(f"No available choices list for menu [{self.get_menu_index(target_menu)}]")
        self.no_wipe_next()

    def ask_cmds(self, args=[]):
        print(get_res_CLI('cmds_help', 'No description for special commands'))
        self.no_wipe_next()

    def ctrl_output(self, args=[]):
        if self.core_ctrl is None:
            print("No application control instance offering an output view currently working")
            self.no_wipe_next()
            return
        arg_l = len(args)
        if arg_l == 0:
            print(self.core_ctrl)
        elif args[0] in ['l', 'lvl', 'level']:
            if arg_l == 2:
                self.core_ctrl.set_level(int(args[1]))
            print("Current detail level for application view :", self.core_ctrl.get_level())
        elif args[0] in ['v', 'view']:
            if arg_l == 2:
                if not self.core_ctrl.set_current_todisplay(args[1]):
                    print("Error, give a viewable resource name :", ','.join(self.core_ctrl.poss_display))
            print("Current viewed resource :", self.core_ctrl.to_disp)
        elif args[0] == 'infos':
            print("Current controller maintaining application view :\n", self.core_ctrl)
        self.no_wipe_next()

    def set_cfg_param(self, args=[]):
        arg_l = len(args)
        if arg_l == 0:
            print("Current config")
        elif args[0] in ['l', 'lvl', 'level']:
            if arg_l == 2:
                self.curr_display_lvl = int(args[1])
            print("Current display level :", self.curr_display_lvl)
        self.no_wipe_next()

    # ----- Functions to get available command choices -----

    def get_available_mods(self):
        # Get all available mods in the current library, actives and passives
        # [[actives m_id] , [passives m_id]]
        return self.core.get_available_mods(only_names=True)

    def get_routine_setids(self):
        # Get all modules in the current routine as their set_id
        # [[mod in panel pid] , [mod in queue qid]]
        return self.core.get_all_setids()

    def get_map_mapids(self):
        return [self.core.get_all_mapids()]

    # ----- Functions called after a choice is taken (given as a string in arg) -----

    def transit_menu(self, menu_input_name):
        target_menu_index = self.curr_menu['choices'][menu_input_name]
        self.curr_menu = self.index_menus[target_menu_index]

    def after_mod_slct(self, mod_id):
        dflts = self.get_user_confirm(f"[{mod_id}] use defaults params (Y/n)? ")
        in_rout = self.get_user_confirm(f"[{mod_id}] append it in routine (Y/n) ?")
        if dflts:
            mod_inst = self.core.instantiate_module(mod_id)
        else:
            input_params = {}
            _, PARAMS, desc_params = self.core.modmanager.get_mod_desc_params(mod_id)
            for code_param, (dflt, mand, pref) in PARAMS.items():
                desc = desc_params.get(code_param, "No parameter description")
                perm = "mandatory" if mand else "optional"
                flag = f"flag {pref}" if pref != "" else "no prefix"
                header = f"Parameter {code_param} ({perm}, {flag}) : {desc}"
                marker = f"[default:{dflt if dflt != '' else '<empty>'}] :"
                user_in = input(f"{header}\n{marker}")
                if user_in == "":
                    input_params[code_param] = dflt
                else:
                    input_params[code_param] = user_in
            mod_inst = self.core.instantiate_module(mod_id, curr_params=input_params)
        is_mod_act = mod_inst.is_active()
        timer_name = f"{'queue expiration' if is_mod_act else 'reading'} interval timer"
        dflt_val = mod_inst.get_default_timer() if is_mod_act else mod_inst.get_read_interval()
        input_timer = self.get_user_in_or_dflt(dflt_val,
                                               marker=f"Set {timer_name} if desired (numeric)\n[default:{dflt_val}] :")
        if in_rout:
            setid = self.get_user_in_or_dflt(None, marker="Give a setid if desired (alphanumeric)\n[setid] :")
            self.core.add_to_routine(mod_inst, given_setid=setid, given_timer=abs(int(input_timer)))
        else:
            self.core.add_indep_module(mod_inst)
        self.back_main_menu()

    def after_show_select(self, show_input_name):
        map = {'routine': "routine", 'netmap': "netmap", 'mods library': "library", 'independent mods': "indep",
               'main timer': "timer", 'virtual instance': "vi", 'entry module in routine': "entry",
               'threat events': "threats", 'modification events': "modifs", 'app': "app"}
        res_to_show = map.get(show_input_name, "app")
        if res_to_show == "vi":
            self.curr_menu = self.show_VI
        elif res_to_show == "entry":
            self.curr_menu = self.show_modentry
        else:
            lvl_info = f"(increase it with $set lvl {self.curr_display_lvl + 1}" if self.curr_display_lvl < 10 else ''
            print(f"Displaying app element {show_input_name} with level {self.curr_display_lvl} {lvl_info})\n")
            to_disp = self.core.get_display(res_to_show, level=self.curr_display_lvl)
            print(to_disp if to_disp.strip() else f"   < empty app element : {show_input_name} >\n")
            self.no_wipe_next()

    def after_show_vi_slct(self, mapid):
        vi = self.core.get_from_netmap(mapid)
        lvl_info = f"(increase it with $set lvl {self.curr_display_lvl+1}" if self.curr_display_lvl < 2 else ''
        print(f"Displaying VI informations with level {self.curr_display_lvl} {lvl_info})\n")
        print(vi.detail_str(self.curr_display_lvl))
        show_threats = self.get_user_confirm(marker=f"[{mapid}] Display threats linked with ? (y/N) :", empty_ok=False)
        if show_threats:
            self.core.get_saved_events(mapid, target='threats')
        show_modifs = self.get_user_confirm(marker=f"[{mapid}] Display modifications linked with ? (y/N) :",
                                            empty_ok=False)
        if show_modifs:
            self.core.get_saved_events(mapid, target='modifs')
        self.no_wipe_next()

    def after_show_modentry_slct(self, setid):
        modentry_panel, modentry_queue = self.core.get_from_routine(setid, whole_entry=True)
        lvl_info = f"(increase it with $set lvl {self.curr_display_lvl+1}" if self.curr_display_lvl < 2 else ''
        print(f"Displaying module entry in routine with level {self.curr_display_lvl} {lvl_info})\n")
        s = ""
        if modentry_panel is not None:
            s += f"Module entry in routine PANEL referenced by setid {setid} :\n" \
                 f"{modentry_panel.detail_str(self.curr_display_lvl)}\n"
        if modentry_queue is not None:
            s += f"Module entry in routine QUEUE referenced by setid {setid} :\n" \
                 f"{modentry_queue.detail_str(self.curr_display_lvl)}\n"
        print(s if s is not "" else f"   < No module entry in routine referenced by setid {setid} >")
        self.no_wipe_next()

    def after_remove_mod_slct(self, mod_setid):
        self.core.remove_from_routine(mod_setid)
        self.back_main_menu()

    def after_clear_select(self, target):
        code = self.get_choice_val(target)
        advert = f"Clearing {target} will empty it and loose all its components (irreversible).\n" \
                 f"Are you sure? (y/N) :"
        valid = self.get_user_confirm(marker=advert, val=('y', 'o', 'yes', 'oui', 'ok'))
        if valid:
            self.core.clear_target(code)
        self.back_main_menu()

    def after_save_select(self, target):
        # Save components state and/or whole app configuration by writing formatted files (yaml, xml)
        target = self.get_choice_val(target)
        ask_path = lambda res, dflt : \
            self.get_user_in_or_dflt(dflt,
                                     f"Give a name for the {res} file to save in (not full path but with extension),\n"
                                     f"default full path : {dflt}\n[filename] :")
        set_current = lambda res, path : \
            self.get_user_confirm(marker=f"Use {path}\n as current file descriptor for {res}\n"
            f" so that next (auto-)save will be done considering this file? (y/N) :", empty_ok=False)
        if self.core_ctrl is not None:
            if target in ["routine", "app"]:
                f = ask_path("routine", self.core_ctrl.paths['routine'])
                full_path = self.core_ctrl.save_routine(filepath=f)
                if set_current("routine", full_path):
                    self.core_ctrl.set_current_routine(full_path)
            if target in ["netmap", "app"]:
                f = ask_path("netmap", self.core_ctrl.paths['netmap'])
                full_path = self.core_ctrl.save_netmap(filepath=f)
                if set_current("netmap", full_path):
                    self.core_ctrl.set_current_netmap(full_path)
            if target in ["config", "app"]:
                f = ask_path("app paths configuration", self.core_ctrl.paths['config'])
                full_path = self.core_ctrl.save_coreconfig(filepath=f)
                if set_current("app paths configuration", full_path):
                    self.core_ctrl.set_current_coreconfig(full_path)
            self.back_main_menu()
        else:
            print("No reference to the core controller where saving procedure is defined")
            self.no_wipe_next()

    def after_resume_slct(self, to_resume):
        target = self.get_choice_val(to_resume)
        self.core.resume_it(target)
        self.back_main_menu()

    def after_pause_slct(self, to_resume):
        target = self.get_choice_val(to_resume)
        self.core.pause_it(target)
        self.back_main_menu()

    def iv_creation(self, preset):
        if preset in ['basic', 'scratch']:
            mac = self.get_user_in_or_dflt(default=None, marker="[MAC address]: ")
            ip = self.get_user_in_or_dflt(default=None, marker="[IP address]: ")
            hostname = self.get_user_in_or_dflt(default=None, marker="[hostname]: ")
            vi = VirtualInstance(mac=mac, ip=ip, hostname=hostname, user_created=True)
            if preset == 'scratch':
                print("Add known port infos entries")
                port = self.get_user_in_or_dflt(default=None, marker="[used port]: ")
                while port is not None:
                    vi.get_ports_table().set_port(int(port))
                    port = self.get_user_in_or_dflt(default=None, marker="[used port]: ")
                print("Additional divers fields")
                for field in vi.unused_div_fields():
                    field_val = self.get_user_in_or_dflt(default=None, marker=f"[{field}]: ")
                    if field_val is not None:
                        vi.add_divinfo(field, field_val)
        mapid = self.get_user_in_or_dflt(default=None, marker="[map id?]: ")
        print(vi.detail_str(level=2))
        if self.get_user_confirm(f"Confirm [{mapid}] adding to netmap ? (Y/n)"):
            self.core.add_to_netmap(vi, mapid)
        self.back_main_menu()

    def after_remove_vi_slct(self, vi_mapid):
        self.core.remove_from_netmap(vi_mapid)
        self.back_main_menu()

    # ----- Menus configurations -----

    def get_choice_val(self, choice_code):
        return self.curr_menu['choices'][choice_code]

    def get_currmenu_index(self):
        return self.get_menu_index(self.curr_menu)

    def get_menu_index(self, menu):
        for menu_id, menu_dict in self.index_menus.items():
            if menu is menu_dict:
                return menu_id

    def setup_menus(self):

        # -- Main menus --
        self.main_menu = {'desc': "Main menu. Type $help for explanations and $choices to display which\n"
                                  "commands are available to navigate through menus and their description",
                          'help': get_res_CLI('main_help'),
                          'choices': {'create': "create",
                                      'remove': "remove",
                                      'clear': "clear",
                                      'show': "show",
                                      'pause': "pause",
                                      'resume': "resume",
                                      'save': "save"},
                          'fct_choice': self.transit_menu,
                          'disp_choice': True}

        self.create = {'desc': "Instantiate an object and integrate it in the application",
                       'help': get_res_CLI('create_help'),
                       'choices': {'module': "newMod",
                                   'virtual instance': "newVI"},
                       'fct_choice': self.transit_menu}

        self.remove = {'desc': "Remove an existing object in the app",
                       'help': get_res_CLI('remove_help'),
                       'choices': {'module': "delMod",
                                   'independent module': "delIndepMod",
                                   'virtual instance': "delVI"},
                       'dflt_choice': 'module',
                       'fct_choice': self.transit_menu}

        self.clear = {'desc': "Clear application elements containers as netmap, routine, independent modules, etc.",
                      'help': get_res_CLI('clear_help'),
                      'choices': {'whole app': "app",
                                  'netmap': "netmap",
                                  'routine': "routine",
                                  'independent modules': "indep",
                                  'library': "library"},
                      'fct_choice': self.after_clear_select}

        self.show = {'desc': "Display current state of application resources",
                     'help': get_res_CLI('show_help'),
                     'choices': [['app', 'routine', 'netmap', 'mods library', 'independent mods', 'main timer'],
                                 ['virtual instance', 'entry module in routine'],
                                 ['threat events', 'modification events']],
                     'dflt_choice': 'routine',
                     'fct_choice': self.after_show_select}

        self.save = {'desc': "Save the current application configuration or components separatly",
                     'help': get_res_CLI('save_help'),
                     'choices': {'whole app (yaml cfg + xml comp.)': "app",
                                 'app config (yaml)': "config",
                                 'routine (xml)': "routine",
                                 'netmap (xml)': "netmap"},
                     'dflt_choice': 'whole app (yaml cfg + xml comp.)',
                     'fct_choice': self.after_save_select}

        self.pause = {'desc': "Pause (interrupt running module threads) routine or its components",
                      'help': get_res_CLI('pause_help'),
                      'choices': {'entire routine': "routine",
                                  'panel only': "panel",
                                  'queue only': "queue"},
                      'dflt_choice': 'entire routine',
                      'fct_choice': self.after_pause_slct}

        self.resume = {'desc': "Resume or start routine or its components",
                       'help': get_res_CLI('resume_help'),
                       'choices': {'entire routine': "routine",
                                   'panel only': "panel",
                                   'queue only': "queue"},
                       'dflt_choice': 'entire routine',
                       'fct_choice': self.after_resume_slct}

        # -- Secondary menu --
        self.create_mod = {'desc': "Choose a module in the current library and instantiate it",
                           'marker': "[mod_id] :", 'choices': self.get_available_mods,
                           'fct_choice': self.after_mod_slct}

        self.create_VI = {'desc': "Create a new 'virtual instance' ie a network equipment in-app representation",
                          'choices': [['basic', 'scratch']],
                          'dflt_choice': 'basic',
                          'fct_choice': self.iv_creation}

        self.show_VI = {'desc': "Select an existing virtual instance and show its details (fields, linked events, ..)",
                        'marker': "[mapid] :", 'choices': self.get_map_mapids,
                        'fct_choice': self.after_show_vi_slct}

        self.show_modentry = {'desc': "Select a module entry in panel/queue to display info about this instance",
                              'marker': "[setid] :", 'choices': self.get_routine_setids,
                              'fct_choice': self.after_show_modentry_slct}

        self.remove_mod = {'desc': "Remove a module from routine by its setid",
                           'marker': "[setid] :", 'choices': self.get_routine_setids,
                           'fct_choice': self.after_remove_mod_slct}

        self.remove_indep_mod = {'desc': "Remove a module from routine independent running module"}

        self.remove_VI = {'desc': "Remove a virtual instance from the netmap by mapid",
                          'marker': "[mapid] :", 'choices': self.get_map_mapids,
                          'fct_choice': self.after_remove_vi_slct}

        # Association between choice code value and real menu objects
        self.index_menus = {"main": self.main_menu,
                            "create": self.create, "remove": self.remove,
                            "clear": self.clear,
                            "pause": self.pause, "resume": self.resume,
                            "show": self.show, "showVI": self.show_VI, "showEntry": self.show_modentry,
                            "save": self.save,
                            "newVI": self.create_VI, "newMod": self.create_mod,
                            "delMod": self.remove_mod, "delIndepMod": self.remove_indep_mod, "delVI": self.remove_VI}


if __name__ == "__main__":
    core = Core()
    parser = CLIparser(core)
    parser.start_parsing()
