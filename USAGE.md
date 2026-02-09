# Example Usage and Testing Guide

## Local Testing (Recommended First Step)

### 1. Quick Test with Dry-Run

```bash
cd /home/matt/code/k8s-image-updater

# Run setup
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Set GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Test without making any changes
python main.py --dry-run --verbose
```

**Expected Output:**
```
2026-02-05 10:00:00 - INFO - K8s Image Updater Agent Starting
2026-02-05 10:00:00 - INFO - Loading configuration from config.yaml
2026-02-05 10:00:00 - INFO - Scanning Kubernetes cluster for deployments...
2026-02-05 10:00:00 - INFO - Found 15 deployments
2026-02-05 10:00:00 - INFO - Checking registries for image updates...
2026-02-05 10:00:00 - INFO -   ✓ Update available: sonarr 4.0.16 → 4.0.17
2026-02-05 10:00:00 - INFO -   ✓ Update available: overseerr 1.34.0 → 1.35.0
2026-02-05 10:00:00 - INFO - Found 2 updates available
...
2026-02-05 10:00:00 - INFO - Dry-run mode: Skipping PR creation
```

### 2. Test Configuration

Edit `config.yaml` to point to your repositories:

```bash
vim config.yaml
```

Update these sections:
```yaml
github:
  owner: "mtstrong"  # Your GitHub username
  repo: "homelab"    # Your repository name

kubernetes:
  manifest_paths:
    - "/home/matt/code/homelab/kubernetes/"
    - "/home/matt/Manifest/"
```

### 3. Run Without Dry-Run (Creates Actual PR)

```bash
# This will create a real PR!
python main.py --config config.yaml
```

## Kubernetes Deployment

### 1. Update Secrets

Edit the GitHub token in the manifest:

```bash
vim kubernetes/cronjob.yaml
```

Find and replace:
```yaml
stringData:
  token: "YOUR_GITHUB_TOKEN_HERE"  # Replace with actual token
```

### 2. Deploy to Cluster

```bash
kubectl apply -f kubernetes/cronjob.yaml
```

Verify deployment:
```bash
kubectl get cronjob -n image-updater
kubectl get serviceaccount -n image-updater
kubectl get clusterrole k8s-image-updater
```

### 3. Manual Test Run

Trigger a manual run without waiting for the schedule:

```bash
./run-manual.sh
```

This will:
- Create a job from the CronJob
- Stream the logs in real-time
- Show the final status

### 4. Check Logs

```bash
# List all jobs
kubectl get jobs -n image-updater

# Get logs from latest job
JOB=$(kubectl get jobs -n image-updater --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl logs -n image-updater job/$JOB
```

## Common Scenarios

### Scenario 1: Conservative Updates (Production)

Only allow patch updates:

```yaml
update_policy:
  allow_major: false
  allow_minor: false
  allow_patch: true
```

### Scenario 2: Active Updates (Development)

Allow minor and patch updates:

```yaml
update_policy:
  allow_major: false
  allow_minor: true
  allow_patch: true
```

### Scenario 3: Aggressive Updates (Testing)

Allow all updates:

```yaml
update_policy:
  allow_major: true
  allow_minor: true
  allow_patch: true
```

### Scenario 4: Specific Namespaces Only

```yaml
kubernetes:
  namespaces:
    - "sonarr"
    - "overseerr"
    - "radarr"
```

### Scenario 5: Ignore Specific Images

```yaml
update_policy:
  ignore_images:
    - ".*:latest"
    - ".*:dev"
    - ".*:nightly"
    - "custom-app:.*"  # Ignore all versions of custom-app
```

## Expected Workflow

1. **Monday 9 AM UTC**: CronJob triggers automatically
2. **Agent scans cluster**: Discovers all deployments
3. **Check registries**: Queries DockerHub, LSCR, etc. for updates
4. **Filter by policy**: Only includes allowed update types
5. **Clone repo**: Clones your GitHub repository
6. **Update manifests**: Modifies YAML files with new image tags
7. **Create PR**: Opens a pull request with detailed changelog
8. **You review**: Check the PR, review changelogs
9. **Merge**: Merge the PR when ready
10. **Deploy**: Use your normal deployment process (kubectl apply, ArgoCD, etc.)

## Troubleshooting

### Issue: "Could not configure Kubernetes client"

**Solution**: Ensure kubeconfig is accessible or agent is running in-cluster

```bash
# Test kubectl access
kubectl cluster-info

# If running locally, ensure KUBECONFIG is set
export KUBECONFIG=~/.kube/config
```

### Issue: "GitHub token not configured"

**Solution**: Set the GITHUB_TOKEN environment variable

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Or update `config.yaml`:
```yaml
github:
  token: "ghp_your_token_here"
```

### Issue: "No deployments found"

**Solution**: Check namespace configuration

```bash
# List all namespaces
kubectl get namespaces

# Check if deployments exist
kubectl get deployments -A
```

Update `config.yaml` to include the right namespaces:
```yaml
kubernetes:
  namespaces: []  # Empty = all namespaces
  # OR specific namespaces:
  # namespaces:
  #   - "default"
  #   - "sonarr"
```

### Issue: "Could not find manifest file"

**Solution**: Verify manifest paths in config

```bash
# Check where your manifests are located
find /home/matt -name "deployment.yaml" -type f 2>/dev/null | head -10
```

Update `config.yaml`:
```yaml
kubernetes:
  manifest_paths:
    - "/full/path/to/kubernetes/"
    - "/full/path/to/Manifest/"
```

### Issue: Rate Limiting from DockerHub

**Solution**: Authenticate with DockerHub (if you have an account)

Add to `config.yaml`:
```yaml
registries:
  dockerhub:
    enabled: true
    username: "your-dockerhub-username"
    password: "your-dockerhub-token"
```

## Advanced Configuration

### Custom Schedule

Edit the CronJob schedule:

```yaml
# Every Monday at 9 AM UTC
schedule: "0 9 * * 1"

# Every day at 2 AM UTC
schedule: "0 2 * * *"

# Every Sunday at midnight UTC
schedule: "0 0 * * 0"

# Every 3 days at 3 PM UTC
schedule: "0 15 */3 * *"
```

### Custom Docker Image

Build and use your own image:

```bash
# Build image
docker build -t your-registry/k8s-image-updater:v1.0 .

# Push to registry
docker push your-registry/k8s-image-updater:v1.0

# Update cronjob.yaml
# Change: image: python:3.11-slim
# To:     image: your-registry/k8s-image-updater:v1.0
```

### Notifications (Future Enhancement)

Add Slack webhook notification:

```python
# In github_pr.py, add after PR creation:
import requests
requests.post(
    "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    json={"text": f"New image updates PR created: {pr_url}"}
)
```

## Integration with CI/CD

### ArgoCD

If using ArgoCD, it will automatically detect and sync the changes after you merge the PR.

### Flux

If using Flux, it will reconcile the changes based on your sync interval.

### Manual kubectl

```bash
# After merging PR, pull latest
cd /home/matt/code/homelab
git pull

# Apply changes
kubectl apply -f kubernetes/sonarr/deployment.yaml
kubectl apply -f kubernetes/overseerr/deployment.yaml
```

## Monitoring

### View CronJob History

```bash
# See successful runs
kubectl get jobs -n image-updater --field-selector status.successful=1

# See failed runs
kubectl get jobs -n image-updater --field-selector status.failed=1
```

### Set up Alerts

Create a monitoring alert for failed jobs:

```yaml
# Prometheus alert rule
- alert: ImageUpdaterFailed
  expr: kube_job_status_failed{namespace="image-updater"} > 0
  annotations:
    summary: "K8s Image Updater job failed"
```

## Security Best Practices

1. **GitHub Token**: Use a token with minimal permissions (only `repo`)
2. **RBAC**: The ServiceAccount only has read permissions on the cluster
3. **Secrets**: Never commit secrets to git
4. **Branch Protection**: Enable branch protection on your main branch
5. **Review**: Always review PRs before merging

## Next Steps

1. ✅ Test locally with dry-run
2. ✅ Verify configuration
3. ✅ Deploy to Kubernetes
4. ✅ Run manual test
5. ✅ Review first PR
6. ✅ Set up monitoring/alerts
7. ✅ Document your deployment process
8. ✅ Enjoy automated updates!
