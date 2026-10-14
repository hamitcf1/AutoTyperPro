import json
from pathlib import Path
import tempfile
import unittest
from localization import Translator

class RegistryTests(unittest.TestCase):
    def fixture(self, directory):
        root=Path(directory)
        (root/'manifest.json').write_text(json.dumps({'default':'en','locales':[{'code':'en','native_name':'English','contributors':[]},{'code':'es','native_name':'Español','contributors':['Translator']}]}))
        (root/'en.json').write_text(json.dumps({'hello':'Hello {name}','missing':'Fallback'}))
        (root/'es.json').write_text(json.dumps({'hello':'Hola {name}'}))
        return root
    def test_partial_third_locale_is_discovered_and_falls_back(self):
        from localization import locale_options,translation_report
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory)
            self.assertIn(('es','Español'),locale_options(root))
            self.assertEqual(Translator('es',root=root).text('hello',name='Ada'),'Hola Ada')
            self.assertEqual(Translator('es',root=root).text('missing'),'Fallback')
            self.assertEqual(translation_report(root)['locales']['es']['translated'],1)
    def test_placeholder_mismatch_falls_back_and_is_reported(self):
        from localization import translation_report
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory);(root/'es.json').write_text('{"hello":"Hola {wrong}"}')
            self.assertEqual(Translator('es',root=root).text('hello',name='Ada'),'Hello Ada')
            self.assertTrue(translation_report(root)['errors'])
    def test_duplicate_keys_and_path_traversal_are_rejected(self):
        from localization import locale_options,translation_report
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory);(root/'es.json').write_text('{"hello":"A","hello":"B"}')
            self.assertTrue(translation_report(root)['errors'])
            (root/'manifest.json').write_text('{"default":"en","locales":[{"code":"../secret","native_name":"Bad","contributors":[]}]}')
            self.assertEqual(locale_options(root),[('en','English')])
            self.assertTrue(translation_report(root)['errors'])
    def test_invalid_manifest_does_not_break_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory);(root/'manifest.json').write_text('broken')
            self.assertEqual(Translator('es',root=root).text('hello',name='Ada'),'Hello Ada')
    def test_symlinked_catalog_does_not_read_outside_locale_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);root=base/'locales';root.mkdir();self.fixture(root)
            private=base/'private.json';private.write_text('{"hello":"Private {name}"}')
            (root/'es.json').unlink();(root/'es.json').symlink_to(private)
            self.assertEqual(Translator('es',root=root).text('hello',name='Ada'),'Hello Ada')
    def test_incompatible_format_specifier_uses_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory);(root/'es.json').write_text('{"hello":"Hola {name:d}"}')
            self.assertEqual(Translator('es',root=root).text('hello',name='Ada'),'Hello Ada')
