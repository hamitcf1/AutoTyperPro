"""Snapshot physical character gestures on the main thread; workers never call TIS."""
import ctypes as C
import threading

MODES=((0,()),(2,(56,)),(8,(58,)),(10,(56,58)))

def build_keymap(translate):
    mapping={};dead=[]
    def remember(text,strokes):
        if len(text)!=1 or not (text.isprintable() or text=='\t'):return
        previous=mapping.get(text)
        cost=lambda value:(len(value),sum(len(mods) for code,mods in value))
        if previous is None or cost(strokes)<cost(previous):mapping[text]=strokes
    for state,modifiers in MODES:
        for code in range(128):
            text,pending=translate(code,state,0)
            if pending:dead.append((code,modifiers,pending))
            else:remember(text,((code,modifiers),))
    for first,first_mods,pending in dead:
        for state,modifiers in MODES:
            for code in range(128):
                text,next_dead=translate(code,state,pending)
                if not next_dead:remember(text,((first,first_mods),(code,modifiers)))
    return mapping

def current_keymap():
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('Keyboard layout must be captured on the main thread')
    hit=C.CDLL('/System/Library/Frameworks/Carbon.framework/Frameworks/HIToolbox.framework/HIToolbox')
    cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    def bind(lib,name,result,*arguments):
        function=getattr(lib,name);function.restype=result;function.argtypes=arguments;return function
    copy=bind(hit,'TISCopyCurrentKeyboardLayoutInputSource',C.c_void_p)
    prop=bind(hit,'TISGetInputSourceProperty',C.c_void_p,C.c_void_p,C.c_void_p)
    data=bind(cf,'CFDataGetBytePtr',C.c_void_p,C.c_void_p)
    release=bind(cf,'CFRelease',None,C.c_void_p)
    keyboard_type=bind(hit,'LMGetKbdType',C.c_uint8)()
    convert=bind(hit,'UCKeyTranslate',C.c_int32,C.c_void_p,C.c_uint16,C.c_uint16,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(C.c_uint32),C.c_uint32,C.POINTER(C.c_uint32),C.POINTER(C.c_uint16))
    key=C.c_void_p.in_dll(hit,'kTISPropertyUnicodeKeyLayoutData').value
    source=copy()
    if not source:raise RuntimeError('No active keyboard layout')
    try:
        layout=prop(source,key)
        if not layout:raise RuntimeError('The active input method has no physical keyboard layout')
        pointer=data(layout)
        def translate(code,modifiers,pending):
            dead=C.c_uint32(pending);length=C.c_uint32();units=(C.c_uint16*8)()
            status=convert(pointer,code,0,modifiers,keyboard_type,0,C.byref(dead),8,C.byref(length),units)
            if status or length.value>8:return '',0
            return bytes(units)[:length.value*2].decode('utf-16-le'),dead.value
        return build_keymap(translate)
    finally:release(source)
