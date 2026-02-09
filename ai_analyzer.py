"""
AI Analyzer Module

Uses LLM (OpenAI API) to analyze changelogs for breaking changes,
security issues, and deployment risks.
"""

import logging
import os
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI-powered changelog and risk analysis"""
    
    def __init__(self, config):
        """Initialize AI analyzer"""
        self.config = config
        self.enabled = config.get('ai', {}).get('enabled', True)
        
        if not self.enabled:
            logger.info("AI analysis disabled")
            return
        
        # Get API key
        api_key = config.get('ai', {}).get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            logger.warning("OpenAI API key not configured. AI analysis will be skipped.")
            self.enabled = False
            return
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('ai', {}).get('model', 'gpt-4o-mini')
        
        logger.info(f"AI analyzer initialized with model: {self.model}")
    
    def analyze_update(
        self,
        deployment: Dict,
        update: Dict,
        changelog: Optional[Dict]
    ) -> Dict:
        """
        Analyze an update and return risk assessment
        
        Returns:
        {
            'risk_score': float (0-10),
            'risk_level': str (low/medium/high/critical),
            'breaking_changes': List[str],
            'security_updates': List[str],
            'notable_changes': List[str],
            'recommendations': List[str],
            'summary': str
        }
        """
        if not self.enabled:
            return self._default_analysis(update)
        
        logger.info(f"Analyzing update: {deployment['name']} {update['current_tag']} → {update['latest_tag']}")
        
        try:
            # Prepare context for AI
            context = self._build_analysis_context(deployment, update, changelog)
            
            # Get AI analysis
            analysis = self._analyze_with_ai(context)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(update, analysis)
            
            return {
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'breaking_changes': analysis.get('breaking_changes', []),
                'security_updates': analysis.get('security_updates', []),
                'notable_changes': analysis.get('notable_changes', []),
                'recommendations': analysis.get('recommendations', []),
                'summary': analysis.get('summary', ''),
                'ai_enabled': True
            }
        
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self._default_analysis(update)
    
    def _build_analysis_context(
        self,
        deployment: Dict,
        update: Dict,
        changelog: Optional[Dict]
    ) -> str:
        """Build context string for AI analysis"""
        
        lines = [
            f"Application: {deployment['deployment']}",
            f"Container Image: {deployment['image']}",
            f"Current Version: {update['current_tag']}",
            f"New Version: {update['latest_tag']}",
            f"Update Type: {update['update_type']}",
            ""
        ]
        
        if changelog:
            lines.append("Changelog:")
            lines.append("=" * 60)
            lines.append(changelog.get('content', 'No changelog available'))
            lines.append("=" * 60)
        else:
            lines.append("Changelog: Not available")
        
        return "\n".join(lines)
    
    def _analyze_with_ai(self, context: str) -> Dict:
        """Use OpenAI to analyze the changelog"""
        
        system_prompt = """You are an expert DevOps engineer analyzing container image updates for a Kubernetes cluster.
Your job is to review changelogs and identify:
1. Breaking changes that could break the application
2. Security updates or vulnerabilities fixed
3. Notable features or improvements
4. Deployment recommendations

Respond in JSON format with these fields:
{
    "breaking_changes": ["list of breaking changes"],
    "security_updates": ["list of security updates"],
    "notable_changes": ["list of notable changes"],
    "recommendations": ["list of recommendations for deployment"],
    "summary": "brief 2-3 sentence summary"
}

If the changelog is not available or unclear, provide a basic analysis based on version numbers."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            logger.debug(f"AI analysis completed: {len(analysis.get('breaking_changes', []))} breaking changes found")
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return {
                'breaking_changes': [],
                'security_updates': [],
                'notable_changes': [],
                'recommendations': [],
                'summary': 'AI analysis failed'
            }
    
    def _calculate_risk_score(self, update: Dict, analysis: Dict) -> float:
        """
        Calculate risk score (0-10)
        
        Factors:
        - Update type (major=high, minor=medium, patch=low)
        - Breaking changes count
        - Security updates (reduces risk)
        - AI analysis
        """
        score = 0.0
        
        # Base score from update type
        update_type_scores = {
            'major': 7.0,
            'minor': 4.0,
            'patch': 2.0,
            'unknown': 5.0
        }
        score += update_type_scores.get(update['update_type'], 5.0)
        
        # Breaking changes increase risk
        breaking_count = len(analysis.get('breaking_changes', []))
        score += min(breaking_count * 1.5, 3.0)
        
        # Security updates reduce risk slightly
        security_count = len(analysis.get('security_updates', []))
        score -= min(security_count * 0.5, 2.0)
        
        # Clamp to 0-10 range
        score = max(0.0, min(10.0, score))
        
        return round(score, 1)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score < 3.0:
            return 'low'
        elif risk_score < 6.0:
            return 'medium'
        elif risk_score < 8.0:
            return 'high'
        else:
            return 'critical'
    
    def _default_analysis(self, update: Dict) -> Dict:
        """Fallback analysis when AI is disabled or fails"""
        
        # Simple heuristic-based analysis
        update_type = update['update_type']
        
        risk_scores = {
            'major': 7.0,
            'minor': 4.0,
            'patch': 2.0,
            'unknown': 5.0
        }
        
        risk_score = risk_scores.get(update_type, 5.0)
        
        recommendations = []
        if update_type == 'major':
            recommendations.append("Test thoroughly in staging environment")
            recommendations.append("Review changelog for breaking changes")
        elif update_type == 'minor':
            recommendations.append("Review release notes")
            recommendations.append("Monitor application after deployment")
        else:
            recommendations.append("Low risk update - can deploy with standard process")
        
        return {
            'risk_score': risk_score,
            'risk_level': self._get_risk_level(risk_score),
            'breaking_changes': [],
            'security_updates': [],
            'notable_changes': [],
            'recommendations': recommendations,
            'summary': f"Automated analysis: {update_type} version update",
            'ai_enabled': False
        }
    
    def generate_pr_insights(self, all_analyses: List[Dict]) -> str:
        """Generate AI insights summary for PR description"""
        
        if not self.enabled:
            return ""
        
        try:
            # Count risk levels
            risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            for analysis in all_analyses:
                level = analysis.get('risk_level', 'medium')
                risk_counts[level] = risk_counts.get(level, 0) + 1
            
            # Collect all breaking changes
            all_breaking = []
            for analysis in all_analyses:
                all_breaking.extend(analysis.get('breaking_changes', []))
            
            # Generate summary
            lines = [
                "## 🤖 AI-Powered Risk Analysis",
                "",
                "### Risk Distribution",
                f"- 🔴 Critical: {risk_counts['critical']}",
                f"- 🟠 High: {risk_counts['high']}",
                f"- 🟡 Medium: {risk_counts['medium']}",
                f"- 🟢 Low: {risk_counts['low']}",
                ""
            ]
            
            if all_breaking:
                lines.append("### ⚠️ Breaking Changes Detected")
                lines.append("")
                for change in all_breaking[:5]:  # Limit to top 5
                    lines.append(f"- {change}")
                lines.append("")
            
            # Overall recommendation
            if risk_counts['critical'] > 0 or risk_counts['high'] > 0:
                lines.extend([
                    "### 🚨 Recommendation",
                    "",
                    "**High-risk updates detected.** Please:",
                    "- Review all breaking changes carefully",
                    "- Test in staging environment first",
                    "- Plan for potential rollback",
                    ""
                ])
            elif risk_counts['medium'] > 0:
                lines.extend([
                    "### ✅ Recommendation",
                    "",
                    "**Medium-risk updates.** Standard deployment process recommended:",
                    "- Review release notes",
                    "- Monitor applications after deployment",
                    ""
                ])
            else:
                lines.extend([
                    "### ✅ Recommendation",
                    "",
                    "**Low-risk updates.** Safe to deploy with standard process.",
                    ""
                ])
            
            return "\n".join(lines)
        
        except Exception as e:
            logger.error(f"Error generating PR insights: {e}")
            return ""
