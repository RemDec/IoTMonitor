from src.appcore import *
from src.utils.misc_fcts import str_multiframe
import os


class CLIparser:

    def __init__(self, core, core_controller=None):
        self.core_ctrl = core_controller
        self.core = core
        self.setup_menus()
        self.get_input = False
        self.curr_menu = {}
        self.curr_choices = []
        self.reserved = {'main()': self.back_main_menu, 'prev()': "",
                         'exit()': self.exit}
        self.clear_cls = True
        self.curr_display_lvl = 0

    def start_parsing(self):
        self.get_input = True
        self.curr_menu = self.main_menu
        self.loop_parsing()

    def stop_parsing(self):
        self.get_input = False

    def loop_parsing(self):
        while self.get_input:
            self.curr_choices = self.compute_choices()
            header = self.header_from_menu()
            user_in = input(header)
            if user_in in self.reserved:
                self.handle_reserved_kw(user_in)
            else:
                completed_in = self.match_input_to_choice(user_in)
                if len(completed_in) == 0:
                    print("No corresponding command for this menu")
                    self.clear_cls = False
                elif len(completed_in) > 1:
                    print("Ambiguous choice between", ', '.join(completed_in))
                    self.clear_cls = False
                else:
                    user_in = completed_in[0]
                    self.curr_menu['fct_choice'](user_in)
                self.clear_console()
                self.clear_cls = True

    def compute_choices(self):
        choices = self.curr_menu['choices']
        # treated choices format [[ch1, ch2, ..], [ch3, ch4, ..], ...] (1 list per newline)
        if callable(choices):
            return choices()
        if isinstance(choices, dict):
            return [choices.keys()]

    def header_from_menu(self):
        disp_desc = self.curr_menu.get('disp_desc', True)
        disp_choice = self.curr_menu.get('disp_choice', True)
        marker = self.curr_menu.get('marker', ">>>")
        s = ""
        if disp_desc and self.curr_menu['desc'] != "":
            s = str_multiframe(self.curr_menu['desc'])
        if disp_choice:
            s += "Following commands/choices are available :\n"
            for choice_line in self.curr_choices:
                s += ' | '.join(choice_line) + '\n'
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
        self.reserved[keyword]()

    def get_user_confirm(self, marker="Confirm ? (Y/n) ", val=('', 'y', 'o', 'yes', 'oui', 'ok')):
        res = input(marker)
        return res.lower() in val

    def clear_console(self):
        if self.clear_cls:
            os.system('cls' if os.name == 'nt' else 'clear')

    # Functions related to reserved keywords

    def back_main_menu(self):
        self.clear_console()
        self.clear_cls = True
        self.curr_menu = self.main_menu

    def exit(self, kill_app=False):
        if self.core_ctrl is not None:
            # exiting app delegated to controller
            self.core_ctrl.stop_app()
            return
        self.stop_parsing()
        if kill_app:
            self.core.quit()

    # Functions to get available command choices

    def get_availbale_mod(self):
        return self.core.get_available_mods(only_names=True)

    def get_routine_setids(self):
        return self.core.get_all_setids()

    # Functions called after a choice is taken (given as a string in arg)

    def transit_menu(self, menu_input_name):
        target_menu_index = self.curr_menu['choices'][menu_input_name]
        self.curr_menu = self.index_menus[target_menu_index]

    def after_mod_slct(self, mod_id):
        dflts = self.get_user_confirm(f"[{mod_id}] use defaults params (Y/n)? ")
        in_rout = self.get_user_confirm(f"[{mod_id}] append it in routine (Y/n) ?")
        if dflts:
            mod_inst = mod_id
        else:
            print("Get params entries from desc")
            input_params = {}
            _, PARAMS, desc_params = self.core.modmanager.get_mod_desc_params(mod_id)
            for code_param, (dflt, mand, pref) in PARAMS.items():
                desc = desc_params.get(code_param, "No parameter description")
                perm = "mandatory" if mand else "optional"
                flag = f"flag {pref}" if pref != "" else "no prefix"
                header = f"Parameter {code_param} ({perm}, {flag}) : {desc}"
                marker = f"[default:{dflt}] :"
                user_in = input(f"{header}\n{marker}")
                if user_in == "":
                    input_params[code_param] = dflt
                else:
                    input_params[code_param] = user_in
            mod_inst = self.core.instantiate_module(mod_id, curr_params=input_params)
        if in_rout:
            self.core.add_to_routine(mod_inst)
        else:
            self.core.add_indep_module(mod_inst)
        self.back_main_menu()

    def after_show_select(self, show_input_name):
        res_to_show = self.curr_menu['choices'][show_input_name]
        print(self.core.get_display(res_to_show, level=self.curr_display_lvl))
        self.clear_cls = False

    def after_delmod_slct(self, mod_setid):
        self.core.remove_from_routine(mod_setid)
        self.back_main_menu()

    def after_resume_slct(self, to_resume):
        target = self.get_choice_val(to_resume)
        self.core.resume_it(target)
        self.back_main_menu()

    # Menus configurations

    def get_choice_val(self, choice_code):
        return self.curr_menu['choices'][choice_code]

    def setup_menus(self):
        # -- Main menus --
        self.main_menu = {'desc': "",
                             'choices': {'create': "create",
                                         'remove': "remove",
                                         'show': "show",
                                         'pause': "pause",
                                         'resume': "resume"},
                             'fct_choice': self.transit_menu,
                             'disp_choice': False}

        self.create = {'desc': "Instantiate an object and integrate it",
                       'choices': {'module': "newMod",
                                   'virtual instance': "newVI"},
                       'fct_choice': self.transit_menu}

        self.remove = {'desc': "Remove an existing object in the app",
                       'choices': {'module': "delMod",
                                   'independent module': "delIndepMod",
                                   'virtual instance': "delVI"},
                       'fct_choice': self.transit_menu}

        self.show = {'desc': "Display current state of resources",
                     'choices': {'routine': "routine",
                                 'netmap': "netmap",
                                 'module library': "library",
                                 'main timer': "timer",
                                 'independent modules': "indep"},
                     'fct_choice': self.after_show_select}

        self.pause = {'desc': "", 'marker': ">>", 'choices': []}

        self.resume = {'desc': "Resume or start routine or its components",
                       'choices': {'entire routine': "routine",
                                   'panel only': "panel",
                                   'queue only': "queue"},
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

        # Association between choice code and real objects
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