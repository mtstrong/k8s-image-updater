"""
Kubernetes Cluster Scanner Module

Scans the K8s cluster for deployments and extracts container image information.
"""

import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class K8sScanner:
    """Scan Kubernetes cluster for deployments"""
    
    def __init__(self, app_config):
        """Initialize scanner with configuration"""
        self.config = app_config
        self._init_k8s_client()
    
    def _init_k8s_client(self):
        """Initialize Kubernetes client"""
        try:
            # Try in-cluster config first (when running as pod)
            config.load_incluster_config()
            logger.info("Using in-cluster Kubernetes configuration")
        except config.ConfigException:
            # Fall back to kubeconfig file
            try:
                config.load_kube_config()
                logger.info("Using kubeconfig file")
            except config.ConfigException as e:
                raise RuntimeError(f"Could not configure Kubernetes client: {e}")
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
    
    def scan_cluster(self):
        """Scan cluster and return list of deployments with image info"""
        deployments = []
        namespaces = self._get_namespaces_to_scan()
        
        for namespace in namespaces:
            try:
                logger.debug(f"Scanning namespace: {namespace}")
                deps = self._scan_namespace(namespace)
                deployments.extend(deps)
            except ApiException as e:
                logger.error(f"Error scanning namespace {namespace}: {e}")
                continue
        
        return deployments
    
    def _get_namespaces_to_scan(self):
        """Get list of namespaces to scan"""
        configured_namespaces = self.config.get('kubernetes', {}).get('namespaces', [])
        
        if configured_namespaces:
            return configured_namespaces
        
        # Get all namespaces
        try:
            ns_list = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in ns_list.items]
        except ApiException as e:
            logger.error(f"Error listing namespaces: {e}")
            return []
    
    def _scan_namespace(self, namespace):
        """Scan a single namespace for deployments"""
        deployments = []
        
        try:
            deps = self.apps_v1.list_namespaced_deployment(namespace)
            
            for dep in deps.items:
                deployment_info = self._extract_deployment_info(dep, namespace)
                if deployment_info:
                    deployments.extend(deployment_info)
        
        except ApiException as e:
            logger.error(f"Error listing deployments in {namespace}: {e}")
        
        return deployments
    
    def _extract_deployment_info(self, deployment, namespace):
        """Extract container image information from deployment"""
        results = []
        
        deployment_name = deployment.metadata.name
        containers = deployment.spec.template.spec.containers
        
        for container in containers:
            image_full = container.image
            
            # Parse image name and tag
            if ':' in image_full:
                image, tag = image_full.rsplit(':', 1)
            else:
                image = image_full
                tag = 'latest'
            
            # Skip if image matches ignore patterns
            if self._should_ignore_image(image_full):
                logger.debug(f"Ignoring image: {image_full}")
                continue
            
            results.append({
                'namespace': namespace,
                'deployment': deployment_name,
                'name': f"{deployment_name}/{container.name}",
                'container': container.name,
                'image': image,
                'current_tag': tag,
                'full_image': image_full
            })
        
        return results
    
    def _should_ignore_image(self, image):
        """Check if image should be ignored based on configuration"""
        import re
        
        ignore_patterns = self.config.get('update_policy', {}).get('ignore_images', [])
        
        for pattern in ignore_patterns:
            if re.match(pattern, image):
                return True
        
        return False
