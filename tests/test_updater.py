import unittest
from pathlib import Path
import tempfile
import shutil
from agent.dependency_updater import DependencyUpdater

class TestDependencyUpdater(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.updater = DependencyUpdater()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_update_dependencies(self):
        repo_path = Path(self.test_dir)
        req_file = repo_path / "requirements.txt"
        req_file.write_text("""
requests==2.0.0
flask>=1.0.0 # comment
django
numpy==1.18.0
""")
        
        vulns = [
            {"PkgName": "requests", "FixedVersion": "2.31.0"},
            {"PkgName": "flask", "FixedVersion": "2.0.0"},
            {"PkgName": "django", "FixedVersion": "4.0.0"}
        ]
        
        updated = self.updater.update_dependencies(repo_path, vulns)
        
        self.assertTrue(updated)
        content = req_file.read_text()
        
        self.assertIn("requests==2.31.0", content)
        self.assertIn("flask==2.0.0 # comment", content)
        self.assertIn("django==4.0.0", content)
        self.assertIn("numpy==1.18.0", content)

if __name__ == "__main__":
    unittest.main()
