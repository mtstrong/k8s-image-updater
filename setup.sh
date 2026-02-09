#!/bin/bash
# Quick setup script for K8s Image Updater

set -e

echo "=================================================="
echo "K8s Image Updater - Setup Script"
echo "=================================================="
echo ""

# Check if running in correct directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this script from the k8s-image-updater directory"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ -z "$python_version" ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi
echo "✓ Python $python_version found"
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check for GitHub token
echo "Checking GitHub token..."
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN environment variable not set"
    echo ""
    echo "To set it, run:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo ""
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required permissions: repo (full)"
else
    echo "✓ GITHUB_TOKEN is set"
fi
echo ""

# Check kubectl access
echo "Checking Kubernetes access..."
if command -v kubectl &> /dev/null; then
    if kubectl cluster-info &> /dev/null; then
        echo "✓ kubectl configured and cluster accessible"
    else
        echo "⚠️  kubectl is installed but cluster is not accessible"
    fi
else
    echo "⚠️  kubectl is not installed"
fi
echo ""

# Test configuration
echo "Testing configuration..."
if [ -f "config.yaml" ]; then
    echo "✓ config.yaml found"
    
    # Validate YAML syntax
    python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ config.yaml is valid YAML"
    else
        echo "⚠️  config.yaml has syntax errors"
    fi
else
    echo "⚠️  config.yaml not found - using default configuration"
fi
echo ""

echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your settings:"
echo "   vim config.yaml"
echo ""
echo "2. Set your GitHub token:"
echo "   export GITHUB_TOKEN='your_token_here'"
echo ""
echo "3. Test the agent (dry-run):"
echo "   source venv/bin/activate"
echo "   python main.py --dry-run --verbose"
echo ""
echo "4. Deploy to Kubernetes:"
echo "   kubectl apply -f kubernetes/cronjob.yaml"
echo ""
echo "For more information, see README.md"
echo ""
