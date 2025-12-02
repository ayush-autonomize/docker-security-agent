# Project Structure

This document lists the files and directories in the `docker-security-agent` project and describes their purpose.

## Root Directory

| File | Description |
| :--- | :--- |
| **`main.py`** | **Entry Point**. The main script that starts the agent. It loads configurations and triggers the `RepoRunner` for each repository. |
| **`requirements.txt`** | Lists the Python libraries required to run the agent (e.g., `docker`, `PyYAML`, `requests`). |
| **`README.md`** | Main documentation for the project, including installation, usage, and troubleshooting guides. |
| **`.env`** | Local configuration file for environment variables (e.g., `GITHUB_TOKEN`). **Ignored by Git.** |
| **`.env.example`** | Template for the `.env` file. Shows required variables without exposing secrets. |
| **`.gitignore`** | Specifies files and directories that Git should ignore (e.g., `__pycache__`, `.env`, `temp_repos/`). |

## `agent/` Directory
Contains the core logic and modules of the security agent.

| File | Description |
| :--- | :--- |
| **`repo_runner.py`** | **Orchestrator**. Manages the full workflow for a single repo: Clone -> Build -> Scan -> Update -> Test -> PR. |
| **`docker_runner.py`** | Handles Docker operations: building images and running Trivy scans. Includes conflict detection logic. |
| **`dependency_updater.py`** | Logic for parsing and updating dependency files (`requirements.txt`, `package.json`, `pom.xml`, etc.). |
| **`git_client.py`** | Wrapper for Git interactions: cloning, branching, committing, pushing, and creating Pull Requests via GitHub API. |
| **`test_runner.py`** | Executes tests in the target repository (e.g., running `pytest` or `npm test`). |
| **`trivy_parser.py`** | Helper to parse the JSON output from Trivy and extract High/Medium vulnerabilities. |
| **`config_loader.py`** | Utility to safely load and parse YAML configuration files. |
| **`__init__.py`** | Marks the directory as a Python package. |

## `configs/` Directory
Configuration files for the agent.

| File | Description |
| :--- | :--- |
| **`repos.yaml`** | Defines the list of repositories to scan, their URLs, and test commands. |
| **`agent.yaml`** | Global configuration for the agent (e.g., working directory, scan settings). |

## `.github/workflows/` Directory
CI/CD configurations.

| File | Description |
| :--- | :--- |
| **`security-agent.yml`** | **GitHub Actions Workflow**. Defines the automated schedule (weekly) and manual triggers for running the agent in the cloud. |

## `scripts/` Directory
Helper scripts.

| File | Description |
| :--- | :--- |
| **`run_local.sh`** | A convenience shell script to run the agent locally. |

## `tests/` Directory
Contains unit tests for the agent's code (e.g., `test_dependency_updater.py`).
