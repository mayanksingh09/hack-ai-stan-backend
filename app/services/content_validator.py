"""
Content Validation Service for validating generated content against platform rules
and providing fallback content generation for failed validations.
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from models.platform_rules import PlatformType, get_platform_rules, PlatformRules
from models.content import VideoTranscript, PlatformContent, ContentGenerationOptions

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must be fixed - content unusable
    WARNING = "warning"  # Should be fixed - content may underperform
    INFO = "info"       # Nice to fix - minor optimization


@dataclass
class ValidationIssue:
    """Represents a validation issue found in content."""
    field: str
    severity: ValidationSeverity
    message: str
    current_value: Any
    expected_value: Optional[Any] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    score: float  # 0-100, quality score
    issues: List[ValidationIssue]
    platform: PlatformType
    content: PlatformContent


class ContentValidator:
    """Service for validating generated content against platform rules and quality standards."""
    
    def __init__(self):
        self.quality_weights = {
            "character_limit": 0.3,
            "tag_count": 0.25,
            "content_quality": 0.2,
            "platform_style": 0.15,
            "engagement_potential": 0.1
        }
    
    def validate_content(self, content: PlatformContent, 
                        strict_mode: bool = True) -> ValidationResult:
        """Validate content against platform rules and quality standards."""
        rules = get_platform_rules(content.platform)
        issues = []
        
        # Validate character limits
        char_issues = self._validate_character_limits(content, rules)
        issues.extend(char_issues)
        
        # Validate tag count
        tag_issues = self._validate_tag_count(content, rules)
        issues.extend(tag_issues)
        
        # Validate content quality
        quality_issues = self._validate_content_quality(content, rules)
        issues.extend(quality_issues)
        
        # Validate platform-specific requirements
        platform_issues = self._validate_platform_specific(content, rules)
        issues.extend(platform_issues)
        
        # Calculate overall validity
        error_count = len([issue for issue in issues if issue.severity == ValidationSeverity.ERROR])
        is_valid = error_count == 0 if strict_mode else error_count <= 1
        
        # Calculate quality score
        score = self._calculate_quality_score(content, rules, issues)
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            platform=content.platform,
            content=content
        )
    
    def _validate_character_limits(self, content: PlatformContent, 
                                 rules: PlatformRules) -> List[ValidationIssue]:
        """Validate character limits for the platform."""
        issues = []
        
        # Title character limit
        if content.character_count > rules.title_max_length:
            issues.append(ValidationIssue(
                field="title",
                severity=ValidationSeverity.ERROR,
                message=f"Title exceeds maximum length",
                current_value=content.character_count,
                expected_value=rules.title_max_length,
                suggestion=f"Reduce title to {rules.title_max_length} characters or less"
            ))
        elif content.character_count > rules.title_max_length * 0.9:
            issues.append(ValidationIssue(
                field="title",
                severity=ValidationSeverity.WARNING,
                message="Title is very close to character limit",
                current_value=content.character_count,
                expected_value=rules.title_max_length,
                suggestion="Consider shortening for better display"
            ))
        
        # Special case for X/Twitter total character limit
        if content.platform == PlatformType.X_TWITTER:
            total_chars = len(content.title) + sum(len(tag) + 1 for tag in content.tags)
            if total_chars > rules.title_max_length:
                issues.append(ValidationIssue(
                    field="total_content",
                    severity=ValidationSeverity.ERROR,
                    message="Total content (title + hashtags) exceeds character limit",
                    current_value=total_chars,
                    expected_value=rules.title_max_length,
                    suggestion="Reduce title length or number of hashtags"
                ))
        
        return issues
    
    def _validate_tag_count(self, content: PlatformContent, 
                          rules: PlatformRules) -> List[ValidationIssue]:
        """Validate hashtag/tag count for the platform."""
        issues = []
        
        if content.tag_count < rules.tag_min_count:
            issues.append(ValidationIssue(
                field="tags",
                severity=ValidationSeverity.ERROR,
                message=f"Too few tags",
                current_value=content.tag_count,
                expected_value=f"{rules.tag_min_count}-{rules.tag_max_count}",
                suggestion=f"Add {rules.tag_min_count - content.tag_count} more relevant tags"
            ))
        elif content.tag_count > rules.tag_max_count:
            issues.append(ValidationIssue(
                field="tags",
                severity=ValidationSeverity.ERROR,
                message=f"Too many tags",
                current_value=content.tag_count,
                expected_value=f"{rules.tag_min_count}-{rules.tag_max_count}",
                suggestion=f"Remove {content.tag_count - rules.tag_max_count} tags"
            ))
        
        return issues
    
    def _validate_content_quality(self, content: PlatformContent, 
                                rules: PlatformRules) -> List[ValidationIssue]:
        """Validate content quality and engagement potential."""
        issues = []
        
        # Check for empty or very short titles
        if len(content.title.strip()) < 10:
            issues.append(ValidationIssue(
                field="title",
                severity=ValidationSeverity.ERROR,
                message="Title too short to be engaging",
                current_value=len(content.title.strip()),
                expected_value="10+ characters",
                suggestion="Create a more descriptive, engaging title"
            ))
        
        # Check for repetitive hashtags
        unique_tags = set(tag.lower() for tag in content.tags)
        if len(unique_tags) < len(content.tags):
            issues.append(ValidationIssue(
                field="tags",
                severity=ValidationSeverity.WARNING,
                message="Duplicate hashtags detected",
                current_value=len(content.tags),
                expected_value=len(unique_tags),
                suggestion="Remove duplicate hashtags for better reach"
            ))
        
        # Check hashtag formatting
        malformed_tags = [tag for tag in content.tags if not tag.startswith('#') or len(tag) <= 1]
        if malformed_tags:
            issues.append(ValidationIssue(
                field="tags",
                severity=ValidationSeverity.ERROR,
                message="Malformed hashtags detected",
                current_value=malformed_tags,
                suggestion="Ensure all tags start with # and have content"
            ))
        
        # Check for low confidence score
        if content.confidence_score < 0.6:
            issues.append(ValidationIssue(
                field="confidence",
                severity=ValidationSeverity.WARNING,
                message="Low AI confidence in generated content",
                current_value=content.confidence_score,
                expected_value="0.6+",
                suggestion="Consider regenerating content for better quality"
            ))
        
        return issues
    
    def _validate_platform_specific(self, content: PlatformContent, 
                                  rules: PlatformRules) -> List[ValidationIssue]:
        """Validate platform-specific requirements."""
        issues = []
        
        # Platform-specific validation rules
        if content.platform == PlatformType.LINKEDIN:
            # Check for professional tone
            casual_indicators = ['hey', 'guys', 'lol', 'omg', 'awesome', 'epic']
            title_lower = content.title.lower()
            found_casual = [word for word in casual_indicators if word in title_lower]
            if found_casual:
                issues.append(ValidationIssue(
                    field="tone",
                    severity=ValidationSeverity.WARNING,
                    message="Content may be too casual for LinkedIn",
                    current_value=found_casual,
                    suggestion="Use more professional language"
                ))
        
        elif content.platform == PlatformType.TIKTOK:
            # Check for trend awareness
            if not any(tag.lower() in ['#fyp', '#viral', '#trending'] for tag in content.tags):
                issues.append(ValidationIssue(
                    field="tags",
                    severity=ValidationSeverity.INFO,
                    message="Consider adding trending TikTok hashtags",
                    suggestion="Add #fyp, #viral, or #trending for better reach"
                ))
        
        elif content.platform == PlatformType.INSTAGRAM:
            # Check for emoji usage (Instagram prefers visual elements)
            if '😀' not in content.title and '🎯' not in content.title and not any(char in content.title for char in '✨🌟💫🔥💯'):
                issues.append(ValidationIssue(
                    field="visual_appeal",
                    severity=ValidationSeverity.INFO,
                    message="Consider adding emojis for better visual appeal",
                    suggestion="Add relevant emojis to increase engagement"
                ))
        
        return issues
    
    def _calculate_quality_score(self, content: PlatformContent, rules: PlatformRules, 
                               issues: List[ValidationIssue]) -> float:
        """Calculate quality score (0-100) based on content and validation issues."""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                base_score -= 25
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 10
            elif issue.severity == ValidationSeverity.INFO:
                base_score -= 5
        
        # Bonus points for good practices
        
        # Character limit utilization (sweet spot: 70-90% of limit)
        char_utilization = content.character_count / rules.title_max_length
        if 0.7 <= char_utilization <= 0.9:
            base_score += 5
        
        # Tag count optimization
        tag_range = rules.tag_max_count - rules.tag_min_count
        if tag_range > 0:
            optimal_tags = rules.tag_min_count + (tag_range * 0.7)  # 70% of range
            if abs(content.tag_count - optimal_tags) <= 2:
                base_score += 5
        
        # Confidence score bonus
        if content.confidence_score >= 0.8:
            base_score += 5
        elif content.confidence_score >= 0.9:
            base_score += 10
        
        return max(0.0, min(100.0, base_score))
    
    def suggest_improvements(self, validation_result: ValidationResult) -> List[str]:
        """Generate improvement suggestions based on validation results."""
        suggestions = []
        
        for issue in validation_result.issues:
            if issue.suggestion:
                suggestions.append(f"{issue.field.title()}: {issue.suggestion}")
        
        # General quality improvements
        if validation_result.score < 80:
            suggestions.append("Consider regenerating content for higher quality")
        
        if validation_result.content.confidence_score < 0.7:
            suggestions.append("Low AI confidence - try different tone or keywords")
        
        return suggestions
    
    def create_fallback_content(self, platform: PlatformType, transcript: VideoTranscript,
                              original_validation: ValidationResult) -> PlatformContent:
        """Create fallback content when original content fails validation."""
        rules = get_platform_rules(platform)
        
        # Analyze issues to create better content
        char_issues = [issue for issue in original_validation.issues 
                      if issue.field == "title" and "character" in issue.message.lower()]
        tag_issues = [issue for issue in original_validation.issues 
                     if issue.field == "tags"]
        
        # Create simplified, rule-compliant content
        fallback_title = self._create_fallback_title(transcript, rules, char_issues)
        fallback_tags = self._create_fallback_tags(transcript, rules, tag_issues)
        
        fallback_content = PlatformContent(
            platform=platform,
            title=fallback_title,
            tags=fallback_tags,
            confidence_score=0.6  # Lower confidence for fallback
        )
        
        # Validate fallback content
        fallback_validation = self.validate_content(fallback_content, strict_mode=False)
        
        if fallback_validation.is_valid:
            logger.info(f"Fallback content created for {platform.value}")
            return fallback_content
        else:
            logger.warning(f"Fallback content also failed validation for {platform.value}")
            return self._create_minimal_content(platform, transcript)
    
    def _create_fallback_title(self, transcript: VideoTranscript, rules: PlatformRules,
                             char_issues: List[ValidationIssue]) -> str:
        """Create a safe fallback title."""
        base_title = transcript.title or "Video Content"
        
        # If title is too long, truncate intelligently
        if char_issues and rules.title_max_length:
            max_len = rules.title_max_length - 3  # Leave space for "..."
            if len(base_title) > max_len:
                # Try to cut at word boundary
                words = base_title.split()
                truncated = ""
                for word in words:
                    if len(truncated + word + " ") <= max_len:
                        truncated += word + " "
                    else:
                        break
                base_title = truncated.strip() + "..."
        
        return base_title[:rules.title_max_length] if rules.title_max_length else base_title
    
    def _create_fallback_tags(self, transcript: VideoTranscript, rules: PlatformRules,
                            tag_issues: List[ValidationIssue]) -> List[str]:
        """Create safe fallback tags."""
        # Extract basic keywords from transcript
        words = transcript.content.lower().split()
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        # Get unique keywords
        unique_keywords = list(set(keywords))[:rules.tag_max_count]
        
        # Ensure we have enough tags
        tags = [f"#{keyword}" for keyword in unique_keywords]
        
        # Fill up to minimum if needed
        while len(tags) < rules.tag_min_count:
            generic_tags = ["#content", "#video", "#social", "#media", "#digital"]
            for tag in generic_tags:
                if tag not in tags and len(tags) < rules.tag_min_count:
                    tags.append(tag)
        
        return tags[:rules.tag_max_count]
    
    def _create_minimal_content(self, platform: PlatformType, transcript: VideoTranscript) -> PlatformContent:
        """Create minimal viable content as last resort."""
        rules = get_platform_rules(platform)
        
        minimal_title = "Video Content"[:rules.title_max_length]
        minimal_tags = ["#content"]
        
        # Add minimum required tags
        while len(minimal_tags) < rules.tag_min_count:
            minimal_tags.append(f"#tag{len(minimal_tags)}")
        
        return PlatformContent(
            platform=platform,
            title=minimal_title,
            tags=minimal_tags[:rules.tag_max_count],
            confidence_score=0.3  # Very low confidence for minimal content
        )


# Global validator instance
_content_validator = None


def get_content_validator() -> ContentValidator:
    """Get global content validator instance."""
    global _content_validator
    if _content_validator is None:
        _content_validator = ContentValidator()
    return _content_validator 