"""First-run introduction, separate from the main activity interface."""
import sys
import customtkinter as ctk
from PIL import Image
from preferences import resource, VERSION


class Introduction(ctk.CTkFrame):
    def __init__(self,app):
        super().__init__(app.root,fg_color='#141816',corner_radius=0)
        self.app=app; self.step=0
        self.place(relx=0,rely=0,relwidth=1,relheight=1)
        top=ctk.CTkFrame(self,fg_color='transparent'); top.pack(fill='x',padx=36,pady=28)
        app.label(top,f'AutoTyper Pro  /  {VERSION}',13,'#97A79C').pack(side='left')
        app.button(top,'Tanıtımı atla',self.finish,width=116).pack(side='right')
        self.panel=ctk.CTkFrame(self,fg_color='#1D2420',corner_radius=24,width=820,height=540)
        self.panel.place(relx=.5,rely=.51,anchor='center'); self.panel.pack_propagate(False)
        image=Image.open(resource('assets/icon.png'))
        self.logo=ctk.CTkImage(image,image,size=(104,104))
        ctk.CTkLabel(self.panel,text='',image=self.logo).pack(pady=(30,14))
        self.eyebrow=app.label(self.panel,'',12,'#ACD5AE','bold'); self.eyebrow.pack()
        self.title=app.label(self.panel,'',34,weight='bold',justify='center'); self.title.pack(pady=(14,12))
        self.description=app.label(self.panel,'',15,'#97A79C',justify='center',wraplength=680)
        self.description.pack(pady=(0,16))
        self.detail=ctk.CTkFrame(self.panel,fg_color='#171D19',corner_radius=12,width=660,height=90)
        self.detail.pack(fill='x',padx=54,pady=(0,12)); self.detail.pack_propagate(False)
        self.detail_text=app.label(self.detail,'',13,'#ACD5AE',justify='center',wraplength=620)
        self.detail_text.pack(expand=True)
        self.actions=ctk.CTkFrame(self.panel,fg_color='transparent'); self.actions.pack(fill='x',padx=54,pady=(12,24))
        self.back=app.button(self.actions,'Geri',self.previous,width=96); self.back.pack(side='left')
        self.dots=app.label(self.actions,'',13,'#97A79C'); self.dots.pack(side='left',padx=24)
        self.next=app.button(self.actions,'Devam et  →',self.advance,primary=True,width=168); self.next.pack(side='right')
        self.permission=app.button(self.actions,'İzin ayarları ↗',app.permission_action,width=144)
        self.render()
        # A brief first-run entrance; never delays controls or keyboard actions.
        for index in range(1,7):
            app.root.after(index*25,lambda i=index:self.panel.place_configure(rely=.5+.01*(1-i/6)**3) if self.winfo_exists() else None)
    def render(self):
        steps=[('01  /  METNİN, SENİN RİTMİN','İki araç.\nDaha az tekrar.','Auto Typer, metnini seçtiğin hızda hedef uygulamaya yazar.\nDoğal ritim, satır davranışı ve başlangıç beklemesi senin kontrolünde.','Metni ekle → Ritmini seç → Başlat ve hedef uygulamaya geç.'),
               ('02  /  MOUSE JIGGLER','Küçük bir hareket.\nKontrol hep sende.','Boşta kaldığında imleci hafifçe hareket ettirir ve yerine getirir.\nYazma sırasında bekler. Sekme değiştirsen de durumunu gösterir.','Tıklama yapmaz. ESC iki aracı da durdurur. F18 isteğe bağlıdır.'),
               ('03  /  HAZIRLIK','Başlamaya hazırsın.','Klavye ve fare etkinliği yalnızca sen başlattığında çalışır.\nMetnin cihazında kalır; hesap veya internet bağlantısı gerekmez.','')]
        eyebrow,title,description,detail=steps[self.step]
        self.eyebrow.configure(text=eyebrow); self.title.configure(text=title); self.description.configure(text=description)
        self.dots.configure(text='  '.join('●' if i==self.step else '○' for i in range(3)))
        self.back.configure(state='disabled' if self.step==0 else 'normal')
        self.next.configure(text='Uygulamaya geç  ↗' if self.step==2 else 'Devam et  →')
        self.permission.pack_forget()
        if self.step==2 and sys.platform=='darwin':
            ready=self.app.backend.allowed()
            detail='Giriş izni hazır. Hemen başlayabilirsin.' if ready else 'Sistem Ayarları → Gizlilik ve Güvenlik → Erişilebilirlik\n(yeni macOS sürümlerinde Aygıt Denetimi ve Veri Erişimi).'
            if not ready:self.permission.pack(side='right',padx=(0,10))
        elif self.step==2: detail='Kurulum tamamlandı. Yönetici olarak çalışan hedefler ek yetki gerektirebilir.'
        self.detail_text.configure(text=detail)
    def advance(self):
        if self.step==2:self.finish()
        else:self.step+=1;self.render()
    def previous(self):self.step=max(0,self.step-1);self.render()
    def finish(self):
        try:self.app.preferences.complete_intro()
        except OSError:self.app.tell('Tanıtım tercihi kaydedilemedi; uygulamayı kullanabilirsin.',True)
        self.destroy();self.app.intro=None;self.app.check_permissions()
