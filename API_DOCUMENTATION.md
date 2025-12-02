# Docker Security Agent API Documentation

This document describes the FastAPI backend for the Docker Security Agent. The API allows you to list configured repositories, trigger security scans in the background, and track their status.

## Features

*   **RESTful API**: Built with FastAPI for high performance and automatic documentation.
*   **Asynchronous Processing**: Scans run in the background using `BackgroundTasks`, so the API remains responsive.
*   **Status Tracking**: In-memory tracking of scan status (queued, running, success, failed).
*   **Integration**: Directly reuses the existing `RepoRunner` logic to clone, scan, fix, and create PRs.

## Base URL

By default, the API runs at:
`http://127.0.0.1:8000`

## Endpoints

### 1. Health Check
Check if the API server is up and running.

*   **URL**: `/health`
*   **Method**: `GET`
*   **Response**:
    ```json
    {
      "status": "ok"
    }
    ```

### 2. List Repositories
Get a list of all repositories configured in `configs/repos.yaml`.

*   **URL**: `/repos`
*   **Method**: `GET`
*   **Response**:
    ```json
    [
      {
        "name": "test4",
        "url": "https://github.com/ayush-autonomize/test4.git",
        "test_command": "echo \"No tests\""
      }
    ]
    ```

### 3. Trigger Scan
Start a security scan for a specific repository. This runs asynchronously in the background.

*   **URL**: `/scan/{repo_name}`
*   **Method**: `POST`
*   **Path Parameters**:
    *   `repo_name`: The name of the repository to scan (must match a name in `configs/repos.yaml`).
*   **Response**:
    ```json
    {
      "status": "started",
      "repo": "test4"
    }
    ```

### 4. Check Scan Status
Get the current status of a scan for a specific repository.

*   **URL**: `/scan-status/{repo_name}`
*   **Method**: `GET`
*   **Path Parameters**:
    *   `repo_name`: The name of the repository.
*   **Response** (Example - Running):
    ```json
    {
      "status": "running",
      "message": "Building image..."
    }
    ```
*   **Response** (Example - Success):
    ```json
    {
      "status": "success",
      "message": "Scan completed successfully",
      "pr_url": "https://github.com/ayush-autonomize/test4/pull/2"
    }
    ```

## Running the Server

1.  **Activate Virtual Environment**:
    ```bash
    source .venv/bin/activate
    ```

2.  **Start the Server**:
    ```bash
    uvicorn api.main:app --reload
    ```

3.  **Access Interactive Docs**:
    Open your browser to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
