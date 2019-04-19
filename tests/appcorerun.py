from src.appcore import *
from time import sleep

core = Core()

print("## After default instantiating core ##\n", core)
print("## Loaded modules from dflt lib ##\n", core.get_available_mods(stringed=True))
nmap = core.instantiate_module("nmapexplo")
core.add_to_routine("arbcmd", "CMD_name", 20)
core.add_to_routine(nmap, "Nmap", 30)
print("## After adding actives in Queue ##\n", core)
core.add_to_routine("pingit", given_timer=10)
cmdbg = core.instantiate_module("arbcmd_bg")
core.add_to_routine(cmdbg)
print("## After adding passives in Panel ##\n", core)

print("\n\n## Starting routine ... ##\n")
core.resume()

for i in range(2):
    sleep(10)
    print(f"\n\n## After {i*10} seconds ##\n", core)

core.change_mod_params("Nmap", {"IP": "192.168.0.*"})
sleep(2)

print("\n\n ## After changing Nmap params ##\n", core)

import threading
print(threading.enumerate())
core.quit()
print(threading.enumerate())