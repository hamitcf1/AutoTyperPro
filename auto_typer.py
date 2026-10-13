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
from engine import TypingConfig, JigglerConfig, type_text, jiggle
from platform_backend import create_backend, open_permissions, play_sound

BG = '#141816'
PANEL = '#1D2420'
INSET = '#171D19'
LINE = '#303C34'
INK = '#F0F3EF'
MUTED = '#97A79C'
ACCENT = '#ACD5AE'
HOVER = '#C2E3C3'
DANGER = '#EDB6A9'
FONT = 'SF Pro Display' if sys.platform == 'darwin' else 'Segoe UI'
SPEEDS = {'Çok hızlı': 30, 'Hızlı': 60, 'Dengeli': 100, 'Yavaş': 150, 'Çok yavaş': 250, 'Rastgele': -1}
NEWLINES = {'Boşluk': 'space', 'Shift + Enter': 'shift_enter', 'Atla': 'ignore'}


def duration(seconds):
    seconds = max(0, round(seconds))
    return f'{seconds // 60:02d}:{seconds % 60:02d}'


class AutoTyper:
    def __init__(self, show_intro=True):
        ctk.set_appearance_mode('dark')
        self.root = ctk.CTk(fg_color=BG)
        self.root.title(f'AutoTyper Pro {VERSION}')
        self.root.geometry('1120x800')
        self.root.minsize(980, 740)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.backend = create_backend()
        self.preferences=Preferences();self.intro=None;self.permission_checked=0;self.restart_command=None
        self.permission_ready=False
        self.typing_events = queue.Queue(); self.jiggler_events = queue.Queue()
        self.typing_stop = threading.Event(); self.jiggler_stop = threading.Event()
        self.typing_thread = None; self.jiggler_thread = None
        self.typing_active = threading.Event()
        self.total = 0; self.typed = 0; self.active_config = None; self.active_text = ''
        self.jiggler_started = None; self.listener_started = False; self.closing = False
        self.page = 'Auto Typer'; self.movement_count = 0
        self.speed = ctk.StringVar(value='Dengeli')
        self.newline = ctk.StringVar(value='Boşluk')
        self.natural = ctk.BooleanVar(value=True)
        self.word_pauses = ctk.BooleanVar(value=False)
        self.sound = ctk.BooleanVar(value=True)
        self.f18 = ctk.BooleanVar(value=False)
        self.setup_gui()
        self.root.bind('<Escape>', lambda _: self.emergency_stop())
        self.root.bind('<Command-Return>', lambda _: self.start_typing() if self.page == 'Auto Typer' else self.start_jiggler())
        self.root.bind('<Control-Return>', lambda _: self.start_typing() if self.page == 'Auto Typer' else self.start_jiggler())
        self.root.after(100, self.poll)
        self.root.after(200, self.check_permissions)
        if show_intro and not self.preferences.intro_complete():self.root.after(250,self.show_introduction)

    def label(self, parent, text, size=14, color=INK, weight='normal', **kwargs):
        return ctk.CTkLabel(parent, text=text, text_color=color, font=(FONT, size, weight), anchor='w', **kwargs)

    def button(self, parent, text, command, primary=False, **kwargs):
        return ctk.CTkButton(parent, text=text, command=command, height=kwargs.pop('height',38), corner_radius=9,
            font=(FONT, 13, 'bold' if primary else 'normal'), fg_color=ACCENT if primary else LINE,
            hover_color=HOVER if primary else '#435447', text_color=BG if primary else INK,
            text_color_disabled='#6C7B70', **kwargs)

    def entry(self, parent, value, width=76):
        entry = ctk.CTkEntry(parent, width=width, height=36, fg_color=INSET, border_color=LINE,
                             corner_radius=8, font=(FONT, 14), text_color=INK)
        entry.insert(0, str(value)); return entry

    def switch(self, parent, text, var, command=None):
        return ctk.CTkSwitch(parent, text=text, variable=var, command=command,
            font=(FONT, 13), text_color=INK, progress_color=ACCENT, fg_color=LINE,
            button_color=INK, button_hover_color=HOVER, switch_width=34, switch_height=18)

    def setup_gui(self):
        self.root.grid_columnconfigure(0, weight=1); self.root.grid_rowconfigure(2, weight=1)
        header = ctk.CTkFrame(self.root, fg_color='transparent', height=76)
        header.grid(row=0, column=0, sticky='ew', padx=30, pady=(20, 8))
        header.grid_columnconfigure(1, weight=1)
        mark = ctk.CTkFrame(header, width=42, height=42, corner_radius=12, fg_color=ACCENT)
        mark.grid(row=0, column=0, rowspan=2, padx=(0,12)); mark.grid_propagate(False)
        icon=Image.open(resource('assets/icon.png'))
        self.brand_icon=ctk.CTkImage(icon,icon,size=(42,42))
        ctk.CTkLabel(mark, text='',image=self.brand_icon).place(relx=.5, rely=.5, anchor='center')
        if sys.platform=='win32':self.root.iconbitmap(str(resource('assets/icon.ico')))
        self.label(header, 'AutoTyper', 20, weight='bold').grid(row=0, column=1, sticky='sw')
        self.label(header, 'PRO  /  DESKTOP TOOLS', 10, MUTED).grid(row=1, column=1, sticky='nw')
        self.nav = ctk.CTkSegmentedButton(header, values=['Auto Typer', 'Mouse Jiggler'], command=self.show_page,
            height=38, corner_radius=10, font=(FONT, 13), fg_color=PANEL, selected_color=LINE,
            selected_hover_color='#435447', unselected_color=PANEL, unselected_hover_color=LINE,
            text_color=INK, dynamic_resizing=False, width=290)
        self.nav.set('Auto Typer'); self.nav.grid(row=0, column=2, rowspan=2, padx=24)
        self.activity_badge = self.label(header, '●  Hazır', 12, ACCENT)
        self.activity_badge.grid(row=0, column=3, rowspan=2)
        self.permission_bar = ctk.CTkFrame(self.root, fg_color='#332B23', corner_radius=10)
        self.permission_bar.grid(row=1, column=0, sticky='ew', padx=30, pady=(0,10))
        self.permission_bar.grid_columnconfigure(0, weight=1)
        self.permission_text = self.label(self.permission_bar, 'Klavye ve fare kontrolü için erişilebilirlik izni gerekiyor.', 12, '#E4CEAC')
        self.permission_text.grid(row=0, column=0, sticky='w', padx=14, pady=12)
        self.permission_text.configure(wraplength=490,justify='left')
        self.button(self.permission_bar,'Yeniden kontrol et',self.check_permissions,width=135).grid(row=0,column=1,padx=4)
        self.button(self.permission_bar,'Ayarlar ↗',self.permission_action,width=80).grid(row=0,column=2,padx=4)
        self.button(self.permission_bar,'Yeniden başlat',self.restart,width=116).grid(row=0,column=3,padx=8)
        self.permission_bar.grid_remove()
        self.body = ctk.CTkFrame(self.root, fg_color='transparent')
        self.body.grid(row=2, column=0, sticky='nsew', padx=30)
        self.body.grid_columnconfigure(0, weight=1); self.body.grid_rowconfigure(0, weight=1)
        self.typer_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.jiggler_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.build_typer(); self.build_jiggler()
        self.typer_page.grid(row=0, column=0, sticky='nsew')
        footer = ctk.CTkFrame(self.root, fg_color='transparent')
        footer.grid(row=3, column=0, sticky='ew', padx=30, pady=(10,18)); footer.grid_columnconfigure(0, weight=1)
        self.status = self.label(footer, 'Metnini ekle. Ritmini seç. Yazmaya başla.', 12, MUTED, wraplength=650, justify='left')
        self.status.grid(row=0, column=0, sticky='w')
        self.status.configure(wraplength=520)
        self.button(footer,'Tanıtım',self.show_introduction,width=68,height=28).grid(row=0,column=1,padx=12)
        self.label(footer, 'ESC  tüm etkinlikleri durdurur', 11, MUTED).grid(row=0, column=2, sticky='e')
        self.mutable_typing = [self.speed_menu, self.newline_menu, self.start_delay, self.min_delay, self.max_delay,
            self.natural_switch, self.pause_switch, self.paste_btn, self.clear_btn]

    def page_title(self, page, number, title, description):
        heading = ctk.CTkFrame(page, fg_color='transparent')
        heading.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(14,22))
        self.label(heading, number, 11, ACCENT, 'bold').pack(anchor='w', pady=(0,5))
        self.label(heading, title, 32, weight='bold').pack(anchor='w')
        self.label(heading, description, 13, MUTED).pack(anchor='w', pady=(5,0))

    def build_typer(self):
        page = self.typer_page
        page.grid_columnconfigure(0, weight=1); page.grid_columnconfigure(1, minsize=300)
        page.grid_rowconfigure(1, weight=1)
        self.page_title(page, '01  /  AUTO TYPER', 'Kelimelerin, senin ritmin.', 'Metnini herhangi bir uygulamaya, seçtiğin hızda ve doğal bir ritimle yazdır.')
        editor = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=16)
        editor.grid(row=1, column=0, sticky='nsew', padx=(0,18)); editor.grid_columnconfigure(0, weight=1); editor.grid_rowconfigure(1, weight=1)
        toolbar = ctk.CTkFrame(editor, fg_color='transparent'); toolbar.grid(row=0, column=0, sticky='ew', padx=20, pady=(16,10))
        toolbar.grid_columnconfigure(0, weight=1)
        self.label(toolbar, 'Metin alanı', 15, weight='bold').grid(row=0, column=0, sticky='w')
        self.copy_btn = self.button(toolbar, 'Kopyala', self.copy_text, width=70); self.copy_btn.grid(row=0, column=1, padx=4)
        self.paste_btn = self.button(toolbar, 'Yapıştır', self.paste_text, width=70); self.paste_btn.grid(row=0, column=2, padx=4)
        self.clear_btn = self.button(toolbar, 'Temizle', self.clear_text, width=70); self.clear_btn.grid(row=0, column=3, padx=(4,0))
        self.text_input = ctk.CTkTextbox(editor, fg_color=INSET, corner_radius=10, border_width=1, border_color=LINE,
            font=(FONT, 16), text_color=INK, wrap='word', spacing1=5, spacing3=5)
        self.text_input.grid(row=1, column=0, sticky='nsew', padx=16, pady=(0,12))
        self.text_input.bind('<<Modified>>', self.on_modified)
        self.empty_hint = self.label(self.text_input, 'Bir metinle başla.\n\nBuraya yaz veya panodan yapıştır.\nBaşlattıktan sonra hedef uygulamaya geç.', 15, MUTED, justify='left')
        self.empty_hint.place(x=24, y=26)
        self.empty_hint.bind('<Button-1>', lambda _: self.text_input.focus_set())
        stats = ctk.CTkFrame(editor, fg_color='transparent'); stats.grid(row=2, column=0, sticky='ew', padx=20, pady=(0,16))
        self.char_label = self.label(stats, '0 karakter', 12, MUTED); self.char_label.pack(side='left')
        self.word_label = self.label(stats, '0 kelime', 12, MUTED); self.word_label.pack(side='left', padx=20)
        self.estimate_label = self.label(stats, '≈ 00:00', 12, ACCENT); self.estimate_label.pack(side='right')
        options = ctk.CTkScrollableFrame(page, fg_color=PANEL, corner_radius=16, width=280)
        options.grid(row=1, column=1, sticky='nsew'); options.grid_columnconfigure(0, weight=1)
        self.label(options, 'Yazma ayarları', 17, weight='bold').grid(row=0, column=0, sticky='w', padx=16, pady=(16,18))
        self.label(options, 'Yazma hızı', 12, MUTED).grid(row=1, column=0, sticky='w', padx=16)
        self.speed_menu = ctk.CTkOptionMenu(options, values=list(SPEEDS), variable=self.speed, command=self.settings_changed,
            height=38, fg_color=LINE, button_color=LINE, button_hover_color='#435447', dropdown_fg_color=PANEL,
            dropdown_hover_color=LINE, text_color=INK, font=(FONT, 14), corner_radius=8)
        self.speed_menu.grid(row=2, column=0, sticky='ew', padx=16, pady=(8,6))
        self.speed_hint = self.label(options, '100 ms / karakter', 11, ACCENT); self.speed_hint.grid(row=3, column=0, sticky='w', padx=16)
        self.random_frame = ctk.CTkFrame(options, fg_color='transparent')
        self.random_frame.grid(row=4, column=0, sticky='ew', padx=16, pady=(8,0))
        self.min_delay = self.entry(self.random_frame, 10); self.min_delay.pack(side='left')
        self.label(self.random_frame, ' – ', 12, MUTED).pack(side='left')
        self.max_delay = self.entry(self.random_frame, 5000); self.max_delay.pack(side='left')
        self.label(self.random_frame, ' ms', 12, MUTED).pack(side='left'); self.random_frame.grid_remove()
        delay_row = ctk.CTkFrame(options, fg_color='transparent'); delay_row.grid(row=5, column=0, sticky='ew', padx=16, pady=(20,12))
        self.label(delay_row, 'Başlangıç beklemesi', 13).pack(side='left')
        self.start_delay = self.entry(delay_row, 3, 54); self.start_delay.pack(side='right')
        self.label(options, 'Hedef uygulamaya geçmek için saniye.', 11, MUTED).grid(row=6, column=0, sticky='w', padx=16)
        ctk.CTkFrame(options, height=1, fg_color=LINE).grid(row=7, column=0, sticky='ew', padx=16, pady=20)
        self.natural_switch = self.switch(options, 'Doğal yazma', self.natural, self.update_stats)
        self.natural_switch.grid(row=8, column=0, sticky='w', padx=16, pady=(0,12))
        self.pause_switch = self.switch(options, 'Kelimeler arasında bekle', self.word_pauses, self.update_stats)
        self.pause_switch.grid(row=9, column=0, sticky='w', padx=16, pady=(0,18))
        self.label(options, 'Satır sonları', 12, MUTED).grid(row=10, column=0, sticky='w', padx=16)
        self.newline_menu = ctk.CTkOptionMenu(options, values=list(NEWLINES), variable=self.newline, command=lambda _: self.update_stats(),
            height=36, fg_color=LINE, button_color=LINE, button_hover_color='#435447', dropdown_fg_color=PANEL,
            text_color=INK, font=(FONT, 13), corner_radius=8)
        self.newline_menu.grid(row=11, column=0, sticky='ew', padx=16, pady=(8,18))
        self.switch(options, 'Ses bildirimleri', self.sound).grid(row=12, column=0, sticky='w', padx=16, pady=(0,18))
        for entry in (self.start_delay, self.min_delay, self.max_delay): entry.bind('<KeyRelease>', lambda _: self.update_stats())
        controls = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=14)
        controls.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(16,0)); controls.grid_columnconfigure(0, weight=1)
        self.run_label = self.label(controls, 'Başlamaya hazır', 15, weight='bold'); self.run_label.grid(row=0, column=0, sticky='w', padx=20, pady=(14,0))
        self.progress_label = self.label(controls, 'Hedef uygulamaya geçmek için 3 saniyen olacak.', 12, MUTED)
        self.progress_label.grid(row=1, column=0, sticky='w', padx=20, pady=(4,12))
        self.progress = ctk.CTkProgressBar(controls, height=4, fg_color=LINE, progress_color=ACCENT)
        self.progress.set(0); self.progress.grid(row=2, column=0, columnspan=3, sticky='ew', padx=20, pady=(0,16))
        self.stop_btn = self.button(controls, 'Durdur', self.stop_typing, width=90, state='disabled')
        self.stop_btn.grid(row=0, column=1, rowspan=2, padx=8)
        self.start_btn = self.button(controls, 'Yazmaya başla  ↗', self.start_typing, primary=True, width=178)
        self.start_btn.grid(row=0, column=2, rowspan=2, padx=(0,20))

    def build_jiggler(self):
        page = self.jiggler_page
        page.grid_columnconfigure(0, weight=1); page.grid_columnconfigure(1, minsize=300); page.grid_rowconfigure(1, weight=1)
        self.page_title(page, '02  /  MOUSE JIGGLER', 'Küçük hareket. Kesintisiz akış.', 'Sen boşta kaldığında imleci hafifçe hareket ettirir ve yerine getirir.')
        hero = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=16)
        hero.grid(row=1, column=0, sticky='nsew', padx=(0,18)); hero.grid_columnconfigure(0, weight=1); hero.grid_rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(hero, bg=PANEL, highlightthickness=0, height=200)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=16, pady=(16,0))
        self.canvas.bind('<Configure>', self.draw_cursor)
        self.jig_state = self.label(hero, 'İmleç dinleniyor.', 25, weight='bold'); self.jig_state.grid(row=1, column=0, pady=(2,6))
        self.jig_description = self.label(hero, 'Başlatana kadar fare hareketi yapılmaz.', 13, MUTED)
        self.jig_description.grid(row=2, column=0, pady=(0,24))
        stats = ctk.CTkFrame(hero, fg_color=INSET, corner_radius=12)
        stats.grid(row=3, column=0, sticky='ew', padx=24, pady=(0,24)); stats.grid_columnconfigure((0,1,2), weight=1)
        self.elapsed_label = self.label(stats, '00:00', 24, ACCENT); self.elapsed_label.grid(row=0, column=0, pady=(16,3))
        self.moves_label = self.label(stats, '0', 24, ACCENT); self.moves_label.grid(row=0, column=1, pady=(16,3))
        self.idle_label = self.label(stats, '00:00', 24, ACCENT); self.idle_label.grid(row=0, column=2, pady=(16,3))
        for i, title in enumerate(('Geçen süre', 'Hareket', 'Boşta süre')): self.label(stats, title, 11, MUTED).grid(row=1, column=i, pady=(0,16))
        settings = ctk.CTkScrollableFrame(page, fg_color=PANEL, corner_radius=16, width=280)
        settings.grid(row=1, column=1, sticky='nsew'); settings.grid_columnconfigure(0, weight=1)
        self.label(settings, 'Hareket ayarları', 17, weight='bold').grid(row=0, column=0, sticky='w', padx=22, pady=(22,24))
        self.label(settings, 'Boşta kalma eşiği', 13).grid(row=1, column=0, sticky='w', padx=22)
        row = ctk.CTkFrame(settings, fg_color='transparent'); row.grid(row=2, column=0, sticky='w', padx=22, pady=(8,8))
        self.idle_entry = self.entry(row, 60, 100); self.idle_entry.pack(side='left')
        self.label(row, ' saniye', 12, MUTED).pack(side='left', padx=8)
        self.label(settings, 'Son girişinden sonra bu kadar bekler.', 11, MUTED).grid(row=3, column=0, sticky='w', padx=22)
        self.label(settings, 'Hareket aralığı', 13).grid(row=4, column=0, sticky='w', padx=22, pady=(24,0))
        row = ctk.CTkFrame(settings, fg_color='transparent'); row.grid(row=5, column=0, sticky='w', padx=22, pady=(8,8))
        self.interval_entry = self.entry(row, 30, 100); self.interval_entry.pack(side='left')
        self.label(row, ' saniye', 12, MUTED).pack(side='left', padx=8)
        self.label(settings, 'Hareketler arasındaki en kısa süre.', 11, MUTED).grid(row=6, column=0, sticky='w', padx=22)
        ctk.CTkFrame(settings, height=1, fg_color=LINE).grid(row=7, column=0, sticky='ew', padx=22, pady=24)
        self.f18_switch = self.switch(settings, 'F18 tuş etkinliği', self.f18)
        self.f18_switch.grid(row=8, column=0, sticky='w', padx=22)
        self.label(settings, 'İsteğe bağlıdır. Bazı uygulamalarda\nbir kısayolu tetikleyebilir.', 11, MUTED, justify='left').grid(row=9, column=0, sticky='w', padx=22, pady=(10,20))
        self.label(settings, 'Yazma sırasında otomatik bekler.\nTıklama yapmaz. ESC ile durur.', 12, ACCENT, justify='left').grid(row=10, column=0, sticky='w', padx=22, pady=(0,20))
        controls = ctk.CTkFrame(page, fg_color=PANEL, corner_radius=14)
        controls.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(16,0)); controls.grid_columnconfigure(0, weight=1)
        self.label(controls, 'Kontrol sende.', 15, weight='bold').grid(row=0, column=0, sticky='w', padx=20, pady=(18,4))
        self.label(controls, 'Yalnızca açıkken çalışır. Uygulamayı kapatınca durur.', 12, MUTED).grid(row=1, column=0, sticky='w', padx=20, pady=(0,18))
        self.jig_stop_btn = self.button(controls, 'Durdur', self.stop_jiggler, width=90, state='disabled')
        self.jig_stop_btn.grid(row=0, column=1, rowspan=2, padx=8)
        self.jig_start_btn = self.button(controls, 'Jiggler’ı başlat  ↗', self.start_jiggler, primary=True, width=178)
        self.jig_start_btn.grid(row=0, column=2, rowspan=2, padx=(0,20))

    def draw_cursor(self, event=None):
        canvas = self.canvas; canvas.delete('all')
        x = canvas.winfo_width()/2; y = canvas.winfo_height()/2
        for r, color in ((94,'#222E26'), (69,'#29382D'), (44,'#354C3A')):
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline='')
        canvas.create_oval(x-95,y-95,x+95,y+95,outline='#3A5140',dash=(3,8))
        canvas.create_line(x-122,y,x-106,y,fill=ACCENT,width=2)
        canvas.create_line(x+106,y,x+122,y,fill=ACCENT,width=2)
        canvas.create_polygon(x-18,y-31,x-18,y+29,x-3,y+15,x+10,y+39,x+22,y+33,x+8,y+10,x+30,y+9,
            fill=ACCENT, outline=INK, width=2)
        canvas.create_text(x+74,y-57,text='1 pt',fill=MUTED,font=(FONT,11))

    def show_page(self, value):
        self.page = value
        self.typer_page.grid_remove(); self.jiggler_page.grid_remove()
        (self.typer_page if value == 'Auto Typer' else self.jiggler_page).grid(row=0,column=0,sticky='nsew')

    def tell(self, text, error=False): self.status.configure(text=text, text_color=DANGER if error else MUTED)

    def check_permissions(self):
        allowed = self.backend.allowed()
        changed=allowed!=self.permission_ready
        self.permission_ready=allowed;self.permission_checked=time.monotonic()
        if allowed: self.permission_bar.grid_remove()
        else:
            self.permission_bar.grid()
            self.permission_text.configure(text='İzin bu işlemde etkin değil. İzin verdiysen yeniden başlat; metnin korunur.')
        if changed and allowed:self.tell('Giriş izni hazır. Başlayabilirsin.')
        if changed and not allowed:self.emergency_stop()
        return allowed

    def permission_action(self):
        if self.check_permissions():return
        open_permissions()
        self.tell(f'Çalışan uygulama: {sys.executable}',True)

    def show_introduction(self):
        if self.closing or self.intro:return
        if self.typing_active.is_set() or (self.jiggler_thread and self.jiggler_thread.is_alive()):
            self.tell('Tanıtımı açmadan önce etkinlikleri durdur.');return
        self.intro=Introduction(self)

    def restart(self):
        if self.closing:return
        token=secrets.token_urlsafe(32)
        state={'_resume_token':token,'text':self.text_input.get('1.0','end-1c'),'speed':self.speed.get(),'newline':self.newline.get(),
               'natural':self.natural.get(),'word_pauses':self.word_pauses.get(),'sound':self.sound.get(),
               'start_delay':self.start_delay.get(),'min_delay':self.min_delay.get(),'max_delay':self.max_delay.get(),
               'idle':self.idle_entry.get(),'interval':self.interval_entry.get(),'f18':self.f18.get()}
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',prefix='autotyper-resume-',suffix='.json',delete=False) as f:
                json.dump(state,f,ensure_ascii=False);path=f.name
        except OSError as exc:self.tell(f'Yeniden başlatma durumu kaydedilemedi: {exc}',True);return
        self.restart_command=[sys.executable]+([] if getattr(sys,'frozen',False) else [str(Path(__file__).resolve())])+['--resume-state',path,'--resume-token',token,'--skip-intro']
        self.close()

    def restore_state(self,path,token=None):
        path=Path(path)
        owned=False
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data,dict):raise ValueError('Invalid resume state')
            owned=bool(token and data.get('_resume_token')==token and path.name.startswith('autotyper-resume-') and path.suffix=='.json'
                       and not path.is_symlink() and path.parent.resolve()==Path(tempfile.gettempdir()).resolve())
            self.text_input.insert('1.0',data.get('text',''))
            for name in ('speed','newline','natural','word_pauses','sound','f18'):
                if name in data:getattr(self,name).set(data[name])
            for name,key in [('start_delay','start_delay'),('min_delay','min_delay'),('max_delay','max_delay'),('idle_entry','idle'),('interval_entry','interval')]:
                if key in data:entry=getattr(self,name);entry.delete(0,'end');entry.insert(0,str(data[key]))
            self.settings_changed()
        except (OSError,ValueError,TypeError,AttributeError):self.tell('Önceki oturum geri yüklenemedi.',True)
        finally:
            if owned:path.unlink(missing_ok=True)

    def ensure_permission(self):
        if not self.check_permissions():
            self.tell('Erişilebilirlik izni gerekiyor. İzin ayarlarını açıp uygulamayı etkinleştir.', True); return False
        if not self.listener_started or not self.backend.escape_healthy():
            self.listener_started = False
            try: self.backend.listen_escape(self.emergency_stop); self.listener_started = True
            except Exception as exc:
                self.tell(f'Global ESC dinleyicisi başlatılamadı: {exc}', True); return False
        return True

    def settings_changed(self, value=None):
        random_mode = self.speed.get() == 'Rastgele'
        if random_mode: self.random_frame.grid()
        else: self.random_frame.grid_remove()
        self.speed_hint.configure(text='Her karakterde farklı bekleme' if random_mode else f'{SPEEDS[self.speed.get()]} ms / karakter')
        self.update_stats()

    def config(self):
        try:
            return TypingConfig(delay_ms=SPEEDS[self.speed.get()], start_delay=float(self.start_delay.get()),
                min_ms=int(self.min_delay.get()), max_ms=int(self.max_delay.get()), natural=self.natural.get(),
                word_pauses=self.word_pauses.get(), newline=NEWLINES[self.newline.get()]).validate()
        except (ValueError, KeyError) as exc:
            if 'aralığında' in str(exc): raise
            raise ValueError('Bekleme alanlarına geçerli sayılar girin.') from exc

    def on_modified(self, event=None):
        if self.text_input.edit_modified():
            self.text_input.edit_modified(False); self.update_stats()

    def update_stats(self):
        text = self.text_input.get('1.0', 'end-1c')
        self.char_label.configure(text=f'{len(text):,} karakter'); self.word_label.configure(text=f'{len(text.split()):,} kelime')
        if text: self.empty_hint.place_forget()
        else: self.empty_hint.place(x=24,y=26)
        if not self.typing_active.is_set():
            try:
                config = self.config(); self.estimate_label.configure(text=f'≈ {duration(config.estimate(text))}')
                self.progress_label.configure(text=f'Hedef uygulamaya geçmek için {config.start_delay:g} saniyen olacak.')
            except ValueError: self.estimate_label.configure(text='Ayarları kontrol et')

    def copy_text(self):
        text = self.text_input.get('1.0', 'end-1c')
        if not text: self.tell('Kopyalanacak metin yok.'); return
        self.root.clipboard_clear(); self.root.clipboard_append(text); self.tell('Metin panoya kopyalandı.')

    def paste_text(self):
        if self.typing_active.is_set(): return
        try: text = self.root.clipboard_get()
        except tk.TclError: self.tell('Panoda metin bulunamadı.', True); return
        self.text_input.delete('1.0','end'); self.text_input.insert('1.0',text); self.update_stats(); self.tell('Metin panodan eklendi.')

    def clear_text(self):
        if self.typing_active.is_set(): return
        self.text_input.delete('1.0','end'); self.update_stats(); self.progress.set(0); self.tell('Metin alanı temizlendi.')

    def sound_event(self, name):
        if self.sound.get(): play_sound(name)

    def start_typing(self):
        if self.typing_thread and self.typing_thread.is_alive(): return
        text = self.text_input.get('1.0','end-1c')
        if not text: self.tell('Başlamadan önce metin ekle.', True); self.text_input.focus_set(); return
        try: config = self.config()
        except ValueError as exc: self.tell(str(exc),True); return
        if not self.ensure_permission(): return
        self.active_text = text; self.active_config = config; self.total = len(text); self.typed = 0
        self.typing_events = queue.Queue(); self.typing_stop.clear(); self.typing_active.set()
        self.text_input.configure(state='disabled')
        for widget in self.mutable_typing: widget.configure(state='disabled')
        self.start_btn.configure(state='disabled'); self.stop_btn.configure(state='normal')
        self.progress.set(0); self.tell('Hedef uygulamaya geç. ESC ile istediğin an durdurabilirsin.')
        self.typing_thread = threading.Thread(target=type_text,args=(text,config,self.backend,self.typing_stop,self.typing_events),daemon=True)
        self.typing_thread.start()

    def stop_typing(self):
        if self.typing_active.is_set():
            self.typing_stop.set(); self.stop_btn.configure(state='disabled'); self.run_label.configure(text='Durduruluyor…')

    def emergency_stop(self):
        # May run on the native listener thread. Only touch synchronization primitives.
        self.typing_stop.set(); self.jiggler_stop.set()

    def finish_typing(self, kind, detail):
        self.typing_active.clear()
        self.text_input.configure(state='normal')
        for widget in self.mutable_typing: widget.configure(state='normal')
        self.start_btn.configure(state='normal'); self.stop_btn.configure(state='disabled')
        labels = {'finished':'Yazma tamamlandı.', 'stopped':'Yazma durduruldu.', 'error':'Yazma başarısız.'}
        self.run_label.configure(text=labels[kind])
        self.tell(detail if kind == 'error' else labels[kind], kind == 'error')
        self.sound_event('finish' if kind == 'finished' else 'stop')
        if kind == 'finished': self.progress.set(1)
        self.progress_label.configure(text=f'{self.typed} / {self.total} karakter  ·  %{round(self.typed/max(1,self.total)*100)}')

    def start_jiggler(self):
        if self.jiggler_thread and self.jiggler_thread.is_alive(): return
        if sys.platform not in ('darwin','win32'): self.tell('Mouse Jiggler macOS ve Windows gerektirir.',True); return
        try: config = JigglerConfig(float(self.idle_entry.get()),float(self.interval_entry.get()),self.f18.get()).validate()
        except ValueError as exc: self.tell(str(exc) if 'aralığında' in str(exc) else 'Süre alanlarına geçerli sayılar girin.',True); return
        if not self.ensure_permission(): return
        self.jiggler_events = queue.Queue(); self.jiggler_stop.clear(); self.jiggler_started = time.monotonic(); self.movement_count = 0
        self.moves_label.configure(text='0'); self.jig_start_btn.configure(state='disabled'); self.jig_stop_btn.configure(state='normal')
        for widget in (self.idle_entry,self.interval_entry,self.f18_switch): widget.configure(state='disabled')
        self.jig_state.configure(text='Jiggler etkin.'); self.tell('Mouse Jiggler başladı. Yalnızca boşta kaldığında hareket eder.')
        self.jiggler_thread = threading.Thread(target=jiggle,args=(config,self.backend,self.jiggler_stop,self.typing_active.is_set,self.jiggler_events),daemon=True)
        self.jiggler_thread.start()

    def stop_jiggler(self):
        if self.jiggler_thread and self.jiggler_thread.is_alive():
            self.jiggler_stop.set(); self.jig_stop_btn.configure(state='disabled'); self.jig_state.configure(text='Durduruluyor…')

    def poll(self):
        if self.closing: return
        if time.monotonic()-self.permission_checked>=2:self.check_permissions()
        listener_failed = self.listener_started and not self.backend.escape_healthy()
        if listener_failed:
            self.listener_started = False
            self.emergency_stop()
        # Bound each drain so very fast typing cannot starve the UI event loop.
        for _ in range(500):
            try: kind, value = self.typing_events.get_nowait()
            except queue.Empty: break
            if kind == 'countdown': self.run_label.configure(text=f'{value:.1f} saniye sonra başlıyor…')
            elif kind == 'typing': self.run_label.configure(text='Yazılıyor…'); self.sound_event('start')
            elif kind == 'progress':
                self.typed = value; self.progress.set(value/max(1,self.total))
                remaining = self.active_config.estimate(self.active_text[value:],include_start=False)
                self.progress_label.configure(text=f'{value} / {self.total} karakter  ·  %{round(value/max(1,self.total)*100)}  ·  ≈ {duration(remaining)} kaldı')
            elif kind in ('finished','stopped','error'): self.finish_typing(kind,value)
        for _ in range(100):
            try: kind, value = self.jiggler_events.get_nowait()
            except queue.Empty: break
            if kind == 'movement': self.movement_count = value; self.moves_label.configure(text=str(value))
            elif kind == 'idle': self.idle_label.configure(text=duration(value))
            elif kind in ('jiggler_stopped','jiggler_error'):
                self.jig_state.configure(text='Jiggler durduruldu.' if kind == 'jiggler_stopped' else 'Jiggler başarısız.')
                self.jig_start_btn.configure(state='normal'); self.jig_stop_btn.configure(state='disabled')
                for widget in (self.idle_entry,self.interval_entry,self.f18_switch): widget.configure(state='normal')
                self.tell(value if kind == 'jiggler_error' else 'Mouse Jiggler durduruldu.', kind == 'jiggler_error')
        jig_active = bool(self.jiggler_thread and self.jiggler_thread.is_alive())
        typing = self.typing_active.is_set()
        self.activity_badge.configure(text='●  Yazılıyor · Jiggler bekliyor' if typing and jig_active else '●  Yazılıyor' if typing else '●  Jiggler etkin' if jig_active else '●  Hazır')
        if jig_active:
            self.elapsed_label.configure(text=duration(time.monotonic()-self.jiggler_started))
            self.jig_description.configure(text='Yazma bitene kadar bekliyor.' if typing else 'Boşta kalma süreni izliyor. ESC ile durdurabilirsin.')
        else: self.jig_description.configure(text='Başlatana kadar fare hareketi yapılmaz.')
        if listener_failed:
            self.tell('Global ESC bağlantısı kesildi; etkinlikler durduruldu. İzni kontrol edip yeniden başlat.', True)
        self.root.after(100,self.poll)

    def close(self):
        if self.closing: return
        self.closing = True; self.emergency_stop(); self.backend.close()
        self.root.withdraw(); self.await_shutdown()

    def await_shutdown(self):
        if any(t and t.is_alive() for t in (self.typing_thread,self.jiggler_thread, self.backend.listener if hasattr(self.backend, 'listener') else None)):
            self.root.after(30,self.await_shutdown)
        else:
            if self.restart_command:
                try:subprocess.Popen(self.restart_command)
                except OSError as exc:
                    self.closing=False;self.restart_command=None;self.listener_started=False
                    self.root.deiconify();self.tell(f'Yeniden başlatılamadı; metnin korunuyor: {exc}',True)
                    self.root.after(100,self.poll);return
            self.root.destroy()

    def run(self): self.root.mainloop()


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--skip-intro',action='store_true');parser.add_argument('--resume-state')
    parser.add_argument('--diagnostics',action='store_true')
    parser.add_argument('--resume-token')
    parser.add_argument('--smoke-test',action='store_true')
    args=parser.parse_args()
    if args.diagnostics:
        backend=create_backend()
        print(json.dumps({'version':VERSION,'platform':sys.platform,'executable':sys.executable,'permission':backend.allowed(),
                          'ax_trusted':bool(backend.trusted()) if hasattr(backend,'trusted') else None,
                          'post_allowed':bool(backend.post_allowed()) if hasattr(backend,'post_allowed') else None}))
        backend.close()
    else:
        app=AutoTyper(show_intro=not(args.skip_intro or args.smoke_test))
        if args.resume_state:app.restore_state(args.resume_state,args.resume_token)
        if args.smoke_test:app.root.after(1200,app.close)
        app.run()
