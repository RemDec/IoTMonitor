
class ModifEvent:
    """

    A Modification Event is mainly represented by an 'old state' and a 'new state', state is relative to a value of
    something in the application (it is arbitrary). However, the concerned element must be of a type in a defined list.
    The modification is likely relative to a resource of the element. For example the value of IP field (resource) for
    a given Virtual Instance (element of type virt_inst). If the element has an id that identifies it in the app like
    a mapid for a VI or a setid for a routine Module, it may be passed to the constructor.
    """

    def __init__(self, modified_res, obj_type='app_res', obj_id=None, modificator='app', old_state=None, new_state=None):
        """

        Args:
            modified_res(str): arbitrary string describing the modified resource
            obj_type(str): one of available element whose resource can be modified, or 'app_res' if not determined
            obj_id(str): the id of the element identifying it in the app component or None if undetermined
            modificator(str): a string describing the origin of the modification (likely a module id or the user)
            old_state(str): the resource state before modification
            new_state(str): the resource state after modification
        """
        self.OBJ_TYPES = ['app_res', 'app_cfg', 'library', 'routine', 'module', 'netmap', 'virt_inst',
                          'indep', 'indep_mod']
        self.modified_res = modified_res
        self.obj_type = self.verify_res_type(obj_type)
        self.obj_id = obj_id
        self.modificator = modificator
        self.old_state = old_state
        self.new_state = new_state

    def verify_res_type(self, given_type):
        if not(given_type in self.OBJ_TYPES):
            return 'app_res'
        return given_type

    def is_relative_to_obj(self, obj_str):
        return obj_str == self.obj_type

    def is_relative_to_id(self, app_id):
        if self.obj_id is None:
            return False
        return app_id == self.obj_id

    def rel_to_vi(self):
        if self.obj_id is None or self.obj_id == "":
            return False
        return self.obj_id

    def __eq__(self, other):
        if not isinstance(other, ModifEvent):
            return False
        same_target = (self.modified_res, self.obj_type, self.obj_id) == (other.modified_res, other.obj_type, other.obj_id)
        same_modif = (self.old_state, self.new_state) == (other.old_state, other.new_state)
        return same_target and same_modif

    def detail_str(self, level=1):
        id = f"id in app:{self.obj_id}, " if self.obj_id is not None else ""
        typ = f"object type:{self.obj_type}"
        s = f"-o- modification on object resource {self.modified_res} ({id}{typ}) by {self.modificator}\n"
        if level == 1:
            if self.old_state is None:
                s += f"    no old state provided\n"
            else:
                s += f"    old state was : {self.old_state}\n"
            if self.new_state is None:
                s += f"    no new state provided\n"
            else:
                s += f"    new state is {self.new_state}\n"
        elif level >= 2:
            if self.old_state is None:
                s += f"----| no old state description provided\n"
            else:
                s += f"----| old state description :\n{self.old_state}\n"
            if self.new_state is None:
                s += f"----| no new state description provided\n"
            else:
                s += f"----| new state description is \n{self.new_state}\n"
        return s

    def __str__(self):
        return self.detail_str()


