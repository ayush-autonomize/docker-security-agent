"""Utility to update dependencies in a repository."""
from pathlib import Path
from typing import Union, List, Dict, Optional
import re
import json
import subprocess
import shutil

class BaseUpdater:
    def update(self, repo_path: Path, vulnerabilities: List[Dict]) -> List[str]:
        raise NotImplementedError

class PythonUpdater(BaseUpdater):
    def update(self, repo_path: Path, vulnerabilities: List[Dict]) -> List[str]:
        req_file = repo_path / "requirements.txt"
        if not req_file.exists():
            return []

        updates = {}
        for v in vulnerabilities:
            pkg = v.get("PkgName")
            fixed = v.get("FixedVersion")
            if pkg and fixed:
                if "," in fixed:
                    fixed = fixed.split(",")[-1].strip()
                updates[pkg] = fixed

        if not updates:
            return []

        print(f"Attempting to update {len(updates)} packages in requirements.txt")
        try:
            content = req_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Warning: Failed to read {req_file} as UTF-8, trying UTF-16")
            content = req_file.read_text(encoding="utf-16")
            
        lines = content.splitlines()
        new_lines = []
        modified = False
        updated_pkgs = []

        for line in lines:
            clean_line = line.split("#")[0].strip()
            if not clean_line:
                new_lines.append(line)
                continue
            
            updated_this_line = False
            for pkg, fixed_ver in updates.items():
                pattern = re.compile(f"^{re.escape(pkg)}([<>=!~]+.*)?$")
                if pattern.match(clean_line):
                    comment = ""
                    if "#" in line:
                        comment = " #" + line.split("#", 1)[1]
                    new_line = f"{pkg}>={fixed_ver}{comment}"
                    new_lines.append(new_line)
                    modified = True
                    updated_this_line = True
                    updated_pkgs.append(pkg)
                    print(f"Updated {pkg} to {fixed_ver}")
                    break
            
            if not updated_this_line:
                new_lines.append(line)

        if modified:
            req_file.write_text("\n".join(new_lines) + "\n")
            return updated_pkgs
        return []

class NodeUpdater(BaseUpdater):
    def update(self, repo_path: Path, vulnerabilities: List[Dict]) -> List[str]:
        pkg_file = repo_path / "package.json"
        if not pkg_file.exists():
            return []

        updates = {}
        for v in vulnerabilities:
            pkg = v.get("PkgName")
            fixed = v.get("FixedVersion")
            if pkg and fixed:
                updates[pkg] = fixed

        if not updates:
            return []

        print(f"Attempting to update {len(updates)} packages in package.json")
        try:
            data = json.loads(pkg_file.read_text())
        except json.JSONDecodeError:
            print("Failed to parse package.json")
            return []

        modified = False
        updated_pkgs = []
        
        # Check dependencies and devDependencies
        for section in ["dependencies", "devDependencies"]:
            if section in data:
                for pkg, fixed_ver in updates.items():
                    if pkg in data[section]:
                        # Update to exact version for security
                        print(f"Updated {pkg} in {section} to {fixed_ver}")
                        data[section][pkg] = fixed_ver
                        modified = True
                        updated_pkgs.append(pkg)

        if modified:
            pkg_file.write_text(json.dumps(data, indent=2) + "\n")
            
            # Try to update package-lock.json if npm is available
            if shutil.which("npm"):
                print("Running npm install --package-lock-only to update lockfile...")
                try:
                    subprocess.run(
                        ["npm", "install", "--package-lock-only"],
                        cwd=repo_path,
                        check=True,
                        capture_output=True
                    )
                    print("Updated package-lock.json")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to update package-lock.json: {e}")
            else:
                print("npm not found. Skipping package-lock.json update.")
                
            return updated_pkgs
        return []

class PoetryUpdater(BaseUpdater):
    def update(self, repo_path: Path, vulnerabilities: List[Dict]) -> List[str]:
        pyproject = repo_path / "pyproject.toml"
        if not pyproject.exists():
            return []

        updates = {}
        for v in vulnerabilities:
            if v.get("PkgName") and v.get("FixedVersion"):
                updates[v["PkgName"]] = v["FixedVersion"]

        if not updates:
            return []

        updated_pkgs = []
        # Try using poetry CLI first
        if shutil.which("poetry"):
            print("Found poetry, using CLI...")
            for pkg, ver in updates.items():
                try:
                    # poetry add package==version
                    print(f"Running poetry add {pkg}>={ver}")
                    subprocess.run(
                        ["poetry", "add", f"{pkg}>={ver}"],
                        cwd=repo_path,
                        check=True,
                        capture_output=True
                    )
                    updated_pkgs.append(pkg)
                except subprocess.CalledProcessError:
                    print(f"Failed to update {pkg} via poetry")
        
        # Fallback to text replacement if CLI failed or not found
        if len(updated_pkgs) < len(updates):
            print("Falling back to pyproject.toml text replacement...")
            content = pyproject.read_text()
            new_lines = []
            modified = False
            
            for line in content.splitlines():
                clean_line = line.strip()
                updated_this_line = False
                
                # Simple TOML parsing: name = "version" or name = { ... }
                for pkg, ver in updates.items():
                    if pkg in updated_pkgs: continue # Already updated via CLI
                    
                    # Regex for: pkg = "..." or pkg = { ... }
                    # Very basic, assumes standard formatting
                    if re.match(f'^{pkg}\\s*=', clean_line):
                        # Replace version string
                        # This is risky with complex toml, but works for simple cases
                        # pkg = "^1.2.3" -> pkg = "1.2.4"
                        if '"' in line:
                            # pkg = "1.2.3"
                            new_line = re.sub(r'"[^"]*"', f'"{ver}"', line)
                            new_lines.append(new_line)
                            modified = True
                            updated_this_line = True
                            updated_pkgs.append(pkg)
                            print(f"Updated {pkg} in pyproject.toml (text)")
                            break
                
                if not updated_this_line:
                    new_lines.append(line)
            
            if modified:
                pyproject.write_text("\n".join(new_lines) + "\n")

        return updated_pkgs

class PipenvUpdater(BaseUpdater):
    def update(self, repo_path: Path, vulnerabilities: List[Dict]) -> List[str]:
        pipfile = repo_path / "Pipfile"
        if not pipfile.exists():
            return []

        updates = {}
        for v in vulnerabilities:
            if v.get("PkgName") and v.get("FixedVersion"):
                updates[v["PkgName"]] = v["FixedVersion"]

        if not updates:
            return []

        updated_pkgs = []
        if shutil.which("pipenv"):
            print("Found pipenv, using CLI...")
            for pkg, ver in updates.items():
                try:
                    print(f"Running pipenv install {pkg}>={ver}")
                    subprocess.run(
                        ["pipenv", "install", f"{pkg}>={ver}"],
                        cwd=repo_path,
                        check=True,
                        capture_output=True,
                        env={**os.environ, "PIPENV_IGNORE_VIRTUALENVS": "1"}
                    )
                    updated_pkgs.append(pkg)
                except subprocess.CalledProcessError:
                    print(f"Failed to update {pkg} via pipenv")

        # Fallback text replacement
        if len(updated_pkgs) < len(updates):
            print("Falling back to Pipfile text replacement...")
            content = pipfile.read_text()
            new_lines = []
            modified = False
            
            for line in content.splitlines():
                clean_line = line.strip()
                updated_this_line = False
                
                for pkg, ver in updates.items():
                    if pkg in updated_pkgs: continue
                    
                    # Pipfile format: pkg = "..."
                    if re.match(f'^{pkg}\\s*=', clean_line):
                        if '"' in line:
                            # We want to replace the version inside quotes
                            # But we need to be careful about "==version" vs "version"
                            # The current implementation replaces the whole string inside quotes with the new version
                            # If the original was "==2.25.1", we might want "==2.26.0"
                            # But Trivy gives us "2.26.0". 
                            # Pipfile usually accepts "==version" or "version" (which implies ==).
                            # Let's just use the simple replacement for now, but fix the test expectation or logic.
                            
                            # Actually, let's try to preserve the operator if it exists inside the quotes
                            quote_content_match = re.search(r'"([^"]*)"', line)
                            if quote_content_match:
                                old_ver_str = quote_content_match.group(1)
                                if old_ver_str.startswith("=="):
                                     new_ver_str = f"=={ver}"
                                else:
                                     new_ver_str = ver
                                
                                new_line = line.replace(f'"{old_ver_str}"', f'"{new_ver_str}"')
                                new_lines.append(new_line)
                                modified = True
                                updated_this_line = True
                                updated_pkgs.append(pkg)
                                print(f"Updated {pkg} in Pipfile (text)")
                                break
                
                if not updated_this_line:
                    new_lines.append(line)
            
            if modified:
                pipfile.write_text("\n".join(new_lines) + "\n")

        return updated_pkgs

class MavenUpdater(BaseUpdater):
    def update(self, repo_path: Path, vulnerabilities: List[Dict]) -> List[str]:
        pom = repo_path / "pom.xml"
        if not pom.exists():
            return []

        updates = {}
        for v in vulnerabilities:
            if v.get("PkgName") and v.get("FixedVersion"):
                updates[v["PkgName"]] = v["FixedVersion"]

        if not updates:
            return []
            
        print(f"Attempting to update {len(updates)} packages in pom.xml")
        content = pom.read_text()
        original_content = content
        updated_pkgs = []
        
        # Very basic XML regex replacement to avoid lxml dependency for now
        # Looks for:
        # <dependency>
        #   <groupId>...</groupId>
        #   <artifactId>pkg_name</artifactId>
        #   <version>...</version>
        # </dependency>
        
        for pkg, ver in updates.items():
            # We need to match artifactId. 
            # Note: Trivy might report "group:artifact", we should handle that.
            # If PkgName has a colon, split it.
            artifact_id = pkg
            if ":" in pkg:
                _, artifact_id = pkg.split(":", 1)
            
            # Regex to find the version tag associated with this artifact
            # This is tricky with regex. We'll try a simple approach:
            # Find <artifactId>pkg</artifactId> ... <version>old</version>
            # This assumes standard formatting.
            
            pattern = re.compile(
                f"(<artifactId>{re.escape(artifact_id)}</artifactId>\\s*<version>)([^<]+)(</version>)",
                re.DOTALL | re.MULTILINE
            )
            
            if pattern.search(content):
                content = pattern.sub(f"\\g<1>{ver}\\g<3>", content)
                updated_pkgs.append(pkg)
                print(f"Updated {pkg} in pom.xml")

        if content != original_content:
            pom.write_text(content)
            return updated_pkgs
            
        return []

class DependencyUpdater:
    def __init__(self):
        self.updaters = [
            PythonUpdater(), 
            NodeUpdater(),
            PoetryUpdater(),
            PipenvUpdater(),
            MavenUpdater()
        ]

    def update_dependencies(self, repo_path: Union[str, Path], vulnerabilities: List[Dict]) -> List[str]:
        """Update dependencies based on vulnerabilities using available updaters."""
        repo_path = Path(repo_path)
        all_updated = []
        
        for updater in self.updaters:
            updated = updater.update(repo_path, vulnerabilities)
            all_updated.extend(updated)
                
        return all_updated
