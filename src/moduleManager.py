default_descfile = "../modules/modules_descriptor.xml"


class ModManager:

    def __init__(self, desc_file=default_descfile):
        self.desc_file = desc_file

    def to_xml_desc(self, mod_instance):
        # translation to xml general description, doesn't keep any settable param used in the module
        pass

    def params_to_xml(self, mod_instance):
        # generate xml struct with module proper identifier and used params on it, to reinstance later
        pass

    def add_to_desc_file(self, mod):
        # append a module signature on current used library
        pass

    def mod_desc_from_instance(self, mod_instance):
        # internal function. Return a mod descriptor easily translatable in different ways to xml
        pass

    def get_mod_desc(self, id):
        # create a module descriptor from entry in xml with id corresponding
        pass

    def get_all_desc(self):
        # fill a list with all module descriptors of registered modules in desc_file
        pass

    def is_available(self, mod_id):
        # check for presence and dependencies of the given module
        pass


class ModDescriptor:

    def __init__(self, mod_inst=None, xml_signature=None):
        self.extract_modinfos(mod_inst)
        self.extract_paraminfos(mod_inst)

    # ----- From module instance -----

    def extract_modinfos(self, mod_inst):
        self.m_id = mod_inst.get_module_id()
        self.m_active = mod_inst.is_active()
        self.short_desc = mod_inst.get_description()
        if self.m_active:
            self.def_timer = mod_inst.get_default_timer()
        else:
            self.def_timer = mod_inst.get_read_interval()

    def extract_paraminfos(self, mod_inst):
        pass

    # ----- To XML -----

    def modinfos_to_xml(self):
        pass

    def paraminfos_to_xml(self):
        pass

    # ----- From XML signature -----

    def parse_modinfos(self, xml_sign):
        pass

    def parse_paraminfos(self, xml_sign):
        pass

    # ----- To module instance -----

    def get_mod_instance(self):
        pass
