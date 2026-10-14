"""Ownership, translation credits and user-reviewed support reports."""
import customtkinter as ctk
import webbrowser
from app_info import CREATOR,ORGANIZATION,CREATOR_URL,ORGANIZATION_URL,REPOSITORY,technical_summary,bug_report_url
from localization import tr,translation_report
from preferences import VERSION

def open_link(app,url):
    try:
        if not webbrowser.open(url):app.tell(tr('support.browser_error'),True)
    except Exception:app.tell(tr('support.browser_error'),True)

def copy_text(app,text):
    app.root.clipboard_clear();app.root.clipboard_append(text);app.tell(tr('support.copied'))

def report_bug(app):
    window=ctk.CTkToplevel(app.root);window.title(tr('support.report'));window.geometry('600x430');window.minsize(520,400)
    window.configure(fg_color=app.root.cget('fg_color'));window.grid_columnconfigure(0,weight=1);window.grid_rowconfigure(2,weight=1)
    app.label(window,tr('support.report'),24,weight='bold').grid(row=0,column=0,sticky='w',padx=24,pady=(24,10))
    app.label(window,tr('support.privacy'),13,wraplength=530).grid(row=1,column=0,sticky='ew',padx=24,pady=8)
    preview=ctk.CTkTextbox(window,fg_color=app.text_input.cget('fg_color'),corner_radius=14);preview.grid(row=2,column=0,sticky='nsew',padx=24,pady=12);preview.insert('1.0',technical_summary())
    controls=ctk.CTkFrame(window,fg_color='transparent');controls.grid(row=3,column=0,sticky='ew',padx=24,pady=(0,24))
    app.button(controls,tr('support.copy'),lambda:copy_text(app,preview.get('1.0','end-1c'))).pack(side='left')
    app.button(controls,tr('support.open_report'),lambda:open_link(app,bug_report_url(preview.get('1.0','end-1c'))),primary=True).pack(side='right')
    window.after(100,window.lift)
    return window

def show_support(app):
    existing=getattr(app,'support_window',None)
    if existing is not None and existing.winfo_exists():existing.lift();return existing
    window=ctk.CTkToplevel(app.root);app.support_window=window;window.title('AutoTyper Pro · '+tr('support.about'));window.geometry('620x680');window.minsize(550,500);window.configure(fg_color=app.root.cget('fg_color'))
    panel=ctk.CTkScrollableFrame(window,fg_color='transparent');panel.pack(fill='both',expand=True,padx=24,pady=24)
    app.label(panel,'AutoTyper Pro',28,weight='bold').pack(anchor='w')
    app.label(panel,tr('support.version',version=VERSION),13).pack(anchor='w',pady=(4,20))
    app.label(panel,f'{CREATOR} · {ORGANIZATION}',17,weight='bold').pack(anchor='w',pady=(0,8))
    app.label(panel,tr('support.description'),14,wraplength=510).pack(anchor='w',pady=(0,20))
    links=[('support.creator',CREATOR_URL),('support.organization',ORGANIZATION_URL),('support.project',REPOSITORY),('support.releases',REPOSITORY+'/releases/latest'),('support.translate',REPOSITORY+'/blob/main/docs/TRANSLATING.md')]
    for key,url in links:app.button(panel,tr(key)+' ↗',lambda url=url:open_link(app,url)).pack(fill='x',pady=4)
    app.button(panel,tr('support.report'),lambda:report_bug(app),primary=True).pack(fill='x',pady=(16,6))
    app.button(panel,tr('support.copy'),lambda:copy_text(app,technical_summary())).pack(fill='x',pady=4)
    app.label(panel,tr('support.credits'),16,weight='bold').pack(anchor='w',pady=(22,8))
    for entry in translation_report()['locales'].values():
        app.label(panel,entry['native_name']+' · '+(', '.join(entry['contributors']) or tr('support.community')),13,wraplength=500).pack(anchor='w',pady=3)
    window.after(100,window.lift)
    return window
