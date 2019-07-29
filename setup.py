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

print("\n--- Project specific operations ---\n")
print("  > Be aware to install external dependencies if autoinstall with 'develop' didn't work, use\n"
      "sudo apt-get install python-yaml python3-lxml libxml2-dev libxslt1-dev xterm\n")
print("  > Underlying Modules programs (nmap for example) must be installed on this system. Such programs\n"
      "  referenced in the used Modules Library can be automatically installed using --installprogs flag\n"
      "  at application call (IoTmonitor.py execution with python 3.7)(add -h flag to get help on it)\n")
print("  > Cleaning target files for auto-save purpose...\n")
clean()
print("  > Rewriting modules library based on programmatically defined default modules...\n")
rewrite()
