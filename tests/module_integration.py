from src.utils.filesManager import ModuleIntegrator, get_dflt_entry
from src.utils.moduleManager import Library
from modules.actives.nmapExplorer import AModNmapExplorer
from modules.actives.nmapPortDiscovery import AModNmapPortDisc
from modules.passives.pingTarget import PModPing

libtestpath = get_dflt_entry("div_outputs", 'void_modlib.xml')

with open(libtestpath, 'w'):
    pass

modlib = Library(modlib_file=libtestpath)
modinst = AModNmapExplorer()
modinst2 = PModPing()
modinst3 = AModNmapPortDisc()

#modlib.create_modlib(modlist=[modinst])
ModuleIntegrator(modinst, library=libtestpath)
ModuleIntegrator(modinst2, library=libtestpath)
ModuleIntegrator(modinst3, library=libtestpath)

ModuleIntegrator('modules.actives.arbitraryCmd', module_class='AModArbitraryCmd', library=libtestpath)
ModuleIntegrator('modules.passives.arbitraryCmdBg', library=libtestpath)