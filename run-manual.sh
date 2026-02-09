#!/bin/bash
# Manual trigger for K8s Image Updater (run outside of schedule)

set -e

NAMESPACE="image-updater"
JOB_NAME="k8s-image-updater-manual-$(date +%s)"

echo "=================================================="
echo "K8s Image Updater - Manual Trigger"
echo "=================================================="
echo ""

# Check if CronJob exists
if ! kubectl get cronjob k8s-image-updater -n $NAMESPACE &> /dev/null; then
    echo "Error: CronJob 'k8s-image-updater' not found in namespace '$NAMESPACE'"
    echo ""
    echo "Deploy it first with:"
    echo "  kubectl apply -f kubernetes/cronjob.yaml"
    exit 1
fi

echo "Creating manual job from CronJob..."
kubectl create job --from=cronjob/k8s-image-updater "$JOB_NAME" -n $NAMESPACE

echo "✓ Job created: $JOB_NAME"
echo ""
echo "Waiting for job to start..."
sleep 3

# Get pod name
POD_NAME=$(kubectl get pods -n $NAMESPACE -l job-name=$JOB_NAME -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD_NAME" ]; then
    echo "⚠️  Could not find pod for job"
    echo ""
    echo "Check status with:"
    echo "  kubectl get jobs -n $NAMESPACE"
    exit 1
fi

echo "✓ Pod created: $POD_NAME"
echo ""
echo "Streaming logs (press Ctrl+C to stop)..."
echo ""
echo "=================================================="
echo ""

# Follow logs
kubectl logs -n $NAMESPACE -f "$POD_NAME" 2>/dev/null || true

echo ""
echo "=================================================="
echo ""

# Check final status
JOB_STATUS=$(kubectl get job "$JOB_NAME" -n $NAMESPACE -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "Unknown")

if [ "$JOB_STATUS" = "Complete" ]; then
    echo "✓ Job completed successfully!"
elif [ "$JOB_STATUS" = "Failed" ]; then
    echo "✗ Job failed"
    echo ""
    echo "Check logs with:"
    echo "  kubectl logs -n $NAMESPACE $POD_NAME"
else
    echo "Job status: $JOB_STATUS"
fi

echo ""
echo "Clean up with:"
echo "  kubectl delete job $JOB_NAME -n $NAMESPACE"
echo ""
