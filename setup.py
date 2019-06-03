from setuptools import setup


def clean():
    from src.utils.filesManager import clean_last_files
    clean_last_files()


def rewrite():
    from src.utils.misc_fcts import write_modlib
    from src.utils.filesManager import clean_last_files
    write_modlib()
    clean_last_files()


setup(name='IoTMonitor',
      version='1.0',
      description='Home monitoring tool and framework',
      url='https://github.com/RemDec/IoTMonitor',
      author='Remy Decocq',
      author_email='remy.decocq@student.umons.ac.be',
      license='GNU',
      packages=['src', 'modules'],
      install_requires=['lxml'])

print("--- Project specific operations ---\n")
print("  Cleaning target files for auto-save purpose...")
clean()
print("  Rewriting modules library based on programmatically defined default modules...")
print("  Empty autosave files...")
rewrite()
