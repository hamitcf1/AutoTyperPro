"""Physical key maps. Labels refer to key positions, not recorded text."""
MAC_KEYS = {'a':0,'s':1,'d':2,'f':3,'h':4,'g':5,'z':6,'x':7,'c':8,'v':9,'b':11,'q':12,'w':13,'e':14,'r':15,'y':16,'t':17,'u':32,'i':34,'o':31,'p':35,'j':38,'k':40,'l':37,'n':45,'m':46}
MAC_KEYS.update(dict(zip('1234567890',(18,19,20,21,23,22,26,28,25,29))))
MAC_KEYS.update({'space':49,'enter':36,'tab':48,'backspace':51,'delete':117,'left':123,'right':124,'up':126,'down':125,'home':115,'end':119,'page_up':116,'page_down':121})
MAC_KEYS.update(dict(zip(('f'+str(i) for i in range(1,21)),(122,120,99,118,96,97,98,100,101,109,103,111,105,107,113,106,64,79,80,90))))
WIN_KEYS = {letter:ord(letter.upper()) for letter in 'abcdefghijklmnopqrstuvwxyz0123456789'}
WIN_KEYS.update({'space':32,'enter':13,'tab':9,'backspace':8,'delete':46,'left':37,'right':39,'up':38,'down':40,'home':36,'end':35,'page_up':33,'page_down':34})
WIN_KEYS.update({'f'+str(i):0x6F+i for i in range(1,21)})
MODIFIERS = ('shift','control','alt','command')
MAC_MODIFIERS = {'shift':56,'control':59,'alt':58,'command':55}
WIN_MODIFIERS = {'shift':0xA0,'control':0xA2,'alt':0xA4,'command':0x5B}
MAC_MODIFIER_FLAGS = {56:1<<17,60:1<<17,59:1<<18,62:1<<18,58:1<<19,61:1<<19,55:1<<20,54:1<<20}
SUPPORTED_KEYS = tuple(sorted(set(MAC_KEYS) & set(WIN_KEYS)))
