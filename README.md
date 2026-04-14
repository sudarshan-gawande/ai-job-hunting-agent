# 🤖 AI Job Hunting Agent

> **A fully automated job search agent that runs 24/7, finds matching jobs, scores them with AI, drafts recruiter emails, and sends you alerts — all for ₹0/month.**

Built with Python, Claude AI, Google Gemini, and SerpAPI.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude AI](https://img.shields.io/badge/Built%20with-Claude%20AI-7C3AED)](https://claude.ai)
[![Gemini](https://img.shields.io/badge/Scoring-Google%20Gemini-4285F4)](https://aistudio.google.com)

---

## 🎯 What It Does

You configure it once with your profile (skills, experience, target cities). It then runs automatically and:

| Feature | Description |
|---------|-------------|
| 🔍 **Multi-source search** | Searches Google Jobs (aggregates LinkedIn, Naukri, Indeed) + LinkedIn direct + RemoteOK |
| 🧠 **AI-powered scoring** | Scores each job 0-100 using Google Gemini (free) or Claude AI |
| ✉️ **Auto-draft emails** | Generates personalized recruiter messages for strong matches |
| 📧 **Email alerts** | Sends you notifications with apply links + drafted messages |
| 🌙 **Night hold** | Pauses from 9 PM to 8 AM to save API calls |
| 📊 **CSV tracking** | Tracks all found jobs in a spreadsheet |
| 📋 **Daily summary** | Morning email with stats (jobs found, strong matches) |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Scheduler (every 8 hours)               │
│                  Night hold: 9 PM - 8 AM                 │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
   ┌─────────────┬─────────────┬─────────────┐
   │ Google Jobs │  LinkedIn   │  RemoteOK   │
   │  (SerpAPI)  │ (Guest API) │ (Free API)  │
   │  last 24h   │  last 24h   │  remote     │
   └──────┬──────┴──────┬──────┴──────┬──────┘
          │             │             │
          └─────────────┼─────────────┘
                        ▼
              ┌──────────────────┐
              │   Dedup + Filter  │
              │  (seen_jobs.json) │
              └────────┬─────────┘
                       ▼
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┬────────────┬────────────┐
   │ Gemini AI  │ Claude AI  │  Keyword   │
   │   (FREE)   │  (Paid)    │  (FREE)    │
   │  try 1st   │  try 2nd   │  fallback  │
   └─────┬──────┴─────┬──────┴─────┬──────┘
         │            │            │
         └────────────┼────────────┘
                      ▼
           ┌─────────────────────┐
           │  Score ≥ 50 → Notify │
           │  Score ≥ 60 → Draft  │
           └──────────┬──────────┘
                      ▼
         ┌────────────┼────────────┐
         ▼            ▼            ▼
  ┌─────────────┬─────────────┬─────────────┐
  │ Email Alert │ CSV Tracker │   Daily     │
  │ (immediate) │(job_tracker)│  Summary    │
  └─────────────┴─────────────┴─────────────┘
```

## ⚡ Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/sudarshan-gawande/ai-job-hunting-agent.git
cd ai-job-hunting-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get API keys (10 minutes)

| Key | Required? | Where to get | Cost |
|-----|-----------|-------------|------|
| Gmail App Password | ✅ Yes | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) | Free |
| SerpAPI | ✅ Yes | [serpapi.com](https://serpapi.com) | Free (100/month) |
| Google Gemini | 🔶 Recommended | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free (1000/day) |
| Anthropic Claude | ⬜ Optional | [console.anthropic.com](https://console.anthropic.com) | ~₹0.85/job |

### 4. Set up environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5. Configure your profile

Edit `config.yaml` with your details — name, skills, target cities, target roles.

### 6. Run

```bash
python job_agent.py
```

```
============================================================
  JOB HUNTING AGENT v5.0
  Target:     DevOps Engineer
  Cities:     Pune, Bangalore, Navi Mumbai
  Roles:      DevOps Engineer, Cloud Engineer
  Night hold: 21:00-08:00
  Sources:    Google Jobs, LinkedIn, RemoteOK
  Scoring:    Gemini (FREE) → Keyword (always)
============================================================

  Searching: DevOps Engineer in Pune...
  [Google Jobs] 8 results
  [LinkedIn] 10 results
  Total unique jobs: 15
  NEW [LinkedIn]: DevOps Engineer at CG-VAK Software
    Score: 90/100 (gemini_ai) — Strong Match
    Recruiter message drafted!
...
  Email sent to you@gmail.com
  Notification sent — 7 matches!
```

## 📧 What You Receive

**Job Alert Email (immediately when jobs found):**

```
Subject: Job Alert: 7 Matches — Top: 90/100 at CG-VAK Software

1. DevOps Engineer — CG-VAK, Pune           [90/100] Gemini AI
   Strong Match | AWS, Kubernetes, Terraform
   [Apply Now] [View Recruiter Message]

2. AWS DevOps Engineer — Viraaj HR, Pune     [90/100] Gemini AI
   Strong Match | AWS, Docker, CI/CD
   [Apply Now] [View Recruiter Message]

3. Cloud Engineer — Siemens Energy, Pune     [71/100] Keyword
   Good Match | AWS, Cloud
   [Apply Now]
```

**Daily Summary (every morning at 8 AM):**
```
Jobs today: 12
Strong matches this week: 5
Total tracked: 87
```

## 🌙 Night Hold

The agent pauses from 9 PM to 8 AM. Why? Because companies don't post jobs at 2 AM, and you're not going to apply at 3 AM. This saves ~30% of your API calls.

```yaml
# config.yaml
night_hold:
  enabled: true
  start: "21:00"
  end: "08:00"
```

## 💰 Cost

| Component | Monthly Cost |
|-----------|-------------|
| SerpAPI | Free (100 searches) |
| LinkedIn scraping | Free |
| RemoteOK | Free |
| Google Gemini AI | Free (1000/day) |
| Gmail | Free |
| **Total** | **₹0/month** |

## 🛠️ Tech Stack

- **Python 3.9+** — Core automation
- **Claude AI / Gemini AI** — Job scoring & matching
- **SerpAPI** — Google Jobs search
- **cloudscraper + BeautifulSoup** — LinkedIn scraping
- **Gmail SMTP** — Email notifications
- **schedule** — Cron-like task scheduling
- **YAML** — Configuration management

## 📁 Project Structure

```
ai-job-hunting-agent/
├── job_agent.py          # Main agent script
├── config.yaml           # Your profile & preferences
├── requirements.txt      # Python dependencies
├── .env.example          # API keys template
├── .gitignore
├── LICENSE
├── README.md
├── docs/
│   └── architecture.md   # Detailed architecture docs
├── Dockerfile            # Docker deployment
└── docker-compose.yml    # Docker compose
```

## 🐳 Docker Deployment

```bash
docker-compose up -d     # Start in background
docker-compose logs -f   # View logs
docker-compose down      # Stop
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/add-new-source`)
3. Commit your changes (`git commit -m 'Add Naukri direct API'`)
4. Push to the branch (`git push origin feature/add-new-source`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

## 🙏 Credits

- Built with the help of [Claude AI](https://claude.ai) by Anthropic
- Job scoring powered by [Google Gemini](https://aistudio.google.com)
- Job search via [SerpAPI](https://serpapi.com)

---

**If this helped you, please ⭐ star the repo!**

**Built by [Sudarshan Gawande](https://www.linkedin.com/in/sudarshan-gawande/) — DevOps Engineer | AWS Certified**
