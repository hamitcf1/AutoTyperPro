import ast
from pathlib import Path
import tempfile
import unittest

class MetadataTests(unittest.TestCase):
    def test_windows_version_resource_generated_from_version(self):
        from tools.build_metadata import write_windows_version
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'version.txt'
            write_windows_version(path,'3.7.12')
            tree=ast.parse(path.read_text())
            tuples=[node for node in ast.walk(tree) if isinstance(node,ast.Tuple) and len(node.elts)==4 and all(isinstance(e,ast.Constant) for e in node.elts)]
            self.assertTrue(any(tuple(e.value for e in node.elts)==(3,7,12,0) for node in tuples))
            self.assertIn('3.7.12',[node.value for node in ast.walk(tree) if isinstance(node,ast.Constant)])
            self.assertIn("StringStruct('CompanyName','AetheriusCo')",path.read_text())
    def test_invalid_version_rejected_before_file_write(self):
        from tools.build_metadata import write_windows_version
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'version.txt'
            with self.assertRaises(ValueError):write_windows_version(path,'3.0; bad')
            self.assertFalse(path.exists())

class FrozenTrayTests(unittest.TestCase):
    def test_windows_spec_explicitly_packages_dynamic_tray_backend(self):
        import sys,tempfile
        from pathlib import Path
        from unittest.mock import Mock,patch
        import PyInstaller.utils.hooks
        source=(Path(__file__).resolve().parents[1]/'AutoTyperPro.spec').read_text()
        with tempfile.TemporaryDirectory() as directory,patch('sys.platform','win32'),patch('PyInstaller.utils.hooks.collect_data_files',return_value=[]):
            analysis=Mock();scope={'SPECPATH':directory,'Analysis':analysis,'PYZ':Mock(),'EXE':Mock(),'COLLECT':Mock(),'BUNDLE':Mock()}
            old_path=list(sys.path)
            try:exec(compile(source,'AutoTyperPro.spec','exec'),scope)
            finally:sys.path[:]=old_path
            self.assertIn('pystray._win32',analysis.call_args.kwargs['hiddenimports'])
