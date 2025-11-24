import unittest
from pathlib import Path
import tempfile
import shutil
from agent.dependency_updater import PoetryUpdater, PipenvUpdater, MavenUpdater

class TestExtendedUpdaters(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_poetry_updater_text_fallback(self):
        # Test fallback when poetry CLI is not present
        (self.repo_path / "pyproject.toml").write_text("""
[tool.poetry.dependencies]
python = "^3.9"
requests = "2.25.1"
flask = "1.1.2"
""")
        updater = PoetryUpdater()
        vulns = [
            {"PkgName": "requests", "FixedVersion": "2.26.0"},
            {"PkgName": "flask", "FixedVersion": "2.0.0"}
        ]
        
        # Mock shutil.which to return None (force fallback)
        original_which = shutil.which
        shutil.which = lambda x: None
        try:
            updated = updater.update(self.repo_path, vulns)
        finally:
            shutil.which = original_which

        content = (self.repo_path / "pyproject.toml").read_text()
        self.assertIn('requests = "2.26.0"', content)
        self.assertIn('flask = "2.0.0"', content)
        self.assertEqual(len(updated), 2)

    def test_pipenv_updater_text_fallback(self):
        (self.repo_path / "Pipfile").write_text("""
[[source]]
url = "https://pypi.org/simple"

[packages]
requests = "==2.25.1"
django = "==3.1"
""")
        updater = PipenvUpdater()
        vulns = [{"PkgName": "requests", "FixedVersion": "2.26.0"}]
        
        original_which = shutil.which
        shutil.which = lambda x: None
        try:
            updated = updater.update(self.repo_path, vulns)
        finally:
            shutil.which = original_which

        content = (self.repo_path / "Pipfile").read_text()
        self.assertIn('requests = "==2.26.0"', content)
        self.assertIn('django = "==3.1"', content)

    def test_maven_updater(self):
        (self.repo_path / "pom.xml").write_text("""
<project>
    <dependencies>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.10.0</version>
        </dependency>
    </dependencies>
</project>
""")
        updater = MavenUpdater()
        vulns = [{"PkgName": "jackson-databind", "FixedVersion": "2.12.0"}]
        
        updated = updater.update(self.repo_path, vulns)
        
        content = (self.repo_path / "pom.xml").read_text()
        self.assertIn("<version>2.12.0</version>", content)
        self.assertEqual(updated, ["jackson-databind"])

if __name__ == "__main__":
    unittest.main()
