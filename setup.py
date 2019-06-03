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
      install_requires=['PyYAML', 'lxml'])

print("--- Project specific operations ---\n")
print("  Be aware to install external dependencies with\n"
      "sudo apt-get install python-yaml python3-lxml libxml2-dev libxslt1-dev xterm")
print("  Cleaning target files for auto-save purpose...")
clean()
print("  Rewriting modules library based on programmatically defined default modules...")
print("  Empty autosave files...")
rewrite()
