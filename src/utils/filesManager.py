from src.utils.misc_fcts import get_root_path
from pathlib import Path

dflt_dirs = {
                    "root": get_root_path(),
                    "actives": 'modules/actives',
                    "passives": 'modules/passives',
                    "logs": 'logs',
                    "configs": 'svd/configs',
                    "netmaps": 'svd/netmaps',
                    "routines": 'svd/routines',
                    "tests": 'tests',
                    "div_outputs": 'tests/test_outputs'
                }

dflt_files = {
                "dflt_lib": ("configs", 'modlib.xml'),
                "dflt_logger": ("configs", 'default_logger.yaml'),
                "last_cfg": ("configs", 'last_coreconfig.yaml'),
                "last_routine": ("routines", 'last_routine.xml'),
                "last_netmap": ("netmaps", 'last_netmap.xml')
            }


def get_dflt_entry(index, suffix=None):
    if suffix is None:
        return FilesManager().get_res_path(index)
    return str(Path(FilesManager().get_res_path(index)) / suffix)


def clean_last_files():
    FilesManager().clean_last_files()


def complete_path(prefix, filename):
    return FilesManager().complete_path(prefix=prefix, filename=filename)


class FilesManager:

    def __init__(self, assoc_dirs=dflt_dirs, assoc_f=dflt_files):
        self.assoc_dirs = assoc_dirs.copy()
        self.assoc_f = assoc_f.copy()

    def new_file_entry(self, index, direntry_index, filename):
        self.assoc_f[index] = (direntry_index, filename)

    def new_dir_entry(self, index, dirpath):
        self.assoc_dirs[index] = dirpath

    def get_res_path(self, res):
        root = self.assoc_dirs.get("root")
        if root is None:
            raise FileNotFoundError
        infiles = self.assoc_f.get(res)
        if infiles is not None:
            # it's a file, have to get its location dir
            prefix = self.assoc_dirs.get(infiles[0])
            if prefix is not None:
                return str(root / prefix / infiles[1])
        else:
            # it's probably a project dir
            dirpath = self.assoc_dirs.get(res)
            if dirpath is not None:
                return str(root / dirpath)

    def complete_path(self, prefix, filename, dflt_ifnonexist='given'):
        if Path(filename).is_absolute():
            if dflt_ifnonexist == 'given':
                return filename
            return filename if self.check_file(filename) else dflt_ifnonexist
        dirpath = self.get_res_path(prefix)
        filepath = str(Path(dirpath) / filename)
        if dflt_ifnonexist == 'given':
            return filepath
        return filepath if self.check_file(filepath) else dflt_ifnonexist

    def check_file(self, path):
        try:
            self.get_res_path(path)
            from os.path import exists
            return exists(path)
        except FileNotFoundError:
            return False

    def check_all_files(self):
        missed = []
        for dir in self.assoc_dirs:
            full_path = self.get_res_path(dir)
            if full_path is None or not self.check_file(full_path):
                missed.append((dir, full_path))
        for file in self.assoc_f:
            if not self.assoc_f[file] in map(lambda x : x[0], missed):
                full_path = self.get_res_path(file)
                if full_path is None or not self.check_file(full_path):
                    missed.append((file, full_path))
        if len(missed) > 0:
            raise FileEntryError(self, missed)

    def clean_last_files(self):
        for f in ['last_cfg', 'last_routine', 'last_netmap']:
            path = self.get_res_path(f)
            with open(path, 'w'):
                pass

    def __str__(self):
        s = f"FileManager with following entries:\n"
        s += f" | DIR : {','.join(self.assoc_dirs.keys())}\n"
        s += f" | FILES : {','.join(self.assoc_f.keys())}\n"
        return s


class FileEntryError(Exception):

    def __init__(self, filemanager, wrong_entries):
        self.filemanager = filemanager
        self.wrong_entries = wrong_entries
        super().__init__(self.strerror())

    def strerror(self):
        s = f"Incorrect entries in dicts maintained by filemanager {repr(self.filemanager)}\n"
        s += f" wrong entries -> paths are following:\n"
        for entry, path in self.wrong_entries:
            s += f" > {entry} : {path}\n"
        return s


class ModuleIntegrator:
    """Flexible helper to new module integration in the application environment

    After a new module writing as a class inheriting abc(Facility)[Active|Passive]Module it should be properly
    integrated in the application. It means being included in the modules library, from where it can later be
    instantiated to manipulate instances of this new module in the application. It can be done programmatically
    with this helper object.

    """

    def __init__(self, module, module_class=None, library=None, auto_integrate=True):
        """

        Args:
            module (str or Module): target Module, if str it must correspond to python package where Module class is
            module_class: name of the class corresponding to the Module, not given implies autosearch by prefix [A|P]mod
            library: the library in which the Module will be included
            auto_integrate (bool): whether should integrate it after instantiating this object
        """
        # Try to find corresponding module class and instantiate it
        self.modinst = self.compute_modinst(module, module_class)
        self.library = self.compute_library(library)
        self.verify_module(self.modinst)
        if auto_integrate:
            self.integrate_module()

    def compute_modinst(self, module, module_class=None):
        from modules.abcModule import Module
        if isinstance(module, Module):
            return module
        elif isinstance(module, str):
            from importlib import import_module
            try:
                pymodule = import_module(module)
                if module_class is None:
                    # Searching in module class dir for the module class name
                    for direntry in dir(pymodule):
                        if direntry.startswith('AMod') or direntry.startswith('PMod'):
                            module_class = direntry
                            break
                    if module_class is None:
                        raise ModuleIntegrationError(f"Class guessing for Module in python module {module} failed.\n"
                                                     f"Check that the class name begins with 'AMod' or 'PMod'")
                return getattr(pymodule, module_class)()
            except ModuleNotFoundError:
                raise ModuleIntegrationError(f"Unable to import python module {module} supposed to contain the module\n"
                                             f"class definition abstracting an underlying program (inheriting Module).")
            except AttributeError:
                raise ModuleIntegrationError(f"Given python module {module} does not have class {module_class}\n"
                                             f"in its attributes.")

    def verify_module(self, instance):
        from modules.abcModule import Module
        from src.utils.misc_fcts import is_program_callable
        err_msg = ''
        if not isinstance(instance, Module):
            err_msg += "! The class designed as the Module implementation does not inherit of superclass Module"
        else:
            modid = instance.get_module_id().strip()
            if modid == '' or self.library.is_available(modid):
                err_msg += "! The module id must be a non-empty string unique among modules already present in library"
            cmd = instance.get_cmd().split()
            if cmd == [] or not is_program_callable(cmd[0]):
                err_msg += "\n! The command calling underlying program must be in the PATH or an executable filepath"
            archetype = instance.is_active()
            if not isinstance(archetype, bool):
                err_msg += "\n! The Module must indicate its corresponding execution archetype with is_active (boolean)"
        if err_msg != '':
            raise ModuleIntegrationError(err_msg)

    def compute_library(self, library):
        from src.utils.moduleManager import Library
        if isinstance(library, Library):
            return library
        elif isinstance(library, str):
            return Library(modlib_file=complete_path('configs', library))
        elif library is None:
            return Library()

    def get_module_id(self):
        return self.modinst.get_module_id()

    def integrate_module(self):
        """Include the module in the library collection

        """
        self.library.add_to_modlib_file(self.modinst)
        self.library.load_modlib()

    def __str__(self):
        from src.utils.misc_fcts import str_param_comp
        s = f">  Module integration to :\n{self.library.detail_str(level=1)}\n" \
            f">  From the instantiated module :\n"
        curr_params, dflt_params, desc_PARAMS = self.modinst.get_params()
        arch = 'ACTIVE' if self.modinst.is_active() else 'PASSIVE'
        s += f"| {arch} module whose description is given as :\n"
        s += f"|  {self.modinst.get_description()}\n"
        s += f"| Associated underlying program : {self.modinst.get_cmd()}\n"
        s += f"| Module parameters :\n"
        s += str_param_comp(curr_params, dflt_params, descriptions=desc_PARAMS, prefix='|  ')
        return s


class ModuleIntegrationError(Exception):

    def __init__(self, error):
        header = "Module integration resulted to an error with following feedback :\n"
        super().__init__(header + error)


if __name__ == '__main__':
    fm = FilesManager()
    print(fm.get_res_path("lib"))
    print(fm.get_res_path("configs"))
    fm.new_dir_entry("testdir", 'test')
    fm.new_file_entry("testfile", "testdir", 'testfile.test')
    print(fm.get_res_path("testdir"))
    print(fm.get_res_path("testfile"))
