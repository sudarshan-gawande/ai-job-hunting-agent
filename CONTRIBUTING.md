# Contributing to AI Job Hunting Agent

Thank you for your interest in contributing! This is a solo project open to community improvements.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ai-job-hunting-agent.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up your environment: `cp .env.example .env` and fill in your keys
5. Install dependencies: `pip install -r requirements.txt`

## Development Guidelines

- Keep all logic in `job_agent.py` — the single-file design is intentional
- All user settings must go through `config.yaml`, not hardcoded
- Use `log.info()` / `log.warning()` / `log.error()` — never `print()`
- Every new source scraper must follow the existing return format:
  ```python
  {"title": "", "company": "", "city": "", "description": "", 
   "link": "", "platform": "", "posted": "", "job_type": ""}
  ```
- Always handle exceptions gracefully — one failing source must not crash the agent

## Testing Your Changes

Before submitting a PR:

```bash
# Run the agent in a single-cycle test
python job_agent.py

# Verify:
# 1. No Python errors or tracebacks
# 2. Jobs are found from at least one source
# 3. Scoring works (Gemini, keyword, or Claude)
# 4. Email sends successfully
# 5. seen_jobs.json updates correctly
```

## Pull Request Process

1. Describe what your PR adds or fixes
2. Include sample log output showing the feature working
3. Update `README.md` if you add new config options or features
4. Keep PRs focused — one feature per PR

## Good First Issues

- Add a new job source (Naukri, Indeed direct, Internshala)
- Add Telegram bot command support (`/status`, `/pause`)
- Add a `--dry-run` CLI flag that skips email sending
- Improve keyword scoring with TF-IDF weighting
- Add config schema validation on startup

## Questions?

Open a GitHub Issue or reach out on [LinkedIn](https://www.linkedin.com/in/sudarshan-gawande/).
