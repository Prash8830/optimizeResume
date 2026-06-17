# Contributing Guide

---

## Commit Convention — Identity Tracking

Every commit must clearly identify WHO made it. This project tracks contributions by identity so Prashant can audit what was done by whom.

### Format

```
<type>(<scope>): <short description>

<optional body>

Author: <Your Name / AI Identity>
Co-Authored-By: <if pair/AI assisted>
```

### Author Identities

| Who | Author tag to use |
|-----|-------------------|
| Prashant (owner) | `Author: Prashant Patil` |
| Claude Sonnet 4.6 (Anthropic AI) | `Author: Claude Sonnet 4.6 (Anthropic)` |
| Any other contributor | `Author: <Full Name> <email>` |
| AI-assisted (human reviewed) | Both `Author:` and `Co-Authored-By:` |

### Examples

```
feat(agents): add JD analyzer node with Gemini keyword extraction

Extracts role_type, required/preferred keywords with weights.
Uses gemini-2.0-flash with structured JSON output.

Author: Claude Sonnet 4.6 (Anthropic)
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

```
fix(ats_checker): correct loop termination when iter_count reaches max

Author: Prashant Patil
```

### Commit Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or file |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructure, no behavior change |
| `test` | Adding/updating tests |
| `chore` | Build, config, deps |
| `style` | Formatting only |

### Scopes

`agents`, `backend`, `frontend`, `storage`, `export`, `auth`, `docs`, `docker`

---

## Branch Strategy

```
main          — stable, always deployable
dev           — active development (PR target)
feat/<name>   — individual feature branches
fix/<name>    — bug fix branches
```

PRs go to `dev` → reviewed → merged to `main`.

---

## Environment Setup

```bash
# Copy env template
cp .env.example .env

# Required variables
GEMINI_API_KEY=<your key from aistudio.google.com>
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/optimizeresume
SECRET_KEY=<random 32-char string for JWT>
CHROMA_PERSIST_DIR=./chroma_db
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Code Style

- Python: Black formatter, isort imports
- Line length: 100
- Type hints: required on all function signatures
- Docstrings: only on public functions, one line max
