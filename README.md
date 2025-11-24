# Docker Security Agent

A fully automated security agent that scans Docker images for vulnerabilities, updates dependencies to fix them, verifies the fixes with tests, and creates Pull Requests.

## Features

- **Automated Scanning**: Uses [Trivy](https://github.com/aquasecurity/trivy) to scan Docker images for vulnerabilities.
- **Auto-Fix**: Automatically updates dependencies to fix HIGH and MEDIUM vulnerabilities.
    - **Python**: Updates `requirements.txt`.
    - **Node.js**: Updates `package.json` (direct dependencies).
- **Verification**: Runs repository tests (e.g., `pytest`, `npm test`) to ensure fixes don't break the build.
- **PR Creation**: Automatically opens a Pull Request with the security fixes.
- **Scheduled Runs**: Configured to run weekly via GitHub Actions.

## Prerequisites

Before running the agent, ensure you have the following installed:

1.  **Docker**: Must be installed and running.
2.  **Trivy**: Vulnerability scanner.
    - Mac: `brew install trivy`
    - Linux: `apt-get install trivy` (or see [Trivy docs](https://aquasecurity.github.io/trivy/v0.18.3/installation/))
3.  **Python 3.10+**: The agent is written in Python.
4.  **Git**: For cloning and pushing changes.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/docker-security-agent.git
    cd docker-security-agent
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### 1. GitHub Token (Required)
You need a GitHub Personal Access Token (PAT) to clone private repositories and create Pull Requests.

1.  Generate a token (Classic) with **`repo`** scope.
2.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
3.  Add your token to `.env`:
    ```env
    GITHUB_TOKEN=ghp_your_token_here
    ```

### 2. Target Repositories
List the repositories you want to scan in `configs/repos.yaml`.

```yaml
repos:
  - name: my-python-app
    url: https://github.com/my-org/my-python-app.git
    test_command: pytest

  - name: my-node-app
    url: https://github.com/my-org/my-node-app.git
    test_command: npm install && npm test
```

## Usage

### Running Locally
Once configured, simply run the agent:

```bash
# Ensure Docker is running!
python main.py
```

The agent will:
1.  Clone each repository defined in `configs/repos.yaml`.
2.  Build the Docker image.
3.  Scan it with Trivy.
4.  If vulnerabilities are found:
    *   Create a new branch.
    *   Update dependencies (`requirements.txt` or `package.json`).
    *   Run the `test_command`.
    *   If tests pass, push the branch and create a PR.

### Running on GitHub Actions
The agent is set up to run automatically on GitHub Actions (see `.github/workflows/security-agent.yml`).

1.  Go to your repository **Settings** > **Secrets and variables** > **Actions**.
2.  Add a New Repository Secret named **`GH_PAT`** with your GitHub Token.
3.  The workflow runs every Monday at 00:00 UTC, or you can trigger it manually from the **Actions** tab.

## Troubleshooting

- **`Trivy not found`**: Ensure Trivy is installed and in your PATH.
- **`Docker build failed`**: Check if the target repository has a valid `Dockerfile`.
- **`PR creation skipped`**: Ensure `GITHUB_TOKEN` is set in `.env` (local) or `GH_PAT` (GitHub Actions).
- **`Tests failed`**: The agent will abort the PR if tests fail to prevent breaking changes. Check the logs to see why tests failed.
