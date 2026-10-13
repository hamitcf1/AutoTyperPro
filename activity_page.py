"""Configurable Anti-AFK page; workers and native events live elsewhere."""
from dataclasses import asdict
import tkinter as tk
import customtkinter as ctk
from engine import JigglerConfig
from activity import PRESETS, migrate_activity
from keycodes import MODIFIERS
from localization import tr
from profile_controls import ProfileControls

class ActivityPage:
    def __init__(self,app,page):
        import auto_typer as style
        self.app=app;self.controls=[]
        page.grid_columnconfigure(0,weight=1);page.grid_columnconfigure(1,minsize=350);page.grid_rowconfigure(2,weight=1)
        app.page_title(page,'02 / MOUSE JIGGLER · ANTI-AFK',tr('ui.5515cdfb9f19'),tr('ui.e23794348c8a'))
        self.profiles=ProfileControls(page,app,'activity',lambda:asdict(self.config()),self.apply)
        self.profiles.grid(row=1,column=0,columnspan=2,sticky='ew',pady=(0,14))
        hero=ctk.CTkFrame(page,fg_color=style.PANEL,corner_radius=16)
        hero.grid(row=2,column=0,sticky='nsew',padx=(0,18));hero.grid_columnconfigure(0,weight=1);hero.grid_rowconfigure(0,weight=1)
        app.canvas=tk.Canvas(hero,bg=style.PANEL,highlightthickness=0,height=180)
        app.canvas.grid(row=0,column=0,sticky='nsew',padx=12,pady=12);app.canvas.bind('<Configure>',app.draw_cursor)
        app.jig_state=app.label(hero,tr('ui.f4dc30229a90'),24,weight='bold');app.jig_state.grid(row=1,column=0,pady=10)
        app.jig_description=app.label(hero,tr('ui.39c13a156e82'),12,style.MUTED,wraplength=380,justify='center');app.jig_description.grid(row=2,column=0,padx=20,pady=10)
        stats=ctk.CTkFrame(hero,fg_color=style.INSET,corner_radius=12);stats.grid(row=3,column=0,sticky='ew',padx=20,pady=20);stats.grid_columnconfigure((0,1,2),weight=1)
        for i,(name,key,value) in enumerate([('elapsed_label','ui.799117ff2b64','00:00'),('moves_label','ui.a6726919b04a','0'),('idle_label','ui.38ca04d61b74','00:00')]):
            widget=app.label(stats,value,23,style.ACCENT);widget.grid(row=0,column=i,pady=(16,4));setattr(app,name,widget)
            app.label(stats,tr(key),11,style.MUTED).grid(row=1,column=i,pady=(0,16))
        self.summary=app.label(hero,'',12,style.ACCENT,wraplength=390,justify='center');self.summary.grid(row=4,column=0,padx=20,pady=(0,20))
        settings=ctk.CTkScrollableFrame(page,fg_color=style.PANEL,corner_radius=16,width=320);settings.grid(row=2,column=1,sticky='nsew')
        settings.grid_columnconfigure(0,weight=1);row=0
        def label(key):
            nonlocal row
            app.label(settings,tr(key),12,style.MUTED).grid(row=row,column=0,sticky='w',padx=16,pady=(18,6));row+=1
        def menu(values,command):
            nonlocal row
            widget=ctk.CTkOptionMenu(settings,values=values,command=command,fg_color=style.LINE,button_color=style.LINE,text_color=style.INK)
            widget.grid(row=row,column=0,sticky='ew',padx=16);self.controls.append(widget);row+=1;return widget
        label('activity.preset');self.preset=menu([tr('activity.'+k) for k in PRESETS]+[tr('activity.custom')],self.select_preset)
        self.preset.set(tr('activity.gentle'))
        reset=app.button(settings,tr('activity.reset'),lambda:self.select_preset(tr('activity.gentle')),height=32)
        reset.grid(row=row,column=0,sticky='ew',padx=16,pady=(8,0));self.controls.append(reset);row+=1
        self.entries={}
        for name,key,value in [('idle_threshold','activity.idle',60),('interval','activity.interval',30),('distance','activity.distance',1),('duration_ms','activity.duration',80)]:
            label(key);entry=app.entry(settings,value,100);entry.grid(row=row,column=0,sticky='ew',padx=16);row+=1
            entry.bind('<KeyRelease>',lambda e:self.changed());self.entries[name]=entry;self.controls.append(entry)
        app.idle_entry=self.entries['idle_threshold'];app.interval_entry=self.entries['interval']
        label('activity.mode');self.mode=menu([tr('activity.'+k) for k in ('horizontal_return','vertical_return','square','off')],lambda v:self.changed())
        self.mode.set(tr('activity.horizontal_return'))
        label('activity.key');self.key=menu([tr('activity.none')]+['F'+str(i) for i in range(13,21)]+[tr('activity.custom_key')],lambda v:self.changed())
        self.key.set(tr('activity.none'))
        self.custom=app.entry(settings,'f18',100);self.custom.grid(row=row,column=0,sticky='ew',padx=16,pady=(8,0));row+=1;self.controls.append(self.custom)
        self.custom.bind('<KeyRelease>',lambda e:self.changed())
        self.modifiers={}
        group=ctk.CTkFrame(settings,fg_color='transparent');group.grid(row=row,column=0,sticky='ew',padx=16,pady=10);row+=1
        for index,name in enumerate(MODIFIERS):
            var=ctk.BooleanVar(value=False);self.modifiers[name]=var
            text={'shift':'Shift','control':'Control','alt':'Alt / Option','command':'Command / Win'}[name]
            widget=ctk.CTkCheckBox(group,text=text,variable=var,command=self.changed,width=130,font=(style.FONT,11),fg_color=style.ACCENT,hover_color=style.HOVER,checkmark_color=style.BG,text_color=style.INK);widget.grid(row=index//2,column=index%2,sticky='w',pady=5);self.controls.append(widget)
        app.label(settings,tr('activity.key_note'),11,style.MUTED,wraplength=290,justify='left').grid(row=row,column=0,padx=16,pady=(0,18))
        controls=ctk.CTkFrame(page,fg_color=style.PANEL,corner_radius=14);controls.grid(row=3,column=0,columnspan=2,sticky='ew',pady=(14,0));controls.grid_columnconfigure(0,weight=1)
        app.label(controls,tr('ui.f2944a83ef76'),15,weight='bold').grid(row=0,column=0,sticky='w',padx=20,pady=20)
        app.jig_stop_btn=app.button(controls,tr('ui.acc8c9e36f29'),app.stop_jiggler,width=90,state='disabled');app.jig_stop_btn.grid(row=0,column=1,padx=8)
        app.jig_start_btn=app.button(controls,tr('ui.add7f870808d'),app.start_jiggler,primary=True,width=180);app.jig_start_btn.grid(row=0,column=2,padx=(0,20))
        self.update_summary()
    def config(self):
        movement=next(k for k in ('horizontal_return','vertical_return','square','off') if tr('activity.'+k)==self.mode.get())
        key=self.key.get()
        key=None if key==tr('activity.none') else self.custom.get().strip().lower() if key==tr('activity.custom_key') else key.lower()
        return JigglerConfig(**{name:float(entry.get()) for name,entry in self.entries.items()},movement=movement,key=key,modifiers=tuple(k for k,var in self.modifiers.items() if var.get())).validate()
    def snapshot(self):
        return {'entries':{k:v.get() for k,v in self.entries.items()},'movement':next(k for k in ('horizontal_return','vertical_return','square','off') if tr('activity.'+k)==self.mode.get()),'key':self.key.get().lower() if self.key.get().startswith('F') else 'custom' if self.key.get()==tr('activity.custom_key') else None,'custom':self.custom.get(),'modifiers':[k for k,v in self.modifiers.items() if v.get()]}
    def restore(self,data):
        for k,v in data['entries'].items():self.entries[k].delete(0,'end');self.entries[k].insert(0,v)
        self.mode.set(tr('activity.'+data['movement']))
        self.key.set(tr('activity.custom_key') if data['key']=='custom' else data['key'].upper() if data['key'] else tr('activity.none'))
        self.custom.delete(0,'end');self.custom.insert(0,data['custom'])
        for k,var in self.modifiers.items():var.set(k in data['modifiers'])
        self.changed()
    def apply(self,data):
        config=JigglerConfig(**migrate_activity(data)).validate()
        for name,entry in self.entries.items():entry.delete(0,'end');entry.insert(0,f'{getattr(config,name):g}')
        self.mode.set(tr('activity.'+config.movement))
        standard=config.key and config.key in ('f'+str(i) for i in range(13,21))
        self.key.set(config.key.upper() if standard else tr('activity.custom_key') if config.key else tr('activity.none'))
        if config.key:self.custom.delete(0,'end');self.custom.insert(0,config.key)
        for k,var in self.modifiers.items():var.set(k in config.modifiers)
        self.changed()
    def select_preset(self,label):
        key=next((key for key in PRESETS if tr('activity.'+key)==label),None)
        if key:self.apply(asdict(PRESETS[key]));self.preset.set(label)
    def changed(self):
        self.preset.set(tr('activity.custom'));self.update_summary();self.profiles.dirty()
        custom=self.key.get()==tr('activity.custom_key')
        if custom:self.custom.grid()
        else:self.custom.grid_remove()
    def update_summary(self):
        try:
            config=self.config();self.summary.configure(text=tr('activity.summary',idle=config.idle_threshold,interval=config.interval,distance=config.distance,key=config.key or '—'))
        except (ValueError,StopIteration):self.summary.configure(text=tr('ui.c5e1d194c109'))
    def set_busy(self,busy):
        for widget in self.controls:widget.configure(state='disabled' if busy else 'normal')
        self.profiles.set_busy(busy)
