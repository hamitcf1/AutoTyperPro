import sys
if __name__ == "__main__":
    sys.modules["auto_typer"] = sys.modules[__name__]
from localization import tr, set_locale, locale_options
"""AutoTyper Pro desktop application. All UI mutations run on the Tk thread."""
import queue
import json
import os
from pathlib import Path
import subprocess
import secrets
import sys
import threading
import time
import tkinter as tk
import tempfile
import customtkinter as ctk
from PIL import Image
from preferences import Preferences, VERSION, resource
from onboarding import Introduction
from support_ui import show_support, report_bug
from desktop_integration import DesktopIntegration
from engine import TypingConfig, JigglerConfig, type_text, jiggle
from platform_backend import create_backend, open_permissions, play_sound
BG = '#111216'
PANEL = '#1D1F25'
INSET = '#16181D'
LINE = '#343741'
INK = '#F0F3EF'
MUTED = '#A0A5B0'
ACCENT = '#ACD5AE'
HOVER = '#C2E3C3'
DANGER = '#EDB6A9'
FONT = 'SF Pro Display' if sys.platform == 'darwin' else 'Segoe UI'
SPEEDS = {'very_fast':30, 'fast':60, 'balanced':100, 'slow':150, 'very_slow':250, 'random':-1}
SPEED_KEYS = ['ui.642c21189b08','ui.586c9d6f169e','ui.df0e900f2f90','ui.65f46db17cc6','ui.178cad18363d','ui.b93c11961893']
NEWLINES = {'space':'space','shift_enter':'shift_enter','ignore':'ignore'}
NEWLINE_KEYS = ['ui.32293ed93f45',None,'ui.fd3df227073d']


def set_palette(appearance):
    global BG, PANEL, INSET, LINE, INK, MUTED, ACCENT, HOVER, DANGER
    ctk.set_appearance_mode(appearance)
    if ctk.get_appearance_mode() == 'Light':
        BG,PANEL,INSET,LINE,INK,MUTED,ACCENT,HOVER,DANGER = ('#F2F3F7','#FFFFFF','#F4F6F3','#DCDDE5','#18261C','#596C5E','#A5CEAA','#8DBE93','#9E3634')
    else:
        BG,PANEL,INSET,LINE,INK,MUTED,ACCENT,HOVER,DANGER = ('#111216','#1D1F25','#16181D','#343741','#F0F3EF','#A0A5B0','#ACD5AE','#C2E3C3','#EDB6A9')


def duration(seconds):
    seconds = max(0, round(seconds))
    return f'{seconds // 60:02d}:{seconds % 60:02d}'

class AutoTyper:

    def __init__(self, show_intro=True):
        self.preferences = Preferences()
        prefs = self.preferences.load()
        set_locale(prefs['locale'])
        set_palette(prefs['appearance'])
        if sys.platform=='win32':
            from desktop_windows import set_taskbar_identity
            set_taskbar_identity()
        from responsive import ResponsiveWindow
        self.root = ResponsiveWindow(fg_color=BG)
        self.root.title(f'AutoTyper Pro {VERSION}')
        self.root.geometry('1120x800')
        self.root.minsize(740, 540)
        self.root.protocol('WM_DELETE_WINDOW', self.request_close)
        self.backend = create_backend()
        self.intro = None
        self.permission_checked = 0
        self.restart_command = None
        self.permission_ready = False
        self.typing_events = queue.Queue()
        self.jiggler_events = queue.Queue()
        self.typing_stop = threading.Event()
        self.jiggler_stop = threading.Event()
        self.typing_thread = None
        self.jiggler_thread = None
        self.typing_active = threading.Event()
        self.macro_active=threading.Event();self.macro_stop=threading.Event();self.macro_events=queue.Queue();self.macro_thread=None
        self.backend._activity_should_yield=lambda:self.typing_active.is_set() or self.macro_active.is_set()
        self.total = 0
        self.typed = 0
        self.active_config = None
        self.active_text = ''
        self.jiggler_started = None
        self.listener_started = False
        self.closing = False
        self.page = 'Auto Typer'
        self.movement_count = 0
        self.speed = ctk.StringVar(value='balanced')
        self.newline = ctk.StringVar(value='space')
        self.natural = ctk.BooleanVar(value=True)
        self.word_pauses = ctk.BooleanVar(value=False)
        self.sound = ctk.BooleanVar(value=prefs['sound'])
        self.setup_gui()
        self.root.bind('<Configure>',self.responsive_layout,add='+')
        self.root.after(0,self.responsive_layout)
        self.desktop_events=queue.Queue()
        self.desktop=DesktopIntegration(self.desktop_events,resource('assets/icon.png'))
        self.desktop.start()
        self.desktop.notifications_enabled=prefs['notifications']
        self.root.bind('<Escape>', lambda _: self.emergency_stop())
        self.root.bind('<Command-Return>', lambda _: self.start_typing() if self.page == 'Auto Typer' else self.start_jiggler())
        self.root.bind('<Control-Return>', lambda _: self.start_typing() if self.page == 'Auto Typer' else self.start_jiggler())
        self.root.after(100, self.poll)
        self.root.after(200, self.check_permissions)
        if show_intro and (not self.preferences.intro_complete()):
            self.root.after(250, self.show_introduction)

    def label(self, parent, text, size=14, color=None, weight='normal', **kwargs):
        return ctk.CTkLabel(parent, text=text, text_color=INK if color is None else color, font=(FONT, size, weight), anchor='w', **kwargs)

    def button(self, parent, text, command, primary=False, **kwargs):
        return ctk.CTkButton(parent, text=text, command=command, height=kwargs.pop('height', 38), corner_radius=19, border_width=1, border_color=ACCENT if primary else LINE, font=(FONT, 13, 'bold' if primary else 'normal'), fg_color=ACCENT if primary else LINE, hover_color=HOVER if primary else '#435447', text_color=BG if primary else INK, text_color_disabled='#6C7B70', **kwargs)

    def entry(self, parent, value, width=76):
        entry = ctk.CTkEntry(parent, width=width, height=36, fg_color=INSET, border_color=LINE, corner_radius=12, font=(FONT, 14), text_color=INK)
        entry.insert(0, str(value))
        return entry

    def switch(self, parent, text, var, command=None):
        return ctk.CTkSwitch(parent, text=text, variable=var, command=command, font=(FONT, 13), text_color=INK, progress_color=ACCENT, fg_color=LINE, button_color=INK, button_hover_color=HOVER, switch_width=34, switch_height=18)

    def setup_gui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        header = ctk.CTkFrame(self.root, fg_color='transparent', height=76)
        header.grid(row=0, column=0, sticky='ew', padx=30, pady=(20, 8))
        header.grid_columnconfigure(1, weight=1)
        mark = ctk.CTkFrame(header, width=42, height=42, corner_radius=12, fg_color=ACCENT)
        mark.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        mark.grid_propagate(False)
        icon = Image.open(resource('assets/icon.png'))
        self.brand_icon = ctk.CTkImage(icon, icon, size=(42, 42))
        ctk.CTkLabel(mark, text='', image=self.brand_icon).place(relx=0.5, rely=0.5, anchor='center')
        if sys.platform == 'win32':
            self.root.iconbitmap(str(resource('assets/icon.ico')))
        self.label(header, 'AutoTyper Pro', 20, weight='bold').grid(row=0, column=1, sticky='sw')
        self.label(header, 'PRO  /  DESKTOP TOOLS', 10, MUTED).grid(row=1, column=1, sticky='nw')
        self.nav = ctk.CTkSegmentedButton(header, values=['Auto Typer', tr('nav.activity'), tr('nav.macros'), tr('settings.title')], command=self.show_page, height=42, corner_radius=21, font=(FONT, 13), fg_color=PANEL, selected_color=LINE, selected_hover_color='#435447', unselected_color=PANEL, unselected_hover_color=LINE, text_color=INK, dynamic_resizing=False, width=410)
        self.nav.set('Auto Typer')
        self.nav.grid(row=0, column=2, rowspan=2, padx=14)
        self.header=header
        self.activity_badge = self.label(header, tr('ui.4106acbcd32a'), 12, ACCENT)
        self.activity_badge.grid(row=0, column=3, rowspan=2)
        self.permission_bar = ctk.CTkFrame(self.root, fg_color='#332B23', corner_radius=10)
        self.permission_bar.grid(row=1, column=0, sticky='ew', padx=30, pady=(0, 10))
        self.permission_bar.grid_columnconfigure(0, weight=1)
        self.permission_text = self.label(self.permission_bar, tr('ui.dd0a4c78f16b'), 12, '#E4CEAC')
        self.permission_text.grid(row=0, column=0, sticky='w', padx=14, pady=12)
        self.permission_text.configure(wraplength=490, justify='left')
        self.button(self.permission_bar, tr('ui.ca2f77a3a651'), self.check_permissions, width=135).grid(row=0, column=1, padx=4)
        self.button(self.permission_bar, tr('ui.44db213c37d6'), self.permission_action, width=80).grid(row=0, column=2, padx=4)
        self.button(self.permission_bar, tr('ui.212c3b2c3360'), self.restart, width=116).grid(row=0, column=3, padx=8)
        self.permission_bar.grid_remove()
        self.body = ctk.CTkFrame(self.root, fg_color='transparent')
        self.body.grid(row=2, column=0, sticky='nsew', padx=30)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)
        self.typer_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.jiggler_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.build_typer()
        self.build_jiggler()
        self.macros_page = ctk.CTkFrame(self.body,fg_color='transparent')
        from macro_page import MacroPage
        self.macro_page=MacroPage(self,self.macros_page)
        self.settings_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.build_settings()
        self.typer_page.grid(row=0, column=0, sticky='nsew')
        footer = ctk.CTkFrame(self.root, fg_color='transparent')
        footer.grid(row=3, column=0, sticky='ew', padx=30, pady=(10, 18))
        footer.grid_columnconfigure(0, weight=1)
        self.status = self.label(footer, tr('ui.a0f874cdf144'), 12, MUTED, wraplength=650, justify='left')
        self.status.grid(row=0, column=0, sticky='w')
        self.status.configure(wraplength=390)
        self.button(footer,'?',lambda:show_support(self),width=28,height=28).grid(row=0,column=4,padx=(8,0))
        self.button(footer,tr('ui.acc8c9e36f29')+' / ESC',self.emergency_stop,width=92,height=28).grid(row=0,column=3,padx=(12,0))
        self.button(footer, tr('ui.c568af74c1f8'), self.show_introduction, width=68, height=28).grid(row=0, column=1, padx=12)
        self.label(footer, tr('ui.5deac40c6ff6'), 11, MUTED).grid(row=0, column=2, sticky='e')
        if getattr(self,'pending_message',None):
            self.tell(*self.pending_message);self.pending_message=None
        self.mutable_typing = [self.speed_menu, self.newline_menu, self.start_delay, self.min_delay, self.max_delay, self.natural_switch, self.pause_switch, self.paste_btn, self.clear_btn]

    def page_title(self, page, number, title, description):
        heading = ctk.CTkFrame(page, fg_color='transparent')
        heading.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(14, 22))
        self.label(heading, number, 11, ACCENT, 'bold').pack(anchor='w', pady=(0, 5))
        self.label(heading, title, 32, weight='bold').pack(anchor='w')
        self.label(heading, description, 13, MUTED).pack(anchor='w', pady=(5, 0))

    def build_typer(self):
        page = self.typer_page
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, minsize=300)
        page.grid_rowconfigure(1, weight=1)
        self.page_title(page, '01  /  TEXT', tr('typing.title'), tr('ui.806aa52cde5b'))
        editor = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=16)
        editor.grid(row=1, column=0, sticky='nsew', padx=(0, 18))
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_rowconfigure(2, weight=1)
        toolbar = ctk.CTkFrame(editor, fg_color='transparent')
        toolbar.grid(row=0, column=0, sticky='ew', padx=20, pady=(16, 10))
        toolbar.grid_columnconfigure(0, weight=1)
        self.label(toolbar, tr('ui.df5883862151'), 15, weight='bold').grid(row=0, column=0, sticky='w')
        self.copy_btn = self.button(toolbar, tr('ui.0b613a663b04'), self.copy_text, width=70)
        self.copy_btn.grid(row=0, column=1, padx=4)
        self.paste_btn = self.button(toolbar, tr('ui.4c7c65963588'), self.paste_text, width=70)
        self.paste_btn.grid(row=0, column=2, padx=4)
        self.clear_btn = self.button(toolbar, tr('ui.021e6221a5d4'), self.clear_text, width=70)
        self.clear_btn.grid(row=0, column=3, padx=(4, 0))
        self.text_input = ctk.CTkTextbox(editor, fg_color=INSET, corner_radius=10, border_width=1, border_color=LINE, font=(FONT, 16), text_color=INK, wrap='word', spacing1=5, spacing3=5)
        from profile_controls import ProfileControls
        from dataclasses import asdict
        self.typing_profiles=ProfileControls(editor,self,'typing',lambda:asdict(self.config()),self.apply_typing_profile)
        self.typing_profiles.grid(row=1,column=0,sticky='ew',padx=20,pady=(0,12))
        self.text_input.grid(row=2, column=0, sticky='nsew', padx=16, pady=(0, 12))
        self.text_input.bind('<<Modified>>', self.on_modified)
        self.empty_hint = self.label(self.text_input, tr('ui.2247f277c900'), 15, MUTED, justify='left')
        self.empty_hint.place(x=24, y=26)
        self.empty_hint.bind('<Button-1>', lambda _: self.text_input.focus_set())
        stats = ctk.CTkFrame(editor, fg_color='transparent')
        stats.grid(row=3, column=0, sticky='ew', padx=20, pady=(0, 16))
        self.char_label = self.label(stats, tr('ui.3ce6e9f2cf64'), 12, MUTED)
        self.char_label.pack(side='left')
        self.word_label = self.label(stats, tr('ui.4d684b0e11da'), 12, MUTED)
        self.word_label.pack(side='left', padx=20)
        self.estimate_label = self.label(stats, '≈ 00:00', 12, ACCENT)
        self.estimate_label.pack(side='right')
        options = ctk.CTkScrollableFrame(page, fg_color=PANEL, corner_radius=16, width=280)
        options.grid(row=1, column=1, sticky='nsew')
        options.grid_columnconfigure(0, weight=1)
        self.label(options, tr('ui.1b240b731c39'), 17, weight='bold').grid(row=0, column=0, sticky='w', padx=16, pady=(16, 18))
        self.label(options, tr('ui.92354769db0a'), 12, MUTED).grid(row=1, column=0, sticky='w', padx=16)
        self.speed_menu = ctk.CTkOptionMenu(options, values=[tr(key) for key in SPEED_KEYS], command=self.settings_changed, height=38, fg_color=LINE, button_color=LINE, button_hover_color='#435447', dropdown_fg_color=PANEL, dropdown_hover_color=LINE, text_color=INK, font=(FONT, 14), corner_radius=8)
        self.speed_menu.set(tr(SPEED_KEYS[list(SPEEDS).index(self.speed.get())]))
        self.speed_menu.grid(row=2, column=0, sticky='ew', padx=16, pady=(8, 6))
        self.speed_hint = self.label(options, tr('ui.c87e970a982e'), 11, ACCENT)
        self.speed_hint.grid(row=3, column=0, sticky='w', padx=16)
        self.random_frame = ctk.CTkFrame(options, fg_color='transparent')
        self.random_frame.grid(row=4, column=0, sticky='ew', padx=16, pady=(8, 0))
        self.min_delay = self.entry(self.random_frame, 10)
        self.min_delay.pack(side='left')
        self.label(self.random_frame, ' – ', 12, MUTED).pack(side='left')
        self.max_delay = self.entry(self.random_frame, 5000)
        self.max_delay.pack(side='left')
        self.label(self.random_frame, ' ms', 12, MUTED).pack(side='left')
        self.random_frame.grid_remove()
        delay_row = ctk.CTkFrame(options, fg_color='transparent')
        delay_row.grid(row=5, column=0, sticky='ew', padx=16, pady=(20, 12))
        self.label(delay_row, tr('ui.7a6d358875d9'), 13).pack(side='left')
        self.start_delay = self.entry(delay_row, 3, 54)
        self.start_delay.pack(side='right')
        self.label(options, tr('ui.1bec5dae2619'), 11, MUTED).grid(row=6, column=0, sticky='w', padx=16)
        ctk.CTkFrame(options, height=1, fg_color=LINE).grid(row=7, column=0, sticky='ew', padx=16, pady=20)
        self.natural_switch = self.switch(options, tr('ui.a187363b0552'), self.natural, self.update_stats)
        self.natural_switch.grid(row=8, column=0, sticky='w', padx=16, pady=(0, 12))
        self.pause_switch = self.switch(options, tr('ui.dea62740e40d'), self.word_pauses, self.update_stats)
        self.pause_switch.grid(row=9, column=0, sticky='w', padx=16, pady=(0, 18))
        self.label(options, tr('ui.6f3ebfdf3062'), 12, MUTED).grid(row=10, column=0, sticky='w', padx=16)
        self.newline_menu = ctk.CTkOptionMenu(options, values=[tr(key) if key else 'Shift + Enter' for key in NEWLINE_KEYS], command=self.newline_changed, height=36, fg_color=LINE, button_color=LINE, button_hover_color='#435447', dropdown_fg_color=PANEL, text_color=INK, font=(FONT, 13), corner_radius=8)
        self.newline_menu.set(tr(NEWLINE_KEYS[list(NEWLINES).index(self.newline.get())]) if self.newline.get() != 'shift_enter' else 'Shift + Enter')
        self.newline_menu.grid(row=11, column=0, sticky='ew', padx=16, pady=(8, 18))
        self.switch(options, tr('ui.f5bed29f5be2'), self.sound, lambda:self.preferences.update({'sound':self.sound.get()})).grid(row=12, column=0, sticky='w', padx=16, pady=(0, 18))
        for entry in (self.start_delay, self.min_delay, self.max_delay):
            entry.bind('<KeyRelease>', lambda _: self.update_stats())
        controls = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=14)
        controls.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(16, 0))
        controls.grid_columnconfigure(0, weight=1)
        self.run_label = self.label(controls, tr('ui.a1d450f3bd61'), 15, weight='bold')
        self.run_label.grid(row=0, column=0, sticky='w', padx=20, pady=(14, 0))
        self.progress_label = self.label(controls, tr('ui.0ef1e0251b83'), 12, MUTED)
        self.progress_label.grid(row=1, column=0, sticky='w', padx=20, pady=(4, 12))
        self.progress = ctk.CTkProgressBar(controls, height=4, fg_color=LINE, progress_color=ACCENT)
        self.progress.set(0)
        self.progress.grid(row=2, column=0, columnspan=3, sticky='ew', padx=20, pady=(0, 16))
        self.stop_btn = self.button(controls, tr('ui.acc8c9e36f29'), self.stop_typing, width=90, state='disabled')
        self.stop_btn.grid(row=0, column=1, rowspan=2, padx=8)
        self.start_btn = self.button(controls, tr('ui.bb28d782799a'), self.start_typing, primary=True, width=178)
        self.start_btn.grid(row=0, column=2, rowspan=2, padx=(0, 20))

    def apply_typing_profile(self, data):
        config=TypingConfig(**data).validate()
        self.speed.set(next(k for k,v in SPEEDS.items() if v==config.delay_ms))
        self.newline.set(config.newline);self.natural.set(config.natural);self.word_pauses.set(config.word_pauses)
        for name,value in [('start_delay',config.start_delay),('min_delay',config.min_ms),('max_delay',config.max_ms)]:
            entry=getattr(self,name);entry.delete(0,'end');entry.insert(0,str(value))
        self.settings_changed();self.newline_menu.set(tr(NEWLINE_KEYS[list(NEWLINES).index(config.newline)]) if config.newline!='shift_enter' else 'Shift + Enter')

    def build_jiggler(self):
        from activity_page import ActivityPage
        self.activity_page = ActivityPage(self,self.jiggler_page)

    def draw_cursor(self, event=None):
        canvas=self.canvas;canvas.delete('all')
        x=canvas.winfo_width()/2;y=canvas.winfo_height()/2
        scale=min(1,max(.35,(canvas.winfo_height()-12)/190))
        for radius,color in ((94,'#222E26'),(69,'#29382D'),(44,'#354C3A')):
            r=radius*scale;canvas.create_oval(x-r,y-r,x+r,y+r,fill=color,outline='')
        r=95*scale;canvas.create_oval(x-r,y-r,x+r,y+r,outline='#3A5140',dash=(3,8))
        for side in (-1,1):canvas.create_line(x+side*122*scale,y,x+side*106*scale,y,fill=ACCENT,width=2)
        shape=[(-18,-31),(-18,29),(-3,15),(10,39),(22,33),(8,10),(30,9)]
        canvas.create_polygon(*[value for dx,dy in shape for value in (x+dx*scale,y+dy*scale)],fill=ACCENT,outline=INK,width=2)
        distance='1'
        if hasattr(self,'activity_page') and self.activity_page.entries['distance'].winfo_exists():distance=self.activity_page.entries['distance'].get()
        canvas.create_text(x+74*scale,y-57*scale,text=distance+' pt',fill=MUTED,font=(FONT,11))

    def show_page(self, value):
        self.page = value
        pages = {'Auto Typer':self.typer_page, tr('nav.activity'):self.jiggler_page, 'Mouse Jiggler':self.jiggler_page, tr('nav.macros'):self.macros_page, tr('settings.title'):self.settings_page}
        for page in (self.typer_page,self.jiggler_page,self.macros_page,self.settings_page): page.grid_remove()
        pages[value].grid(row=0,column=0,sticky='nsew')

    def responsive_layout(self,event=None):
        if self.closing or (event is not None and event.widget is not self.root):return
        from responsive import fit_scale
        dpi=self.root._get_window_scaling()
        width=self.root.winfo_width()/dpi;height=self.root.winfo_height()/dpi
        if width<100 or height<100:return
        scale=fit_scale(width,height,self.preferences.load()['ui_scale'])
        if abs(scale-getattr(self,'_layout_scale',0))>.015:
            self._layout_scale=scale;ctk.set_widget_scaling(scale)
        narrow=width<980
        self.nav.grid_configure(row=2 if narrow else 0,column=0 if narrow else 2,columnspan=4 if narrow else 1,rowspan=1 if narrow else 2,pady=(12,0) if narrow else 0)
        self.typer_page.grid_columnconfigure(1,minsize=230 if narrow else 300)
        self.jiggler_page.grid_columnconfigure(1,minsize=260 if narrow else 350)

    def save_custom_setting(self,**values):
        try:self.preferences.update(values)
        except (OSError,ValueError) as exc:self.tell(str(exc),True)

    def save_settings(self):
        try:
            self.preferences.update({'sound':self.sound.get()})
            self.tell(tr('settings.saved'))
        except OSError as exc:self.tell(str(exc),True)

    def tell(self, text, error=False):
        if not hasattr(self,'status') or not self.status.winfo_exists():
            self.pending_message=(text,error);return
        self.status.configure(text=text, text_color=DANGER if error else MUTED)

    def check_permissions(self):
        allowed = self.backend.allowed()
        changed = allowed != self.permission_ready
        self.permission_ready = allowed
        self.permission_checked = time.monotonic()
        if allowed:
            self.permission_bar.grid_remove()
        else:
            self.permission_bar.grid()
            self.permission_text.configure(text=tr('ui.a3e8004e39b1'))
        if changed and allowed:
            self.tell(tr('ui.612b6041ca9d'))
        if changed and (not allowed):
            self.emergency_stop()
        return allowed

    def permission_action(self):
        if self.check_permissions():
            return
        if hasattr(self.backend, 'request_permission'):
            try:
                self.backend.request_permission()
            except Exception as exc:
                self.tell(tr('ui.e396d3460879', v0=exc), True)
                return
        open_permissions()
        self.tell(tr('ui.66a839ee48cf', v0=sys.executable), True)

    def show_introduction(self):
        if self.closing or self.macro_active.is_set() or self.intro:
            return
        if self.typing_active.is_set() or self.macro_active.is_set() or (self.jiggler_thread and self.jiggler_thread.is_alive()):
            self.tell(tr('ui.3f7939b042e1'))
            return
        self.intro = Introduction(self)

    def snapshot(self):
        return { 'text': self.text_input.get('1.0', 'end-1c'), 'speed': self.speed.get(), 'newline': self.newline.get(), 'natural': self.natural.get(), 'word_pauses': self.word_pauses.get(), 'sound': self.sound.get(), 'start_delay': self.start_delay.get(), 'min_delay': self.min_delay.get(), 'max_delay': self.max_delay.get(), 'idle': self.idle_entry.get(), 'interval': self.interval_entry.get(), 'activity':self.activity_page.snapshot(), 'macro':self.macro_page.snapshot(), 'profiles':{'typing':self.typing_profiles.selected,'activity':self.activity_page.profiles.selected}}

    def apply_state(self, data):
        self.text_input.delete('1.0','end')
        self.text_input.insert('1.0',data.get('text',''))
        for name in ('speed','newline','natural','word_pauses','sound'):
            if name in data: getattr(self,name).set(data[name])
        for name,key in [('start_delay','start_delay'),('min_delay','min_delay'),('max_delay','max_delay'),('idle_entry','idle'),('interval_entry','interval')]:
            if key in data:
                entry=getattr(self,name);entry.delete(0,'end');entry.insert(0,str(data[key]))
        if 'macro' in data:self.macro_page.restore(data['macro'])
        if 'activity' in data:self.activity_page.restore(data['activity'])
        elif 'f18' in data:self.activity_page.apply({'idle_threshold':float(data.get('idle',60)),'interval':float(data.get('interval',30)),'key':'f18' if data['f18'] else None})
        self.settings_changed()
        if 'profiles' in data:
            for kind,bar in [('typing',self.typing_profiles),('activity',self.activity_page.profiles)]:
                bar.selected=data['profiles'].get(kind);bar.refresh();bar.dirty()
        self.newline_menu.set(tr(NEWLINE_KEYS[list(NEWLINES).index(self.newline.get())]) if self.newline.get() != 'shift_enter' else 'Shift + Enter')

    def newline_changed(self, value):
        labels=[tr(key) if key else 'Shift + Enter' for key in NEWLINE_KEYS]
        self.newline.set(list(NEWLINES)[labels.index(value)])
        self.update_stats()

    def build_settings(self):
        from settings_ui import build_settings
        build_settings(self,self.settings_page)

    def change_preferences(self, **values):
        if self.typing_active.is_set() or (self.jiggler_thread and self.jiggler_thread.is_alive()) or self.macro_active.is_set() or self.intro:
            self.tell(tr('settings.idle'));return
        state=self.snapshot()
        try: self.preferences.update(values)
        except (OSError,ValueError) as exc: self.tell(str(exc),True);return
        prefs=self.preferences.load();set_locale(prefs['locale']);set_palette(prefs['appearance'])
        for child in list(self.root.winfo_children()):
            if child is not getattr(self,'report_window',None):child.destroy()
        self.root.configure(fg_color=BG)
        self.setup_gui();self.apply_state(state)
        self.responsive_layout()
        self.nav.set(tr('settings.title'));self.show_page(tr('settings.title'))
        self.check_permissions();self.tell(tr('settings.saved'))

    def restart(self):
        if self.closing:
            return
        if self.macro_active.is_set():self.tell(tr('macro.busy'));return
        token = secrets.token_urlsafe(32)
        state = self.snapshot(); state['_resume_token'] = token
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', prefix='autotyper-resume-', suffix='.json', delete=False) as f:
                json.dump(state, f, ensure_ascii=False)
                path = f.name
        except OSError as exc:
            self.tell(tr('ui.e1c2f39c7ced', v0=exc), True)
            return
        self.restart_command = [sys.executable] + ([] if getattr(sys, 'frozen', False) else [str(Path(__file__).resolve())]) + ['--resume-state', path, '--resume-token', token, '--skip-intro']
        self.close()

    def restore_state(self, path, token=None):
        path = Path(path)
        owned = False
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('Invalid resume state')
            owned = bool(token and data.get('_resume_token') == token and path.name.startswith('autotyper-resume-') and (path.suffix == '.json') and (not path.is_symlink()) and (path.parent.resolve() == Path(tempfile.gettempdir()).resolve()))
            self.apply_state(data)
        except (OSError, ValueError, TypeError, AttributeError):
            self.tell(tr('ui.fd31e1c67335'), True)
        finally:
            if owned:
                path.unlink(missing_ok=True)

    def ensure_permission(self):
        if not self.check_permissions():
            self.tell(tr('ui.bf2aa5605fb3'), True)
            return False
        if not self.listener_started or not self.backend.escape_healthy():
            self.listener_started = False
            try:
                self.backend.listen_escape(self.emergency_stop)
                self.listener_started = True
            except Exception as exc:
                self.tell(tr('ui.84d9dbf56edd', v0=exc), True)
                return False
        return True

    def settings_changed(self, value=None):
        if value is not None:
            self.speed.set(list(SPEEDS)[[tr(key) for key in SPEED_KEYS].index(value)])
        self.speed_menu.set(tr(SPEED_KEYS[list(SPEEDS).index(self.speed.get())]))
        random_mode = self.speed.get() == 'random'
        if random_mode:
            self.random_frame.grid()
        else:
            self.random_frame.grid_remove()
        self.speed_hint.configure(text=tr('ui.4560607fb72d') if random_mode else tr('ui.586d47e68638', v0=SPEEDS[self.speed.get()]))
        self.update_stats()

    def config(self):
        try:
            return TypingConfig(delay_ms=SPEEDS[self.speed.get()], start_delay=float(self.start_delay.get()), min_ms=int(self.min_delay.get()), max_ms=int(self.max_delay.get()), natural=self.natural.get(), word_pauses=self.word_pauses.get(), newline=NEWLINES[self.newline.get()]).validate()
        except (ValueError, KeyError) as exc:
            if tr('ui.394f23ccbfb7') in str(exc):
                raise
            raise ValueError(tr('ui.e304b5e6c26b')) from exc

    def on_modified(self, event=None):
        if self.text_input.edit_modified():
            self.text_input.edit_modified(False)
            self.update_stats()

    def update_stats(self):
        if hasattr(self,'typing_profiles'):self.typing_profiles.dirty()
        text = self.text_input.get('1.0', 'end-1c')
        self.char_label.configure(text=tr('ui.763846500742', v0=len(text)))
        self.word_label.configure(text=tr('ui.a546d243d22f', v0=len(text.split())))
        if text:
            self.empty_hint.place_forget()
        else:
            self.empty_hint.place(x=24, y=26)
        if not self.typing_active.is_set():
            try:
                config = self.config()
                self.estimate_label.configure(text=f'≈ {duration(config.estimate(text))}')
                self.progress_label.configure(text=tr('ui.55510f15861a', v0=config.start_delay))
            except ValueError:
                self.estimate_label.configure(text=tr('ui.c5e1d194c109'))

    def copy_text(self):
        text = self.text_input.get('1.0', 'end-1c')
        if not text:
            self.tell(tr('ui.ede8c870a44a'))
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.tell(tr('ui.aad5c5420716'))

    def paste_text(self):
        if self.typing_active.is_set():
            return
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            self.tell(tr('ui.6f801c31451c'), True)
            return
        self.text_input.delete('1.0', 'end')
        self.text_input.insert('1.0', text)
        self.update_stats()
        self.tell(tr('ui.63f9a7d6f070'))

    def clear_text(self):
        if self.typing_active.is_set():
            return
        self.text_input.delete('1.0', 'end')
        self.update_stats()
        self.progress.set(0)
        self.tell(tr('ui.74009ec5e73b'))

    def sound_event(self, name):
        if self.sound.get():
            prefs=self.preferences.load()
            try:play_sound(name,prefs['sound_theme'],prefs['sound_volume'])
            except (OSError,ValueError):pass

    def start_typing(self):
        if self.macro_active.is_set() or (self.macro_thread and self.macro_thread.is_alive()):self.tell(tr('macro.busy'));return
        if self.typing_thread and self.typing_thread.is_alive():
            return
        text = self.text_input.get('1.0', 'end-1c')
        if not text:
            self.tell(tr('ui.16026de46fb3'), True)
            self.text_input.focus_set()
            return
        try:
            config = self.config()
        except ValueError as exc:
            self.tell(str(exc), True)
            return
        if not self.ensure_permission():
            return
        if hasattr(self.backend,'prepare_typing'):self.backend.prepare_typing()
        self.active_text = text
        self.active_config = config
        self.total = len(text)
        self.typed = 0
        self.typing_events = queue.Queue()
        self.typing_stop.clear()
        self.typing_active.set()
        self.text_input.configure(state='disabled')
        for widget in self.mutable_typing:
            widget.configure(state='disabled')
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.progress.set(0)
        self.tell(tr('ui.59f04116a871'))
        self.typing_thread = threading.Thread(target=type_text, args=(text, config, self.backend, self.typing_stop, self.typing_events), daemon=True)
        self.typing_profiles.set_busy(True)
        self.typing_thread.start()

    def stop_typing(self):
        if self.typing_active.is_set():
            self.typing_stop.set()
            self.stop_btn.configure(state='disabled')
            self.run_label.configure(text=tr('ui.2e0bfe52689c'))

    def emergency_stop(self):
        self.typing_stop.set()
        self.jiggler_stop.set()
        self.macro_stop.set()

    def finish_typing(self, kind, detail):
        self.typing_active.clear()
        self.text_input.configure(state='normal')
        for widget in self.mutable_typing:
            widget.configure(state='normal')
        self.typing_profiles.set_busy(False)
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        labels = {'finished': tr('ui.f126dc372247'), 'stopped': tr('ui.c7b4913020e6'), 'error': tr('ui.3bc412609217')}
        self.run_label.configure(text=labels[kind])
        self.tell(detail if kind == 'error' else labels[kind], kind == 'error')
        self.sound_event('finish' if kind == 'finished' else 'stop')
        if kind in ('finished','error'):self.system_notification(kind)
        if kind == 'finished':
            self.progress.set(1)
        self.progress_label.configure(text=tr('ui.8fd6db2690e0', v0=self.typed, v1=self.total, v2=round(self.typed / max(1, self.total) * 100)))

    def start_jiggler(self):
        if self.jiggler_thread and self.jiggler_thread.is_alive():
            return
        if sys.platform not in ('darwin', 'win32'):
            self.tell('Mouse Jiggler macOS ve Windows gerektirir.', True)
            return
        try:
            config = self.activity_page.config()
        except ValueError as exc:
            self.tell(str(exc) if tr('ui.394f23ccbfb7') in str(exc) else tr('ui.e59279d6ec9f'), True)
            return
        if not self.ensure_permission():
            return
        self.jiggler_events = queue.Queue()
        self.jiggler_stop.clear()
        self.jiggler_started = time.monotonic()
        self.movement_count = 0
        self.moves_label.configure(text='0')
        self.jig_start_btn.configure(state='disabled')
        self.jig_stop_btn.configure(state='normal')
        self.activity_page.set_busy(True)
        self.jig_state.configure(text=tr('ui.af33f69c2bde'))
        self.tell(tr('ui.57da60ba2169'))
        self.jiggler_thread = threading.Thread(target=jiggle, args=(config, self.backend, self.jiggler_stop, lambda:self.typing_active.is_set() or self.macro_active.is_set(), self.jiggler_events), daemon=True)
        self.jiggler_thread.start()

    def stop_jiggler(self):
        if self.jiggler_thread and self.jiggler_thread.is_alive():
            self.jiggler_stop.set()
            self.jig_stop_btn.configure(state='disabled')
            self.jig_state.configure(text=tr('ui.2e0bfe52689c'))

    def poll(self):
        if self.closing:
            return
        if time.monotonic() - self.permission_checked >= 2:
            self.check_permissions()
        listener_failed = self.listener_started and (not self.backend.escape_healthy())
        if listener_failed:
            self.listener_started = False
            self.emergency_stop()
        for _ in range(500):
            try:
                kind, value = self.typing_events.get_nowait()
            except queue.Empty:
                break
            if kind == 'countdown':
                self.run_label.configure(text=tr('ui.7345650fa46b', v0=value))
            elif kind == 'typing':
                self.run_label.configure(text=tr('ui.94d5d34f2605'))
                self.sound_event('start')
            elif kind == 'progress':
                self.typed = value
                self.progress.set(value / max(1, self.total))
                remaining = self.active_config.estimate(self.active_text[value:], include_start=False)
                self.progress_label.configure(text=tr('ui.6eb806b0573d', v0=value, v1=self.total, v2=round(value / max(1, self.total) * 100), v3=duration(remaining)))
            elif kind in ('finished', 'stopped', 'error'):
                self.finish_typing(kind, value)
        for _ in range(100):
            try:
                kind, value = self.jiggler_events.get_nowait()
            except queue.Empty:
                break
            if kind == 'movement':
                self.movement_count = value
                self.moves_label.configure(text=str(value))
            elif kind == 'idle':
                self.idle_label.configure(text=duration(value))
            elif kind in ('jiggler_stopped', 'jiggler_error'):
                self.jig_state.configure(text=tr('ui.f4dc30229a90') if kind == 'jiggler_stopped' else tr('ui.c56abb595b97'))
                self.jig_start_btn.configure(state='normal')
                self.jig_stop_btn.configure(state='disabled')
                self.activity_page.set_busy(False)
                self.tell(value if kind == 'jiggler_error' else tr('ui.8b10cdb83c0e'), kind == 'jiggler_error')
                if kind=='jiggler_error':self.system_notification('error')
        jig_active = bool(self.jiggler_thread and self.jiggler_thread.is_alive())
        typing = self.typing_active.is_set()
        self.activity_badge.configure(text=tr('ui.7c052300f26d') if typing and jig_active else tr('ui.2a4a5f6abd9b') if typing else tr('ui.80c610056213') if jig_active else tr('ui.4106acbcd32a'))
        if jig_active:
            self.elapsed_label.configure(text=duration(time.monotonic() - self.jiggler_started))
            self.jig_description.configure(text=tr('ui.294a25641801') if typing else tr('ui.5f615f507b9c'))
        else:
            self.jig_description.configure(text=tr('ui.39c13a156e82'))
        self.macro_page.poll()
        if self.macro_active.is_set():
            self.activity_badge.configure(text=tr('macro.badge_recording') if self.macro_page.state=='recording' else tr('macro.badge_playing'))
        if listener_failed:
            self.tell(tr('ui.a69e776cd09f'), True)
        self.desktop.update(self.activity_badge.cget('text'),jig_active)
        self.poll_desktop()
        if not self.closing:self.root.after(100, self.poll)

    def system_notification(self,kind):
        keys={'finished':'notification.finished','error':'notification.error','macro_finished':'notification.macro_finished','record_finished':'notification.record_finished'}
        if kind in keys and self.preferences.load()['notifications']:
            self.desktop.notify(tr('notification.title'),tr(keys[kind]))

    def notification_preference(self):
        self.preferences.update({'notifications':self.notifications.get()})
        self.desktop.notifications_enabled=self.notifications.get()
        self.desktop.invalidate_notification_request()
        if self.notifications.get():self.desktop.request_notifications()

    def request_close(self):
        if self.preferences.load()['keep_running']:
            if self.desktop.ready:self.root.withdraw()
            else:self.tell(tr('desktop.unavailable'),True)
        else:self.close()

    def reveal(self,page=None):
        self.root.deiconify();self.root.lift()
        if page:
            self.nav.set(page);self.show_page(page)

    def poll_desktop(self):
        for _ in range(100):
            try:command=self.desktop_events.get_nowait()
            except queue.Empty:break
            if isinstance(command,tuple) and command[0]=='notification_permission':
                if not self.desktop.accept_notification_permission(command):continue
                granted=command[1]
                try:self.preferences.update({'notifications':granted})
                except OSError:
                    self.notifications.set(False);self.desktop.notifications_enabled=False
                    self.tell(tr('desktop.notification_save_failed'),True);continue
                self.notifications.set(granted);self.desktop.notifications_enabled=granted
                self.tell(tr('desktop.notification_ready' if granted else 'desktop.notification_denied'),not granted);continue
            pages={'typing':'Auto Typer','activity':tr('nav.activity'),'macros':tr('nav.macros'),'settings':tr('settings.title')}
            if command=='quit':self.close();return
            if command=='open':self.reveal()
            elif command in pages:self.reveal(pages[command])
            elif command=='about':self.reveal();show_support(self)
            elif command=='report':self.reveal();report_bug(self)
            elif command=='start_activity':self.start_jiggler()
            elif command=='stop_activity':self.jiggler_stop.set()
            elif command=='stop_all':self.emergency_stop()

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.desktop.stop()
        self.emergency_stop()
        self.backend.close()
        self.root.withdraw()
        self.await_shutdown()

    def await_shutdown(self):
        if any((t and t.is_alive() for t in (self.typing_thread, self.jiggler_thread, self.macro_thread, self.backend.listener if hasattr(self.backend, 'listener') else None))):
            self.root.after(30, self.await_shutdown)
        else:
            if self.restart_command:
                try:
                    subprocess.Popen(self.restart_command)
                except OSError as exc:
                    self.closing = False
                    self.restart_command = None
                    self.listener_started = False
                    self.root.deiconify()
                    self.desktop.start()
                    self.tell(tr('ui.150f5a043de2', v0=exc), True)
                    self.root.after(100, self.poll)
                    return
            self.root.destroy()

    def run(self):
        self.root.mainloop()
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-intro', action='store_true')
    parser.add_argument('--resume-state')
    parser.add_argument('--diagnostics', action='store_true')
    parser.add_argument('--resume-token')
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    if args.diagnostics:
        backend = create_backend()
        print(json.dumps({'version': VERSION, 'platform': sys.platform, 'executable': sys.executable, 'permission': backend.allowed(), 'ax_trusted': bool(backend.trusted()) if hasattr(backend, 'trusted') else None, 'post_allowed': bool(backend.post_allowed()) if hasattr(backend, 'post_allowed') else None}))
        backend.close()
    else:
        app = AutoTyper(show_intro=not (args.skip_intro or args.smoke_test))
        if args.resume_state:
            app.restore_state(args.resume_state, args.resume_token)
        if args.smoke_test:
            app.root.after(1200, app.close)
        app.run()
