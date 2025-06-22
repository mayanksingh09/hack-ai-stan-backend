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
    current_value: Any | None = None
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
            "character_limits": 0.25,      # All field character limits
            "tag_optimization": 0.20,      # Tag count and quality
            "content_completeness": 0.20,  # How many relevant fields are populated
            "platform_optimization": 0.15, # Platform-specific best practices
            "engagement_potential": 0.10,  # Content likely to generate engagement
            "optimal_lengths": 0.10        # Using optimal lengths for better performance
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
        
        # Validate optimal lengths for engagement
        optimal_issues = self._validate_optimal_lengths(content, rules)
        issues.extend(optimal_issues)
        
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
        """Validate character limits for all fields on the platform."""
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
        
        # Description character limit
        if content.description and rules.description_max_length:
            desc_length = len(content.description)
            if desc_length > rules.description_max_length:
                issues.append(ValidationIssue(
                    field="description",
                    severity=ValidationSeverity.ERROR,
                    message=f"Description exceeds maximum length",
                    current_value=desc_length,
                    expected_value=rules.description_max_length,
                    suggestion=f"Reduce description to {rules.description_max_length} characters or less"
                ))
        
        # Caption character limit
        if content.caption and rules.caption_max_length:
            caption_length = len(content.caption)
            if caption_length > rules.caption_max_length:
                issues.append(ValidationIssue(
                    field="caption",
                    severity=ValidationSeverity.ERROR,
                    message=f"Caption exceeds maximum length",
                    current_value=caption_length,
                    expected_value=rules.caption_max_length,
                    suggestion=f"Reduce caption to {rules.caption_max_length} characters or less"
                ))
        
        # Post body character limit
        if content.post_body and rules.post_max_length:
            post_length = len(content.post_body)
            if post_length > rules.post_max_length:
                issues.append(ValidationIssue(
                    field="post_body",
                    severity=ValidationSeverity.ERROR,
                    message=f"Post body exceeds maximum length",
                    current_value=post_length,
                    expected_value=rules.post_max_length,
                    suggestion=f"Reduce post body to {rules.post_max_length} characters or less"
                ))
        
        # Bio character limit
        if content.bio and rules.bio_max_length:
            bio_length = len(content.bio)
            if bio_length > rules.bio_max_length:
                issues.append(ValidationIssue(
                    field="bio",
                    severity=ValidationSeverity.ERROR,
                    message=f"Bio exceeds maximum length",
                    current_value=bio_length,
                    expected_value=rules.bio_max_length,
                    suggestion=f"Reduce bio to {rules.bio_max_length} characters or less"
                ))
        
        # Username character limit
        if content.username and rules.username_max_length:
            username_length = len(content.username)
            if username_length > rules.username_max_length:
                issues.append(ValidationIssue(
                    field="username",
                    severity=ValidationSeverity.ERROR,
                    message=f"Username exceeds maximum length",
                    current_value=username_length,
                    expected_value=rules.username_max_length,
                    suggestion=f"Reduce username to {rules.username_max_length} characters or less"
                ))
        
        # Profile name character limit
        if content.profile_name and rules.profile_name_max_length:
            profile_length = len(content.profile_name)
            if profile_length > rules.profile_name_max_length:
                issues.append(ValidationIssue(
                    field="profile_name",
                    severity=ValidationSeverity.ERROR,
                    message=f"Profile name exceeds maximum length",
                    current_value=profile_length,
                    expected_value=rules.profile_name_max_length,
                    suggestion=f"Reduce profile name to {rules.profile_name_max_length} characters or less"
                ))
        
        # Headline character limit
        if content.headline and rules.headline_max_length:
            headline_length = len(content.headline)
            if headline_length > rules.headline_max_length:
                issues.append(ValidationIssue(
                    field="headline",
                    severity=ValidationSeverity.ERROR,
                    message=f"Headline exceeds maximum length",
                    current_value=headline_length,
                    expected_value=rules.headline_max_length,
                    suggestion=f"Reduce headline to {rules.headline_max_length} characters or less"
                ))
        
        # About section character limit
        if content.about_section and rules.about_max_length:
            about_length = len(content.about_section)
            if about_length > rules.about_max_length:
                issues.append(ValidationIssue(
                    field="about_section",
                    severity=ValidationSeverity.ERROR,
                    message=f"About section exceeds maximum length",
                    current_value=about_length,
                    expected_value=rules.about_max_length,
                    suggestion=f"Reduce about section to {rules.about_max_length} characters or less"
                ))
        
        # Connection message character limit
        if content.connection_message and rules.connection_message_max_length:
            message_length = len(content.connection_message)
            if message_length > rules.connection_message_max_length:
                issues.append(ValidationIssue(
                    field="connection_message",
                    severity=ValidationSeverity.ERROR,
                    message=f"Connection message exceeds maximum length",
                    current_value=message_length,
                    expected_value=rules.connection_message_max_length,
                    suggestion=f"Reduce connection message to {rules.connection_message_max_length} characters or less"
                ))
        
        # Special case for X/Twitter total character limit
        if content.platform == PlatformType.X_TWITTER:
            # Use post_body if available, otherwise title
            main_content = content.post_body or content.title
            total_chars = len(main_content) + sum(len(tag) + 1 for tag in content.tags)
            if total_chars > rules.post_max_length:
                issues.append(ValidationIssue(
                    field="total_content",
                    severity=ValidationSeverity.ERROR,
                    message="Total content (post + hashtags) exceeds character limit",
                    current_value=total_chars,
                    expected_value=rules.post_max_length,
                    suggestion="Reduce post length or number of hashtags"
                ))
        
        return issues
    
    def _validate_optimal_lengths(self, content: PlatformContent, 
                                rules: PlatformRules) -> List[ValidationIssue]:
        """Validate optimal lengths for better engagement based on research."""
        issues = []
        
        # Platform-specific optimal length validation
        if content.platform == PlatformType.YOUTUBE:
            # YouTube title optimal length: 70 chars (truncated in search results)
            if rules.title_optimal_length and content.character_count > rules.title_optimal_length:
                issues.append(ValidationIssue(
                    field="title",
                    severity=ValidationSeverity.WARNING,
                    message="Title may be truncated in YouTube search results",
                    current_value=content.character_count,
                    expected_value=f"≤{rules.title_optimal_length} chars",
                    suggestion=f"Keep title under {rules.title_optimal_length} characters for full visibility"
                ))
            
            # YouTube description first 157 chars are crucial
            if content.description and rules.description_optimal_length:
                if len(content.description) > rules.description_optimal_length:
                    # Check if important content is in first 157 chars
                    first_part = content.description[:rules.description_optimal_length]
                    if not any(keyword in first_part.lower() for keyword in ['tutorial', 'learn', 'guide', 'how']):
                        issues.append(ValidationIssue(
                            field="description",
                            severity=ValidationSeverity.INFO,
                            message="Important content should be in first 157 characters",
                            current_value=len(content.description),
                            expected_value=f"Key info in first {rules.description_optimal_length} chars",
                            suggestion="Move key information to the beginning of description"
                        ))
        
        elif content.platform == PlatformType.INSTAGRAM:
            # Instagram caption truncated at 125 chars
            if content.caption and rules.caption_optimal_length:
                if len(content.caption) > rules.caption_optimal_length:
                    issues.append(ValidationIssue(
                        field="caption",
                        severity=ValidationSeverity.WARNING,
                        message="Caption will be truncated with 'more' button",
                        current_value=len(content.caption),
                        expected_value=f"≤{rules.caption_optimal_length} chars",
                        suggestion=f"Keep key message in first {rules.caption_optimal_length} characters"
                    ))
        
        elif content.platform == PlatformType.FACEBOOK:
            # Facebook posts ≤80 chars get 66% higher engagement
            if content.post_body and rules.post_optimal_length:
                if len(content.post_body) > rules.post_optimal_length:
                    issues.append(ValidationIssue(
                        field="post_body",
                        severity=ValidationSeverity.INFO,
                        message="Shorter posts get 66% higher engagement on Facebook",
                        current_value=len(content.post_body),
                        expected_value=f"≤{rules.post_optimal_length} chars",
                        suggestion=f"Consider shortening to {rules.post_optimal_length} characters or less"
                    ))
        
        elif content.platform == PlatformType.X_TWITTER:
            # Twitter posts <100 chars get 17% higher engagement
            main_content = content.post_body or content.title
            if rules.post_optimal_length and len(main_content) > rules.post_optimal_length:
                issues.append(ValidationIssue(
                    field="post_body" if content.post_body else "title",
                    severity=ValidationSeverity.INFO,
                    message="Shorter tweets get 17% higher engagement",
                    current_value=len(main_content),
                    expected_value=f"≤{rules.post_optimal_length} chars",
                    suggestion=f"Consider shortening to under {rules.post_optimal_length} characters"
                ))
        
        elif content.platform == PlatformType.LINKEDIN:
            # LinkedIn posts truncated at ~200 chars with "See more"
            if content.post_body and rules.post_optimal_length:
                if len(content.post_body) > rules.post_optimal_length:
                    issues.append(ValidationIssue(
                        field="post_body",
                        severity=ValidationSeverity.WARNING,
                        message="Post will be truncated with 'See more' link",
                        current_value=len(content.post_body),
                        expected_value=f"≤{rules.post_optimal_length} chars",
                        suggestion=f"Keep key message in first {rules.post_optimal_length} characters"
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
        """Validate platform-specific requirements and heuristics."""
        issues = []
        
        # Platform-specific validation rules
        if content.platform == PlatformType.LINKEDIN:
            # Check for professional tone across all text fields
            casual_indicators = ['hey', 'guys', 'lol', 'omg', 'awesome', 'epic', 'cool', 'dude']
            professional_text = (content.title + ' ' + 
                                (content.post_body or '') + ' ' + 
                                (content.headline or '')).lower()
            
            found_casual = [word for word in casual_indicators if word in professional_text]
            if found_casual:
                issues.append(ValidationIssue(
                    field="tone",
                    severity=ValidationSeverity.WARNING,
                    message="Content may be too casual for LinkedIn",
                    current_value=found_casual,
                    suggestion="Use more professional language"
                ))
            
            # Check for empty post body (LinkedIn favors substantial content)
            if not content.post_body or len(content.post_body.strip()) < 50:
                issues.append(ValidationIssue(
                    field="post_body",
                    severity=ValidationSeverity.WARNING,
                    message="LinkedIn favors substantial content",
                    current_value=len(content.post_body) if content.post_body else 0,
                    expected_value="50+ characters",
                    suggestion="Add more detailed, valuable content for better engagement"
                ))
            
            # Check for professional headline format
            if content.headline and not any(separator in content.headline for separator in ['|', '•', '-']):
                issues.append(ValidationIssue(
                    field="headline",
                    severity=ValidationSeverity.INFO,
                    message="Professional headlines often use separators",
                    suggestion="Consider using | or • to separate roles/skills"
                ))
        
        elif content.platform == PlatformType.TIKTOK:
            # Check for trend awareness
            trending_tags = ['#fyp', '#viral', '#trending', '#foryou', '#foryoupage']
            if not any(tag.lower() in [t.lower() for t in trending_tags] for tag in content.tags):
                issues.append(ValidationIssue(
                    field="tags",
                    severity=ValidationSeverity.INFO,
                    message="Consider adding trending TikTok hashtags",
                    suggestion="Add #fyp, #viral, or #trending for better reach"
                ))
            
            # TikTok captions should be engaging and brief
            if content.caption and len(content.caption) > 100:
                issues.append(ValidationIssue(
                    field="caption",
                    severity=ValidationSeverity.INFO,
                    message="TikTok favors short, punchy captions",
                    current_value=len(content.caption),
                    expected_value="≤100 chars",
                    suggestion="Keep captions brief and engaging"
                ))
        
        elif content.platform == PlatformType.INSTAGRAM:
            # Check for emoji usage in caption (Instagram is visual-first)
            caption_text = content.caption or content.title
            if not any(char in caption_text for char in '😀🎯✨🌟💫🔥💯🚀💖🌈👆📸💻'):
                issues.append(ValidationIssue(
                    field="visual_appeal",
                    severity=ValidationSeverity.INFO,
                    message="Consider adding emojis for better visual appeal",
                    suggestion="Add relevant emojis to increase engagement"
                ))
            
            # Instagram hashtag optimization
            if len(content.tags) < 10:
                issues.append(ValidationIssue(
                    field="tags",
                    severity=ValidationSeverity.INFO,
                    message="Instagram posts perform better with 10+ hashtags",
                    current_value=len(content.tags),
                    expected_value="10-20 hashtags",
                    suggestion="Add more relevant hashtags for better reach"
                ))
        
        elif content.platform == PlatformType.YOUTUBE:
            # YouTube description should have substantial content
            if content.description and len(content.description) < 100:
                issues.append(ValidationIssue(
                    field="description",
                    severity=ValidationSeverity.WARNING,
                    message="YouTube descriptions should be detailed for SEO",
                    current_value=len(content.description),
                    expected_value="100+ characters",
                    suggestion="Add more detailed description for better discoverability"
                ))
            
            # YouTube should have keywords in title for SEO
            if content.title and not any(keyword in content.title.lower() 
                                      for keyword in ['tutorial', 'guide', 'how to', 'learn', 'tips']):
                issues.append(ValidationIssue(
                    field="title",
                    severity=ValidationSeverity.INFO,
                    message="Consider adding educational keywords for YouTube SEO",
                    suggestion="Include words like 'tutorial', 'guide', or 'how to'"
                ))
        
        elif content.platform == PlatformType.FACEBOOK:
            # Facebook algorithm favors posts that generate conversation
            if content.post_body and not any(word in content.post_body.lower() 
                                          for word in ['what', 'how', 'why', 'thoughts', 'opinion', '?']):
                issues.append(ValidationIssue(
                    field="post_body",
                    severity=ValidationSeverity.INFO,
                    message="Facebook favors posts that encourage interaction",
                    suggestion="Consider adding a question or call for opinions"
                ))
        
        elif content.platform == PlatformType.X_TWITTER:
            # Check for engagement tactics
            main_content = content.post_body or content.title
            if not any(word in main_content.lower() for word in ['thread', 'breaking', 'just', 'new']):
                issues.append(ValidationIssue(
                    field="timing",
                    severity=ValidationSeverity.INFO,
                    message="Twitter favors timely, immediate content",
                    suggestion="Consider adding urgency or timeliness indicators"
                ))
        
        elif content.platform == PlatformType.TWITCH:
            # Twitch stream titles should be descriptive and category-specific
            if content.stream_category:
                # Validate that title relates to the category
                if not any(word in content.title.lower() 
                          for word in content.stream_category.lower().split()):
                    issues.append(ValidationIssue(
                        field="title",
                        severity=ValidationSeverity.WARNING,
                        message="Stream title should relate to the category",
                        current_value=content.stream_category,
                        suggestion="Include category-related keywords in title"
                    ))
        
        return issues
    
    def _calculate_quality_score(self, content: PlatformContent, rules: PlatformRules, 
                               issues: List[ValidationIssue]) -> float:
        """Calculate quality score (0-100) based on content and validation issues."""
        # Start with separate scores for each dimension
        scores = {
            "character_limits": 100.0,
            "tag_optimization": 100.0,
            "content_completeness": 100.0,
            "platform_optimization": 100.0,
            "engagement_potential": 100.0,
            "optimal_lengths": 100.0
        }
        
        # Deduct points based on issue type and field
        for issue in issues:
            deduction = 0
            if issue.severity == ValidationSeverity.ERROR:
                deduction = 30
            elif issue.severity == ValidationSeverity.WARNING:
                deduction = 15
            elif issue.severity == ValidationSeverity.INFO:
                deduction = 8
            
            # Apply deductions to relevant scoring dimensions
            if issue.field in ["title", "description", "caption", "post_body", "bio", "username", "profile_name", "headline", "about_section", "connection_message"]:
                if "character" in issue.message.lower() or "length" in issue.message.lower():
                    scores["character_limits"] -= deduction
                elif "optimal" in issue.message.lower() or "truncat" in issue.message.lower():
                    scores["optimal_lengths"] -= deduction
                else:
                    scores["platform_optimization"] -= deduction
            elif issue.field == "tags":
                scores["tag_optimization"] -= deduction
            elif issue.field in ["tone", "visual_appeal", "timing"]:
                scores["engagement_potential"] -= deduction
            else:
                scores["platform_optimization"] -= deduction
        
        # Bonus scoring for good practices
        
        # Content completeness - reward for having multiple relevant fields
        relevant_fields = self._get_relevant_fields_for_platform(content.platform)
        populated_fields = 0
        for field in relevant_fields:
            if hasattr(content, field) and getattr(content, field):
                populated_fields += 1
        
        if relevant_fields:
            completeness_ratio = populated_fields / len(relevant_fields)
            scores["content_completeness"] = 50 + (completeness_ratio * 50)  # 50-100 based on completeness
        
        # Tag optimization bonus
        tag_range = rules.tag_max_count - rules.tag_min_count
        if tag_range > 0:
            optimal_tags = rules.tag_min_count + (tag_range * 0.7)  # 70% of range
            if abs(content.tag_count - optimal_tags) <= 2:
                scores["tag_optimization"] += 10
        
        # Character limit utilization bonus (sweet spot: 70-90% of limit)
        title_utilization = content.character_count / rules.title_max_length
        if 0.7 <= title_utilization <= 0.9:
            scores["character_limits"] += 5
        
        # Confidence score bonus
        if content.confidence_score >= 0.9:
            scores["engagement_potential"] += 15
        elif content.confidence_score >= 0.8:
            scores["engagement_potential"] += 10
        elif content.confidence_score >= 0.7:
            scores["engagement_potential"] += 5
        
        # Platform-specific bonuses
        if content.platform == PlatformType.INSTAGRAM and len(content.tags) >= 15:
            scores["platform_optimization"] += 10  # Instagram loves many hashtags
        elif content.platform == PlatformType.LINKEDIN and content.headline:
            scores["platform_optimization"] += 10  # Professional headline bonus
        elif content.platform == PlatformType.YOUTUBE and content.description and len(content.description) >= 200:
            scores["platform_optimization"] += 10  # Detailed description bonus
        
        # Calculate weighted final score
        final_score = 0.0
        for dimension, weight in self.quality_weights.items():
            # Ensure scores are within bounds
            dimension_score = max(0.0, min(100.0, scores[dimension]))
            final_score += dimension_score * weight
        
        return max(0.0, min(100.0, final_score))
    
    def _get_relevant_fields_for_platform(self, platform: PlatformType) -> List[str]:
        """Get list of relevant fields for a specific platform."""
        base_fields = ["title", "tags"]
        
        platform_fields = {
            PlatformType.YOUTUBE: base_fields + ["description"],
            PlatformType.INSTAGRAM: base_fields + ["caption"],
            PlatformType.FACEBOOK: base_fields + ["post_body"],
            PlatformType.TIKTOK: base_fields + ["caption"],
            PlatformType.X_TWITTER: base_fields + ["post_body"],
            PlatformType.LINKEDIN: base_fields + ["post_body", "headline"],
            PlatformType.TWITCH: base_fields + ["stream_category"]
        }
        
        return platform_fields.get(platform, base_fields)
    
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