from asyncio import BoundedSemaphore
import bpy



def build_tooltips(self, keybind_dict, texts, show_status=False, status=None, show_value=True):

    kb_string = "({key}) {desc}"
    kb_value = ": {var}"


    for _, keyitem in keybind_dict.items():

        value = ""
        if keyitem.get('var'):
            value = format_variable(getattr(self, keyitem['var']))
        
        state = ""
        if show_status:
            if keyitem.get('state') == status:
                state = " - Modifying"

        kb_state = ""
        if show_value:
            kb_state = kb_value.format(var=value+state)
        keybind = kb_string.format(key=keyitem['key'], desc=keyitem['desc'])

        texts.append(keybind+kb_state)


def format_variable(var):
    # TODO : format vectors here as well, instead of in the main code
    if type(var) == bool:
        bool_str = ['Disabled', 'Enabled']
        return bool_str[var]
    else:
        return str(var)

