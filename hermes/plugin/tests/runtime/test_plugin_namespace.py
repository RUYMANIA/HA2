"""Production plugin packages are nested, not top-level sys.path entries."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

class PluginNamespaceTests(unittest.TestCase):
    def test_protected_reader_imports_under_real_plugin_namespace(self):
        root=Path(__file__).resolve().parents[2]
        code="""import importlib,types,sys,tempfile,sqlite3
from pathlib import Path
root=Path(ROOT)
p=types.ModuleType('ha2_plugin_namespace');p.__path__=[str(root)];sys.modules[p.__name__]=p
bridge=importlib.import_module('ha2_plugin_namespace.hermes_bridge.bridge')
assert 'hermes_bridge' not in sys.modules
with tempfile.TemporaryDirectory(prefix='ha2-namespace-') as directory:
 db=Path(directory)/'fixture.db'
 c=sqlite3.connect(db);c.execute('CREATE TABLE fixture(value INTEGER)');c.commit();c.close()
 with bridge.readonly_snapshot(db,allow_auxiliary=True) as reader:
  assert reader.execute('SELECT count(*) FROM fixture').fetchone()[0]==0
print('NESTED_PLUGIN_READER_PASS')
""".replace('ROOT',repr(str(root)))
        result=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
