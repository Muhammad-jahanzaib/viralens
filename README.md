# Royal Research Automation

A powerful, AI-driven content research automation system designed for YouTube creators. This system autonomously aggregates data from multiple sources (Google Trends, Twitter/X, Reddit, YouTube, News), analyzes it using Claude 3.5 Haiku, and generates high-potential video topics with catchy titles, hooks, and thumbnail concepts.

## 🚀 Features

-   **Multi-Source Data Collection**:
    -   **Google Trends**: Identifies breakout and rising search queries.
    -   **Twitter/X**: Finds viral tweets and discussions (min. engagement filtering).
    -   **Reddit**: Scrapes subreddit discussions and "hot" posts without API limits.
    -   **YouTube**: Tracks competitor channels for top-performing videos.
    -   **News**: Aggregates relevant articles from NewsAPI and RSS feeds.
-   **AI Intelligence**:
    -   Powered by **Claude 3.5 Haiku** (Anthropic) for cost-effective, high-quality analysis.
    -   Generates viral hook ideas, key talking points, and thumbnail descriptions.
    -   Scores topics by "Publishing Priority" and "Viral Potential".
-   **Modern Dashboard**:
    -   Real-time progress tracking.
    -   Manage competitors and keywords via a sleek UI.
    -   View historical reports and trends.
    -   **New**: One-click settings import/export.
    -   **New**: Smart configuration validation.
-   **Dynamic Configuration**:
    -   Add/Remove competitors and keywords on the fly.
    -   Auto-detects YouTube Channel IDs from URLs.

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/royal-research-automation.git
    cd royal-research-automation
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**:
    Create a `.env` file in the root directory:
    ```ini
    # API Keys
    ANTHROPIC_API_KEY=your_anthropic_key
    YOUTUBE_API_KEY=your_youtube_key
    NEWSAPI_KEY=your_newsapi_key
    TWITTER_BEARER_TOKEN=your_twitter_token
    
    # Optional Configuration
    LOG_LEVEL=INFO
    ```

## 🚦 Usage

### 1. Start the Dashboard
Launch the web interface to manage settings and run research.
```bash
python app.py
```
Visit `http://localhost:5000` in your browser.

### 2. Configure Settings
-   Go to **Settings** (top right on dashboard).
-   Add your **Competitors** (YouTube URL) and **Keywords**.
-   Ensure you have at least 3 competitors and 2 keywords for best results.

### 3. Run Research
-   Click **Start Research** on the dashboard.
-   Watch the real-time progress as data is collected and analyzed.
-   View the generated topics and "Viral" scores.

### 4. CLI Usage (Optional)
You can also run the system from the command line:
```bash
python main.py --save           # Run and save report
python main.py --test           # Run a quick test (dry run)
```

## 📁 Project Structure

-   `main.py`: Core orchestration logic.
-   `app.py`: Flask web application and API.
-   `collectors/`: Modules for each data source.
-   `generators/`: AI prompt engineering and interaction.
-   `utils/`: Helper functions and managers.
-   `templates/`: HTML for the dashboard.
-   `data/`: Stores generated reports and settings database.

## 📚 Documentation

-   [Architecture Overview](ARCHITECTURE.md)
-   [API Reference](API.md)
-   [Deployment Guide](DEPLOYMENT.md)
-   [Troubleshooting](TROUBLESHOOTING.md)

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

## 📄 License

MIT License.
