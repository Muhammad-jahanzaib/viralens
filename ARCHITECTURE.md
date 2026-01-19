# System Architecture

## Overview
The Royal Research Automation system is built as a modular pipeline that ingests raw data from the web, normalizes it, and feeds it into a Large Language Model (LLM) for synthesis and creative generation.

```mermaid
graph TD
    User[User / Dashboard] -->|Start Research| Orch[Orchestrator (main.py)]
    Orch -->|Load Config| Settings[SettingsManager]
    Settings -->|Get Keywords| DB[(JSON Data)]
    
    subgraph "Phase 1: Collection"
        Orch --> GT[Google Trends]
        Orch --> TW[Twitter API]
        Orch --> RD[Reddit Scraper]
        Orch --> YT[YouTube API]
        Orch --> News[News Aggregator]
    end
    
    subgraph "Phase 2: Processing"
        GT & TW & RD & YT & News -->|Raw Data| Norm[Data Normalizer]
        Norm -->|Formatted Context| Claude[Claude 3.5 Haiku]
    end
    
    subgraph "Phase 3: Output"
        Claude -->|JSON Result| Report[Report Generator]
        Report -->|Save| File[(JSON/HTML Files)]
        Report -->|Display| UI[Web Dashboard]
    end
```

## Core Components

### 1. Orchestrator (`main.py`)
The central nervous system. It manages the linear workflow:
1.  **Initialization**: Loads settings and initializes collector classes.
2.  **Collection**: Calls `collect()` method on each collector sequentially (wrapping them in error handlers to ensure robust execution).
3.  **Transformation**: Formats the raw data into a human/AI-readable string prompt.
4.  **Generation**: Sends the prompt to Anthropic's API.
5.  **Reporting**: Saves the results and returns summary stats.

### 2. Data Collectors (`collectors/`)
Each module is responsible for a single platform. They all share a common pattern but adapt to specific limitations:
-   **`youtube_client.py`**: Uses `google-api-python-client`. Focuses on "Videos" endpoint to find high VPH (Views Per Hour) content.
-   **`reddit_scraper.py`**: Uses `requests` + `BeautifulSoup`. No API key needed. Mimics a browser to scrape "Hot" posts.
-   **`twitter_client.py`**: Uses `tweepy` (API v2). strict filtering for "verified" or high-engagement tweets only.
-   **`google_trends.py`**: Uses `pytrends`. Looks for simple "Rising" queries.

### 3. AI Generator (`generators/claude_client.py`)
Handles the interaction with the LLM. It constructs a massive prompt containing all the collected data and instructs the model to act as a "Viral YouTube Strategist". output is strictly enforced as JSON for programmatic consumption.

### 4. Settings Manager (`utils/settings_manager.py`)
Abstractions for reading/writing the JSON configuration files (`competitors.json`, `keywords.json`). Handles business logic like:
-   Resolving YouTube URLs to Channel IDs via API.
-   Validating keyword categories.
-   Ensuring data persistence.

### 5. Web Interface (`app.py` + `templates/`)
A Flask-based UI.
-   **Backend**: Exposes REST API endpoints (`/api/competitors`, `/api/run`, etc.)
-   **Frontend**: Vanilla JS + Tailwind CSS. Uses Polling/SSE (Server-Sent Events) for real-time progress on long-running jobs.

## Data Flow
1.  **Input**: User defines "Keywords" (topics of interest) and "Competitors" (channels to watch).
2.  **Throughput**: System gathers ~50-100 data points across 5 platforms.
3.  **Processing**: Data is filtered, duplicates removed, and condensed into a ~6k token prompt.
4.  **Output**: AI generates 5-10 specific video contents, ranked by potential.

## File Storage
-   **Reports**: Stored in `data/research_reports/` as `json` (data) and `html` (email-ready view).
-   **Settings**: Stored in `utils/` (or root `data/`) as `competitors.json` and `keywords.json`.
