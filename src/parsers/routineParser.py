from lxml import etree
from lxml.builder import E
from src.utils.moduleManager import ModDescriptor
from src.utils.moduleManager import ModManager
from src.utils.filesManager import get_dflt_entry
from src.routine.routine import Routine, Queue, Panel


# --- Translating routine components to XML and writing it ---

def queue_to_XML(queue):
    queue_XML = E.queue(running=str(queue.is_running), nbr_mods=str(queue.get_nbr_mods()))
    for modentry in queue.get_modentries():
        qid, mod_inst, exptimer = modentry.qid, modentry.module, modentry.init_timer
        mod_desc = ModDescriptor(mod_inst=mod_inst, include_nondefault_param=True)
        queue_XML.append(mod_desc.modconfig_to_xml(set_id=qid, timer_val=exptimer))
    return queue_XML


def panel_to_XML(panel):
    pids = panel.get_idlist()
    panel_XML = E.panel(running=str(panel.is_running), nbr_mods=str(panel.get_nbr_mods()))
    for pid in pids:
        mod_inst = panel.get_mod_by_id(pid)
        mod_desc = ModDescriptor(mod_inst=mod_inst, include_nondefault_param=True)
        panel_XML.append(mod_desc.modconfig_to_xml(set_id=pid, timer_val=mod_inst.get_read_interval()))
    return panel_XML


def routine_to_XML(routine):
    routine_XML = E.routine(running=str(routine.is_running))
    routine_XML.append(queue_to_XML(routine.queue))
    routine_XML.append(panel_to_XML(routine.panel))
    return routine_XML


def write_routine_XML(routine, filepath=None):
    if filepath is None:
        filepath = get_dflt_entry('routines', suffix="last_routine.xml")
    tree = etree.ElementTree(E.xmlsave(routine_to_XML(routine)))
    tree.write(filepath, pretty_print=True, xml_declaration=True)


# --- Parse XML files to build routine elements instances ---

def XML_to_queue(queue_elmt, timer=None, netmap=None, modmanager=None):
    modmanager = modmanager if modmanager is not None else ModManager(load_direct=True)
    running = bool(queue_elmt.get('running'))
    queue = Queue(timer, netmap)
    for modconfig in queue_elmt.findall('modconfig'):
        mod_inst, qid, timer_val = modmanager.modinst_from_modconfig(modconfig, timer=timer, netmap=netmap)
        queue.add_module(mod_inst, given_timer=timer_val, given_id=qid)
    return queue, running


def XML_to_panel(panel_elmt, timer=None, netmap=None, modmanager=None):
    modmanager = modmanager if modmanager is not None else ModManager(load_direct=True)
    running = bool(panel_elmt.get('running'))
    panel = Panel(netmap=netmap)
    for modconfig in panel_elmt.findall('modconfig'):
        mod_inst, pid, read_interval_timer = modmanager.modinst_from_modconfig(modconfig, timer=timer, netmap=netmap)
        mod_inst.set_read_interval(read_interval_timer)
        panel.add_module(mod_inst, given_id=pid)
    return panel, running


def XML_to_routine(routine_elmt, timer=None, netmap=None,
                   modmanager=ModManager(load_direct=True)):
    queue_elmt = routine_elmt.find('queue')
    panel_elmt = routine_elmt.find('panel')
    queue, _ = XML_to_queue(queue_elmt, timer, netmap, modmanager)
    panel, _ = XML_to_panel(panel_elmt, timer, netmap, modmanager)
    return Routine(timer=timer, netmap=netmap, panel=panel, queue=queue)


def parse_routine_XML(filepath=None, resume_routine=False,
                      timer=None, netmap=None,
                      modmanager=ModManager(load_direct=True)):
    if filepath is None:
        filepath = get_dflt_entry('routines', suffix="last_routine.xml")
    with open(filepath, 'r') as f:
        tree = etree.parse(f)
        routine = XML_to_routine(tree.getroot().find('routine'), timer=timer, netmap=netmap, modmanager=modmanager)
        if resume_routine:
            routine.resume()
        return routine


if __name__ == '__main__':
    acts, pas = ModManager(load_direct=True).instantiate_all_available_mods()
    routine = Routine(modules=acts+pas)
    print("### Routine to save in XML ###")
    print(routine.detail_str(level=1))
    write_routine_XML(routine, get_dflt_entry('div_outputs', suffix="testRoutineXML.xml"))
    print("### XML reparsing routine ###")
    parsed_routine = parse_routine_XML(get_dflt_entry('div_outputs', suffix="testRoutineXML.xml"))
    print(parsed_routine.detail_str(level=1))
