"""
Changelog Fetcher Module

Fetches release notes and changelogs from GitHub and other sources.
"""

import logging
import requests
from typing import Optional, Dict, List
from github import Github, GithubException
from packaging import version

logger = logging.getLogger(__name__)


class ChangelogFetcher:
    """Fetch changelogs for container images"""
    
    def __init__(self, config):
        """Initialize changelog fetcher"""
        self.config = config
        github_token = config.get('github', {}).get('token')
        self.github = Github(github_token) if github_token else None
    
    def fetch_changelog(
        self,
        image: str,
        current_tag: str,
        new_tag: str
    ) -> Optional[Dict]:
        """
        Fetch changelog between two versions
        
        Returns dict with:
        - source: str (github_release, dockerhub, etc.)
        - content: str (changelog text)
        - url: str (link to changelog)
        - releases: List[Dict] (individual release notes)
        """
        logger.debug(f"Fetching changelog for {image}: {current_tag} → {new_tag}")
        
        # Try GitHub releases first
        github_repo = self._identify_github_repo(image)
        if github_repo:
            changelog = self._fetch_github_releases(
                github_repo,
                current_tag,
                new_tag
            )
            if changelog:
                return changelog
        
        # Try DockerHub description
        if self._is_dockerhub_image(image):
            changelog = self._fetch_dockerhub_description(image)
            if changelog:
                return changelog
        
        logger.warning(f"Could not fetch changelog for {image}")
        return None
    
    def _identify_github_repo(self, image: str) -> Optional[str]:
        """Try to identify GitHub repository for an image"""
        
        # Known mappings for popular images
        known_repos = {
            'linuxserver/sonarr': 'linuxserver/docker-sonarr',
            'linuxserver/radarr': 'linuxserver/docker-radarr',
            'linuxserver/overseerr': 'linuxserver/docker-overseerr',
            'linuxserver/prowlarr': 'linuxserver/docker-prowlarr',
            'linuxserver/readarr': 'linuxserver/docker-readarr',
            'linuxserver/lidarr': 'linuxserver/docker-lidarr',
            'linuxserver/bazarr': 'linuxserver/docker-bazarr',
            'linuxserver/tautulli': 'linuxserver/docker-tautulli',
            'linuxserver/plex': 'linuxserver/docker-plex',
        }
        
        # Handle lscr.io prefix
        image_clean = image.replace('lscr.io/', '').replace('linuxserver/', 'linuxserver/')
        
        # Check known mappings
        if image_clean in known_repos:
            return known_repos[image_clean]
        
        # Try direct mapping for ghcr.io images
        if image.startswith('ghcr.io/'):
            # ghcr.io/owner/repo -> owner/repo
            parts = image.replace('ghcr.io/', '').split('/')
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        
        return None
    
    def _fetch_github_releases(
        self,
        repo_name: str,
        current_tag: str,
        new_tag: str
    ) -> Optional[Dict]:
        """Fetch GitHub releases between two tags"""
        if not self.github:
            return None
        
        try:
            repo = self.github.get_repo(repo_name)
            
            # Get all releases
            releases = []
            for release in repo.get_releases():
                tag = release.tag_name.lstrip('v')
                
                # Check if this release is between current and new
                if self._version_in_range(tag, current_tag, new_tag):
                    releases.append({
                        'tag': release.tag_name,
                        'name': release.title,
                        'body': release.body,
                        'url': release.html_url,
                        'published_at': release.published_at.isoformat() if release.published_at else None,
                        'prerelease': release.prerelease,
                        'draft': release.draft
                    })
            
            if not releases:
                logger.debug(f"No releases found between {current_tag} and {new_tag}")
                return None
            
            # Combine release notes
            combined_changelog = "\n\n".join([
                f"## {r['tag']} - {r['name']}\n{r['body']}"
                for r in releases
            ])
            
            return {
                'source': 'github_release',
                'content': combined_changelog,
                'url': f"https://github.com/{repo_name}/releases",
                'releases': releases,
                'repo': repo_name
            }
        
        except GithubException as e:
            logger.error(f"Error fetching GitHub releases for {repo_name}: {e}")
            return None
    
    def _fetch_dockerhub_description(self, image: str) -> Optional[Dict]:
        """Fetch DockerHub repository description"""
        try:
            # Parse image name
            if '/' in image:
                namespace, repo = image.rsplit('/', 1)
            else:
                namespace = 'library'
                repo = image
            
            url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            description = data.get('description', '')
            full_description = data.get('full_description', '')
            
            if full_description:
                return {
                    'source': 'dockerhub',
                    'content': full_description,
                    'url': f"https://hub.docker.com/r/{namespace}/{repo}",
                    'description': description
                }
        
        except Exception as e:
            logger.error(f"Error fetching DockerHub description for {image}: {e}")
        
        return None
    
    def _is_dockerhub_image(self, image: str) -> bool:
        """Check if image is from DockerHub"""
        return not any(image.startswith(prefix) for prefix in ['ghcr.io/', 'lscr.io/', 'gcr.io/'])
    
    def _version_in_range(self, tag: str, current: str, new: str) -> bool:
        """Check if a version tag is between current and new versions"""
        from packaging import version
        
        try:
            tag_clean = tag.lstrip('v')
            current_clean = current.lstrip('v')
            new_clean = new.lstrip('v')
            
            # Extract version numbers
            tag_ver = self._extract_version(tag_clean)
            current_ver = self._extract_version(current_clean)
            new_ver = self._extract_version(new_clean)
            
            if not all([tag_ver, current_ver, new_ver]):
                return False
            
            return current_ver < tag_ver <= new_ver
        
        except Exception:
            return False
    
    def _extract_version(self, tag: str) -> Optional[version.Version]:
        """Extract version from tag"""
        import re
        
        match = re.match(r'^(\d+(?:\.\d+)*)', tag)
        if match:
            try:
                return version.parse(match.group(1))
            except Exception:
                pass
        
        return None
