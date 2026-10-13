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
    def test_invalid_version_rejected_before_file_write(self):
        from tools.build_metadata import write_windows_version
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'version.txt'
            with self.assertRaises(ValueError):write_windows_version(path,'3.0; bad')
            self.assertFalse(path.exists())
