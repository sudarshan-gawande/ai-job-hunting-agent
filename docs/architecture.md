# Architecture & Technical Documentation

## Overview

The AI Job Hunting Agent is a single-file Python automation agent (`job_agent.py`) designed for simplicity and zero-cost operation. It runs as a scheduled loop — every 8 hours — fetching fresh jobs from multiple sources, scoring them with AI, and delivering alerts directly to your inbox.

## System Flow

```
Start
  │
  ▼
Load config.yaml → Load .env API keys
  │
  ▼
is_night_hold()? ──Yes──► Sleep, log "night hold active"
  │ No
  ▼
For each (role, city) in cross-product:
  │
  ├──► search_serpapi(role, city)       Google Jobs via SerpAPI
  ├──► search_linkedin(role, city)      LinkedIn guest API
  └──► search_remoteok()                RemoteOK free API
  │
  ▼
Merge + deduplicate (MD5 hash: title+company+city)
Filter out seen_jobs.json entries
  │
  ▼
For each NEW job:
  │
  ├──► score_job(job)
  │      ├── try Gemini AI (1000/day FREE)
  │      ├── try Claude AI (fallback, paid)
  │      └── keyword_score() (always works)
  │
  ├──► if score ≥ 60: generate_recruiter_message(job)
  ├──► add_to_tracker(job)          → job_tracker.csv
  └──► append to seen_jobs.json
  │
  ▼
if any matches with score ≥ 50:
  └──► send_job_notification(matches)  → Gmail SMTP

schedule.every(8h).do(run_job_search)
schedule.every().day.at("08:00").do(send_daily_summary)
```

## Source Modules

### Source 1: Google Jobs (SerpAPI)

**Function:** `search_serpapi(role, city, max_results=10)`

Uses SerpAPI's `google_jobs` engine with `chips: date_posted:today` to fetch only fresh listings. This is the most reliable source as Google aggregates from Naukri, LinkedIn, Indeed, company career pages, and more.

- **API:** `https://serpapi.com/search.json`
- **Cost:** Free (100 searches/month)
- **Returns:** title, company, location, description, apply_link, posted_at, schedule_type

### Source 2: LinkedIn (Guest API)

**Function:** `search_linkedin(role, city, max_results=10)`

Uses `cloudscraper` to bypass LinkedIn's bot detection, then parses the guest job search endpoint. No LinkedIn account or login required.

- **API:** `https://www.linkedin.com/jobs/search/`
- **Cost:** Free
- **Library:** `cloudscraper` + `BeautifulSoup4`

### Source 3: RemoteOK

**Function:** `search_remoteok()`

Fetches from RemoteOK's public JSON API. Only runs if `remote` is in `job_types` in config. Good for finding remote-friendly international roles.

- **API:** `https://remoteok.com/api`
- **Cost:** Free (no key needed)

## AI Scoring

### Gemini AI Scorer

**Model:** `gemini-2.0-flash-lite` (free, 1000 requests/day)

Sends a structured prompt with the job description and candidate profile. Expects JSON response with:
```json
{
  "score": 85,
  "verdict": "Strong Match",
  "matching_keywords": ["AWS", "Kubernetes"],
  "reason": "Candidate's 3.5yr NSE experience with AWS and Kubernetes directly matches..."
}
```

### Claude AI Scorer

**Model:** `claude-3-haiku-20240307` (paid, ~$0.01/job)

Same prompt structure as Gemini. Used as fallback when Gemini quota is exhausted.

### Keyword Scorer

No API required. Pure Python logic:
- `must_have_keywords` match: +20 each
- `nice_to_have_keywords` match: +5 each  
- `exclude_keywords` match: -50 (immediate disqualification path)
- Experience in-range: +10

## Deduplication

**File:** `seen_jobs.json`

Each job generates a hash: `MD5(title.lower() + company.lower() + city.lower())[:12]`

Before processing any job, the agent checks this dictionary. If the hash exists → skip. After processing → store with metadata (score, date, method, platform).

This means the same DevOps Engineer role at CG-VAK in Pune will never be scored or emailed twice, even across separate agent runs or Docker restarts.

## Email System

**Library:** `smtplib` (Python stdlib, no external dependency)

The agent connects to `smtp.gmail.com:587` with STARTTLS and your Gmail App Password.

### Email Rate Limiting

`email_count.json` tracks emails sent per day. When `max_emails_per_day` is reached, notifications are suppressed until the next calendar day.

### HTML Email Builder

`build_job_alert_html(matches)` generates a rich HTML email with:
- Score badge (green/amber/gray based on threshold)
- Platform badge (Google Jobs / LinkedIn / RemoteOK)
- Posted time
- Matching keyword chips
- AI reasoning text
- Apply Now button
- Expandable recruiter message (`<details>` element)

## Scheduling

**Library:** `schedule` (pip install schedule)

```python
schedule.every(8).hours.do(run_job_search)
schedule.every().day.at("08:00").do(send_daily_summary)

while True:
    schedule.run_pending()
    time.sleep(60)
```

The main loop checks every 60 seconds for pending jobs. This is blocking — use Docker or `nohup` for background execution.

## Night Hold Logic

```python
def is_night_hold():
    now = datetime.now()
    current = now.hour * 60 + now.minute
    start = 21 * 60   # 9 PM
    end   = 8 * 60    # 8 AM
    # Overnight range: current >= 21:00 OR current < 8:00
    return current >= start or current < end
```

When active, `run_job_search()` returns immediately without any API calls.

## Data Files

| File | Format | Purpose | Auto-created |
|------|--------|---------|-------------|
| `seen_jobs.json` | JSON dict | Dedup store | Yes |
| `job_tracker.csv` | CSV | Full job history | Yes |
| `email_count.json` | JSON | Daily email counter | Yes |
| `agent.log` | Plain text | Structured log | Yes |

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GMAIL_APP_PASSWORD` | Yes | Gmail SMTP authentication |
| `SERPAPI_KEY` | Yes | Google Jobs search |
| `GEMINI_API_KEY` | Recommended | Free AI scoring |
| `ANTHROPIC_API_KEY` | Optional | Fallback AI scoring |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram notifications |

## Docker Configuration

The `docker-compose.yml` mounts data files as volumes so they persist across container restarts:

```yaml
volumes:
  - ./config.yaml:/app/config.yaml      # Read config from host
  - ./data:/app/data                     # Data directory
  - ./job_tracker.csv:/app/job_tracker.csv
  - ./seen_jobs.json:/app/seen_jobs.json
  - ./agent.log:/app/agent.log
```

`TZ=Asia/Kolkata` ensures night hold timing uses IST, not UTC.
