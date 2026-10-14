import unittest
from urllib.parse import urlparse,parse_qs

class AppInfoTests(unittest.TestCase):
    def test_owner_and_report_are_public_and_contain_no_user_content(self):
        import app_info
        self.assertEqual(app_info.CREATOR,'Hamit Can Fındık')
        self.assertEqual(app_info.ORGANIZATION,'AetheriusCo')
        self.assertEqual(app_info.REPOSITORY,'https://github.com/AetheriusCo/AutoTyperPro')
        summary=app_info.technical_summary()
        self.assertNotIn('/Users/',summary);self.assertNotIn('C:\\Users',summary)
        self.assertNotIn('editor',summary.lower());self.assertNotIn('hostname',summary.lower())
        url=app_info.bug_report_url(summary)
        self.assertEqual(urlparse(url).netloc,'github.com')
        self.assertTrue(urlparse(url).path.startswith('/AetheriusCo/AutoTyperPro/issues/new'))
        self.assertEqual(parse_qs(urlparse(url).query)['platform'],[summary])
