import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
import customtkinter as ctk
from customtkinter.windows.widgets.core_widget_classes.dropdown_menu import DropdownMenu
from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

class WidgetLifecycleTests(unittest.TestCase):
    def test_destroyed_dropdown_is_removed_from_future_scaling_callbacks(self):
        from widget_lifecycle import destroy_tree
        # No Tk constructor or window: model the native popup omitted from
        # winfo_children, but still present in Tk's Python children registry.
        root=ctk.CTk.__new__(ctk.CTk)
        menu=DropdownMenu.__new__(DropdownMenu);menu.master=root;menu.children={};menu.destroy=Mock()
        menu._CTkScalingBaseClass__scaling_type='widget'
        parent=SimpleNamespace(children={'popup':menu},destroy=Mock())
        with patch.object(ScalingTracker,'window_widgets_dict',{root:[menu._set_scaling]}):
            destroy_tree(parent)
            self.assertEqual(ScalingTracker.window_widgets_dict[root],[])
        menu.destroy.assert_called_once();parent.destroy.assert_called_once()
