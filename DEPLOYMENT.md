# Deployment Guide

This guide describes how to deploy the Royal Research Automation system to a production environment (e.g., a VPS or Cloud Server).

## Prerequisites
-   Python 3.9+
-   A server (Ubuntu/Debian recommended)
-   API Keys (Anthropic, YouTube, Twitter, NewsAPI)
-   Basic knowledge of `systemd` and Nginx

## 1. Environment Setup

Clone the repo and set up a virtual environment:

```bash
cd /opt
git clone https://github.com/your-repo/royal-research-automation.git
cd royal-research-automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 2. Configuration

Create the `.env` file with your production keys:

```bash
nano .env
```

```ini
ANTHROPIC_API_KEY=sk-...
YOUTUBE_API_KEY=AIza...
NEWSAPI_KEY=...
TWITTER_BEARER_TOKEN=...
FLASK_ENV=production
```

## 3. Gunicorn Setup

Test Gunicorn manually first:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 4. Systemd Service

Create a service to keep the app running in the background.

```bash
sudo nano /etc/systemd/system/royal-research.service
```

```ini
[Unit]
Description=Royal Research Automation
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/royal-research-automation
Environment="PATH=/opt/royal-research-automation/venv/bin"
EnvironmentFile=/opt/royal-research-automation/.env
ExecStart=/opt/royal-research-automation/venv/bin/gunicorn --workers 4 --bind unix:royal-research.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl start royal-research
sudo systemctl enable royal-research
```

## 5. Nginx Reverse Proxy

Configure Nginx to serve the app on port 80.

```bash
sudo nano /etc/nginx/sites-available/royal-research
```

```nginx
server {
    listen 80;
    server_name research.yourdomain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/royal-research-automation/royal-research.sock;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/royal-research /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 6. Security Checks
-   Ensure firewall allows ports 80/443.
-   Set up SSL (Certbot) for HTTPS.
-   Consider adding Basic Auth to Nginx if the dashboard collects sensitive data.
