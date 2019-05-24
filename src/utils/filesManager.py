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


if __name__ == '__main__':
    fm = FilesManager()
    print(fm.get_res_path("lib"))
    print(fm.get_res_path("configs"))
    fm.new_dir_entry("testdir", 'test')
    fm.new_file_entry("testfile", "testdir", 'testfile.test')
    print(fm.get_res_path("testdir"))
    print(fm.get_res_path("testfile"))
