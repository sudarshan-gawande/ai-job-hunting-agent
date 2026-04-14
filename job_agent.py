#!/usr/bin/env python3
"""
JOB HUNTING AGENT v5.0 — Production Ready
==========================================
Sources:
  1. Google Jobs (SerpAPI)  — aggregates LinkedIn, Naukri, Indeed, etc.
  2. LinkedIn (guest API)   — direct LinkedIn scraping via cloudscraper
  3. RemoteOK (free API)    — remote jobs (if enabled in config)

AI Scoring (priority order):
  1. Google Gemini 2.5 Flash-Lite (FREE — 1000 req/day)
  2. Anthropic Claude (paid — ~$0.01/job)
  3. Keyword scoring (always works, no API needed)

Features:
  - Night hold: pauses from 9PM to 8AM (saves API calls)
  - Smart dedup: never processes same job twice
  - Auto-draft recruiter messages for good matches
  - Email alerts with apply links immediately when jobs found
  - Daily summary email every morning
  - All jobs tracked in CSV file

Install:  pip install -r requirements.txt
Run:      python job_agent.py
"""

import os, re, csv, json, time, yaml, hashlib, smtplib, logging, requests, schedule, sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("JobAgent")


# ─── Load Config ─────────────────────────────────────────────
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CONFIG  = load_config()
PROFILE = CONFIG["profile"]
PREFS   = CONFIG["job_preferences"]
AUTO    = CONFIG["automation"]
NOTIF   = CONFIG["notifications"]

# API Keys
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
SERPAPI_KEY         = os.getenv("SERPAPI_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

CLAUDE_AVAILABLE = bool(ANTHROPIC_API_KEY)
GEMINI_AVAILABLE = bool(GEMINI_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
}

TRACKER_FILE     = "job_tracker.csv"
SEEN_FILE        = "seen_jobs.json"
EMAIL_COUNT_FILE = "email_count.json"


# ─── Night Hold Check ────────────────────────────────────────
def is_night_hold():
    """Returns True if current time is within night hold period (skip searching)."""
    hold = AUTO.get("night_hold", {})
    if not hold.get("enabled", False):
        return False
    now = datetime.now()
    start_h, start_m = map(int, hold.get("start", "21:00").split(":"))
    end_h, end_m     = map(int, hold.get("end", "08:00").split(":"))
    current = now.hour * 60 + now.minute
    start   = start_h * 60 + start_m
    end     = end_h * 60 + end_m
    if start > end:  # overnight (e.g., 21:00 to 08:00)
        return current >= start or current < end
    else:
        return start <= current < end


# ─── Tracker Files ───────────────────────────────────────────
def init_tracker():
    if not Path(TRACKER_FILE).exists():
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "Date", "Job Title", "Company", "City", "Platform",
                "Score", "Score Method", "Status", "Apply Link",
                "Job Type", "Posted", "Notes"
            ])

def load_seen_jobs():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_seen_jobs(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)

def add_to_tracker(d):
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            d.get("title",""), d.get("company",""), d.get("city",""),
            d.get("platform",""), d.get("score",""), d.get("score_method","keyword"),
            d.get("status","Found"), d.get("link",""),
            d.get("job_type",""), d.get("posted",""), d.get("notes",""),
        ])

def get_emails_sent_today():
    today = datetime.now().strftime("%Y-%m-%d")
    if Path(EMAIL_COUNT_FILE).exists():
        with open(EMAIL_COUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("date") == today:
                return data.get("count", 0)
    return 0

def increment_email_count():
    today = datetime.now().strftime("%Y-%m-%d")
    count = get_emails_sent_today() + 1
    with open(EMAIL_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": today, "count": count}, f)


# ══════════════════════════════════════════════════════════════
# SOURCE 1: Google Jobs via SerpAPI
# ══════════════════════════════════════════════════════════════
def search_serpapi(role, city, max_results=10):
    """Best source — aggregates LinkedIn, Naukri, Indeed, company pages, etc."""
    if not SERPAPI_KEY:
        return []
    jobs = []
    try:
        resp = requests.get("https://serpapi.com/search.json", params={
            "engine": "google_jobs",
            "q": f"{role} {city} India",
            "api_key": SERPAPI_KEY,
            "num": max_results,
            "chips": "date_posted:today",
        }, timeout=30)
        data = resp.json()
        for item in data.get("jobs_results", [])[:max_results]:
            apply_link = ""
            opts = item.get("apply_options", [])
            if opts:
                apply_link = opts[0].get("link", "")
            ext = item.get("detected_extensions", {})
            jobs.append({
                "title":       item.get("title", ""),
                "company":     item.get("company_name", ""),
                "city":        item.get("location", city),
                "description": item.get("description", "")[:3000],
                "link":        apply_link,
                "platform":    "Google Jobs",
                "posted":      ext.get("posted_at", ""),
                "job_type":    ext.get("schedule_type", ""),
            })
        log.info(f"  [Google Jobs] {len(jobs)} results")
    except Exception as e:
        log.error(f"  [Google Jobs] Error: {e}")
    return jobs


# ══════════════════════════════════════════════════════════════
# SOURCE 2: LinkedIn (guest API — no login needed)
# ══════════════════════════════════════════════════════════════
def search_linkedin(role, city, max_results=10):
    """LinkedIn public guest API via cloudscraper."""
    jobs = []
    try:
        try:
            import cloudscraper
            session = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False}
            )
        except ImportError:
            log.warning("  [LinkedIn] cloudscraper not installed. Run: pip install cloudscraper")
            session = requests.Session()

        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={requests.utils.quote(role)}"
            f"&location={requests.utils.quote(city + ', India')}"
            f"&f_TPR=r86400"
            f"&start=0"
        )
        resp = session.get(url, headers={**HEADERS, "Referer": "https://www.linkedin.com/"}, timeout=20)
        if resp.status_code != 200:
            log.warning(f"  [LinkedIn] HTTP {resp.status_code}")
            return jobs

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("li")[:max_results]:
            try:
                title_el   = card.select_one("h3.base-search-card__title")
                company_el = card.select_one("h4.base-search-card__subtitle")
                loc_el     = card.select_one("span.job-search-card__location")
                link_el    = card.select_one("a.base-card__full-link")
                date_el    = card.select_one("time")

                title   = title_el.get_text(strip=True)   if title_el   else ""
                company = company_el.get_text(strip=True) if company_el else ""
                loc     = loc_el.get_text(strip=True)     if loc_el     else city
                link    = link_el.get("href", "")         if link_el    else ""
                posted  = date_el.get("datetime", "")     if date_el    else ""

                if title and company:
                    jobs.append({
                        "title":       title,
                        "company":     company,
                        "city":        loc,
                        "description": f"{role} at {company} in {loc}",
                        "link":        link.split("?")[0],
                        "platform":    "LinkedIn",
                        "posted":      posted,
                        "job_type":    "",
                    })
            except Exception:
                continue
        log.info(f"  [LinkedIn] {len(jobs)} results for {role} in {city}")
    except Exception as e:
        log.error(f"  [LinkedIn] Error: {e}")
    return jobs


# ══════════════════════════════════════════════════════════════
# SOURCE 3: RemoteOK (free API, remote jobs)
# ══════════════════════════════════════════════════════════════
def search_remoteok(role, max_results=5):
    """Free API — remote jobs worldwide."""
    jobs = []
    try:
        resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return jobs
        keywords = [role.lower(), "devops", "sre", "cloud", "kubernetes",
                    "aws", "infrastructure", "platform engineer"]
        for item in resp.json()[1:]:
            text = (item.get("position","") + " " + " ".join(item.get("tags", []))).lower()
            if any(kw in text for kw in keywords):
                jobs.append({
                    "title":       item.get("position", ""),
                    "company":     item.get("company", ""),
                    "city":        "Remote",
                    "description": item.get("description", "")[:2000],
                    "link":        item.get("url", ""),
                    "platform":    "RemoteOK",
                    "posted":      item.get("date", "")[:10],
                    "job_type":    "Remote",
                })
            if len(jobs) >= max_results:
                break
        log.info(f"  [RemoteOK] {len(jobs)} results")
    except Exception as e:
        log.error(f"  [RemoteOK] Error: {e}")
    return jobs


# ══════════════════════════════════════════════════════════════
# Aggregate All Sources + Dedup
# ══════════════════════════════════════════════════════════════
def search_all_sources(role, city, max_results=10):
    all_jobs = []

    # Source 1: Google Jobs (aggregates Naukri, Indeed, LinkedIn, company pages)
    all_jobs.extend(search_serpapi(role, city, max_results))
    time.sleep(1)

    # Source 2: LinkedIn direct (finds jobs Google might miss)
    all_jobs.extend(search_linkedin(role, city, max_results))
    time.sleep(2)

    # Source 3: RemoteOK (only if remote is enabled)
    if "remote" in [t.lower() for t in PREFS.get("job_types", [])]:
        all_jobs.extend(search_remoteok(role, 5))
        time.sleep(1)

    # Deduplicate
    seen_keys = set()
    unique = []
    for job in all_jobs:
        key = f"{job.get('title','').lower().strip()}-{job.get('company','').lower().strip()}"
        if key not in seen_keys and job.get("title") and job.get("company"):
            seen_keys.add(key)
            unique.append(job)

    log.info(f"  Total unique jobs: {len(unique)}")
    return unique


# ══════════════════════════════════════════════════════════════
# KEYWORD SCORING (always free)
# ══════════════════════════════════════════════════════════════
def score_job_keywords(job):
    title = job.get("title", "").lower()
    desc  = job.get("description", "").lower()
    full  = title + " " + desc + " " + job.get("company", "").lower()

    score = 0
    matching, missing, reasons = [], [], []

    # Title relevance (0-20)
    target_role = PROFILE["position"].lower()
    role_words = [w for w in target_role.split() if len(w) > 2]
    role_match = sum(1 for w in role_words if w in title)
    score += int((role_match / max(len(role_words), 1)) * 20)
    if role_match >= len(role_words) - 1:
        reasons.append("Job title matches target role")

    # Must-have keywords (0-20)
    must_have = PREFS.get("must_have_keywords", [])
    for kw in must_have:
        (matching if kw.lower() in full else missing).append(kw)
    if must_have:
        score += int((len([k for k in must_have if k.lower() in full]) / len(must_have)) * 20)

    # Nice-to-have keywords (0-15)
    nice = PREFS.get("nice_to_have_keywords", [])
    nice_found = [kw for kw in nice if kw.lower() in full]
    for kw in nice_found:
        matching.append(kw)
    for kw in nice:
        if kw.lower() not in full:
            missing.append(kw)
    if nice:
        score += int((len(nice_found) / len(nice)) * 15)

    # Profile skills (0-15)
    skills = [s.lower() for s in PROFILE.get("skills", [])]
    sk_found = [s for s in skills if s in full]
    for s in sk_found:
        if s.title() not in matching:
            matching.append(s.title())
    if skills:
        score += int((len(sk_found) / len(skills)) * 15)

    # Experience match (0-10)
    exp = PROFILE.get("experience_years", 3)
    m = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*(?:years|yrs)', full)
    if m:
        rmin, rmax = int(m.group(1)), int(m.group(2))
        if rmin <= exp <= rmax:
            score += 10
            reasons.append(f"Exp {rmin}-{rmax} yrs fits your {exp}")
        elif abs(exp - rmin) <= 1:
            score += 6
        elif rmin > exp + 3:
            score -= 10
            reasons.append(f"Requires {rmin}+ yrs")
    else:
        m2 = re.search(r'(\d+)\+?\s*(?:years|yrs)', full)
        if m2:
            rmin = int(m2.group(1))
            if abs(rmin - exp) <= 2:
                score += 8
            elif rmin > exp + 3:
                score -= 10
                reasons.append(f"Requires {rmin}+ yrs")
        else:
            score += 5

    # Domain match (0-10)
    domain_kws = ["fintech","bfsi","banking","finance","stock","exchange",
                  "trading","nse","financial","insurance","payments"]
    if any(dk in full for dk in domain_kws):
        score += 10
        reasons.append("FinTech/BFSI domain")

    # Certification (0-5)
    for cert in PROFILE.get("certifications", []):
        if any(w in full for w in cert.lower().split() if len(w) > 3):
            score += 5
            matching.append(cert)
            break

    # City match (0-5)
    job_city = job.get("city", "").lower()
    if any(c.lower() in job_city for c in PREFS.get("target_cities", [])):
        score += 5

    # Exclude penalty
    for kw in PREFS.get("exclude_keywords", []):
        if kw.lower() in full:
            score -= 25
            reasons.append(f"Excluded: '{kw}'")

    # Known company bonus
    top_cos = ["razorpay","phonepe","cred","groww","zerodha","paytm","flipkart",
               "google","microsoft","amazon","oracle","sap","vmware","redhat",
               "hsbc","jp morgan","goldman","morgan stanley","blackrock",
               "deutsche bank","barclays","citibank"]
    if any(tc in job.get("company","").lower() for tc in top_cos):
        score += 5
        reasons.append("Well-known company")

    score = max(0, min(100, score))
    verdict = ("Strong Match" if score >= 70 else "Good Match" if score >= 55
               else "Moderate Match" if score >= 35 else "Weak Match")

    return {
        "score": score, "verdict": verdict,
        "matching_skills": list(dict.fromkeys(matching))[:10],
        "missing_skills": list(dict.fromkeys(missing))[:5],
        "reason": "; ".join(reasons[:3]) or "Keyword scoring",
        "should_apply": score >= AUTO.get("min_score_to_notify", 50),
        "priority": "high" if score >= 70 else "medium" if score >= 50 else "low",
        "method": "keyword",
    }


# ══════════════════════════════════════════════════════════════
# AI SCORING: Google Gemini (FREE)
# ══════════════════════════════════════════════════════════════
def score_job_gemini(job):
    global GEMINI_AVAILABLE
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return None
    try:
        prompt = (
            f"You are a job matching expert. Score candidate-job fit.\n"
            f"Respond ONLY as JSON (no markdown, no explanation): "
            f'{{"score":<0-100>,"verdict":"<Strong Match|Good Match|Moderate Match|Weak Match>",'
            f'"matching_skills":["..."],"missing_skills":["..."],'
            f'"reason":"<1-2 sentences>","should_apply":<true|false>}}\n\n'
            f"CANDIDATE: {PROFILE['name']}, {PROFILE['experience_years']} yrs, "
            f"Skills: {', '.join(PROFILE['skills'][:8])}, "
            f"Certs: {', '.join(PROFILE['certifications'])}, "
            f"Domain: {PROFILE['domain']}\n\n"
            f"JOB: {job.get('title','')} at {job.get('company','')} in {job.get('city','')}\n"
            f"Description: {job.get('description','')[:1500]}"
        )
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            err = data["error"].get("message", "")
            log.warning(f"  [Gemini] {err[:100]}")
            if "quota" in err.lower() or "limit" in err.lower():
                GEMINI_AVAILABLE = False
            return None

        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
        result["method"] = "gemini_ai"
        result["priority"] = "high" if result.get("score",0) >= 70 else "medium" if result.get("score",0) >= 50 else "low"
        return result
    except json.JSONDecodeError:
        log.warning("  [Gemini] Bad JSON response")
    except Exception as e:
        log.error(f"  [Gemini] Error: {e}")
    return None


# ══════════════════════════════════════════════════════════════
# AI SCORING: Anthropic Claude (paid)
# ══════════════════════════════════════════════════════════════
def score_job_claude(job):
    global CLAUDE_AVAILABLE
    if not ANTHROPIC_API_KEY or not CLAUDE_AVAILABLE:
        return None
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "system": (
                    "Score candidate-job fit. Respond ONLY as JSON:\n"
                    '{"score":<0-100>,"verdict":"<Strong Match|Good Match|Moderate Match|Weak Match>",'
                    '"matching_skills":["..."],"missing_skills":["..."],'
                    '"reason":"<1-2 sentences>","should_apply":<true|false>,"priority":"<high|medium|low>"}'
                ),
                "messages": [{"role": "user", "content": (
                    f"CANDIDATE: {PROFILE['name']}, {PROFILE['experience_years']} yrs, "
                    f"Skills: {', '.join(PROFILE['skills'])}, "
                    f"Certs: {', '.join(PROFILE['certifications'])}, Domain: {PROFILE['domain']}\n\n"
                    f"JOB: {job.get('title')} at {job.get('company')} in {job.get('city')}\n"
                    f"Description: {job.get('description','')[:2000]}"
                )}],
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            msg = data["error"].get("message", "")
            if "credit" in msg.lower() or "balance" in msg.lower():
                log.warning("  [Claude] No credits — disabled.")
                CLAUDE_AVAILABLE = False
            return None
        if data.get("content"):
            text = data["content"][0]["text"].strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(text)
            result["method"] = "claude_ai"
            return result
    except json.JSONDecodeError:
        log.warning("  [Claude] Bad JSON response")
    except Exception as e:
        log.error(f"  [Claude] Error: {e}")
    return None


# ══════════════════════════════════════════════════════════════
# SCORE JOB: Gemini (free) → Claude (paid) → Keywords (always)
# ══════════════════════════════════════════════════════════════
def score_job(job):
    if job.get("description") and len(job["description"]) > 50:
        result = score_job_gemini(job)
        if result:
            return result
        result = score_job_claude(job)
        if result:
            return result
    return score_job_keywords(job)


# ══════════════════════════════════════════════════════════════
# RECRUITER MESSAGE TEMPLATE
# ══════════════════════════════════════════════════════════════
def generate_recruiter_message(job, score_data):
    name     = PROFILE["name"]
    exp      = PROFILE["experience_years"]
    company  = PROFILE.get("current_company", "")
    skills   = ", ".join(PROFILE["skills"][:5])
    certs    = ", ".join(PROFILE["certifications"])
    matching = ", ".join(score_data.get("matching_skills", [])[:4]) or skills
    title    = job.get("title", "DevOps Engineer")
    jco      = job.get("company", "your organization")
    city     = job.get("city", "")
    sig      = CONFIG.get("email_settings", {}).get("signature", f"Best regards,\n{name}")

    subject = f"Application for {title} — {name} | {exp}+ Yrs DevOps | {certs}"
    body = f"""Dear Hiring Team,

I came across the {title} position at {jco}{f' in {city}' if city else ''} and I am very interested.

I am a DevOps Engineer with {exp}+ years at {company}, specializing in {skills}. My FinTech/BFSI background at NSE gives me production-grade experience with cloud infrastructure, Kubernetes orchestration, and CI/CD automation at scale.

Key qualifications for this role:
- Relevant skills: {matching}
- Certification: {certs}
- Production deployments in regulated financial environments

I would welcome a conversation about how my background fits your team. Happy to share my resume if this seems like a good fit.

{sig}"""
    return f"SUBJECT: {subject}\n\nBODY:\n{body}"


# ══════════════════════════════════════════════════════════════
# EMAIL / NOTIFICATIONS
# ══════════════════════════════════════════════════════════════
def send_email(to_email, subject, body_html):
    if not GMAIL_APP_PASSWORD:
        log.error("GMAIL_APP_PASSWORD not set!")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = PROFILE["email"]
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(PROFILE["email"], GMAIL_APP_PASSWORD)
            server.sendmail(PROFILE["email"], to_email, msg.as_string())
        log.info(f"  Email sent to {to_email}")
        return True
    except Exception as e:
        log.error(f"  Email failed: {e}")
        return False

def send_notification(subject, body_html):
    if NOTIF.get("email", {}).get("enabled", True):
        send_email(NOTIF["email"]["send_to"], subject, body_html)
    if NOTIF.get("telegram", {}).get("enabled") and TELEGRAM_BOT_TOKEN:
        try:
            token   = NOTIF["telegram"].get("bot_token", TELEGRAM_BOT_TOKEN)
            chat_id = NOTIF["telegram"].get("chat_id", "")
            if token and chat_id:
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              json={"chat_id": chat_id, "text": subject[:4000], "parse_mode": "HTML"}, timeout=10)
        except Exception:
            pass

def send_job_notification(matches):
    matches.sort(key=lambda x: x.get("score", 0), reverse=True)
    platforms = {}
    for j in matches:
        p = j.get("platform", "?")
        platforms[p] = platforms.get(p, 0) + 1
    plat_str = " | ".join(f"{p}: {n}" for p, n in platforms.items())

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;padding:20px;background:#f9fafb;">
<div style="background:white;border-radius:12px;padding:24px;border:1px solid #e5e7eb;">
  <h2 style="color:#111;margin-top:0;">Job Alert — {len(matches)} Match{'es' if len(matches)!=1 else ''}</h2>
  <p style="color:#666;font-size:13px;">{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  <p style="color:#999;font-size:12px;">Sources: {plat_str}</p>
"""
    for i, job in enumerate(matches, 1):
        score  = job.get("score", 0)
        sd     = job.get("score_data", {})
        color  = "#16a34a" if score >= 70 else "#ca8a04" if score >= 50 else "#dc2626"
        bcolor = "#bbf7d0" if score >= 70 else "#fef08a" if score >= 50 else "#fecaca"
        matching = ", ".join(sd.get("matching_skills", [])[:5])
        method = sd.get("method", "keyword")
        m_label = {"gemini_ai": "Gemini AI", "claude_ai": "Claude AI"}.get(method, "Keyword")

        html += f"""
  <div style="border:1px solid {bcolor};border-left:4px solid {color};border-radius:8px;padding:14px;margin:10px 0;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
      <div style="flex:1;">
        <h3 style="margin:0 0 3px;color:#111;font-size:15px;">{i}. {job.get('title','')}</h3>
        <p style="margin:0;font-size:13px;color:#555;">
          {job.get('company','')} &bull; {job.get('city','')}
          &bull; <span style="background:#e0f2fe;color:#0369a1;padding:1px 6px;border-radius:4px;font-size:11px;">{job.get('platform','')}</span>
          {f'&bull; <span style="color:#888;font-size:11px;">{job.get("posted","")}</span>' if job.get("posted") else ''}
        </p>
      </div>
      <div style="text-align:right;margin-left:10px;">
        <div style="background:{color};color:white;padding:3px 10px;border-radius:20px;font-size:14px;font-weight:bold;">{score}/100</div>
        <div style="font-size:10px;color:#999;margin-top:2px;">{m_label}</div>
      </div>
    </div>
    {f'<p style="font-size:12px;color:#555;margin:8px 0 2px;"><strong>Matching:</strong> {matching}</p>' if matching else ''}
    {f'<p style="font-size:12px;color:#777;margin:2px 0;">{sd.get("reason","")}</p>' if sd.get("reason") else ''}
"""
        if job.get("link"):
            html += f'<a href="{job["link"]}" style="display:inline-block;background:#2563eb;color:white;padding:6px 16px;border-radius:6px;text-decoration:none;font-size:13px;margin-top:8px;">Apply Now</a>\n'
        if job.get("drafted_message"):
            msg_html = (job["drafted_message"].replace("\n","<br>")
                        .replace("SUBJECT:","<strong>Subject:</strong>")
                        .replace("BODY:","<br><strong>Message:</strong>"))
            html += f"""
    <details style="margin-top:10px;">
      <summary style="cursor:pointer;color:#2563eb;font-size:13px;font-weight:500;">View recruiter message</summary>
      <div style="background:#f8fafc;padding:12px;border-radius:6px;margin-top:6px;font-size:13px;line-height:1.7;color:#333;border:1px solid #e2e8f0;">{msg_html}</div>
    </details>
"""
        html += "</div>"

    role_q = requests.utils.quote(PROFILE["position"])
    slug   = PROFILE["position"].lower().replace(" ", "-")
    html += f"""
  <div style="margin-top:18px;padding:12px;background:#f0f9ff;border-radius:8px;">
    <h4 style="margin:0 0 6px;color:#0c4a6e;font-size:13px;">Search directly</h4>
    <p style="margin:2px 0;font-size:12px;">
      <a href="https://www.naukri.com/{slug}-jobs?jobAge=1" style="color:#2563eb;">Naukri</a> &bull;
      <a href="https://in.indeed.com/jobs?q={role_q}&fromage=1" style="color:#2563eb;">Indeed</a> &bull;
      <a href="https://www.linkedin.com/jobs/search/?keywords={role_q}&location=India&f_TPR=r86400" style="color:#2563eb;">LinkedIn</a>
    </p>
  </div>
  <p style="color:#9ca3af;font-size:11px;text-align:center;margin-top:16px;">
    Job Agent v5 &bull; Every {AUTO['search_interval_hours']} hrs &bull; {datetime.now().strftime('%I:%M %p')}
  </p>
</div></body></html>
"""
    top = matches[0]
    send_notification(
        f"Job Alert: {len(matches)} Match{'es' if len(matches)!=1 else ''} — Top: {top.get('score',0)}/100 at {top.get('company','?')}",
        html
    )
    log.info(f"  Notification sent — {len(matches)} matches!")


def send_daily_summary():
    log.info("Sending daily summary...")
    seen = load_seen_jobs()
    today = datetime.now().strftime("%Y-%m-%d")
    today_j = [v for v in seen.values() if v.get("date","").startswith(today)]
    week_j  = [v for v in seen.values() if v.get("date","") >= (datetime.now()-timedelta(days=7)).isoformat()]
    strong  = [j for j in week_j if j.get("score",0) >= 70]
    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<div style="background:white;border-radius:12px;padding:24px;border:1px solid #e5e7eb;">
<h2 style="margin-top:0;">Daily Summary — {datetime.now().strftime('%A, %B %d')}</h2>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
  <tr><td style="padding:8px;border-bottom:1px solid #f3f4f6;">Jobs today</td>
      <td style="padding:8px;text-align:right;font-weight:bold;">{len(today_j)}</td></tr>
  <tr><td style="padding:8px;border-bottom:1px solid #f3f4f6;">Strong matches this week (70+)</td>
      <td style="padding:8px;text-align:right;font-weight:bold;color:#16a34a;">{len(strong)}</td></tr>
  <tr><td style="padding:8px;border-bottom:1px solid #f3f4f6;">Total this week</td>
      <td style="padding:8px;text-align:right;font-weight:bold;">{len(week_j)}</td></tr>
  <tr><td style="padding:8px;">Total all time</td>
      <td style="padding:8px;text-align:right;font-weight:bold;">{len(seen)}</td></tr>
</table></div></body></html>"""
    send_notification(f"Daily Summary: {len(today_j)} today, {len(strong)} strong", html)


# ══════════════════════════════════════════════════════════════
# CORE AGENT LOOP
# ══════════════════════════════════════════════════════════════
def generate_job_id(job):
    key = f"{job.get('title','')}-{job.get('company','')}-{job.get('city','')}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()[:12]

def run_job_search():
    # Night hold check
    if is_night_hold():
        log.info("Night hold active — skipping this cycle. Will resume in the morning.")
        return []

    log.info("=" * 60)
    log.info("STARTING JOB SEARCH CYCLE")
    log.info(f"  Time: {datetime.now().strftime('%I:%M %p')}")
    log.info("=" * 60)

    seen = load_seen_jobs()
    all_matches = []

    for role in PREFS["target_roles"]:
        for city in PREFS["target_cities"]:
            log.info(f"\n  Searching: {role} in {city}...")
            jobs = search_all_sources(role, city)

            for job in jobs:
                job_id = generate_job_id(job)
                if job_id in seen:
                    continue

                log.info(f"  NEW [{job.get('platform','?')}]: {job['title']} at {job.get('company','?')}")

                score_data = score_job(job)
                score  = score_data.get("score", 0)
                method = score_data.get("method", "keyword")

                log.info(f"    Score: {score}/100 ({method}) — {score_data.get('verdict','?')}")

                seen[job_id] = {
                    "title": job["title"], "company": job.get("company",""),
                    "city": job.get("city",""), "score": score,
                    "date": datetime.now().isoformat(),
                    "method": method, "platform": job.get("platform",""),
                }

                drafted = None
                if score >= AUTO.get("min_score_to_draft", 60):
                    drafted = generate_recruiter_message(job, score_data)
                    log.info("    Recruiter message drafted!")

                if score >= AUTO.get("min_score_to_notify", 50):
                    all_matches.append({
                        **job, "score": score,
                        "score_data": score_data,
                        "drafted_message": drafted,
                    })

                add_to_tracker({
                    "title": job["title"], "company": job.get("company",""),
                    "city": job.get("city",""), "platform": job.get("platform",""),
                    "score": score, "score_method": method,
                    "status": "Strong Match" if score >= 70 else "Good Match" if score >= 50 else "Found",
                    "link": job.get("link",""), "job_type": job.get("job_type",""),
                    "posted": job.get("posted",""),
                })
                time.sleep(0.5)

    save_seen_jobs(seen)

    if all_matches:
        send_job_notification(all_matches)
    else:
        log.info("  No new matching jobs this cycle.")

    log.info(f"\n  Cycle done. {len(all_matches)} matches. Total tracked: {len(seen)}")
    return all_matches


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    hold = AUTO.get("night_hold", {})
    hold_str = f"{hold.get('start','21:00')}-{hold.get('end','08:00')}" if hold.get("enabled") else "disabled"

    log.info("=" * 60)
    log.info("  JOB HUNTING AGENT v5.0")
    log.info(f"  Target:     {PROFILE['position']}")
    log.info(f"  Cities:     {', '.join(PREFS['target_cities'])}")
    log.info(f"  Roles:      {', '.join(PREFS['target_roles'])}")
    log.info(f"  Interval:   every {AUTO['search_interval_hours']} hours")
    log.info(f"  Night hold: {hold_str}")

    src = []
    if SERPAPI_KEY: src.append("Google Jobs")
    src.append("LinkedIn")
    if "remote" in [t.lower() for t in PREFS.get("job_types",[])]: src.append("RemoteOK")
    log.info(f"  Sources:    {', '.join(src)}")

    ai = []
    if GEMINI_API_KEY: ai.append("Gemini (FREE)")
    if ANTHROPIC_API_KEY: ai.append("Claude (paid)")
    ai.append("Keyword (always)")
    log.info(f"  Scoring:    {' → '.join(ai)}")
    log.info("=" * 60)

    init_tracker()
    log.info("Running initial search...")
    run_job_search()

    schedule.every(AUTO["search_interval_hours"]).hours.do(run_job_search)
    schedule.every().day.at(AUTO["daily_summary_time"]).do(send_daily_summary)

    log.info(f"\nAgent running 24/7. Next search in {AUTO['search_interval_hours']} hours. Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
