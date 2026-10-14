import tempfile
from pathlib import Path
import unittest
import io,wave,struct
from preferences import Preferences

class CustomPreferencesTests(unittest.TestCase):
    def test_sound_and_scale_choices_persist_and_reject_invalid_values(self):
        with tempfile.TemporaryDirectory() as d:
            prefs=Preferences(Path(d)/'prefs.json')
            prefs.update({'sound_theme':'glass','sound_volume':35,'ui_scale':.85})
            values=Preferences(prefs.path).load()
            self.assertEqual((values['sound_theme'],values['sound_volume'],values['ui_scale']),('glass',35,.85))
            for data in ({'sound_volume':101},{'sound_volume':True},{'sound_theme':'../bad'},{'ui_scale':.1}):
                with self.assertRaises(ValueError):prefs.update(data)
    def test_volume_scales_pcm_without_changing_original(self):
        from notification_audio import attenuate
        stream=io.BytesIO()
        with wave.open(stream,'wb') as out:out.setparams((1,2,22050,0,'NONE','not compressed'));out.writeframes(struct.pack('<hhh',12000,-12000,0))
        original=stream.getvalue();result=attenuate(original,25)
        with wave.open(io.BytesIO(result),'rb') as actual:self.assertEqual(struct.unpack('<hhh',actual.readframes(3)),(3000,-3000,0))
        self.assertEqual(stream.getvalue(),original)
    def test_muted_volume_does_not_play_or_write_cache(self):
        from notification_audio import sound_path
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            self.assertIsNone(sound_path('finish','classic',0,root,root/'cache'))
            self.assertFalse((root/'cache').exists())
    def test_compact_window_fits_without_enlarging_requested_scale(self):
        from responsive import fit_scale
        self.assertAlmostEqual(fit_scale(800,600,1),min(800/980,600/740),places=2)
        self.assertEqual(fit_scale(1600,1200,.85),.85)
    def test_resize_ignores_child_widget_events_and_moves_navigation(self):
        from auto_typer import AutoTyper
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        root=Mock();root._get_window_scaling.return_value=1;root.winfo_width.return_value=800;root.winfo_height.return_value=600
        app=SimpleNamespace(closing=False,root=root,preferences=Mock(),nav=Mock(),typer_page=Mock(),jiggler_page=Mock())
        app.preferences.load.return_value={'ui_scale':1}
        with patch('auto_typer.ctk.set_widget_scaling') as scale:
            AutoTyper.responsive_layout(app,SimpleNamespace(widget=Mock()))
            scale.assert_not_called()
            AutoTyper.responsive_layout(app)
            self.assertEqual(app.nav.grid_configure.call_args.kwargs['row'],2)
            self.assertLess(scale.call_args.args[0],1)
    def test_sound_presets_are_bundled_pcm_and_each_event_exists(self):
        from notification_audio import THEMES,EVENTS,sound_path
        sounds=Path(__file__).resolve().parents[1]/'sounds'
        for theme in THEMES:
            for event in EVENTS:
                path=sound_path(event,theme,100,sounds,sounds/'unused-cache')
                self.assertIsNotNone(path)
                with wave.open(str(path),'rb') as audio:self.assertEqual(audio.getsampwidth(),2)
    def test_widget_scaling_does_not_lock_window_minimum_or_resize_window(self):
        from responsive import ResponsiveWindow
        from unittest.mock import Mock,patch
        import customtkinter as ctk
        window=ResponsiveWindow.__new__(ResponsiveWindow)
        window._get_window_scaling=lambda:1
        with patch.object(ctk.CTk,'_set_scaling') as window_resize:
            ResponsiveWindow._set_scaling(window,.8,1)
            window_resize.assert_not_called()
            ResponsiveWindow._set_scaling(window,.8,1.25)
            window_resize.assert_called_once_with(.8,1.25)
    def test_settings_controls_persist_sound_without_opening_windows(self):
        from auto_typer import AutoTyper
        from settings_ui import build_settings
        from unittest.mock import Mock,patch
        from contextlib import ExitStack
        with tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
            app=AutoTyper.__new__(AutoTyper);app.preferences=Preferences(Path(directory)/'prefs.json')
            app.page_title=Mock();app.label=Mock();app.button=Mock();app.switch=Mock();app.tell=Mock();app.sound=Mock();app.sound.get.return_value=True
            app.sound_event=Mock();app.change_preferences=Mock();app.notification_preference=Mock();app.permission_action=Mock()
            widgets={name:stack.enter_context(patch('settings_ui.ctk.'+name)) for name in ('CTkFrame','CTkScrollableFrame','CTkOptionMenu','CTkSlider','BooleanVar')}
            build_settings(app,Mock())
            widgets['CTkSlider'].call_args.kwargs['command'](35.4)
            self.assertEqual(app.preferences.load()['sound_volume'],35)
            sound_menu=next(call for call in widgets['CTkOptionMenu'].call_args_list if 'Glass' in call.kwargs['values'])
            sound_menu.kwargs['command']('Glass')
            self.assertEqual(app.preferences.load()['sound_theme'],'glass')
            AutoTyper.save_settings(app)
            self.assertTrue(app.preferences.load()['sound'])
