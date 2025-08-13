# 🔒 Security Policy

## Supported Versions

| Version   | Supported          |
|-----------|--------------------|
| 1.x.x     | ✅                  |
| <1.0.0    | ❌                  |

---

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not open a public issue**.
Instead, report it via:

- Email: security@example.com
- GitHub Security Advisory: https://github.com/OWNER/REPO/security/advisories/new

Include:
- Description of the vulnerability
- Steps to reproduce (or proof of concept)
- Affected versions and environment details

We aim to respond within **48 hours** and provide a fix or mitigation within **14 days**.

---

## Handling Secrets

- **Never commit** `.env` or `.secrets` files with real credentials.
- For example see `.env.example` and `.secrets.example` with placeholder values for environment variables.
- In CI/CD (GitHub Actions), store secrets via **Settings → Secrets and variables**.
- For local testing with **Act**, place credentials in `.secrets` (ignored by `.gitignore`).

Example `.env.example`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
SECRET_KEY=changeme
```

Example `.secrets.example`:
```env
DOCKERHUB_USERNAME=your-username
DOCKERHUB_TOKEN=your-token
```

---

### Security Best Practices
- Keep dependencies updated (use Dependabot).
- Scan code with security linters (Bandit, Ruff).
- Use container vulnerability scanners (Trivy, Grype).
- Avoid hardcoding API keys or passwords.

---
