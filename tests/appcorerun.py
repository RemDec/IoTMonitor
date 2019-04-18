from src.appcore import *
from src.utils.filesManager import FilesManager

core = Core()

print("## After default instantiating core ##\n", core)
print("## Loaded modules from dflt lib ##\n", core.get_available_mods(stringed=True))
nmap = core.instantiate_module("nmapexplo")

core.quit()