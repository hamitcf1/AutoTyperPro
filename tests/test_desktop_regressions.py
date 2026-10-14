"""Headless lifecycle regressions: no windows, native input or desktop UI."""
import queue
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from auto_typer import AutoTyper
import auto_typer
from desktop_integration import DesktopIntegration
from desktop_windows import WindowsDesktop
from support_ui import report_bug

class HeadlessDesktopRegressions(unittest.TestCase):
    def test_label_default_resolves_current_palette(self):
        previous=auto_typer.INK
        try:
            auto_typer.INK='#101010'
            with patch.object(auto_typer.ctk,'CTkLabel') as label:
                AutoTyper.label(None,None,'Example')
                self.assertEqual(label.call_args.kwargs['text_color'],'#101010')
        finally:auto_typer.INK=previous
    def test_queued_notification_grant_cannot_override_disabled_choice(self):
        events=queue.Queue();pending=[]
        driver=SimpleNamespace(ready=True,start=lambda:True,request_notifications=pending.append,stop=lambda:None)
        desktop=DesktopIntegration(events,None,driver);desktop.start();desktop.notifications_enabled=True
        desktop.request_notifications();pending.pop()(True);command=events.get_nowait()
        desktop.notifications_enabled=False
        self.assertFalse(desktop.accept_notification_permission(command))
    def test_report_draft_window_survives_preference_rebuild(self):
        report=Mock();normal=Mock()
        app=SimpleNamespace(typing_active=threading.Event(),jiggler_thread=None,macro_active=threading.Event(),intro=None,report_window=report,snapshot=lambda:{},preferences=Mock(),root=Mock(),setup_gui=Mock(),apply_state=Mock(),nav=Mock(),show_page=Mock(),check_permissions=Mock(),responsive_layout=Mock(),tell=Mock())
        app.preferences.load.return_value={'locale':'en','appearance':'dark'}
        app.root.winfo_children.return_value=[normal,report]
        AutoTyper.change_preferences(app,appearance='dark')
        normal.destroy.assert_called_once();report.destroy.assert_not_called()
    def test_reopening_bug_report_reuses_edited_window(self):
        window=Mock();window.winfo_exists.return_value=True
        app=SimpleNamespace(report_window=window)
        with patch('support_ui.ctk.CTkToplevel') as create:
            self.assertIs(report_bug(app),window);create.assert_not_called()
    def test_windows_stop_before_async_setup_still_stops_native_loop(self):
        class Icon:
            visible=False;running=False;effective_stops=0
            def run_detached(self,setup):self.setup=setup
            def stop(self):
                if self.running:self.effective_stops+=1;self.running=False
        driver=WindowsDesktop.__new__(WindowsDesktop);driver.icon=Icon();driver.ready=False;driver.closed=threading.Event();driver.lock=threading.RLock()
        driver.start();driver.stop();driver.icon.running=True;driver.icon.setup(driver.icon)
        self.assertEqual(driver.icon.effective_stops,1);self.assertFalse(driver.icon.visible);self.assertFalse(driver.ready)
