"""Compact preference groups and visible product ownership."""
import sys
import customtkinter as ctk
from localization import tr,locale_options
from support_ui import show_support,report_bug,open_link
from app_info import CREATOR,ORGANIZATION,REPOSITORY

def build_settings(app,page):
    style=sys.modules[app.__class__.__module__]
    app.page_title(page,'04 / PREFERENCES',tr('settings.title'),tr('settings.description'))
    page.grid_columnconfigure(0,weight=1);page.grid_rowconfigure(1,weight=1)
    content=ctk.CTkScrollableFrame(page,fg_color='transparent');content.grid(row=1,column=0,sticky='nsew')
    content.grid_columnconfigure((0,1),weight=1,uniform='preferences')
    def card(title,column):
        panel=ctk.CTkFrame(content,fg_color=style.PANEL,corner_radius=22,border_width=1,border_color=style.LINE)
        panel.grid(row=0,column=column,sticky='nsew',padx=(0,10) if column==0 else (10,0),pady=(0,20));panel.grid_columnconfigure(0,weight=1)
        app.label(panel,title,18,weight='bold').grid(row=0,column=0,columnspan=2,sticky='w',padx=24,pady=(24,20))
        return panel
    general=card(tr('desktop.general'),0);desktop=card(tr('desktop.utility'),1)
    options=locale_options()
    app.label(general,tr('settings.language'),14).grid(row=1,column=0,sticky='w',padx=24,pady=12)
    app.language_menu=ctk.CTkOptionMenu(general,values=[label for code,label in options],command=lambda value:app.change_preferences(locale=next(code for code,label in options if label==value)),fg_color=style.LINE,button_color=style.LINE,text_color=style.INK,width=140,corner_radius=12)
    app.language_menu.set(dict(options).get(app.preferences.load()['locale'],'English'));app.language_menu.grid(row=1,column=1,padx=(0,24),pady=12)
    app.label(general,tr('settings.appearance'),14).grid(row=2,column=0,sticky='w',padx=24,pady=12)
    appearances=['dark','light','system']
    app.appearance_menu=ctk.CTkOptionMenu(general,values=[tr('settings.'+value) for value in appearances],command=lambda value:app.change_preferences(appearance=next(key for key in appearances if tr('settings.'+key)==value)),fg_color=style.LINE,button_color=style.LINE,text_color=style.INK,width=140,corner_radius=12)
    app.appearance_menu.set(tr('settings.'+app.preferences.load()['appearance']));app.appearance_menu.grid(row=2,column=1,padx=(0,24),pady=12)
    app.switch(general,tr('settings.sound'),app.sound,lambda:app.preferences.update({'sound':app.sound.get()})).grid(row=3,column=0,columnspan=2,sticky='w',padx=24,pady=20)
    values=app.preferences.load();app.notifications=ctk.BooleanVar(value=values['notifications']);app.keep_running=ctk.BooleanVar(value=values['keep_running']);app.reduced_motion=ctk.BooleanVar(value=values['reduced_motion'])
    app.switch(general,tr('desktop.reduced_motion'),app.reduced_motion,lambda:app.preferences.update({'reduced_motion':app.reduced_motion.get()})).grid(row=4,column=0,columnspan=2,sticky='w',padx=24,pady=(0,24))
    app.switch(desktop,tr('desktop.notifications'),app.notifications,app.notification_preference).grid(row=1,column=0,sticky='w',padx=24,pady=16)
    app.switch(desktop,tr('desktop.keep_running'),app.keep_running,lambda:app.preferences.update({'keep_running':app.keep_running.get()})).grid(row=2,column=0,sticky='w',padx=24,pady=16)
    app.label(desktop,tr('desktop.background_hint'),12,style.MUTED,wraplength=340,justify='left').grid(row=3,column=0,sticky='w',padx=24,pady=16)
    app.button(desktop,tr('desktop.permissions')+' ↗',app.permission_action,width=180).grid(row=4,column=0,sticky='w',padx=24,pady=(0,24))
    audio=ctk.CTkFrame(content,fg_color=style.PANEL,corner_radius=22,border_width=1,border_color=style.LINE)
    audio.grid(row=1,column=0,columnspan=2,sticky='ew',pady=(0,20));audio.grid_columnconfigure(1,weight=1)
    app.label(audio,tr('settings.audio'),18,weight='bold').grid(row=0,column=0,columnspan=3,sticky='w',padx=24,pady=(22,14))
    app.label(audio,tr('settings.sound_theme'),13).grid(row=1,column=0,sticky='w',padx=24,pady=12)
    themes=('classic','soft','glass')
    sound_menu=ctk.CTkOptionMenu(audio,values=[tr('sound.'+theme) for theme in themes],command=lambda value:app.save_custom_setting(sound_theme=next(theme for theme in themes if tr('sound.'+theme)==value)),fg_color=style.LINE,button_color=style.LINE,text_color=style.INK)
    sound_menu.set(tr('sound.'+values['sound_theme']));sound_menu.grid(row=1,column=1,sticky='w',pady=12)
    app.button(audio,tr('settings.preview_sound'),lambda:app.sound_event('finish'),width=110).grid(row=1,column=2,padx=24,pady=12)
    app.label(audio,tr('settings.sound_volume'),13).grid(row=2,column=0,sticky='w',padx=24,pady=12)
    level=app.label(audio,str(values['sound_volume'])+'%',13)
    level.grid(row=2,column=2,padx=24,pady=12)
    def volume_changed(value):
        volume=round(value);level.configure(text=str(volume)+'%');app.save_custom_setting(sound_volume=volume)
    slider=ctk.CTkSlider(audio,from_=0,to=100,number_of_steps=100,command=volume_changed,progress_color=style.ACCENT,button_color=style.ACCENT)
    slider.set(values['sound_volume']);slider.grid(row=2,column=1,sticky='ew',pady=12)
    app.label(audio,tr('settings.scale'),13).grid(row=3,column=0,sticky='w',padx=24,pady=12)
    scales=(.8,.85,1,1.1,1.25);scale_menu=ctk.CTkOptionMenu(audio,values=[str(round(value*100))+'%' for value in scales],command=lambda value:app.change_preferences(ui_scale=int(value[:-1])/100),fg_color=style.LINE,button_color=style.LINE,text_color=style.INK)
    scale_menu.set(str(round(values['ui_scale']*100))+'%');scale_menu.grid(row=3,column=1,sticky='w',pady=12)
    app.label(audio,tr('settings.autosaved'),12,style.MUTED).grid(row=4,column=0,columnspan=2,sticky='w',padx=24,pady=(8,22))
    app.button(audio,tr('settings.save'),app.save_settings,primary=True,width=140).grid(row=4,column=2,padx=24,pady=(8,22))
    owner=ctk.CTkFrame(content,fg_color=style.PANEL,corner_radius=22,border_width=1,border_color=style.LINE);owner.grid(row=2,column=0,columnspan=2,sticky='ew');owner.grid_columnconfigure(0,weight=1)
    app.label(owner,ORGANIZATION,19,weight='bold').grid(row=0,column=0,sticky='w',padx=24,pady=(22,4))
    app.label(owner,CREATOR,13,style.MUTED).grid(row=1,column=0,sticky='w',padx=24,pady=(0,22))
    actions=ctk.CTkFrame(owner,fg_color='transparent');actions.grid(row=0,column=1,rowspan=2,padx=20,pady=16)
    app.button(actions,tr('support.about'),lambda:show_support(app),width=160).grid(row=0,column=0,padx=4,pady=4)
    app.button(actions,tr('support.report'),lambda:report_bug(app),width=150).grid(row=0,column=1,padx=4,pady=4)
    app.button(actions,tr('support.translate')+' ↗',lambda:open_link(app,REPOSITORY+'/blob/main/docs/TRANSLATING.md'),width=318).grid(row=1,column=0,columnspan=2,padx=4,pady=4,sticky='ew')
