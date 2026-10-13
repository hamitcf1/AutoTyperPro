"""Shared chord sequencing with unconditional modifier cleanup."""
from keycodes import MAC_KEYS, WIN_KEYS, MAC_MODIFIERS, WIN_MODIFIERS

class KeyChordMixin:
    def key_chord(self,key,modifiers,stop):
        keys,mods = (MAC_KEYS,MAC_MODIFIERS) if self.native_platform == 'darwin' else (WIN_KEYS,WIN_MODIFIERS)
        if stop.is_set(): return
        if not modifiers:
            self.press(keys[key]);return
        held=[]
        try:
            for modifier in modifiers:
                if stop.is_set(): return
                code=mods[modifier];held.append(code);self.physical_key_event(code,True)
            if not stop.is_set():
                code=keys[key];held.append(code);self.physical_key_event(code,True)
        finally:
            failure=None
            for code in reversed(held):
                try:self.physical_key_event(code,False)
                except Exception as exc:failure=exc
            if failure:raise failure

    def release_held_inputs(self):
        failure=None
        for code in list(getattr(self,'_held_keys',())):
            try:self.physical_key_event(code,False)
            except Exception as exc:failure=exc
        for button in list(getattr(self,'_held_buttons',())):
            try:self.button_event(button,False,None)
            except Exception as exc:failure=exc
        if failure:raise failure
