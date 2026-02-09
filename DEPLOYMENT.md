# K8s Image Updater - Deployment Guide

## Prerequisites

1. A Kubernetes cluster with kubectl configured
2. GitHub Personal Access Token with the following permissions:
   - `repo` (full control of private repositories)
   - `read:packages` (for pulling container images from GHCR)
   - `write:packages` (for pushing container images to GHCR)

## Step 1: Create GitHub Repository

1. Go to GitHub and create a new repository named `k8s-image-updater`
2. Keep it public or private (up to you)
3. Don't initialize with README (we already have one)

## Step 2: Push Code to GitHub

```bash
cd /home/matt/code/k8s-image-updater
git add .
git commit -m "Initial commit: K8s Image Updater"
git remote add origin https://github.com/mtstrong/k8s-image-updater.git
git push -u origin main
```

## Step 3: GitHub Actions Will Build Image

The GitHub Action will automatically:
- Build the Docker image
- Push it to GitHub Container Registry (ghcr.io)
- Tag it as `latest` and with the commit SHA

The image will be available at: `ghcr.io/mtstrong/k8s-image-updater:latest`

## Step 4: Make GHCR Image Public (Recommended)

After the first push:
1. Go to https://github.com/mtstrong?tab=packages
2. Find the `k8s-image-updater` package
3. Click on it → Package settings
4. Scroll down to "Danger Zone"
5. Click "Change visibility" → Make public

This allows Kubernetes to pull without authentication.

## Step 5: Create Kubernetes Secret for GitHub Token

Create a secret with your GitHub Personal Access Token:

```bash
kubectl create namespace image-updater

# Replace YOUR_GITHUB_TOKEN with your actual token
kubectl create secret generic github-token \
  --from-literal=token=YOUR_GITHUB_TOKEN \
  --namespace=image-updater
```

## Step 6: Optional - Add OpenAI API Key for AI Features

If you want AI-powered changelog analysis:

```bash
kubectl create secret generic openai-secret \
  --from-literal=api-key=YOUR_OPENAI_API_KEY \
  --namespace=image-updater
```

Then update the CronJob to include this environment variable.

## Step 7: Deploy to Kubernetes

```bash
kubectl apply -f kubernetes/cronjob.yaml
```

This creates:
- Namespace: `image-updater`
- ServiceAccount with ClusterRole permissions
- ConfigMap with configuration
- CronJob (runs every Monday at 9 AM UTC)

## Step 8: Verify Deployment

Check if everything is created:

```bash
kubectl get all -n image-updater
kubectl get cronjob -n image-updater
```

## Step 9: Test Run (Optional)

Manually trigger a job to test:

```bash
kubectl create job --from=cronjob/k8s-image-updater manual-test -n image-updater
kubectl logs -n image-updater job/manual-test -f
```

## Customization

### Modify the Schedule

Edit the CronJob schedule in `kubernetes/cronjob.yaml`:

```yaml
spec:
  schedule: "0 9 * * 1"  # Every Monday at 9 AM UTC
```

Common schedules:
- Daily: `"0 9 * * *"`
- Weekly (Sunday): `"0 9 * * 0"`
- Monthly (1st): `"0 9 1 * *"`

### Update Configuration

Edit the ConfigMap in `kubernetes/cronjob.yaml` to customize:
- GitHub repository settings
- Manifest paths
- Update policies (major/minor/patch)
- Registry settings

After editing:
```bash
kubectl apply -f kubernetes/cronjob.yaml
```

## Troubleshooting

### View Logs

```bash
# List jobs
kubectl get jobs -n image-updater

# View logs for the latest job
kubectl logs -n image-updater job/<job-name>
```

### Check CronJob Status

```bash
kubectl describe cronjob k8s-image-updater -n image-updater
```

### Common Issues

1. **"Permission denied" errors**: Check that GitHub token has `repo` scope
2. **"Image pull failed"**: Make sure GHCR package is public or add imagePullSecrets
3. **"No deployments found"**: Verify manifest_paths in config.yaml are correct

## Updating the Application

When you push changes to the GitHub repository:

1. GitHub Actions automatically builds a new image with `latest` tag
2. Delete the current job to force pulling the new image:
   ```bash
   kubectl delete job -n image-updater --all
   ```
3. The next scheduled run will use the new image

Or trigger a manual run:
```bash
kubectl create job --from=cronjob/k8s-image-updater test-update -n image-updater
```

## Monitoring

The CronJob keeps history of:
- Last 3 successful jobs
- Last 3 failed jobs

Monitor via:
```bash
kubectl get jobs -n image-updater -w
```
