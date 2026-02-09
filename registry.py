"""
Container Registry Client Module

Checks container registries for image updates using registry APIs.
"""

import logging
import requests
import re
from typing import Optional, Dict
from packaging import version

logger = logging.getLogger(__name__)


class RegistryClient:
    """Client for querying container registries"""
    
    def __init__(self, config):
        """Initialize registry client with configuration"""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'K8s-Image-Updater/1.0'
        })
    
    def check_for_updates(self, image: str, current_tag: str) -> Optional[Dict]:
        """Check if newer version of image is available"""
        logger.debug(f"Checking updates for {image}:{current_tag}")
        
        # Determine registry
        registry_type = self._identify_registry(image)
        
        if not registry_type:
            logger.warning(f"Unknown registry for image: {image}")
            return None
        
        # Get available tags
        available_tags = self._get_available_tags(image, registry_type)
        
        if not available_tags:
            logger.warning(f"Could not fetch tags for {image}")
            return None
        
        # Find latest compatible version
        latest_tag = self._find_latest_version(
            current_tag,
            available_tags
        )
        
        if not latest_tag or latest_tag == current_tag:
            logger.debug(f"No update available for {image}:{current_tag}")
            return None
        
        # Determine update type
        update_type = self._determine_update_type(current_tag, latest_tag)
        
        # Check if update is allowed by policy
        if not self._is_update_allowed(update_type):
            logger.info(f"Update blocked by policy: {image} {current_tag} → {latest_tag} ({update_type})")
            return None
        
        return {
            'update_available': True,
            'current_tag': current_tag,
            'latest_tag': latest_tag,
            'update_type': update_type,
            'registry': registry_type
        }
    
    def _identify_registry(self, image: str) -> Optional[str]:
        """Identify which registry the image is from"""
        if image.startswith('lscr.io/') or image.startswith('linuxserver/'):
            return 'lscr'
        elif image.startswith('ghcr.io/'):
            return 'ghcr'
        elif '/' in image and '.' not in image.split('/')[0]:
            # DockerHub format: namespace/image
            return 'dockerhub'
        elif '/' not in image:
            # DockerHub official image
            return 'dockerhub'
        else:
            return None
    
    def _get_available_tags(self, image: str, registry_type: str) -> list:
        """Fetch available tags from registry"""
        
        if registry_type == 'dockerhub':
            return self._get_dockerhub_tags(image)
        elif registry_type == 'lscr':
            return self._get_lscr_tags(image)
        elif registry_type == 'ghcr':
            return self._get_ghcr_tags(image)
        else:
            return []
    
    def _get_dockerhub_tags(self, image: str) -> list:
        """Get tags from DockerHub"""
        # Parse image name
        if '/' in image:
            namespace, repo = image.rsplit('/', 1)
        else:
            namespace = 'library'
            repo = image
        
        try:
            url = f"https://registry.hub.docker.com/v2/repositories/{namespace}/{repo}/tags"
            params = {'page_size': 100}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tags = [tag['name'] for tag in data.get('results', [])]
            
            logger.debug(f"Found {len(tags)} tags for {image}")
            return tags
            
        except Exception as e:
            logger.error(f"Error fetching DockerHub tags for {image}: {e}")
            return []
    
    def _get_lscr_tags(self, image: str) -> list:
        """Get tags from LinuxServer.io registry"""
        # LinuxServer images use DockerHub API
        if image.startswith('lscr.io/'):
            image = image.replace('lscr.io/', '')
        
        if not image.startswith('linuxserver/'):
            image = f"linuxserver/{image}"
        
        return self._get_dockerhub_tags(image)
    
    def _get_ghcr_tags(self, image: str) -> list:
        """Get tags from GitHub Container Registry"""
        # GHCR doesn't have a public tags API like DockerHub
        # Would need GitHub token for full functionality
        logger.warning(f"GHCR tag fetching not fully implemented for {image}")
        return []
    
    def _find_latest_version(self, current_tag: str, available_tags: list) -> Optional[str]:
        """Find the latest semantic version from available tags"""
        # Parse current version
        current_ver = self._parse_version(current_tag)
        if not current_ver:
            logger.debug(f"Could not parse version from tag: {current_tag}")
            return None
        
        # Parse all available versions
        version_map = {}
        for tag in available_tags:
            parsed = self._parse_version(tag)
            if parsed:
                version_map[parsed] = tag
        
        if not version_map:
            return None
        
        # Find latest
        versions = sorted(version_map.keys(), reverse=True)
        latest_ver = versions[0]
        
        if latest_ver > current_ver:
            return version_map[latest_ver]
        
        return None
    
    def _parse_version(self, tag: str) -> Optional[version.Version]:
        """Parse version from tag string"""
        # Remove common prefixes
        tag_clean = tag.lstrip('v')
        
        # Handle tags like "4.0.16.2944-ls301" -> "4.0.16.2944"
        # Extract version-like pattern
        match = re.match(r'^(\d+(?:\.\d+)*)', tag_clean)
        if match:
            version_str = match.group(1)
            try:
                return version.parse(version_str)
            except Exception:
                pass
        
        return None
    
    def _determine_update_type(self, current_tag: str, latest_tag: str) -> str:
        """Determine if update is major, minor, or patch"""
        current_ver = self._parse_version(current_tag)
        latest_ver = self._parse_version(latest_tag)
        
        if not current_ver or not latest_ver:
            return 'unknown'
        
        # Compare major.minor.patch
        current_parts = str(current_ver).split('.')
        latest_parts = str(latest_ver).split('.')
        
        # Pad to at least 3 parts
        while len(current_parts) < 3:
            current_parts.append('0')
        while len(latest_parts) < 3:
            latest_parts.append('0')
        
        if current_parts[0] != latest_parts[0]:
            return 'major'
        elif current_parts[1] != latest_parts[1]:
            return 'minor'
        else:
            return 'patch'
    
    def _is_update_allowed(self, update_type: str) -> bool:
        """Check if update type is allowed by policy"""
        policy = self.config.get('update_policy', {})
        
        if update_type == 'major':
            return policy.get('allow_major', False)
        elif update_type == 'minor':
            return policy.get('allow_minor', True)
        elif update_type == 'patch':
            return policy.get('allow_patch', True)
        
        return False
