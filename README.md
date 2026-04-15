<h1 align="center">🤖 AI Job Hunting Agent</h1>

<p align="center">
  <strong>A fully automated job search agent that runs 24/7 — finds jobs, scores them with AI, drafts recruiter emails, and sends you alerts. All for ₹0/month.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
  <a href="https://claude.ai"><img src="https://img.shields.io/badge/Built%20with-Claude%20AI-7C3AED" alt="Claude AI"></a>
  <a href="https://aistudio.google.com"><img src="https://img.shields.io/badge/Scoring-Google%20Gemini-4285F4" alt="Gemini"></a>
  <a href="https://hub.docker.com"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-setup-guide">Setup Guide</a> •
  <a href="#-cost-breakdown">Cost</a>
</p>

---

## 🎯 The Problem

Every job seeker spends 3-4 hours daily scrolling through LinkedIn, Naukri, and Indeed — reading hundreds of JDs to find a handful that actually match. Then writing personalized emails to each recruiter. Then losing track of where they applied. Then missing fresh postings because they didn't check in time.

## 💡 The Solution

This agent automates the entire pipeline. You configure it once with your profile, and it runs 24/7:

```
You sleep → Agent searches jobs → AI scores each one → Drafts recruiter emails → Emails you → You just click "Apply"
```

**Your daily effort: ~10 minutes** — just click the apply links and send the pre-drafted messages.

---

## 📸 Screenshots

### Console Output
<p align="center">
  <img src="docs/images/console-log1.png" alt="Console Output Diagram" width="800">
</p>
<p align="center">
  <img src="docs/images/console-log2.png" alt="Console Output Diagram" width="800">
</p>

### Email Alert
<p align="center">
  <img src="docs/images/email1.png" alt="Email Alert Diagram" width="800">
</p>
<p align="center">
  <img src="docs/images/email2.png" alt="Email Alert Diagram" width="800">
</p>

### Job Tracker (CSV)
<p align="center">
  <img src="docs/images/tracker-csv.png" alt="Job Tracker (CSV) Diagram" width="800">
</p>

---

## 🏗️ Architecture

<p align="center">
  <img src="docs/images/job-agent-v2.gif" alt="Architecture Diagram" width="800">
</p>


### Data Flow

1. **Scheduler** triggers every N hours (configurable). Checks if it's night hold time — if yes, skips.
2. **Job Sources** — For each (role × city) combination, the agent queries Google Jobs, LinkedIn, and RemoteOK. All sources filter for last 24 hours.
3. **Deduplication** — Jobs are hashed by (title + company + city). Already-seen jobs from previous cycles are skipped via `seen_jobs.json`.
4. **AI Scoring** — Each new job is scored 0-100. The agent tries Gemini first (free), falls back to Claude (paid), then keyword scoring (always works).
5. **Thresholding** — Only jobs above `min_score_to_notify` are included in alerts. Jobs above `min_score_to_draft` get personalized recruiter emails drafted automatically.
6. **Output** — Email sent immediately with matches + apply links + recruiter messages. All jobs logged to CSV. Daily summary sent every morning.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-source search** | Google Jobs (aggregates LinkedIn, Naukri, Indeed, Glassdoor, 100+ sites) + LinkedIn direct + RemoteOK |
| **AI scoring (0-100)** | Google Gemini (free, 1000/day) → Anthropic Claude (paid, best quality) → Keyword matching (always works) |
| **Auto-draft emails** | Generates personalized recruiter messages for every strong match with your skills, experience, and context |
| **Email alerts** | Immediate Gmail notifications with apply links, scores, and pre-drafted recruiter messages |
| **Night hold** | Configurable quiet hours (default 9PM-8AM) — saves ~30% API calls, no jobs posted at night anyway |
| **Smart dedup** | Never sends the same job twice, even across multiple sources and cycles |
| **CSV tracking** | Every job logged with date, company, city, score, platform, apply link, status |
| **Daily summary** | Morning email with stats: jobs found today, strong matches this week, total tracked |
| **Docker support** | Containerized deployment with auto-restart |
| **Configurable** | YAML config for roles, cities, job types, thresholds, intervals, night hold times |

### How Scoring Works

**With AI (Gemini/Claude):** The AI reads the full job description and understands context — it knows "3-5 years" matches your 3.5 years, recognizes Razorpay as FinTech (your domain), and understands the difference between a mid-level role and a VP position.

**Without AI (Keyword fallback):** Smart keyword matching algorithm scores based on:

| Factor | Max Points | How |
|--------|-----------|-----|
| Title relevance | 20 | Does "DevOps Engineer" appear in the title? |
| Must-have keywords | 20 | DevOps, AWS, Kubernetes found in description? |
| Nice-to-have keywords | 15 | Terraform, Docker, CI/CD, Jenkins, etc. |
| Profile skills match | 15 | Your full skill list vs. JD |
| Experience match | 10 | Does "3-5 years" fit your 3.5 years? |
| Domain match | 10 | FinTech/BFSI keywords in JD? |
| Certification bonus | 5 | AWS Certified mentioned? |
| City match | 5 | Job is in your target city? |
| Exclude penalty | -25 | "VP", "Director", "10+ years" found? |
| Known company bonus | +5 | Razorpay, Google, Microsoft, HSBC, etc. |

---

## 📁 Project Structure

```
ai-job-hunting-agent/
│
├── job_agent.py              # Main agent script (all logic)
├── config.yaml               # Your profile, preferences, thresholds
├── requirements.txt          # Python dependencies
├── .env.example              # API keys template
├── .gitignore                # Files excluded from Git
├── LICENSE                   # MIT License
├── README.md                 # This file
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose for easy deployment
│
├── docs/
│   ├── SETUP_GUIDE.md        # Detailed setup instructions
│   └── images/
│       ├── architecture.png  # Architecture diagram
│       ├── console-output.png# Terminal screenshot
│       ├── email-alert.png   # Gmail screenshot
│       ├── job-tracker.png   # Excel CSV screenshot
│       ├── serpapi-key.png   # SerpAPI dashboard screenshot
│       ├── gemini-key.png    # Google AI Studio screenshot
│       └── gmail-app-pwd.png # Gmail app password screenshot
│
├── seen_jobs.json            # (auto-generated) Already processed jobs
├── job_tracker.csv           # (auto-generated) All tracked jobs
├── email_count.json          # (auto-generated) Daily email counter
└── agent.log                 # (auto-generated) Detailed logs
```

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/sudarshan-gawande/ai-job-hunting-agent.git
cd ai-job-hunting-agent

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env          # Add your API keys
nano config.yaml              # Edit your profile

# 4. Run
python job_agent.py
```

---

## 📖 Setup Guide (Detailed)

### Prerequisites

- Python 3.9 or higher
- A Gmail account with 2FA enabled
- 10 minutes for API key setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/sudarshan-gawande/ai-job-hunting-agent.git
cd ai-job-hunting-agent
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies: `pyyaml`, `requests`, `python-dotenv`, `schedule`, `cloudscraper`, `beautifulsoup4`

### Step 3: Get API Keys

#### 3a. Gmail App Password (REQUIRED)

This lets the agent send you email alerts.

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already on
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Select app: **Mail**, device: **Other** → type "Job Agent"
5. Click **Generate** → Copy the 16-character password

<p align="left">
  <img src="docs/images/gmail-password.png" alt="Email Alert Diagram" width="800">
</p>

#### 3b. SerpAPI Key (REQUIRED)

This powers the Google Jobs search — aggregates LinkedIn, Naukri, Indeed, and 100+ sites.

1. Go to [serpapi.com](https://serpapi.com) → Sign up (free)
2. Go to Dashboard → Copy your **API Key**
<p align="left">
  <img src="docs/images/serpapi-key.png" alt="SerpAPI Key" width="800">
</p>
3. Free plan: 250 searches/month
<p align="left">
  <img src="docs/images/serpapi-key1.png" alt="SerpAPI Key" width="800">
</p>


#### 3c. Google Gemini API Key (RECOMMENDED — Free AI)

This gives your agent AI-powered job scoring for free.

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **"Create API key in new project"**
<p align="left">
  <img src="docs/images/gemini-key.png" alt="Google Gemini API Key" width="800">
</p>
3. Copy the key (starts with `AIza...`)
4. Free: 1,000 requests/day — more than enough

> **Important:** The agent uses `gemini-2.5-flash-lite` model. Do NOT use `gemini-2.0-flash` — it was deprecated in Feb 2026.

#### 3d. Anthropic Claude API Key (OPTIONAL — Paid AI)

Premium AI scoring. Only needed if Gemini quota is insufficient.

1. Go to [console.anthropic.com](https://console.anthropic.com) → Sign up
2. Add $5 minimum credit (~₹420)
3. Go to Settings → API Keys → Create Key
<p align="left">
  <img src="docs/images/claude-api-key.png" alt="Claude API Key" width="800">
</p>
4. Cost: ~₹0.85 per job scored

### Step 4: Set Up Environment Variables

```bash
# Linux/Mac
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env` with your keys:

```dotenv
# REQUIRED
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
SERPAPI_KEY=your_serpapi_key_here

# RECOMMENDED (free AI scoring)
GEMINI_API_KEY=AIzaSy_your_gemini_key_here

# OPTIONAL (paid AI scoring)
ANTHROPIC_API_KEY=sk-ant-your_claude_key_here

# OPTIONAL (Telegram notifications)
TELEGRAM_BOT_TOKEN=
```

### Step 5: Configure Your Profile

Edit `config.yaml`:

```yaml
profile:
  name: "Your Name"
  email: "your-email@gmail.com"
  position: "DevOps Engineer"
  experience_years: 3.5
  skills:
    - AWS
    - Kubernetes
    - Terraform
    - Docker
    # Add your skills...
  certifications:
    - "AWS Certified Cloud Practitioner"
  domain: "FinTech / BFSI"
  current_company: "Your Company"

job_preferences:
  target_roles:
    - "DevOps Engineer"
    - "Cloud Engineer"
    #  Add more but it consume more api call...
  target_cities:
    - "Pune"
    - "Bangalore"
    - "Navi Mumbai"
    #  Add more but it consume more api call...
  job_types:
    - "onsite"
    - "hybrid"
    - "remote"
```

### Step 6: Run the Agent

```bash
python job_agent.py
```

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start in background
docker compose up -d --build

# View logs
docker compose logs -f

# Stop
docker compose down
```
<p align="left">
  <img src="docs/images/docker-compose.png" alt="Docker Compose" width="800">
</p>

### Using Docker Directly

```bash
# Build
docker build -t job-agent .

# Run
docker run -d \
  --name job-hunting-agent \
  --restart always \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/job_tracker.csv:/app/job_tracker.csv \
  -v $(pwd)/seen_jobs.json:/app/seen_jobs.json \
  -e TZ=Asia/Kolkata \
  job-agent
```

---

## ☁️ Deploy on AWS (Free Tier)

Run the agent 24/7 on an AWS EC2 instance (free for 12 months):

### Step 1: Launch EC2 Instance

- AMI: **Amazon Linux 2023** or **Ubuntu 24.04**
- Instance type: **t2.micro** (free tier eligible)
- Storage: 8 GB (default)
- Security group: Allow SSH (port 22)

### Step 2: Connect and Setup

```bash
ssh -i your-key.pem ec2-user@your-ec2-ip

# Install Python
sudo yum install python3 python3-pip -y  # Amazon Linux
# OR
sudo apt install python3 python3-pip -y  # Ubuntu

# Clone repo
git clone https://github.com/sudarshan-gawande/ai-job-hunting-agent.git
cd ai-job-hunting-agent

# Install dependencies
pip3 install -r requirements.txt

# Set up environment
cp .env.example .env
nano .env  # paste your keys

# Edit config
nano config.yaml  # set your profile
```

### Step 3: Run as Background Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/job-agent.service
```

```ini
[Unit]
Description=AI Job Hunting Agent
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/ai-job-hunting-agent
ExecStart=/usr/bin/python3 job_agent.py
Restart=always
RestartSec=30
Environment=TZ=Asia/Kolkata

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable job-agent
sudo systemctl start job-agent
sudo systemctl status job-agent   # verify it's running

# View logs
journalctl -u job-agent -f
```

### AWS Cost

| Component | Cost |
|-----------|------|
| EC2 t2.micro | Free (12 months) |
| EBS 8GB | Free (12 months) |
| Data transfer | Free (up to 100GB/month) |
| **Total** | **₹0 for first year** |

After 12 months: ~₹500-700/month for t2.micro. Alternatively, use a ₹200/month VPS from DigitalOcean or Hetzner.

---

## 💰 Cost Breakdown

### Free Tier (Default)

| Service | Monthly Cost | Daily Limit | What For |
|---------|-------------|-------------|----------|
| SerpAPI | Free | ~3/day (100/month) | Google Jobs search |
| LinkedIn scraping | Free | No limit | Direct LinkedIn results |
| RemoteOK API | Free | No limit | Remote jobs |
| Google Gemini AI | Free | 1,000/day | AI job scoring |
| Gmail SMTP | Free | 500/day | Email notifications |
| **Total** | **₹0/month** | | |

### With Claude AI (Optional Premium)

| Service | Monthly Cost | What For |
|---------|-------------|----------|
| Everything above | ₹0 | Job search + notifications |
| Anthropic Claude | ₹250-500 | Premium AI scoring (~₹0.85/job) |
| **Total** | **~₹250-500/month** | |

### With AWS Hosting (Optional)

| Service | Monthly Cost | What For |
|---------|-------------|----------|
| Everything above | ₹0 | Job search + notifications |
| AWS EC2 t2.micro | ₹0 (year 1) / ₹500 (after) | 24/7 hosting |
| **Total** | **₹0 first year** | |

---

## ⚙️ Configuration Reference

### Automation Settings

```yaml
automation:
  search_interval_hours: 1      # How often to search
  min_score_to_notify: 50       # Jobs included in email (50 = good+ matches)
  min_score_to_draft: 60        # Jobs that get recruiter messages
  min_score_to_auto_send: 999   # 999 = disabled. Set 85+ when confident
  max_emails_per_day: 10        # Safety limit for auto-send
  daily_summary_time: "08:00"   # Morning summary email time

  night_hold:
    enabled: true               # Pause during night
    start: "21:00"              # 9 PM stop
    end: "08:00"                # 8 AM resume
```

### Choosing Your Interval

| Your Setup | Recommended Interval | SerpAPI/month | Lasts |
|------------|---------------------|---------------|-------|
| 1 role, 1 city | 3 hours | 240 | Full month |
| 2 roles, 3 cities | 8 hours | ~180 | ~20 days |
| 3 roles, 6 cities | 12 hours | ~270 | ~28 days |

### How AI Scoring Priority Works

```
Job found → Has description > 50 chars?
                │
                ├── Yes → Try Gemini (free)
                │           │
                │           ├── Success → Use Gemini score ✅
                │           │
                │           └── Failed → Try Claude (paid)
                │                          │
                │                          ├── Success → Use Claude score ✅
                │                          │
                │                          └── Failed → Use Keyword score ✅
                │
                └── No → Use Keyword score directly ✅
```

If you have both Gemini and Claude keys, Gemini is always tried first (saves money). Claude is the fallback. Keywords always work as the final safety net.

---

## 🌙 Night Hold Feature

The agent pauses job searching during configurable night hours. Why?

- Companies don't post jobs at 2 AM
- You're not applying at 3 AM anyway
- Saves ~30% of your monthly API calls
- Agent resumes automatically in the morning

```yaml
night_hold:
  enabled: true
  start: "21:00"    # 9 PM — stop searching
  end: "08:00"      # 8 AM — resume searching
```

When a search cycle triggers during night hold, the agent logs `"Night hold active — skipping"` and waits for the next cycle.

---

## 📧 Email Types

### 1. Job Alert (Immediate)

Sent immediately after every search cycle that finds new matching jobs.

```
Subject: Job Alert: 5 Matches — Top: 90/100 at CG-VAK

1. DevOps Engineer — CG-VAK, Pune               [90/100] Gemini AI
   Strong Match | Matching: AWS, Kubernetes, Terraform
   [Apply Now]
   [View Recruiter Message — ready to copy-paste]

2. AWS DevOps Engineer — Viraaj HR, Pune         [90/100] Gemini AI
   [Apply Now]
   [View Recruiter Message]

3. DevOps Engineer — CloudSmartz, Pune           [57/100] Keyword
   Good Match
   [Apply Now]

Quick Search: Naukri | Indeed | LinkedIn
```


### 2. Daily Summary (Once per day)

Sent at your configured time (default 8 AM). Just stats, no job details.

```
Subject: Daily Summary: 12 today, 3 strong matches

Jobs today: 12
Strong matches this week (70+): 3
Total this week: 34
Total all time: 87
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GMAIL_APP_PASSWORD not set` | Create `.env` file (not just `.env.example`) and add your key |
| `No job sources configured` | Add `SERPAPI_KEY` to `.env` |
| `[Gemini] quota exceeded` | Gemini resets daily. Or create key in new project. |
| `[Claude] No credits` | Add $5 credit at console.anthropic.com or remove the key |
| Email not received | Check spam folder. Verify Gmail App Password. |
| `lxml build failed` | Use `html.parser` instead — change `"lxml"` to `"html.parser"` in code |
| `cloudscraper not found` | Run `pip install cloudscraper` |
| Agent stops when terminal closes | Use Docker, tmux, or systemd service |
| Same jobs appearing | This means `seen_jobs.json` was deleted. Normal — they'll be skipped next cycle. |
| Scores too low | Enable Gemini for AI scoring — keyword scores are lower by design |
| Too many weak matches | Increase `min_score_to_notify` to 50 or 60 in `config.yaml` |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.9+** | Core automation engine |
| **Claude AI** (Anthropic) | Helped design and build the entire project |
| **Google Gemini 2.5** | Free AI-powered job scoring |
| **SerpAPI** | Google Jobs search API |
| **cloudscraper** | Bypass LinkedIn anti-bot protection |
| **BeautifulSoup** | HTML parsing for LinkedIn results |
| **Gmail SMTP** | Email notifications via SSL |
| **schedule** | Cron-like Python task scheduler |
| **PyYAML** | Configuration file parsing |
| **Docker** | Containerized deployment |

---

## 🤝 Contributing

Contributions are welcome! Here are some ideas:

- Add more job sources (Glassdoor API, AngelList, etc.)
- Telegram bot for interactive notifications
- Web dashboard to view tracked jobs
- Resume auto-tailor for each JD
- Interview prep question generator

### How to Contribute

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/add-glassdoor`
3. Commit your changes: `git commit -m 'feat: add Glassdoor job source'`
4. Push to the branch: `git push origin feature/add-glassdoor`
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Claude AI](https://claude.ai)** by Anthropic — Helped design the architecture, write the code, debug issues, and generate documentation. The entire project was built collaboratively with Claude.
- **[Google Gemini](https://aistudio.google.com)** — Free AI scoring engine
- **[SerpAPI](https://serpapi.com)** — Google Jobs search API

---

## ⭐ Star History

If this project helped you, please give it a star! It helps others discover it.

---

<p align="center">
  <strong>Built by <a href="https://www.linkedin.com/in/sudarshan-gawande/">Sudarshan Gawande</a></strong><br>
  DevOps Engineer | 3.5+ years at NSE | AWS Certified<br><br>
  <a href="https://www.linkedin.com/in/sudarshan-gawande/">LinkedIn</a> •
  <a href="https://github.com/sudarshan-gawande">GitHub</a> •
  <a href="https://sudarshangawande.com">Portfolio</a>
</p>
