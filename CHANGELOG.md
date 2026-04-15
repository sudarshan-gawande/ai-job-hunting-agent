# Changelog

All notable changes to this project will be documented here.

## [v5.0] — 2026-04-14

### Added
- Google Gemini 2.5 Flash-Lite as primary AI scorer (FREE, 1000/day)
- RemoteOK as third job source for remote positions
- Night hold feature: pauses 9 PM – 8 AM to save API quota
- Daily summary email every morning at 8 AM
- Email rate limiting via `email_count.json` (max_emails_per_day)
- Rich HTML email with expandable recruiter messages
- Docker + docker-compose support with persistent volumes
- `seen_jobs.json` dedup store with MD5-based job IDs
- `job_tracker.csv` with full job audit trail

### Improved
- AI scoring priority: Gemini → Claude → Keyword (graceful fallback chain)
- LinkedIn scraping via cloudscraper (more reliable than requests)
- Structured logging to both file and console with timestamps

## [v4.0] — Previous

- Claude AI as primary scorer
- Google Jobs (SerpAPI) + LinkedIn sources
- Basic email notification
- CSV job tracking
