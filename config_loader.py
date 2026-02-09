"""
Configuration Loader Module

Loads and validates configuration from YAML file.
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage configuration"""
    
    @staticmethod
    def load(config_path):
        """Load configuration from YAML file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables
        config = ConfigLoader._apply_env_overrides(config)
        
        # Validate configuration
        ConfigLoader._validate(config)
        
        return config
    
    @staticmethod
    def _apply_env_overrides(config):
        """Apply environment variable overrides"""
        # GitHub token from environment
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            config['github']['token'] = github_token
            logger.info("Using GITHUB_TOKEN from environment")
        
        # Kubeconfig path
        kubeconfig = os.getenv('KUBECONFIG')
        if kubeconfig:
            config.setdefault('kubernetes', {})['kubeconfig'] = kubeconfig
        
        return config
    
    @staticmethod
    def _validate(config):
        """Validate required configuration"""
        # Validate GitHub config
        if not config.get('github', {}).get('token'):
            raise ValueError(
                "GitHub token not configured. Set in config.yaml or GITHUB_TOKEN env var"
            )
        
        required_github = ['owner', 'repo', 'base_branch']
        for key in required_github:
            if not config.get('github', {}).get(key):
                raise ValueError(f"Missing required GitHub config: {key}")
        
        logger.info("Configuration validated successfully")
