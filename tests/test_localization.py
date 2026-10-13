import json
from pathlib import Path
from string import Formatter
import unittest

class LocalizationTests(unittest.TestCase):
    def test_translation_fallback_and_catalog_contract(self):
        from localization import Translator
        english = Translator('en'); turkish = Translator('tr')
        self.assertEqual(english.text('settings.title'), 'Settings')
        self.assertEqual(turkish.text('settings.title'), 'Ayarlar')
        self.assertEqual(Translator('xx').text('settings.title'), 'Settings')
        self.assertIn('f18', english.text('activity.summary', idle=60, interval=30, distance=1, key='f18'))
        catalogs = [json.loads((Path(__file__).parents[1]/'locales'/f'{code}.json').read_text()) for code in ('en','tr')]
        self.assertEqual(set(catalogs[0]), set(catalogs[1]))
        for key, value in catalogs[0].items():
            fields = lambda s: {name for _,name,_,_ in Formatter().parse(s) if name is not None}
            self.assertEqual(fields(value),fields(catalogs[1][key]), key)
    def test_validation_errors_follow_selected_language(self):
        from localization import set_locale
        from engine import TypingConfig
        set_locale('en')
        with self.assertRaises(ValueError) as error: TypingConfig(start_delay=-1).validate()
        self.assertIn('between',str(error.exception))
        set_locale('tr')
        with self.assertRaises(ValueError) as error: TypingConfig(start_delay=-1).validate()
        self.assertIn('aralığında',str(error.exception))
        set_locale('en')
