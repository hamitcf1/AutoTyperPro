from pathlib import Path
import unittest
from unittest.mock import Mock

class StatusIconTests(unittest.TestCase):
    def test_mac_status_icon_uses_brand_template_with_native_size(self):
        from desktop_macos import MacDesktop
        desktop=MacDesktop.__new__(MacDesktop)
        desktop.icon_path=Path('/app/assets/icon.png')
        desktop.appkit=Mock()
        icon=Mock()
        desktop.appkit.NSImage.alloc.return_value.initWithContentsOfFile_.return_value=icon
        self.assertIs(desktop._status_image(),icon)
        desktop.appkit.NSImage.alloc.return_value.initWithContentsOfFile_.assert_called_once_with('/app/assets/menubar-template.png')
        icon.setSize_.assert_called_once_with((18,18))
        icon.setTemplate_.assert_called_once_with(True)

    def test_template_is_transparent_and_packaged_for_mac(self):
        from PIL import Image
        root=Path(__file__).resolve().parents[1]
        with Image.open(root/'assets/menubar-template.png') as image:
            alpha=image.getchannel('A')
            self.assertEqual(alpha.getpixel((0,0)),0)
            self.assertLess(sum(bool(value) for value in alpha.getdata()),image.width*image.height/2)
        from unittest.mock import patch
        import sys
        analysis=Mock()
        scope={'SPECPATH':str(root),'Analysis':analysis,'PYZ':Mock(),'EXE':Mock(),'COLLECT':Mock(),'BUNDLE':Mock()}
        original=list(sys.path)
        try:
            with patch('sys.platform','darwin'),patch('PyInstaller.utils.hooks.collect_data_files',return_value=[]):
                exec(compile((root/'AutoTyperPro.spec').read_text(),'AutoTyperPro.spec','exec'),scope)
        finally:sys.path[:]=original
        self.assertIn((str(root/'assets/menubar-template.png'),'assets'),analysis.call_args.kwargs['datas'])

    def test_missing_brand_asset_keeps_a_visible_system_fallback(self):
        from desktop_macos import MacDesktop
        desktop=MacDesktop.__new__(MacDesktop);desktop.icon_path=Path('/app/assets/icon.png');desktop.appkit=Mock()
        desktop.appkit.NSImage.alloc.return_value.initWithContentsOfFile_.return_value=None
        icon=desktop.appkit.NSImage.imageWithSystemSymbolName_accessibilityDescription_.return_value
        self.assertIs(desktop._status_image(),icon)
        icon.setTemplate_.assert_called_once_with(True)
