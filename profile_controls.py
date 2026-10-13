"""Shared saved-profile controls for typing and Anti-AFK pages."""
from tkinter import filedialog, messagebox
import customtkinter as ctk
from profiles import ProfileStore, new_profile
from localization import tr

class ProfileControls(ctk.CTkFrame):
    def __init__(self,parent,app,kind,read_config,apply_config):
        super().__init__(parent,fg_color='transparent')
        self.app=app;self.kind=kind;self.read_config=read_config;self.apply_config=apply_config
        self.store=ProfileStore();self.selected=None;self.items={}
        self.grid_columnconfigure(0,weight=1)
        self.menu=ctk.CTkOptionMenu(self,values=[tr('profile.unsaved')],command=self.choose)
        self.menu.grid(row=0,column=0,sticky='ew',padx=(0,8))
        self.actions=ctk.CTkOptionMenu(self,values=[tr('profile.'+a) for a in ('save','rename','duplicate','delete','import','export')],command=self.act,width=125)
        self.actions.set(tr('profile.save'));self.actions.grid(row=0,column=1)
        self.refresh()
    def refresh(self):
        try:
            profiles=[p for p in self.store.load() if p['kind']==self.kind]
            self.items={p['name']+' · '+p['id'][:6]:p for p in profiles}
            self.menu.configure(values=[tr('profile.unsaved')]+list(self.items))
            label=next((label for label,p in self.items.items() if p['id']==self.selected),tr('profile.unsaved'))
            self.menu.set(label)
        except ValueError as exc:self.app.tell(tr('profile.error',error=exc),True)
    def choose(self,label):
        if label not in self.items:self.selected=None;return
        profile=self.items[label];self.apply_config(profile['config']);self.selected=profile['id']
    def dirty(self):
        if self.selected:
            selected=next((p for p in self.items.values() if p['id']==self.selected),None)
            try:matches=selected and self.read_config()==selected['config']
            except ValueError:matches=False
            if not matches:self.menu.set(tr('profile.unsaved'))
    def set_busy(self,busy):
        for widget in (self.menu,self.actions):widget.configure(state='disabled' if busy else 'normal')
    def act(self,label):
        action=next(a for a in ('save','rename','duplicate','delete','import','export') if tr('profile.'+a)==label)
        try:
            selected=next((p for p in self.items.values() if p['id']==self.selected),None)
            if action=='import':
                path=filedialog.askopenfilename(parent=self.app.root,filetypes=[('JSON','*.json')])
                if not path:return
                profile=self.store.import_file(path,expected_kind=self.kind)
                self.selected=profile['id'];self.apply_config(profile['config'])
            elif action=='export':
                profile=selected or new_profile('Configuration',self.kind,self.read_config())
                path=filedialog.asksaveasfilename(parent=self.app.root,defaultextension='.json',filetypes=[('JSON','*.json')])
                if path:self.store.export_file(profile,path)
            elif action=='delete':
                if selected and messagebox.askyesno(tr('profile.delete'),tr('profile.confirm_delete'),parent=self.app.root):
                    self.store.delete(selected['id']);self.selected=None
            else:
                if action=='rename' and not selected:return
                name=ctk.CTkInputDialog(text=tr('profile.name'),title=tr('profile.'+action)).get_input()
                if not name:return
                profile=dict(selected) if action=='rename' else new_profile(name,self.kind,self.read_config())
                profile['name']=name;self.store.save(profile);self.selected=profile['id']
            self.refresh();self.app.tell(tr('profile.saved'))
        except (ValueError,OSError) as exc:self.app.tell(tr('profile.error',error=exc),True)
