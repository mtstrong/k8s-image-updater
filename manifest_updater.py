"""
Manifest Updater Module

Updates Kubernetes YAML manifest files with new container image tags.
"""

import logging
import os
import yaml
import re
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class ManifestUpdater:
    """Update Kubernetes manifest files with new image tags"""
    
    def __init__(self, config):
        """Initialize updater with configuration"""
        self.config = config
    
    def update_manifests(self, updates_available: List[Dict]) -> List[str]:
        """Update manifest files and return list of modified files"""
        updated_files = []
        manifest_paths = self._get_manifest_paths()
        
        # Find all deployment manifests
        deployment_files = self._find_deployment_files(manifest_paths)
        logger.info(f"Found {len(deployment_files)} deployment manifest files")
        
        # Process each update
        for update_item in updates_available:
            deployment = update_item['deployment']
            update = update_item['update']
            
            # Find the manifest file for this deployment
            manifest_file = self._find_manifest_for_deployment(
                deployment_files,
                deployment
            )
            
            if not manifest_file:
                logger.warning(
                    f"Could not find manifest file for "
                    f"{deployment['namespace']}/{deployment['deployment']}"
                )
                continue
            
            # Update the manifest file
            success = self._update_manifest_file(
                manifest_file,
                deployment,
                update
            )
            
            if success and manifest_file not in updated_files:
                updated_files.append(manifest_file)
        
        logger.info(f"Successfully updated {len(updated_files)} manifest files")
        return updated_files
    
    def _get_manifest_paths(self) -> List[Path]:
        """Get list of manifest paths to search"""
        paths = []
        configured_paths = self.config.get('kubernetes', {}).get('manifest_paths', [])
        
        for path_str in configured_paths:
            # Handle relative paths
            if path_str.startswith('../'):
                # Relative to parent directory
                base_path = Path.cwd().parent
                path = base_path / path_str[3:]
            else:
                path = Path(path_str)
            
            if path.exists():
                paths.append(path)
            else:
                logger.warning(f"Manifest path does not exist: {path}")
        
        return paths
    
    def _find_deployment_files(self, manifest_paths: List[Path]) -> List[Path]:
        """Find all deployment YAML files in manifest paths"""
        deployment_files = []
        patterns = self.config.get('kubernetes', {}).get(
            'deployment_patterns',
            ['**/deployment.yaml', '**/*-deployment.yaml']
        )
        
        for base_path in manifest_paths:
            for pattern in patterns:
                files = base_path.glob(pattern)
                deployment_files.extend(files)
        
        # Remove duplicates
        return list(set(deployment_files))
    
    def _find_manifest_for_deployment(
        self,
        deployment_files: List[Path],
        deployment: Dict
    ) -> Path:
        """Find the manifest file that contains the given deployment"""
        namespace = deployment['namespace']
        dep_name = deployment['deployment']
        image_name = deployment['image']
        
        for manifest_file in deployment_files:
            try:
                with open(manifest_file, 'r') as f:
                    content = f.read()
                    docs = yaml.safe_load_all(content)
                    
                    for doc in docs:
                        if not doc or doc.get('kind') != 'Deployment':
                            continue
                        
                        # Check if this is the right deployment
                        metadata = doc.get('metadata', {})
                        if metadata.get('name') == dep_name:
                            # Also check namespace if specified
                            doc_namespace = metadata.get('namespace')
                            if not doc_namespace or doc_namespace == namespace:
                                # Verify image is present
                                if self._deployment_contains_image(doc, image_name):
                                    return manifest_file
            
            except Exception as e:
                logger.error(f"Error reading manifest {manifest_file}: {e}")
                continue
        
        return None
    
    def _deployment_contains_image(self, deployment_doc: Dict, image_name: str) -> bool:
        """Check if deployment contains the specified image"""
        try:
            containers = deployment_doc['spec']['template']['spec']['containers']
            for container in containers:
                container_image = container.get('image', '')
                # Check if image name matches (without tag)
                if image_name in container_image or container_image.startswith(image_name):
                    return True
        except (KeyError, TypeError):
            pass
        
        return False
    
    def _update_manifest_file(
        self,
        manifest_file: Path,
        deployment: Dict,
        update: Dict
    ) -> bool:
        """Update a specific manifest file with new image tag"""
        try:
            logger.info(f"Updating {manifest_file}")
            
            # Read the file
            with open(manifest_file, 'r') as f:
                content = f.read()
            
            # Build the old and new image strings
            old_image = f"{deployment['image']}:{deployment['current_tag']}"
            new_image = f"{deployment['image']}:{update['latest_tag']}"
            
            # Replace the image
            updated_content = content.replace(old_image, new_image)
            
            if updated_content == content:
                logger.warning(f"No changes made to {manifest_file} (image string not found)")
                return False
            
            # Write back to file
            with open(manifest_file, 'w') as f:
                f.write(updated_content)
            
            logger.info(
                f"  Updated {deployment['deployment']}: "
                f"{deployment['current_tag']} → {update['latest_tag']}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating manifest {manifest_file}: {e}")
            return False
