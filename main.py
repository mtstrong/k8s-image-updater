#!/usr/bin/env python3
"""
K8s Image Updater Agent - Main Entry Point

This agent scans Kubernetes deployments for container images,
checks for available updates, and creates GitHub PRs to update manifests.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from scanner import K8sScanner
from registry import RegistryClient
from manifest_updater import ManifestUpdater
from github_pr import GitHubPRCreator
from config_loader import ConfigLoader
from changelog_fetcher import ChangelogFetcher
from ai_analyzer import AIAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/k8s-image-updater.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(
        description='K8s Image Updater Agent - Automated container image updates'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Scan and report updates without creating PR'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info("K8s Image Updater Agent Starting")
    logger.info(f"Date: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = ConfigLoader.load(args.config)
        
        # Initialize components
        scanner = K8sScanner(config)
        registry_client = RegistryClient(config)
        manifest_updater = ManifestUpdater(config)
        github_pr_creator = GitHubPRCreator(config)
        changelog_fetcher = ChangelogFetcher(config)
        ai_analyzer = AIAnalyzer(config)
        
        # Step 1: Scan K8s cluster for current deployments
        logger.info("Scanning Kubernetes cluster for deployments...")
        deployments = scanner.scan_cluster()
        logger.info(f"Found {len(deployments)} deployments")
        
        if not deployments:
            logger.warning("No deployments found. Exiting.")
            return 0
        
        # Step 2: Check for available updates
        logger.info("Checking registries for image updates...")
        updates_available = []
        
        for deployment in deployments:
            logger.debug(f"Checking {deployment['name']} - {deployment['image']}")
            update_info = registry_client.check_for_updates(
                deployment['image'],
                deployment['current_tag']
            )
            
            if update_info and update_info['update_available']:
                # Fetch changelog
                changelog = None
                if config.get('ai', {}).get('analyze_changelogs', True):
                    logger.debug(f"Fetching changelog for {deployment['name']}")
                    changelog = changelog_fetcher.fetch_changelog(
                        deployment['image'],
                        deployment['current_tag'],
                        update_info['latest_tag']
                    )
                
                # AI analysis
                analysis = None
                if config.get('ai', {}).get('risk_prediction', True):
                    logger.debug(f"Running AI analysis for {deployment['name']}")
                    analysis = ai_analyzer.analyze_update(
                        deployment,
                        update_info,
                        changelog
                    )
                
                updates_available.append({
                    'deployment': deployment,
                    'update': update_info,
                    'changelog': changelog,
                    'analysis': analysis
                })
                
                # Log with risk indicator
                risk_indicator = ""
                if analysis:
                    risk_level = analysis.get('risk_level', 'unknown')
                    risk_icons = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🟠',
                        'critical': '🔴'
                    }
                    risk_indicator = f" {risk_icons.get(risk_level, '⚪')} Risk: {risk_level.upper()}"
                
                logger.info(
                    f"  ✓ Update available: {deployment['name']} "
                    f"{deployment['current_tag']} → {update_info['latest_tag']}"
                    f"{risk_indicator}"
                )
        
        logger.info(f"Found {len(updates_available)} updates available")
        
        if not updates_available:
            logger.info("No updates available. Exiting.")
            return 0
        
        # Generate summary report
        summary = generate_summary(updates_available)
        logger.info("\n" + summary)
        
        if args.dry_run:
            logger.info("Dry-run mode: Skipping PR creation")
            return 0
        
        # Step 3: Update manifest files
        logger.info("Updating manifest files...")
        updated_files = manifest_updater.update_manifests(updates_available)
        logger.info(f"Updated {len(updated_files)} manifest files")
        
        # Step 4: Create GitHub PR
        logger.info("Creating GitHub Pull Request...")
        pr_url = github_pr_creator.create_pr(
            updated_files=updated_files,
            updates=updates_available,
            summary=summary
        )
        
        logger.info(f"✓ Pull Request created: {pr_url}")
        logger.info("=" * 60)
        logger.info("K8s Image Updater Agent Completed Successfully")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


def generate_summary(updates_available):
    """Generate a summary report of available updates"""
    lines = [
        "",
        "=" * 60,
        "WEEKLY IMAGE UPDATE SUMMARY",
        "=" * 60,
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        f"Total Updates: {len(updates_available)}",
        ""
    ]
    
    # Group by update type
    major = [u for u in updates_available if u['update']['update_type'] == 'major']
    minor = [u for u in updates_available if u['update']['update_type'] == 'minor']
    patch = [u for u in updates_available if u['update']['update_type'] == 'patch']
    
    lines.append("Updates by Category:")
    lines.append("")
    lines.append(f"  Major: {len(major)}")
    lines.append(f"  Minor: {len(minor)}")
    lines.append(f"  Patch: {len(patch)}")
    lines.append("")
    
    # Risk distribution (if AI analysis available)
    analyses = [u.get('analysis') for u in updates_available if u.get('analysis')]
    if analyses:
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for analysis in analyses:
            level = analysis.get('risk_level', 'medium')
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        lines.append("Risk Distribution:")
        lines.append("")
        lines.append(f"  🔴 Critical: {risk_counts['critical']}")
        lines.append(f"  🟠 High: {risk_counts['high']}")
        lines.append(f"  🟡 Medium: {risk_counts['medium']}")
        lines.append(f"  🟢 Low: {risk_counts['low']}")
        lines.append("")
    
    lines.append("Detailed Updates:")
    lines.append("")
    
    for item in updates_available:
        dep = item['deployment']
        upd = item['update']
        analysis = item.get('analysis')
        
        # Build update line
        update_line = (
            f"  • {dep['namespace']}/{dep['name']}: "
            f"{dep['image']}:{dep['current_tag']} → :{upd['latest_tag']} "
            f"[{upd['update_type'].upper()}]"
        )
        
        # Add risk indicator
        if analysis:
            risk_level = analysis.get('risk_level', 'unknown')
            risk_icons = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }
            update_line += f" {risk_icons.get(risk_level, '⚪')}"
        
        lines.append(update_line)
        
        # Add breaking changes if any
        if analysis and analysis.get('breaking_changes'):
            for change in analysis['breaking_changes'][:2]:  # Limit to 2
                lines.append(f"      ⚠️  {change}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


if __name__ == '__main__':
    sys.exit(main())
