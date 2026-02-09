# AI-Powered Features Guide

## Overview

The K8s Image Updater now includes **real AI capabilities** using OpenAI's GPT models to analyze changelogs and predict deployment risks.

## What's Actually AI Now?

### 1. Changelog Analysis (LLM-Powered)
- Fetches release notes from GitHub and DockerHub
- Uses GPT-4o-mini to analyze changelog content
- Identifies:
  - 🔴 **Breaking changes** that could break your app
  - 🔒 **Security vulnerabilities** fixed
  - ✨ **Notable features** and improvements
  - 💡 **Deployment recommendations**

### 2. Risk Prediction (AI + Heuristics)
- Calculates risk score (0-10) based on:
  - Update type (major/minor/patch)
  - Number of breaking changes detected
  - Security updates included
  - LLM analysis of changelog content
- Provides risk level: Low / Medium / High / Critical

### 3. Intelligent PR Descriptions
- AI-generated summaries in PRs
- Risk distribution analysis
- Actionable recommendations
- Links to changelogs

## Setup

### 1. Get OpenAI API Key

```bash
# Sign up at https://platform.openai.com/
# Create an API key
export OPENAI_API_KEY="sk-proj-..."
```

### 2. Configure AI Features

Edit `config.yaml`:

```yaml
ai:
  enabled: true
  openai_api_key: ""  # Or use OPENAI_API_KEY env var
  model: "gpt-4o-mini"  # Faster and cheaper
  # model: "gpt-4o"     # More accurate
  analyze_changelogs: true
  risk_prediction: true

reporting:
  include_ai_analysis: true
```

### 3. Test It

```bash
# Dry run with AI analysis
export OPENAI_API_KEY="sk-proj-..."
python main.py --dry-run --verbose
```

## Example Output

### Console Output with AI

```
Checking registries for image updates...
  ✓ Update available: sonarr/sonarr 4.0.16 → 4.0.17 🟢 Risk: LOW
  ✓ Update available: overseerr/overseerr 1.34.0 → 1.35.0 🟡 Risk: MEDIUM
  ✓ Update available: app/custom 2.1.0 → 3.0.0 🔴 Risk: CRITICAL

============================================================
WEEKLY IMAGE UPDATE SUMMARY
============================================================
Date: 2026-02-05
Total Updates: 3

Updates by Category:
  Major: 1
  Minor: 1
  Patch: 1

Risk Distribution:
  🔴 Critical: 1
  🟠 High: 0
  🟡 Medium: 1
  🟢 Low: 1

Detailed Updates:
  • sonarr/sonarr: 4.0.16 → 4.0.17 [PATCH] 🟢
  • overseerr/overseerr: 1.34.0 → 1.35.0 [MINOR] 🟡
  • custom/app: 2.1.0 → 3.0.0 [MAJOR] 🔴
      ⚠️  Database schema changes require manual migration
      ⚠️  API endpoint /v2/users removed
============================================================
```

### GitHub PR with AI Analysis

```markdown
## 🤖 Automated Container Image Updates

### 🤖 AI-Powered Risk Analysis

#### Risk Distribution
- 🔴 Critical: 1
- 🟠 High: 0
- 🟡 Medium: 1
- 🟢 Low: 1

#### ⚠️ Breaking Changes Detected
- Database schema changes require manual migration
- API endpoint /v2/users removed - use /v3/users instead
- Configuration file format changed from JSON to YAML

#### 🚨 Recommendation
**High-risk updates detected.** Please:
- Review all breaking changes carefully
- Test in staging environment first
- Plan for potential rollback

### Detailed Changes

#### Namespace: `custom`
- 🔴 **app** `custom/app:2.1.0` → `:3.0.0` *(major)* `Risk: CRITICAL (9.0/10)`
  - ⚠️  **Breaking Changes:**
    - Database schema changes require manual migration
    - API endpoint /v2/users removed
    - Configuration format changed
  - 🔒 **Security Updates:**
    - Fixed critical XSS vulnerability (CVE-2026-1234)
  - 📝 Major version upgrade with breaking API changes. Requires database migration and configuration updates.
  - 📖 [View Changelog](https://github.com/custom/app/releases)

#### Namespace: `overseerr`
- 🟡 **overseerr** `linuxserver/overseerr:1.34.0` → `:1.35.0` *(minor)* `Risk: MEDIUM (4.5/10)`
  - 📝 Minor update with new features and bug fixes. No breaking changes detected.
  - 📖 [View Changelog](https://github.com/linuxserver/docker-overseerr/releases)

#### Namespace: `sonarr`
- 🟢 **sonarr** `lscr.io/linuxserver/sonarr:4.0.16` → `:4.0.17` *(patch)* `Risk: LOW (2.0/10)`
  - 📝 Patch update with bug fixes. Safe to deploy.
  - 📖 [View Changelog](https://github.com/linuxserver/docker-sonarr/releases)
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    K8s Image Updater                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Scan Cluster → Find deployments                        │
│                                                             │
│  2. Check Registries → Find updates                        │
│                                                             │
│  3. Fetch Changelog → Get release notes from GitHub        │
│     ├─ GitHub Releases API                                 │
│     ├─ DockerHub API                                       │
│     └─ Known repository mappings                           │
│                                                             │
│  4. AI Analysis (OpenAI GPT-4o-mini) ←── THIS IS THE AI!  │
│     ├─ Send changelog to LLM                               │
│     ├─ Extract breaking changes                            │
│     ├─ Identify security updates                           │
│     ├─ Generate recommendations                            │
│     └─ Calculate risk score                                │
│                                                             │
│  5. Update Manifests → Modify YAML files                   │
│                                                             │
│  6. Create PR → Generate AI-enriched description           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AI Analysis Process

1. **Changelog Fetch**: Gets release notes from GitHub/DockerHub
2. **Context Building**: Creates prompt with version info + changelog
3. **LLM Call**: Sends to OpenAI GPT-4o-mini
4. **Structured Analysis**: Returns JSON with:
   - Breaking changes list
   - Security updates list
   - Notable changes
   - Recommendations
   - Summary
5. **Risk Calculation**: Combines LLM output with heuristics
6. **PR Enhancement**: Adds AI insights to pull request

## Cost Considerations

### OpenAI API Costs (as of 2026)

**GPT-4o-mini** (Recommended):
- $0.150 per 1M input tokens
- $0.600 per 1M output tokens
- ~2,000 tokens per analysis
- **Cost per update**: ~$0.001 (one-tenth of a cent)
- **Cost for 10 updates/week**: ~$0.01/week = **$0.52/year**

**GPT-4o** (More accurate):
- $2.50 per 1M input tokens  
- $10.00 per 1M output tokens
- **Cost per update**: ~$0.02
- **Cost for 10 updates/week**: ~$0.20/week = **$10.40/year**

### Recommendation

Use `gpt-4o-mini` - it's 20x cheaper and more than adequate for changelog analysis.

## Disabling AI Features

If you don't want to use AI or OpenAI:

```yaml
ai:
  enabled: false  # Disables all AI features
```

The tool will fall back to:
- Simple heuristic-based risk scoring
- No changelog analysis
- Basic update categorization

**You still get automatic updates, just without AI insights.**

## Supported Image Sources

### Changelog Detection

The tool can fetch changelogs from:

1. **GitHub Releases** (Best)
   - LinuxServer.io images (auto-detected)
   - GHCR images (ghcr.io/owner/repo)
   - Custom mappings in `changelog_fetcher.py`

2. **DockerHub Descriptions**
   - Falls back to repository description
   - Less detailed than GitHub releases

3. **Manual Mappings**
   - Add your custom images to `changelog_fetcher.py`:

```python
known_repos = {
    'your/custom-image': 'github-org/repo-name',
}
```

## Advanced Configuration

### Custom Prompts

Edit `ai_analyzer.py` to customize the LLM prompt:

```python
system_prompt = """You are a DevOps engineer...
Focus on:
1. Security vulnerabilities
2. Database migrations
3. Breaking API changes
..."""
```

### Risk Score Tuning

Adjust risk calculation in `ai_analyzer.py`:

```python
def _calculate_risk_score(self, update: Dict, analysis: Dict) -> float:
    # Customize these weights
    update_type_scores = {
        'major': 7.0,    # Increase for more caution
        'minor': 4.0,
        'patch': 2.0,
    }
    # ...
```

### Model Selection

Different models for different needs:

- `gpt-4o-mini`: Fast, cheap, good enough (recommended)
- `gpt-4o`: More accurate, slower, 20x more expensive
- `gpt-3.5-turbo`: Cheapest, less accurate (not recommended)

## Troubleshooting

### "AI analysis failed"

**Possible causes:**
1. OpenAI API key not set or invalid
2. API rate limit reached
3. Network connectivity issues

**Solution:**
```bash
# Verify API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check logs
python main.py --dry-run --verbose
```

### "Could not fetch changelog"

**Possible causes:**
1. Image repository not in known mappings
2. No GitHub releases available
3. GitHub API rate limit

**Solution:**
- Add custom mapping in `changelog_fetcher.py`
- Or disable changelog fetching:
```yaml
ai:
  analyze_changelogs: false
```

### High API costs

**Solution:**
1. Switch to `gpt-4o-mini`
2. Reduce update frequency
3. Filter which namespaces to check
4. Set `max_updates_per_pr` limit

## Privacy & Security

### Data Sent to OpenAI

- Container image names and versions
- Changelog content (from public GitHub/DockerHub)
- No secrets, credentials, or internal code

### API Key Security

- Store in environment variable: `OPENAI_API_KEY`
- Or Kubernetes secret (see deployment guide)
- Never commit to git

### OpenAI Data Policy

Per OpenAI's API policy:
- Data is not used to train models
- Data is retained for 30 days for abuse monitoring
- Zero retention option available for enterprise

## Benefits of AI Analysis

### Before (Without AI)
```
Update available: app 2.0.0 → 3.0.0 [MAJOR]
```
👎 You have no idea what changed or if it's safe

### After (With AI)
```
Update available: app 2.0.0 → 3.0.0 [MAJOR] 🔴 Risk: CRITICAL (9.0/10)
  ⚠️  Database schema changes require manual migration
  ⚠️  API endpoint /v2/users removed - use /v3/users
  🔒 Fixed critical XSS vulnerability (CVE-2026-1234)
  💡 Test thoroughly in staging before production
```
👍 You know exactly what to expect and how to prepare

## Next Steps

1. ✅ Get OpenAI API key
2. ✅ Configure `config.yaml`
3. ✅ Test with `--dry-run`
4. ✅ Deploy and enjoy AI-powered updates!

## Real-World Example

Check `/home/matt/code/k8s-image-updater/EXAMPLES.py` for complete output examples with AI analysis.
