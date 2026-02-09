# K8s Image Updater Agent

An automated AI agent that scans your Kubernetes cluster weekly for container image updates and creates GitHub Pull Requests with updated manifests.

## Features

- 🔍 **Automatic Scanning**: Scans all Kubernetes deployments in your cluster
- 📦 **Multi-Registry Support**: Works with DockerHub, LinuxServer.io (lscr), and GitHub Container Registry
- 🔄 **Version Detection**: Intelligently detects semantic versioning and finds latest compatible versions
- 🤖 **AI-Powered Analysis**: Uses OpenAI GPT to analyze changelogs for breaking changes and security issues
- 📊 **Risk Prediction**: Calculates deployment risk scores (0-10) with AI + heuristics
- ⚙️ **Configurable Policy**: Control which types of updates are allowed (major/minor/patch)
- 🤖 **Automated PRs**: Creates well-formatted GitHub PRs with detailed changelogs and AI insights
- 📅 **Weekly Schedule**: Runs automatically via Kubernetes CronJob
- 🔐 **Secure**: Uses Kubernetes RBAC and secrets for authentication

## Quick Start

### 1. Configure the Agent

Edit `config.yaml` to match your setup:

```yaml
github:
  owner: "your-github-username"
  repo: "your-repo-name"
  base_branch: "main"

kubernetes:
  manifest_paths:
    - "kubernetes/"
    - "../Manifest/"

# AI-Powered Features (Optional but Recommended!)
ai:
  enabled: true
  openai_api_key: ""  # Or set OPENAI_API_KEY env var
  model: "gpt-4o-mini"  # Fast and cheap (~$0.50/year)

update_policy:
  allow_major: false  # Be conservative with major updates
  allow_minor: true
  allow_patch: true
```

### 2. Set GitHub Token

Create a GitHub Personal Access Token with `repo` permissions, then:

```bash
# Set GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Optional: Set OpenAI API key for AI features
export OPENAI_API_KEY="sk-proj-your_key_here"
```

### 3. Deploy to Kubernetes

```bash
kubectl apply -f kubernetes/cronjob.yaml
```

### 4. Manual Test Run

Test the agent locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Set GitHub token
export GITHUB_TOKEN="your_token_here"

# Run in dry-run mode
python main.py --dry-run --verbose
```

## Configuration

### Update Policy

Control which updates are applied:

- `allow_major`: Allow major version updates (e.g., 1.x → 2.x) - **Recommended: false**
- `allow_minor`: Allow minor version updates (e.g., 1.1 → 1.2) - **Recommended: true**
- `allow_patch`: Allow patch version updates (e.g., 1.1.1 → 1.1.2) - **Recommended: true**

### Schedule

The CronJob is configured to run weekly (Mondays at 9 AM UTC):

```yaml
schedule: "0 9 * * 1"
```

Adjust this to your preference using standard cron syntax.

### Ignored Images

Add patterns to ignore specific images:

```yaml
ignore_images:
  - ".*:latest"
  - ".*:dev"
  - ".*:test"
```

## Architecture

```
┌─────────────────────┐
│  Kubernetes Cluster │
│                     │
│  ┌───────────────┐  │
│  │   CronJob     │  │ ← Runs weekly
│  │   (Monday)    │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │  Image Updater│  │
│  │     Agent     │  │
│  └───────┬───────┘  │
│          │          │
└──────────┼──────────┘
           │
           ├─► Scan Cluster (K8s API)
           │
           ├─► Check Registries (DockerHub, etc.)
           │
           ├─► Update Manifests (YAML files)
           │
           └─► Create PR (GitHub API)
                   │
                   ▼
           ┌──────────────┐
           │   GitHub     │
           │  Repository  │
           └──────────────┘
```

## Components

- **scanner.py**: Scans Kubernetes cluster for deployments
- **registry.py**: Checks container registries for updates
- **changelog_fetcher.py**: Fetches release notes from GitHub/DockerHub
- **ai_analyzer.py**: AI-powered changelog analysis and risk prediction
- **manifest_updater.py**: Updates YAML manifest files
- **github_pr.py**: Creates GitHub pull requests
- **config_loader.py**: Loads and validates configuration
- **main.py**: Main orchestration logic
with AI-powered insights:

```markdown
🤖 Weekly Container Image Updates - 2026-02-05 (5 updates)

## 🤖 AI-Powered Risk Analysis

### Risk Distribution
- 🔴 Critical: 1
- 🟠 High: 0
- 🟡 Medium: 2
- 🟢 Low: 2

### ⚠️ Breaking Changes Detected
- Database schema changes require manual migration
- API endpoint /v2/users removed - use /v3/users

### 🚨 Recommendation
**High-risk updates detected.** Please test in staging first.

## Summary
- Major: 1
- Minor: 2
- Patch: 2

### Namespace: sonarr
- 🟢 sonarr: lscr.io/linuxserver/sonarr:4.0.16 → :4.0.17 (patch) `Risk: LOW (2.0/10)`
  - 📝 Patch update with bug fixes. Safe to deploy.
  - 📖 [View Changelog](https://github.com/linuxserver/docker-sonarr/releases)

### Namespace: app
- 🔴 app: custom/app:2.0.0 → :3.0.0 (major) `Risk: CRITICAL (9.0/10)`
  - ⚠️  **Breaking Changes:**
    - Database schema changes require manual migration
    - API endpoint /v2/users removed
  - 🔒 **Security Updates:**
    - Fixed critical XSS vulnerability
  - 📖 [View Changelog](https://github.com/custom/app/releasesch)

### Namespace: overseerr
- 🟡 overseerr: linuxserver/overseerr:1.34.0 → :1.35.0 (minor)
```

## Security Considerations

- GitHub token is stored as a Kubernetes Secret
- Service Account has minimal required permissions (read-only cluster access)
- Agent runs in isolated namespace
- All API calls are logged

## Troubleshooting

### Check CronJob Status

```bash
kubectl get cronjobs -n image-updater
kubectl get jobs -n image-updater
```

### View Logs

```bash
# Get latest job
JOB=$(kubectl get jobs -n image-updater --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

# View logs
kubectl logs -n image-updater job/$JOB -f
```

### Test Locally

```bash
# Dry run to see what would be updated
python main.py --dry-run --verbose

# Test with actual cluster
python main.py --config config.yaml
```

## AAI Features

For full AI capabilities, see [AI_FEATURES.md](AI_FEATURES.md) for:
- Changelog analysis with LLMs
- Risk prediction algorithms
- Cost breakdown (~$0.50/year with gpt-4o-mini)
- Privacy and security considerations

### dvanced Usage

### Custom Docker Image

Build and push your own image:

```bash
docker build -t your-registry/k8s-image-updater:latest .
docker push your-registry/k8s-image-updater:latest

# Update cronjob.yaml to use your image
```

### Multiple Repositories

To manage multiple repositories, create separate CronJob instances with different ConfigMaps.

## Contributing

Improvements welcome! Consider adding:
- Support for more registries (Quay.io, AWS ECR, etc.)
- Slack/Discord notifications
- Rollback capabilities
- Integration with ArgoCD/Flux

## License

MIT License - feel free to use and modify as needed.
