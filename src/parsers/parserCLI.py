from src.appcore import *
from src.utils.misc_fcts import str_multiframe
from src.parsers.parser_res import get_res_CLI
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
        self.curr_display_lvl = 1

    # ----- Parsing execution flow -----

    def start_parsing(self):
        self.get_input = True
        self.curr_menu = self.main_menu
        self.loop_parsing()

    def stop_parsing(self):
        self.get_input = False

    def loop_parsing(self):
        while self.get_input:
            self.curr_choices = self.compute_curr_choices()
            header = self.header_from_menu(include_header=self.display_header)
            user_in = input(header)
            self.display_header = True
            if user_in.startswith('$'):
                self.handle_reserved_kw(user_in[1:])
            else:
                if user_in == "" and self.curr_menu.get('dflt_choice', False):
                    user_in = self.curr_menu['dflt_choice']
                completed_in = self.match_input_to_choice(user_in)
                if len(completed_in) == 0:
                    print(f"No corresponding choice for this menu [id:{self.get_currmenu_index()}]"
                          f" (type $choices or $help)")
                    self.no_wipe_next()
                elif len(completed_in) > 1:
                    print("Ambiguous choice between", ', '.join(completed_in))
                    self.no_wipe_next()
                else:
                    user_in = completed_in[0]
                    self.curr_menu['fct_choice'](user_in)
                self.clear_console()
                self.clear_cls = True

    # ----- Internal utilities functions -----

    def compute_curr_choices(self):
        return self.compute_choices(self.curr_menu)

    def compute_choices(self, menu):
        choices = menu['choices']
        # treated choices format [[ch1, ch2, ..], [ch3, ch4, ..], ...] (1 list per newline)
        if callable(choices):
            return choices()
        if isinstance(choices, dict):
            return [choices.keys()]

    def str_curr_choices(self):
        return self.str_choices(self.curr_menu, 0)

    def str_choices(self, menu, detail_lvl=None):
        detail_lvl = self.curr_display_lvl if detail_lvl is None else detail_lvl
        s = ""
        dflt_choice = menu.get('dflt_choice', None)
        if detail_lvl == 0:
            for choice_line in self.compute_choices(menu):
                with_indic_dflt = [choice if choice != dflt_choice else f"< {choice} >" for choice in choice_line]
                s += ' | '.join(with_indic_dflt) + '\n'
        else:
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
                s = str_multiframe(f"[{self.get_currmenu_index()}] {self.curr_menu['desc']}")
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

    def handle_reserved_kw(self, keyword):
        # keyword is all command without the '$' prefix
        cmd = list(filter(None, keyword.split(' ')))
        self.reserved[cmd.pop(0)](args=cmd)

    def get_user_confirm(self, marker="Confirm ? (Y/n) ", val=('', 'y', 'o', 'yes', 'oui', 'ok')):
        res = input(marker)
        return res.lower() in val

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
            print("No application view instance currently working")
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

    def get_availbale_mod(self):
        return self.core.get_available_mods(only_names=True)

    def get_routine_setids(self):
        return self.core.get_all_setids()

    # ----- Functions called after a choice is taken (given as a string in arg) -----

    def transit_menu(self, menu_input_name):
        target_menu_index = self.curr_menu['choices'][menu_input_name]
        self.curr_menu = self.index_menus[target_menu_index]

    def after_mod_slct(self, mod_id):
        dflts = self.get_user_confirm(f"[{mod_id}] use defaults params (Y/n)? ")
        in_rout = self.get_user_confirm(f"[{mod_id}] append it in routine (Y/n) ?")
        if dflts:
            mod_inst = mod_id
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
        if in_rout:
            setid = self.get_user_in_or_dflt(None, marker="Give a setid if desired (alphanumeric)\n[setid] :")
            self.core.add_to_routine(mod_inst, given_setid=setid)
        else:
            self.core.add_indep_module(mod_inst)
        self.back_main_menu()

    def after_show_select(self, show_input_name):
        res_to_show = self.curr_menu['choices'][show_input_name]
        print(self.core.get_display(res_to_show, level=self.curr_display_lvl))
        self.no_wipe_next()

    def after_delmod_slct(self, mod_setid):
        self.core.remove_from_routine(mod_setid)
        self.back_main_menu()

    def after_resume_slct(self, to_resume):
        target = self.get_choice_val(to_resume)
        self.core.resume_it(target)
        self.back_main_menu()

    def after_pause_slct(self, to_resume):
        target = self.get_choice_val(to_resume)
        self.core.pause_it(target)
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
                                      'show': "show",
                                      'pause': "pause",
                                      'resume': "resume"},
                          'fct_choice': self.transit_menu,
                          'disp_choice': False}

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

        self.show = {'desc': "Display current state of application resources",
                     'help': get_res_CLI('show_help'),
                     'choices': {'routine': "routine",
                                 'netmap': "netmap",
                                 'module library': "library",
                                 'main timer': "timer",
                                 'independent modules': "indep"},
                     'dflt_choice': 'routine',
                     'fct_choice': self.after_show_select}

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
        self.create_mod = {'desc': "Choose a module in the current library",
                           'marker': "[mod_id] :", 'choices': self.get_availbale_mod,
                           'fct_choice': self.after_mod_slct}

        self.create_VI = {'desc': "", 'marker': ">>", 'choices': []}

        self.remove_mod = {'desc': "Remove a module from routine by its setid",
                           'marker': "[setid] :", 'choices': self.get_routine_setids,
                           'fct_choice': self.after_delmod_slct}

        self.remove_indep_mod = {'desc': "Remove a module from routine independent running module"}

        self.remove_VI = {'desc': "Remove a virtual instance from the netmap"}

        # Association between choice code value and real menu objects
        self.index_menus = {"main": self.main_menu,
                            "create": self.create, "remove": self.remove,
                            "pause": self.pause, "resume": self.resume,
                            "show": self.show,
                            "newVI": self.create_VI, "newMod": self.create_mod,
                            "delMod": self.remove_mod, "delIndepMod": self.remove_indep_mod, "delVI": self.remove_VI}


if __name__ == "__main__":
    core = Core()
    parser = CLIparser(core)
    parser.start_parsing()
