
virt_inst = {}
module = {'desc': "Instantiate a new module", 'choices' : ['test1', 'test2']}

create = {'desc': "Create an object to insert in the app", 'choices': {'VI' : virt_inst, 'module': module}}

curr = create
while True:
    c = curr['choices']
    choices = str(c.keys()) if isinstance(c, dict) else str(c)
    i = input(f"{curr['desc']}\n{choices}\n>>>")
    curr = curr['choices'][i]