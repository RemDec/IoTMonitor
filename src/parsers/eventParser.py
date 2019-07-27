from lxml import etree
from lxml.builder import E
from src.logging.modifEvent import ModifEvent
from src.logging.threatEvent import ThreatEvent


# --- Transform events instances into XML elements ---

def modif_to_XML(modifevent):
    modifelmt = E.modifevent(target=modifevent.modified_res, type=modifevent.obj_type)
    if modifevent.old_state is not None:
        modifelmt.append(E.oldstate(modifevent.old_state))
    if modifevent.new_state is not None:
        modifelmt.append(E.newstate(modifevent.new_state))
    div = E.diveventinfos()
    if modifevent.obj_id is not None:
        div.set("objid", modifevent.obj_id)
    if modifevent.modificator is not None:
        div.set("modificator", modifevent.modificator)
    modifelmt.append(div)
    return modifelmt


def threat_to_XML(threatevent):
    threatelmt = E.threatevent(originmod=threatevent.from_module, level=str(threatevent.level))
    if threatevent.msg is not None:
        threatelmt.append(E.alertmsg(threatevent.msg))
    if threatevent.patch is not None:
        threatelmt.append(E.patchmsg(threatevent.patch))
    div = E.diveventinfos()
    if threatevent.mapid is not None:
        div.set("objid", threatevent.mapid)
    threatelmt.append(div)
    return threatelmt


def event_to_XML(anyevent):
    if isinstance(anyevent, ModifEvent):
        return modif_to_XML(anyevent)
    elif isinstance(anyevent, ThreatEvent):
        return threat_to_XML(anyevent)


# --- Transform XML elements into events instances ---

def XML_to_modif(modif_elmt):
    modified_res = modif_elmt.get('target')
    obj_type = modif_elmt.get('type')
    oldstate_elmt = modif_elmt.find('oldstate')
    old_state = oldstate_elmt.text if oldstate_elmt is not None else None
    newstate_elmt = modif_elmt.find('newstate')
    new_state = newstate_elmt.text if newstate_elmt is not None else None
    div = modif_elmt.find('diveventinfos')
    obj_id = div.get('objid')
    modificator = div.get('modificator', 'app')
    return ModifEvent(modified_res, elmt_type=obj_type, elmt_id=obj_id, modificator=modificator,
                      old_state=old_state, new_state=new_state)


def XML_to_threat(threat_elmt):
    from_mod = threat_elmt.get("originmod")
    level = int(threat_elmt.get("level"))
    msg_elmt = threat_elmt.find('alertmsg')
    msg = msg_elmt.text if msg_elmt is not None else None
    patch_elmt = threat_elmt.find('patchmsg')
    patch = patch_elmt.text if patch_elmt is not None else None
    div = threat_elmt.find('diveventinfos')
    mapid = div.get('objid')
    return ThreatEvent(from_mod, level=level, mapid=mapid, msg=msg, patch=patch)


def XML_to_event(event_elmt):
    if event_elmt.tag == 'threatevent':
        return XML_to_threat(event_elmt)
    elif event_elmt.tag == 'modifevent':
        return XML_to_modif(event_elmt)


if __name__ == '__main__':
    t1 = ThreatEvent("mymodule", 3, "netmapVI_id", "Alert raised by module!")
    t2 = ThreatEvent("second_module", 5, "target_mapid", "Very SERIOUS alert!", patch="Consult CVE 555.11-23\nfor details")
    t3 = ThreatEvent("mymodule", 1, "target_mapid", "Same module raised easy alert")
    m1 = ModifEvent("instance MAC field", "virt_inst", "myinst_id", "scanmodule", "unknown", "1C:39:47:12:AA:B3")
    m2 = ModifEvent("'target' module parameter", "module", None, "app user", "192.168/16", "10.102/16")
    m3 = ModifEvent("VI hostname field", elmt_type='virt_inst', elmt_id='target_mapid', modificator='user',
                    old_state='old_hostname', new_state='NEW_HOSTNAME')
    print(etree.tostring(threat_to_XML(t1), pretty_print=True).decode())
    print(etree.tostring(threat_to_XML(t2), pretty_print=True).decode())
    print(etree.tostring(threat_to_XML(t3), pretty_print=True).decode())

    print(etree.tostring(modif_to_XML(m1), pretty_print=True).decode())
    print(etree.tostring(modif_to_XML(m2), pretty_print=True).decode())
    print(etree.tostring(modif_to_XML(m3), pretty_print=True).decode())