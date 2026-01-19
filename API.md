# API Reference

The Royal Research Automation system exposes a RESTful API for managing settings and triggering research jobs.

**Base URL**: `http://localhost:5000`

## Research Operations

### Start Research
Triggers the full research workflow in a background thread.

-   **Endpoint**: `POST /api/run`
-   **Response**:
    ```json
    {
      "status": "started"
    }
    ```
-   **Error (409)**: If a job is already running.

### Get Status
Get the status of the current or last run.

-   **Endpoint**: `GET /api/status`
-   **Response**:
    ```json
    {
      "running": false,
      "stage": "Complete",
      "progress": 100,
      "result": { ... },
      "error": null
    }
    ```

### Stream Progress (SSE)
Subscribe to real-time progress updates via Server-Sent Events.

-   **Endpoint**: `GET /api/stream`

---

## Settings: Competitors

### List Competitors
-   **Endpoint**: `GET /api/competitors`
-   **Response**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": 1,
          "name": "Competitor Name",
          "url": "https://youtube.com/...",
          "channel_id": "UC...",
          "enabled": true
        }
      ]
    }
    ```

### Add Competitor
Automatically detects Channel ID from the URL.

-   **Endpoint**: `POST /api/competitors`
-   **Body**:
    ```json
    {
      "name": "Channel Name",
      "url": "https://youtube.com/@channel",
      "description": "Optional desc"
    }
    ```

### Update Competitor
-   **Endpoint**: `PUT /api/competitors/<id>`
-   **Body**: `{ "name": "...", ... }`

### Delete Competitor
-   **Endpoint**: `DELETE /api/competitors/<id>`

### Toggle Status
Enable or disable a competitor.

-   **Endpoint**: `POST /api/competitors/<id>/toggle`

---

## Settings: Keywords

### List Keywords
-   **Endpoint**: `GET /api/keywords`

### Add Keyword
-   **Endpoint**: `POST /api/keywords`
-   **Body**:
    ```json
    {
      "keyword": "Meghan Markle",
      "category": "primary"
    }
    ```
-   **Note**: `category` must be `"primary"` or `"secondary"`.

### Toggle Keyword
-   **Endpoint**: `POST /api/keywords/<id>/toggle`

---

## System

### Validate Settings
Checks if the current configuration is valid for running research.

-   **Endpoint**: `GET /api/settings/validate`
-   **Response**:
    ```json
    {
      "success": true,
      "valid": true,
      "issues": [],
      "warnings": ["No NewsAPI key found"],
      "ready": true
    }
    ```

### Get Stats
Get quick counts of active/total settings.

-   **Endpoint**: `GET /api/settings/stats`
-   **Response**:
    ```json
    {
      "success": true,
      "data": {
        "competitors": { "total": 5, "active": 3 },
        "keywords": { "total": 10, "active": 8 }
      }
    }
    ```
