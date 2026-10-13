"""Macro library, explicit capture controls and path preview."""
import queue
import threading
import time
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk
from macros import MacroStore, play_macro, number
from macro_recorder import Recorder
from localization import tr

class MacroPage:
    def __init__(self,app,page):
        import auto_typer as style
        self.app=app;self.store=MacroStore();self.draft=None;self.selected=None;self.state='idle';self.recording_started=None;self.mutable=[]
        app.page_title(page,'03 / MACROS',tr('macro.title'),tr('macro.description'))
        page.grid_columnconfigure(1,weight=1);page.grid_rowconfigure(1,weight=1)
        library=ctk.CTkFrame(page,fg_color=style.PANEL,corner_radius=16,width=220);library.grid(row=1,column=0,sticky='nsew',padx=(0,16));library.grid_propagate(False)
        library.grid_columnconfigure(0,weight=1);library.grid_rowconfigure(1,weight=1)
        app.label(library,tr('macro.library'),16,weight='bold').grid(row=0,column=0,sticky='w',padx=18,pady=18)
        self.library=ctk.CTkScrollableFrame(library,fg_color='transparent');self.library.grid(row=1,column=0,sticky='nsew',padx=8)
        actions=ctk.CTkFrame(library,fg_color='transparent');actions.grid(row=2,column=0,sticky='ew',padx=16,pady=16)
        self.library_actions=ctk.CTkOptionMenu(actions,values=[tr('profile.'+key) for key in ('save','rename','duplicate','delete','import','export')],command=self.library_action,fg_color=style.LINE,button_color=style.LINE,text_color=style.INK,dropdown_fg_color=style.PANEL,dropdown_text_color=style.INK)
        self.library_actions.set(tr('profile.save'));self.library_actions.pack(fill='x');self.mutable.append(self.library_actions)
        main=ctk.CTkScrollableFrame(page,fg_color=style.PANEL,corner_radius=16);main.grid(row=1,column=1,sticky='nsew');main.grid_columnconfigure(0,weight=1)
        self.title=app.label(main,tr('macro.new'),21,weight='bold');self.title.grid(row=0,column=0,sticky='w',padx=20,pady=(20,6))
        self.info=app.label(main,tr('macro.empty'),12,style.MUTED,wraplength=500);self.info.grid(row=1,column=0,sticky='w',padx=20,pady=(0,12))
        self.canvas=tk.Canvas(main,height=190,bg=style.INSET,highlightthickness=0);self.canvas.grid(row=2,column=0,sticky='ew',padx=20);self.canvas.bind('<Configure>',lambda e:self.draw_preview())
        app.label(main,tr('macro.capture'),14,weight='bold').grid(row=3,column=0,sticky='w',padx=20,pady=(20,10))
        options=ctk.CTkFrame(main,fg_color='transparent');options.grid(row=5,column=0,sticky='ew',padx=20)
        self.capture={}
        for i,key in enumerate(('move','button','key','scroll')):
            var=ctk.BooleanVar(value=key=='move');self.capture[key]=var
            widget=ctk.CTkCheckBox(options,text=tr('macro.capture_'+key),variable=var,font=(style.FONT,12),fg_color=style.ACCENT,hover_color=style.HOVER,checkmark_color=style.BG,text_color=style.INK);widget.grid(row=i//2,column=i%2,sticky='w',padx=(0,20),pady=6);self.mutable.append(widget)
        app.label(main,tr('macro.keyboard_notice'),11,style.MUTED,wraplength=500,justify='left').grid(row=4,column=0,sticky='w',padx=20,pady=(0,10))
        options=ctk.CTkFrame(main,fg_color='transparent');options.grid(row=6,column=0,sticky='ew',padx=20,pady=(0,20))
        self.entries={}
        for i,(name,label,default) in enumerate([('start_delay','macro.delay',3),('repeats','macro.repeats',1),('repeat_delay','macro.gap',0)]):
            app.label(options,tr(label),11,style.MUTED).grid(row=0,column=i,sticky='w',padx=(0,16))
            entry=app.entry(options,default,90);entry.grid(row=1,column=i,sticky='w',padx=(0,16),pady=8);self.entries[name]=entry;self.mutable.append(entry)
        app.label(options,tr('macro.speed'),11,style.MUTED).grid(row=2,column=0,sticky='w',pady=(8,0))
        self.speed=ctk.CTkOptionMenu(options,values=['0.25×','0.5×','1×','2×','4×'],width=90,fg_color=style.LINE,button_color=style.LINE,text_color=style.INK,dropdown_fg_color=style.PANEL,dropdown_text_color=style.INK);self.speed.set('1×');self.speed.grid(row=3,column=0,sticky='w',pady=8);self.mutable.append(self.speed)
        self.fit=ctk.BooleanVar(value=False)
        fit=ctk.CTkCheckBox(options,text=tr('macro.fit'),variable=self.fit,font=(style.FONT,11),fg_color=style.ACCENT,hover_color=style.HOVER,checkmark_color=style.BG,text_color=style.INK);fit.grid(row=3,column=1,columnspan=2,sticky='w',padx=16);self.mutable.append(fit)
        controls=ctk.CTkFrame(page,fg_color=style.PANEL,corner_radius=14);controls.grid(row=2,column=0,columnspan=2,sticky='ew',pady=(14,0));controls.grid_columnconfigure(0,weight=1)
        self.status=app.label(controls,tr('macro.ready'),12,style.MUTED,wraplength=360);self.status.grid(row=0,column=0,sticky='w',padx=18,pady=18)
        self.stop_button=app.button(controls,tr('ui.acc8c9e36f29'),self.stop,width=75,state='disabled');self.stop_button.grid(row=0,column=1,padx=6)
        self.record_button=app.button(controls,tr('macro.record'),self.start_record,width=115);self.record_button.grid(row=0,column=2,padx=6)
        self.play_button=app.button(controls,tr('macro.play'),self.start_play,primary=True,width=115,state='disabled');self.play_button.grid(row=0,column=3,padx=(6,18))
        self.refresh_library();self.draw_preview()
    def refresh_library(self):
        for child in self.library.winfo_children():child.destroy()
        try:
            for item in self.store.list():
                button=self.app.button(self.library,item['name'],lambda item=item:self.select(item),height=34)
                button.pack(fill='x',padx=4,pady=4)
                if self.app.macro_active.is_set():button.configure(state='disabled')
            if self.store.errors:self.app.tell(tr('macro.library_errors',count=len(self.store.errors)),True)
        except ValueError as exc:self.app.tell(str(exc),True)
    def select(self,item):
        if self.app.macro_active.is_set():return
        self.selected=item['id'];self.draft=item['macro'];self.title.configure(text=item['name']);self.describe();self.play_button.configure(state='normal')
    def describe(self):
        if self.draft:self.info.configure(text=tr('macro.details',count=len(self.draft.events),duration=self.draft.events[-1].time,platform=self.draft.platform))
        self.draw_preview()
    def draw_preview(self):
        import auto_typer as style
        self.canvas.delete('all');w=max(100,self.canvas.winfo_width());h=max(100,self.canvas.winfo_height())
        if not self.draft:
            self.canvas.create_text(w/2,h/2,text=tr('macro.preview'),fill=style.MUTED,font=(style.FONT,14));return
        displays=self.draft.displays;left=min(d['left'] for d in displays);top=min(d['top'] for d in displays)
        width=max(d['left']+d['width'] for d in displays)-left;height=max(d['top']+d['height'] for d in displays)-top
        scale=min((w-36)/width,(h-30)/height);ox=(w-width*scale)/2;oy=(h-height*scale)/2
        def point(x,y):return ox+(x-left)*scale,oy+(y-top)*scale
        for display in displays:
            self.canvas.create_rectangle(*point(display['left'],display['top']),*point(display['left']+display['width'],display['top']+display['height']),outline=style.LINE,width=2)
        coords=[]
        for event in self.draft.events:
            if event.kind not in ('move','button'):continue
            x,y=point(event.data['x'],event.data['y']);coords.extend((x,y))
            if event.kind=='button' and event.data['down']:self.canvas.create_oval(x-3,y-3,x+3,y+3,fill=style.ACCENT,outline='')
        if len(coords)>=4:self.canvas.create_line(*coords,fill=style.ACCENT,width=2)
        elif coords:self.canvas.create_oval(coords[0]-3,coords[1]-3,coords[0]+3,coords[1]+3,fill=style.ACCENT)
    def library_action(self,label):
        if self.app.macro_active.is_set():return
        action=next(key for key in ('save','rename','duplicate','delete','import','export') if tr('profile.'+key)==label)
        try:
            if action=='import':
                path=filedialog.askopenfilename(parent=self.app.root,filetypes=[('JSON','*.json')])
                if path:self.select(self.store.import_file(path))
            elif action=='export':
                if not self.selected:return
                path=filedialog.asksaveasfilename(parent=self.app.root,defaultextension='.json',filetypes=[('JSON','*.json')])
                if path:self.store.export_file(self.selected,path)
            elif action=='delete':
                if self.selected and messagebox.askyesno(tr('profile.delete'),tr('profile.confirm_delete'),parent=self.app.root):
                    self.store.delete(self.selected);self.selected=None;self.draft=None;self.title.configure(text=tr('macro.new'));self.info.configure(text=tr('macro.empty'));self.draw_preview();self.play_button.configure(state='disabled')
            else:
                if not self.draft:return
                name=ctk.CTkInputDialog(text=tr('profile.name'),title=tr('profile.'+action)).get_input()
                if not name:return
                identity=self.selected if action=='rename' else None
                self.selected=self.store.save(name,self.draft,identity);self.title.configure(text=name)
            self.refresh_library()
        except (ValueError,OSError) as exc:self.app.tell(str(exc),True)
    def settings(self):
        delay=float(self.entries['start_delay'].get());number(delay,0,60)
        repeats=int(self.entries['repeats'].get());number(repeats,1,100)
        gap=float(self.entries['repeat_delay'].get());number(gap,0,3600)
        return dict(start_delay=delay,repeats=repeats,repeat_delay=gap,speed=float(self.speed.get().rstrip('×')),fit_to_primary=self.fit.get())
    def begin(self):
        if self.app.typing_active.is_set() or (self.app.macro_thread and self.app.macro_thread.is_alive()):self.app.tell(tr('macro.busy'));return False
        if not self.app.ensure_permission():return False
        self.app.macro_stop.clear();self.app.macro_active.set();self.set_busy(True);return True
    def start_record(self):
        try:
            delay=self.settings()['start_delay'];capture=frozenset(k for k,var in self.capture.items() if var.get())
            if not capture:raise ValueError(tr('macro.capture_required'))
        except ValueError as exc:self.app.tell(str(exc),True);return
        if not self.begin():return
        self.state='countdown';self.app.macro_thread=threading.Thread(target=self.record_worker,args=(capture,delay),daemon=True);self.app.macro_thread.start()
    def record_worker(self,capture,delay):
        recorder=None
        try:
            deadline=time.monotonic()+delay
            while not self.app.macro_stop.is_set() and time.monotonic()<deadline:
                self.app.macro_events.put(('macro_countdown',deadline-time.monotonic()));self.app.macro_stop.wait(min(.1,max(0,deadline-time.monotonic())))
            if self.app.macro_stop.is_set():self.app.macro_events.put(('macro_stopped',None));return
            recorder=Recorder(self.app.backend,capture,self.app.macro_events)
            with self.app.backend.lock:recorder.start()
            self.app.macro_events.put(('record_started',time.monotonic()))
            while not self.app.macro_stop.wait(.1) and not recorder.limit_reached():pass
            macro=recorder.stop();recorder=None
            self.app.macro_events.put(('record_finished',macro))
        except Exception as exc:self.app.macro_events.put(('macro_error',str(exc)))
        finally:
            if recorder:
                try:recorder.stop()
                except Exception:pass
    def start_play(self):
        if not self.draft:return
        try:settings=self.settings()
        except ValueError as exc:self.app.tell(str(exc),True);return
        if not self.begin():return
        self.state='countdown';self.app.macro_thread=threading.Thread(target=play_macro,args=(self.draft,self.app.backend,self.app.macro_stop,self.app.macro_events),kwargs=settings,daemon=True);self.app.macro_thread.start()
    def stop(self):
        self.app.macro_stop.set();self.stop_button.configure(state='disabled');self.status.configure(text=tr('ui.2e0bfe52689c'))
    def set_busy(self,busy):
        for widget in self.mutable:widget.configure(state='disabled' if busy else 'normal')
        for widget in self.library.winfo_children():widget.configure(state='disabled' if busy else 'normal')
        self.stop_button.configure(state='normal' if busy else 'disabled');self.record_button.configure(state='disabled' if busy else 'normal');self.play_button.configure(state='disabled' if busy or self.draft is None else 'normal')
    def poll(self):
        for i in range(500):
            try:kind,value=self.app.macro_events.get_nowait()
            except queue.Empty:break
            if kind=='macro_countdown':self.status.configure(text=tr('ui.7345650fa46b',v0=value))
            elif kind=='record_started':self.state='recording';self.recording_started=value
            elif kind=='macro_started':self.state='playing';self.status.configure(text=tr('macro.playing'))
            elif kind=='macro_progress':self.status.configure(text=tr('macro.progress',done=value[0],total=value[1]))
            elif kind=='record_limit':self.status.configure(text=tr('macro.limit'))
            elif kind in ('record_finished','macro_finished','macro_stopped','macro_error'):
                if kind=='record_finished':
                    self.draft=value;self.selected=None;self.title.configure(text=tr('macro.new'));self.describe()
                self.state='idle';self.app.macro_active.clear();self.set_busy(False)
                message=value if kind=='macro_error' else tr('macro.'+('recorded' if kind=='record_finished' else 'finished' if kind=='macro_finished' else 'stopped'))
                self.status.configure(text=message);self.app.tell(message,kind=='macro_error')
        if self.state=='recording':self.status.configure(text=tr('macro.recording',elapsed=time.monotonic()-self.recording_started))
    def snapshot(self):
        return {'entries':{k:v.get() for k,v in self.entries.items()},'capture':{k:v.get() for k,v in self.capture.items()},'speed':self.speed.get(),'fit':self.fit.get(),'selected':self.selected,'draft':self.draft.document() if self.draft else None}
    def restore(self,data):
        from macros import validate_macro
        for key,value in data['entries'].items():self.entries[key].delete(0,'end');self.entries[key].insert(0,value)
        for key,value in data['capture'].items():self.capture[key].set(value)
        self.speed.set(data['speed']);self.fit.set(data['fit']);self.selected=data.get('selected')
        if data.get('draft'):
            self.draft=validate_macro(data['draft']);self.describe();self.play_button.configure(state='normal')
            if self.selected:
                saved=next((item for item in self.store.list() if item['id']==self.selected),None)
                if saved:self.title.configure(text=saved['name'])
