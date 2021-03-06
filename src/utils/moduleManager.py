from lxml import etree
from lxml.builder import E
from src.utils.misc_fcts import str_param_comp
from src.utils.filesManager import get_dflt_entry

default_libfile = get_dflt_entry("dflt_lib")


class Library:

    def __init__(self, modlib_file=default_libfile, load_direct=False):
        self.modlib_file = modlib_file
        self.available_mods = []
        if load_direct:
            self.load_modlib()

    def create_modlib(self, modlist=[], include_nondefault_param=False):
        actives = E.actives()
        passives = E.passives()
        tree = etree.ElementTree(E.modlib(actives, passives))
        for mod_instance in modlist:
            mod_desc = ModDescriptor(mod_inst=mod_instance, include_nondefault_param=include_nondefault_param)
            entry = mod_desc.modinfos_to_xml(include_nondefault_param=include_nondefault_param)
            if mod_desc.m_active:
                actives.append(entry)
            else:
                passives.append(entry)
            self.available_mods.append(mod_desc)
        tree.write(self.modlib_file, pretty_print=True, xml_declaration=True)

    def load_modlib(self):
        # parse de module library file to build available modules descriptors
        self.clear()
        if self.modfile_empty():
            return
        with open(self.modlib_file, 'r') as f:
            tree = etree.parse(f)
        root = tree.getroot()
        infoslist = root.find("actives").findall("actmod") + root.find("passives").findall("passmod")
        for mod in infoslist:
            self.available_mods.append(ModDescriptor(xml_tree=mod))

    def add_to_modlib_file(self, mod):
        # append a module signature on current used module library in modlib_file
        if self.modfile_empty():
            self.create_modlib(modlist=[mod])
            return
        if self.is_available(mod.get_module_id()):
            return
        parser = etree.XMLParser(remove_blank_text=True)
        modlib_elmt = etree.parse(self.modlib_file, parser).getroot()
        target_container = modlib_elmt.find("actives") if mod.is_active() else modlib_elmt.find("passives")
        xml_element_mod = ModDescriptor(mod_inst=mod).modinfos_to_xml()
        target_container.append(xml_element_mod)
        etree.ElementTree(modlib_elmt).write(self.modlib_file, pretty_print=True)

    def change_modlib(self, new_file):
        self.modlib_file = new_file
        self.load_modlib()

    def clear(self):
        self.available_mods.clear()

    def get_mod_from_id(self, id, curr_params=None, timer=None, netmap=None):
        # from mod_id and current module descriptors list, instantiate a fresh module instance
        for mod_desc in self.available_mods:
            if mod_desc.m_id == id:
                mod_inst = mod_desc.get_mod_instance(timer=timer, netmap=netmap)
                if curr_params is not None:
                    mod_inst.set_params(curr_params)
                return mod_inst

    def get_mod_desc_params(self, id):
        desc = self.get_mod_desc(id)
        if desc is not None:
            return desc.get_all_params()

    def is_available(self, mod_id, reload_lib=False):
        # check for presence and dependencies of the given module
        for mod_desc in self.available_mods:
            if mod_desc.m_id == mod_id:
                return True
        if reload_lib:
            self.load_modlib()
            return self.is_available(mod_id)
        return False

    def modinfos_to_xml(self, mod_instance, keep_params=True):
        # translation to xml general description, doesn't keep any settable param used in the module
        return ModDescriptor(mod_inst=mod_instance).modinfos_to_xml(include_nondefault_param=keep_params)

    def modconfig_to_xml(self, mod_instance, set_id=None):
        # generate xml struct with module proper identifier and used params on it (not all general), to reinstance later
        return ModDescriptor(mod_inst=mod_instance).modconfig_to_xml(set_id)

    def modinst_from_modconfig(self, xml_config, timer=None, netmap=None):
        # instantiate a module from its xml modconfig element (as returned by modconfig_to_xml) and set params in config
        mod_desc = ModDescriptor()
        mod_desc.parse_modconfig(xml_config)
        if self.is_available(mod_desc.m_id):
            mod_inst = self.get_mod_from_id(mod_desc.m_id, timer=timer, netmap=netmap)
            mod_inst.set_params(mod_desc.curr_params)
            timer_val = mod_desc.def_timer if not(mod_desc.def_timer is None or mod_desc.def_timer < 1) else 0
            return mod_inst, mod_desc.setid, timer_val

    def get_mod_desc(self, id):
        for desc in self.available_mods:
            if desc.m_id == id:
                return desc

    def get_all_desc(self):
        # return a list with all module descriptors of registered modules in modlib_file
        return self.available_mods

    def list_all_mod_desc(self):
        actives = [desc for desc in self.available_mods if desc.m_active]
        passives = [desc for desc in self.available_mods if not desc.m_active]
        return actives, passives

    def list_all_modid(self):
        act = [desc.m_id for desc in self.available_mods if desc.m_active]
        pas = [desc.m_id for desc in self.available_mods if not desc.m_active]
        return act, pas

    def instantiate_all_available_mods(self, timer=None, netmap=None):
        actives_desc, passives_desc = self.list_all_mod_desc()
        act_instances = [mod_desc.get_mod_instance(timer=timer, netmap=netmap) for mod_desc in actives_desc]
        pas_instances = [mod_desc.get_mod_instance(timer=timer, netmap=netmap) for mod_desc in passives_desc]
        return act_instances, pas_instances

    def modfile_empty(self):
        from os import stat
        return stat(self.modlib_file).st_size == 0

    def detail_str(self, level=0):
        s = f"Module manager (library) loaded from {self.modlib_file}\n"
        if level == 0:
            s += f"currently maintaining {len(self.available_mods)} modules"
        elif level == 1:
            act, pas = self.list_all_modid()
            s += f"listing current available modules from this file:\n" \
                 f"Actives: {', '.join(act)}\n" \
                 f"Passives: {', '.join(pas)}\n"
        else:
            act, pas = self.list_all_mod_desc()
            s += f"maintaining following module descriptors :\n"
            s += f"\n      <[[ {len(act)} ACTIVE MODULES ]]>\n"
            for desc in act:
                s += f" < {desc.m_id} >\n{desc}\n"

            s += f"\n      <[[ {len(pas)} PASSIVE MODULES ]]>\n"
            for desc in pas:
                s += f" < {desc.m_id} >\n{desc}\n"
        return s

    def __str__(self):
        return self.detail_str(level=1)


class ModDescriptor:
    """

    Transitional class stating for a module created from a module instance or a XML code and able to reoutput module
    configuration as another module instance or XML code. See it like a container for a module configuration
    (parameters, id, ...) from which you can poll desired representation in a given form (instance or XML)
                         |-->|                   |-->
          mod. instance      |  mod. descriptor  |      XML signature/code
                          <--|                   |<--|
    A Module can be divided in 2 info sets : Module infos (modinfos) stands for general values relative to the Module
    class, like its modid, description, default timer, class name and python module defined in. Module configuration is
    relative to the current parameters of a Module instance, its id in the app.
    """

    def __init__(self, mod_inst=None, xml_tree=None, include_nondefault_param=False):
        self.m_id = "unknown"
        self.m_active = False
        self.setid = "unknown"
        self.txt_desc = "No module description provided"
        self.cmd = "unknown"
        self.def_timer = -1
        self.pymod = "unknown python module"
        self.pyclass = "unknown python class"
        self.install = {}
        self.curr_params, self.PARAMS, self.desc_params = ({}, {}, {})
        if mod_inst is not None:
            self.extract_modinfos(mod_inst, include_nondefault_param)
        if xml_tree is not None:
            self.parse_modinfos(xml_tree, include_nondefault_param)

    # ----- From module instance -----

    def extract_modinfos(self, mod_inst, include_nondefault_param=False):
        self.m_id = mod_inst.get_module_id()
        self.m_active = mod_inst.is_active()
        self.txt_desc = mod_inst.get_description()
        self.cmd = mod_inst.get_cmd()
        if self.m_active:
            self.def_timer = mod_inst.get_default_timer()
        else:
            self.def_timer = mod_inst.get_read_interval()
        self.pymod = mod_inst.__module__
        self.pyclass = mod_inst.__class__.__name__
        self.install = mod_inst.install_info() if mod_inst.install_info() is not None else {}
        self.extract_paraminfos(mod_inst, include_nondefault_param)

    def extract_paraminfos(self, mod_inst, include_nondefault_param):
        all_params = mod_inst.get_params()
        if include_nondefault_param:
            self.curr_params, self.PARAMS, self.desc_params = all_params
        else:
            self.PARAMS, self.desc_params = all_params[1], all_params[2]

    # ----- To XML -----

    def modinfos_to_xml(self, include_nondefault_param=False):
        # outputs a XML tree describing the module itself
        modtype = "actmod" if self.m_active else "passmod"
        modattr = {"modid": self.m_id, "cmd": self.cmd, "pymod": self.pymod, "pyclass": self.pyclass}
        saved_params = self.curr_param_to_xml() if include_nondefault_param else E.savedparams()
        xml = E(modtype,
                E.desc(self.txt_desc),
                self.defparam_to_xml(),
                saved_params,
                self.install_info_to_xml(),
                modattr)
        return xml

    def modconfig_to_xml(self, set_id=None, timer_val=None):
        # generate a XML saving module configuration and set identifier (pid or qid)
        # reference the m_id of the module so it can be reinstancied using a modinfo entry
        # (which indicates corresponding python module to import, classname, ...)
        if set_id is None:
            xml = E.modconfig(modid=self.m_id)
        else:
            if timer_val is None:
                xml = E.modconfig(modid=self.m_id, setid=set_id)
            else:
                xml = E.modconfig(modid=self.m_id, setid=set_id, timer=str(timer_val))
        xml.append(self.curr_param_to_xml())
        return xml

    def install_info_to_xml(self):
        install_elmt = etree.Element("install")
        if self.install.get('program', False):
            install_elmt.set('program', self.install['program'])
        if self.install.get('version', False):
            install_elmt.set('version', self.install['version'])
        if self.install.get('install', False):
            for manager, package in self.install['install'].items():
                if package is not None:
                    elmt_package = E.package(manager=manager, name=package)
                    install_elmt.append(elmt_package)
        return install_elmt
                
    def defparam_to_xml(self):
        params = E.defparams()
        for parname, (defval, mand, prefix) in self.PARAMS.items():
            desc = self.desc_params.get(parname, 'no description')
            attributes = {'code': parname, 'mandatory': str(mand), 'default': defval, 'prefix': prefix}
            params.append(E.param(desc, attributes))
        return params

    def curr_param_to_xml(self):
        saved_params = E.savedparams()
        for parname, value in self.curr_params.items():
            saved_params.append(E.param(code=parname, value=value))
        return saved_params

    # ----- From XML tree -----

    def parse_modinfos(self, xml_tree, saved_params=True):
        # xml sign should be element 'actmod' or 'passmod' as returned by modinfos_xml()
        if xml_tree.tag == "actmod":
            self.m_active = True
        self.m_id = xml_tree.get("modid")
        self.cmd = xml_tree.get("cmd")
        self.pymod = xml_tree.get("pymod")
        self.pyclass = xml_tree.get("pyclass")
        self.txt_desc = xml_tree.find("desc").text
        self.parse_install(xml_tree.find('install'))
        self.parse_defparam(xml_tree)
        if saved_params:
            self.parse_savedparam(xml_tree)

    def parse_modconfig(self, xml_tree):
        # modconfig is a save of parameters for a module, including the unique id of this module and
        # setid, permitting to reinstanciate it if we have the corresp mod_id class (need pymod pyclass
        # defined in self in addition to do it with self.get_mod_instance())
        self.m_id = xml_tree.get("modid")
        self.setid = xml_tree.get("setid")
        try:
            self.def_timer = int(xml_tree.get("timer"))
        except (ValueError, TypeError):
            pass
        self.parse_savedparam(xml_tree)

    def parse_install(self, xml_install):
        if xml_install.get('program'):
            self.install['program'] = xml_install.get('program')
        if xml_install.get('version'):
            self.install['version'] = xml_install.get('version')
        if self.install.get('install') is None:
            self.install['install'] = {}
        for package in xml_install.findall('package'):
            self.install['install'][package.get('manager')] = package.get('name')

    def parse_defparam(self, xml_tree):
        defaults = xml_tree.find("defparams")
        params = defaults.findall("param")
        for param in params:
            code = param.get("code")
            mand = True if param.get("mandatory") == "True" else False
            dflt_paramtuple = (param.get("default"), mand, param.get("prefix"))
            self.PARAMS[code] = dflt_paramtuple
            self.desc_params[code] = param.text
        return self.PARAMS, self.desc_params

    def parse_savedparam(self, xml_tree):
        saved = xml_tree.find("savedparams")
        params = saved.findall("param")
        for param in params:
            self.curr_params[param.get("code")] = param.get("value")
        return self.curr_params

    # ----- To module instance -----

    def get_mod_instance(self, default_params=True, timer=None, netmap=None):
        from importlib import import_module
        modclass = getattr(import_module(self.pymod), self.pyclass)
        mod_inst = modclass(netmap=netmap) if self.m_active else modclass(timer=timer, netmap=netmap)
        if default_params:
            return mod_inst
        mod_inst.set_params(self.curr_params)
        if not self.m_active:
            mod_inst.set_read_interval(self.def_timer)
        return mod_inst

    # ----- Misc -----

    def get_all_params(self):
        return self.curr_params, self.PARAMS, self.desc_params

    def __str__(self):
        modtype = "A" if self.m_active else "P"
        params_comp = str_param_comp(self.curr_params, self.PARAMS, descriptions=self.desc_params, prefix='| ')
        s = f"Module descriptor for [{self.m_id}]({modtype}) def in {self.pymod} by {self.pyclass} class.\n" \
            f"Description : {self.txt_desc}\n"
        s += f"Overlayer for program '{self.cmd}' with considered param setup :\n{params_comp}"
        return s


if __name__ == '__main__':
    from modules.actives.nmapExplorer import *
    nmap = AModNmapExplorer(params={"IP": "MODIFIED PARAM"})
    desc = ModDescriptor(mod_inst=nmap, include_nondefault_param=True)
    print(f"## Got descriptor from nmap instance : ##\n{desc}")
    nmap2 = desc.get_mod_instance()
    print(f"Parameters of instance from desc :\n{nmap2.params}")
    nmap2 = desc.get_mod_instance(default_params=False)
    print(f"Parameters of instance from desc keeping curr par :\n{nmap2.params}")

    print("## Mod desc infos to XML ##\n", etree.tostring(desc.modinfos_to_xml(True), pretty_print=True).decode())
    print("## Mod desc config to XML ##\n", etree.tostring(desc.modconfig_to_xml("givenqid"), pretty_print=True).decode())

    from modules.passives.pingTarget import *
    ping = PModPing()
    manager = Library(get_dflt_entry("div_outputs", suffix="testModManager.xml"))
    manager.create_modlib([nmap, nmap2, ping], True)
    manager.load_modlib()
    print("## Create and reload modlib ##")
    for mod in manager.available_mods:
        print(mod)