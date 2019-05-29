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

    def complete_path(self, prefix, filename):
        if Path(filename).is_absolute():
            return filename
        dirpath = self.get_res_path(prefix)
        return str(Path(dirpath) / filename)

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

    def __init__(self, module, module_class=None, library=None, auto_integrate=True):
        self.modinst = self.compute_modinst(module, module_class)
        self.library = self.compute_library(library)
        self.library.load_modlib()
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
                    # Searching in module dir for the module class name
                    for direntry in dir(pymodule):
                        if direntry.startswith('AMod') or direntry.startswith('PMod'):
                            module_class = direntry
                            break
                    if module_class is None:
                        raise NotImplementedError(f"Class guessing for Module in python module {module} failed.\n"
                                                  f"Check that the class name begins with 'AMod' or 'PMod'")
                return getattr(pymodule, module_class)()
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(f"Unable to import python {module} supposed to contain Module class def.")

    def compute_library(self, library):
        from src.utils.moduleManager import ModManager
        if isinstance(library, ModManager):
            return library
        elif isinstance(library, str):
            return ModManager(modlib_file=complete_path('configs', library))
        elif library is None:
            return ModManager()

    def integrate_module(self):
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


if __name__ == '__main__':
    fm = FilesManager()
    print(fm.get_res_path("lib"))
    print(fm.get_res_path("configs"))
    fm.new_dir_entry("testdir", 'test')
    fm.new_file_entry("testfile", "testdir", 'testfile.test')
    print(fm.get_res_path("testdir"))
    print(fm.get_res_path("testfile"))
