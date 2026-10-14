import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from motion import introduce
class MotionTests(unittest.TestCase):
    def test_reduced_motion_is_immediate_and_schedules_nothing(self):
        root=Mock();panel=Mock();panel._motion_generation=0
        introduce(root,panel,True)
        root.after.assert_not_called();panel.place_configure.assert_called_once_with(rely=.5)
    def test_old_transition_callbacks_do_not_move_new_transition(self):
        callbacks=[];root=SimpleNamespace(after=lambda delay,callback:callbacks.append(callback))
        panel=Mock();panel._motion_generation=0;panel.winfo_exists.return_value=True
        introduce(root,panel);previous=list(callbacks);callbacks.clear();introduce(root,panel)
        for callback in previous:callback()
        panel.place_configure.assert_not_called()
        for callback in callbacks:callback()
        self.assertEqual(panel.place_configure.call_args.kwargs['rely'],.5)
        self.assertEqual(len(callbacks),9)
