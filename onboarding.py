from localization import tr
"""First-run introduction, separate from the main activity interface."""
import sys
import customtkinter as ctk
from PIL import Image
from preferences import resource, VERSION

class Introduction(ctk.CTkFrame):

    def __init__(self, app):
        import sys
        style=sys.modules[app.__class__.__module__]
        super().__init__(app.root, fg_color=style.BG, corner_radius=0)
        self.app = app
        self.step = 0
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.pack(fill='x', padx=36, pady=28)
        app.label(top, f'AutoTyper Pro  /  {VERSION}', 13, style.MUTED).pack(side='left')
        app.button(top, tr('ui.af42e27ab88c'), self.finish, width=116).pack(side='right')
        self.panel = ctk.CTkFrame(self, fg_color=style.PANEL, corner_radius=24, width=820, height=540)
        self.panel.place(relx=0.5, rely=0.5 if app.preferences.load()['reduced_motion'] else 0.51, anchor='center')
        self.panel.pack_propagate(False)
        image = Image.open(resource('assets/icon.png'))
        self.logo = ctk.CTkImage(image, image, size=(104, 104))
        ctk.CTkLabel(self.panel, text='', image=self.logo).pack(pady=(30, 14))
        self.eyebrow = app.label(self.panel, '', 12, style.ACCENT, 'bold')
        self.eyebrow.pack()
        self.title = app.label(self.panel, '', 34, weight='bold', justify='center')
        self.title.pack(pady=(14, 12))
        self.description = app.label(self.panel, '', 15, style.MUTED, justify='center', wraplength=680)
        self.description.pack(pady=(0, 16))
        self.detail = ctk.CTkFrame(self.panel, fg_color=style.INSET, corner_radius=12, width=660, height=90)
        self.detail.pack(fill='x', padx=54, pady=(0, 12))
        self.detail.pack_propagate(False)
        self.detail_text = app.label(self.detail, '', 13, style.ACCENT, justify='center', wraplength=620)
        self.detail_text.pack(expand=True)
        self.actions = ctk.CTkFrame(self.panel, fg_color='transparent')
        self.actions.pack(fill='x', padx=54, pady=(12, 24))
        self.back = app.button(self.actions, tr('ui.4928cfc92f64'), self.previous, width=96)
        self.back.pack(side='left')
        self.dots = app.label(self.actions, '', 13, style.MUTED)
        self.dots.pack(side='left', padx=24)
        self.next = app.button(self.actions, tr('ui.fb1103e69888'), self.advance, primary=True, width=168)
        self.next.pack(side='right')
        self.permission = app.button(self.actions, tr('ui.89abb54abe71'), app.permission_action, width=144)
        self.render()

    def render(self):
        steps = [(tr('ui.e1a345f10b2b'), tr('ui.1cff31c8bcd6'), tr('ui.e5f87cf79caa'), tr('ui.21efba887838')), ('02  /  MOUSE JIGGLER', tr('ui.5b87196fc8fd'), tr('ui.b8484c8f9490'), tr('ui.6dbddd0b7c39')), (tr('ui.04b0915c8230'), tr('ui.e5d20bc15f12'), tr('ui.dd2e64bfd76d'), '')]
        eyebrow, title, description, detail = steps[self.step]
        self.eyebrow.configure(text=eyebrow)
        self.title.configure(text=title)
        self.description.configure(text=description)
        self.dots.configure(text='  '.join(('●' if i == self.step else '○' for i in range(3))))
        self.back.configure(state='disabled' if self.step == 0 else 'normal')
        self.next.configure(text=tr('ui.2cf5cafba4a0') if self.step == 2 else tr('ui.fb1103e69888'))
        self.permission.pack_forget()
        if self.step == 2 and sys.platform == 'darwin':
            ready = self.app.backend.allowed()
            detail = tr('ui.b470c634c05a') if ready else tr('ui.6527b03b7014')
            if not ready:
                self.permission.pack(side='right', padx=(0, 10))
        elif self.step == 2:
            detail = tr('ui.690bc12babeb')
        self.detail_text.configure(text=detail)
        from motion import introduce
        introduce(self.app.root,self.panel,self.app.preferences.load()['reduced_motion'])

    def advance(self):
        if self.step == 2:
            self.finish()
        else:
            self.step += 1
            self.render()

    def previous(self):
        self.step = max(0, self.step - 1)
        self.render()

    def finish(self):
        try:
            self.app.preferences.complete_intro()
        except OSError:
            self.app.tell(tr('ui.3bb93f60f7bd'), True)
        self.destroy()
        self.app.intro = None
        self.app.check_permissions()
