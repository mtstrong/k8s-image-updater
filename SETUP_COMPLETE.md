# 🎉 K8s Image Updater - Setup Complete!

Your k8s-image-updater application is now fully set up with GitHub CI/CD and ready for Kubernetes deployment!

## ✅ What's Been Done

### 1. GitHub Repository
- **Repository**: https://github.com/mtstrong/k8s-image-updater
- **Status**: ✓ Created and code pushed
- **Visibility**: Public

### 2. CI/CD Pipeline
- **GitHub Actions**: Configured and working
- **Container Registry**: GitHub Container Registry (GHCR)
- **Image**: `ghcr.io/mtstrong/k8s-image-updater:latest`
- **Status**: ✓ First build completed successfully

### 3. Kubernetes Manifests
- **Location**: `kubernetes/cronjob.yaml`
- **Resources Created**:
  - Namespace: `image-updater`
  - ServiceAccount with ClusterRole permissions
  - ConfigMap for configuration
  - CronJob (runs every Monday at 9 AM UTC)

## 🚀 Quick Start - Deploy to Kubernetes

### Prerequisites
You need a GitHub Personal Access Token with `repo` scope.

### Option 1: Quick Deploy (Recommended)
```bash
cd /home/matt/code/k8s-image-updater
export GITHUB_TOKEN='your_github_token_here'
./deploy.sh
```

### Option 2: Manual Deploy
```bash
# 1. Create namespace
kubectl create namespace image-updater

# 2. Create GitHub token secret
kubectl create secret generic github-token \
  --from-literal=token=YOUR_GITHUB_TOKEN \
  --namespace=image-updater

# 3. Deploy the CronJob
kubectl apply -f kubernetes/cronjob.yaml

# 4. Verify
kubectl get all -n image-updater
```

## 🔍 Important Next Steps

### 1. Make GHCR Image Public (Required for easy K8s access)
The image is currently private. To make it public:

1. Go to https://github.com/mtstrong?tab=packages
2. Click on `k8s-image-updater` package
3. Go to "Package settings"
4. Under "Danger Zone", click "Change visibility"
5. Make it public

**Alternative**: Add imagePullSecrets to Kubernetes if you want to keep it private.

### 2. Test the Deployment
Manually trigger a job to test:
```bash
kubectl create job --from=cronjob/k8s-image-updater manual-test -n image-updater
kubectl logs -n image-updater job/manual-test -f
```

### 3. Optional: Enable AI Features
If you want AI-powered changelog analysis with OpenAI:

```bash
kubectl create secret generic openai-secret \
  --from-literal=api-key=YOUR_OPENAI_API_KEY \
  --namespace=image-updater
```

Then add to the CronJob env vars:
```yaml
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: openai-secret
      key: api-key
```

## 📋 How It Works

1. **Weekly Scan**: Every Monday at 9 AM UTC, the CronJob runs
2. **Image Detection**: Scans all Kubernetes deployments for container images
3. **Update Check**: Checks DockerHub, LSCR, and GHCR for newer versions
4. **AI Analysis**: (If enabled) Uses GPT to analyze changelogs for risks
5. **PR Creation**: Creates GitHub PRs with detailed update information
6. **Manual Review**: You review and merge the PRs

## 🔧 Customization

### Change Schedule
Edit the CronJob schedule in `kubernetes/cronjob.yaml`:
```yaml
spec:
  schedule: "0 9 * * 1"  # Cron format
```

Common schedules:
- Daily: `"0 9 * * *"`
- Weekly (Sunday): `"0 9 * * 0"`
- Twice a week: `"0 9 * * 1,4"`

### Update Configuration
Edit the ConfigMap in `kubernetes/cronjob.yaml`:
- Modify GitHub settings
- Adjust manifest paths
- Change update policies (major/minor/patch)
- Configure registry settings

Apply changes:
```bash
kubectl apply -f kubernetes/cronjob.yaml
```

## 📚 Documentation

- [README.md](README.md) - Main documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide
- [USAGE.md](USAGE.md) - Usage instructions
- [AI_FEATURES.md](AI_FEATURES.md) - AI features documentation

## 🐛 Troubleshooting

### View Logs
```bash
# List all jobs
kubectl get jobs -n image-updater

# View specific job logs
kubectl logs -n image-updater job/<job-name>

# Follow logs in real-time
kubectl logs -n image-updater job/<job-name> -f
```

### Common Issues

1. **Image Pull Errors**: Make GHCR image public or add imagePullSecrets
2. **Permission Errors**: Verify GitHub token has `repo` scope
3. **No Deployments Found**: Check manifest_paths in ConfigMap

### Check CronJob Status
```bash
kubectl describe cronjob k8s-image-updater -n image-updater
```

## 🔄 Making Updates

When you make changes to the code:

```bash
cd /home/matt/code/k8s-image-updater
git add .
git commit -m "Your change description"
git push
```

The GitHub Action will automatically:
1. Build new Docker image
2. Push to GHCR with `latest` tag
3. Next CronJob run will use the new image

To force immediate update:
```bash
kubectl delete job -n image-updater --all
kubectl create job --from=cronjob/k8s-image-updater test-new-version -n image-updater
```

## 🎯 What This System Does For You

- ✅ Automatically monitors your Kubernetes cluster for outdated images
- ✅ Checks for updates from multiple container registries
- ✅ Uses AI to assess update risks and breaking changes
- ✅ Creates detailed PRs with changelogs and recommendations
- ✅ Runs on autopilot - no manual intervention needed
- ✅ Helps keep your cluster secure with latest patches

## 📞 Need Help?

- Check the [README.md](README.md) for detailed feature documentation
- View [EXAMPLES.py](EXAMPLES.py) for code examples
- Check GitHub Actions logs: https://github.com/mtstrong/k8s-image-updater/actions

---

**Repository**: https://github.com/mtstrong/k8s-image-updater
**Container Image**: ghcr.io/mtstrong/k8s-image-updater:latest
**Created**: February 9, 2026
