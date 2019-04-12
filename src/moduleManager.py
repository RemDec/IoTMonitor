from modules.abcModule import *
from lxml import etree
from lxml.builder import E

default_descfile = "../modules/modules_descriptor.xml"


class ModManager:

    def __init__(self, desc_file=default_descfile):
        self.desc_file = desc_file

    def to_xml_desc(self, mod_instance, keep_params=True):
        # translation to xml general description, doesn't keep any settable param used in the module
        return ModDescriptor(mod_inst=mod_instance).modinfos_to_xml(include_curr_param=keep_params)

    def curr_params_to_xml(self, mod_instance):
        # generate xml struct with module proper identifier and used params on it, to reinstance later
        pass

    def add_to_desc_file(self, mod):
        # append a module signature on current used library
        pass

    def mod_desc_from_instance(self, mod_instance):
        # internal function. Return a mod descriptor easily translatable in different ways to xml
        pass

    def get_mod_desc(self, id_or_inst):
        # create a module descriptor from entry in xml with id corresponding or existing module instance
        if isinstance(id_or_inst, str):
            pass
        elif isinstance(id_or_inst, Module):
            return ModDescriptor(mod_inst=id_or_inst)

    def get_all_desc(self):
        # fill a list with all module descriptors of registered modules in desc_file
        pass

    def is_available(self, mod_id):
        # check for presence and dependencies of the given module
        pass


class ModDescriptor:

    # Transitional class stating for a module created from a module instance or a XML code
    # and able to reoutput module configuration as another module instance or XML code
    # See it like a container for a module configuration (parameters, id, ...) from which you
    # can poll desired representation in a given format (instance or XML)
    #                      |-->|                   |-->
    #       mod. instance      |  mod. descriptor  |      XML signature/code
    #                       <--|                   |<--|

    def __init__(self, mod_inst=None, xml_signature=None):
        self.extract_modinfos(mod_inst)
        self.extract_paraminfos(mod_inst)
        self.parse_modinfos(xml_signature)
        self.parse_paraminfos(xml_signature)

    # ----- From module instance -----

    def extract_modinfos(self, mod_inst):
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

    def extract_paraminfos(self, mod_inst):
        self.curr_params, self.PARAMS, self.desc_params = mod_inst.get_params()

    # ----- To XML -----

    def modinfos_to_xml(self, include_curr_param=False):
        modtype = "actmod" if self.m_active else "passmod"
        modattr = {"id": self.m_id, "pymod": self.pymod, "pyclass": self.pyclass}
        saved_params = self.curr_param_to_xml() if include_curr_param else E.savedparams()
        xml = E(modtype,
                    E.desc(self.txt_desc),
                    self.defparam_to_xml(),
                    saved_params,
                    E.dependencies(),
                modattr)
        return xml

    def defparam_to_xml(self):
        params = E.defparams()
        for parname, (defval, mand, prefix) in self.PARAMS.items():
            desc = self.desc_params.get(parname)
            params.append(E.param(desc, code=parname, mandatory=str(mand), prefix=prefix))
        return params

    def curr_param_to_xml(self):
        saved_params = E.savedparams()
        for parname, value in self.curr_params.items():
            saved_params.append(E.param(code=parname, value=value))
        return saved_params

    # ----- From XML signature -----

    def parse_modinfos(self, xml_sign):
        pass

    def parse_paraminfos(self, xml_sign):
        pass

    # ----- To module instance -----

    def get_mod_instance(self, default_params=True):
        from importlib import import_module
        mod_inst = getattr(import_module(self.pymod), self.pyclass)()
        if default_params:
            return mod_inst
        mod_inst.set_params(self.curr_params)
        if not self.m_active:
            mod_inst.set_read_interval(self.def_timer)
        return mod_inst

    def __str__(self):
        modtype = "A" if self.m_active else "P"
        s = f"Module descriptor for [{self.m_id}]({modtype}) def in {self.pymod} by {self.pyclass} class\n"
        s += f"overlayer for cmd {self.cmd} with params {self.curr_params}"
        return s


if __name__ == '__main__':
    from modules.actives.nmapExplorer import *
    nmap = AModNmapExplorer(params={"IP": "MODIFIED PARAM"})
    desc = ModDescriptor(mod_inst=nmap)
    print(f"Got descriptor :\n{desc}")
    nmap2 = desc.get_mod_instance()
    print(f"Parameters of instance from desc :\n{nmap2.params}")
    nmap2 = desc.get_mod_instance(default_params=False)
    print(f"Parameters of instance from desc keeping curr par :\n{nmap2.params}")

    print(etree.tostring(desc.modinfos_to_xml(True), pretty_print=True).decode())
