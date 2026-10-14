"""Read only the foreground process using NSWorkspace, without AX permission.

https://developer.apple.com/documentation/appkit/nsworkspace/frontmostapplication
No remote content or clipboard is read. Objective-C calls use explicit ABI types.
"""
import ctypes as C
from functools import lru_cache

REMOTE_CLIENTS=('screen sharing.app/','remote desktop.app/','windows app.app/','anydesk.app/','vnc viewer.app/','parsec.app/')
def is_remote_client(path):return any(name in path.lower() for name in REMOTE_CLIENTS)

@lru_cache(maxsize=1)
def _api():
    C.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit')
    objc=C.CDLL('/usr/lib/libobjc.A.dylib');proc=C.CDLL('/usr/lib/libproc.dylib')
    def bind(lib,name,result,*args):
        function=getattr(lib,name);function.restype=result;function.argtypes=args;return function
    klass=bind(objc,'objc_getClass',C.c_void_p,C.c_char_p)
    selector=bind(objc,'sel_registerName',C.c_void_p,C.c_char_p)
    address=C.cast(objc.objc_msgSend,C.c_void_p).value
    send=C.CFUNCTYPE(C.c_void_p,C.c_void_p,C.c_void_p)(address)
    integer=C.CFUNCTYPE(C.c_int32,C.c_void_p,C.c_void_p)(address)
    push=bind(objc,'objc_autoreleasePoolPush',C.c_void_p)
    pop=bind(objc,'objc_autoreleasePoolPop',None,C.c_void_p)
    path=bind(proc,'proc_pidpath',C.c_int32,C.c_int32,C.c_void_p,C.c_uint32)
    return klass,selector,send,integer,push,pop,path

def frontmost_process():
    klass,selector,send,integer,push,pop,path=_api();pool=push()
    try:
        workspace=send(klass(b'NSWorkspace'),selector(b'sharedWorkspace'))
        if not workspace:return None
        app=send(workspace,selector(b'frontmostApplication'))
        if not app:return None
        identifier=integer(app,selector(b'processIdentifier'))
        buffer=C.create_string_buffer(4096)
        if identifier<=0 or path(identifier,buffer,len(buffer))<=0:return None
        return identifier,buffer.value.decode('utf-8',errors='replace')
    finally:pop(pool)
