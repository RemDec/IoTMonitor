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
                "dflt_logger": ("configs", 'default_logger.yaml')
            }


def get_dflt_entry(index, suffix=None):
    if suffix is None:
        return FilesManager().get_res_path(index)
    return str(Path(FilesManager().get_res_path(index)) / suffix)


class FilesManager:

    def __init__(self, assoc_dirs=dflt_dirs, assoc_f=dflt_files):
        self.assoc_dirs = assoc_dirs
        self.assoc_f = assoc_f

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

    def check_file(self, path):
        return True

    def check_all_files(self):
        return True


if __name__ == '__main__':
    fm = FilesManager()
    print(fm.get_res_path("lib"))
    print(fm.get_res_path("configs"))
    fm.new_dir_entry("testdir", 'test')
    fm.new_file_entry("testfile", "testdir", 'testfile.test')
    print(fm.get_res_path("testdir"))
    print(fm.get_res_path("testfile"))
