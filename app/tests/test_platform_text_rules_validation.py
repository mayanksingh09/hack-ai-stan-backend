"""
Tests to validate that all required platform text rule entries are documented.
These tests will fail if any required rule documentation is missing.
"""
import os
import re
from pathlib import Path
import pytest

from app.models.platform_rules import PlatformType, get_platform_rules


class TestPlatformTextRulesDocumentation:
    """Tests that ensure platform text rules documentation is complete."""
    
    @property
    def docs_file_path(self):
        """Path to the platform text rules documentation file."""
        return Path("docs/platform_text_rules.md")
    
    def test_platform_text_rules_file_exists(self):
        """Test that the platform text rules documentation file exists."""
        assert self.docs_file_path.exists(), (
            f"Platform text rules documentation file not found at {self.docs_file_path}"
        )
    
    def test_platform_text_rules_file_not_empty(self):
        """Test that the platform text rules documentation file is not empty."""
        assert self.docs_file_path.stat().st_size > 0, (
            "Platform text rules documentation file is empty"
        )
    
    def test_all_supported_platforms_documented(self):
        """Test that all supported platforms have entries in the documentation."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_platforms = []
        for platform in PlatformType:
            # Convert platform enum to expected documentation format
            platform_names = [
                platform.value,  # e.g., "youtube"
                platform.value.replace('_', ' ').title(),  # e.g., "X Twitter"
                platform.value.replace('_', ' ').upper(),  # e.g., "X TWITTER"
                platform.value.replace('_', '').title(),  # e.g., "XTwitter"
            ]
            
            # Special cases for platform naming in docs
            if platform == PlatformType.X_TWITTER:
                platform_names.extend(['X (Twitter)', 'X', 'Twitter'])
            elif platform == PlatformType.YOUTUBE:
                platform_names.extend(['YouTube'])
            elif platform == PlatformType.INSTAGRAM:
                platform_names.extend(['Instagram'])
            elif platform == PlatformType.FACEBOOK:
                platform_names.extend(['Facebook'])
            elif platform == PlatformType.TIKTOK:
                platform_names.extend(['TikTok'])
            elif platform == PlatformType.LINKEDIN:
                platform_names.extend(['LinkedIn'])
            elif platform == PlatformType.TWITCH:
                platform_names.extend(['Twitch'])
            
            platform_found = False
            for name in platform_names:
                if f"**{name}**" in content or f"| **{name}**" in content:
                    platform_found = True
                    break
            
            if not platform_found:
                missing_platforms.append(platform.value)
        
        assert not missing_platforms, (
            f"The following platforms are missing from documentation: {missing_platforms}"
        )
    
    def test_required_text_fields_documented(self):
        """Test that required text fields are documented for each platform."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define required text fields for each platform based on research
        required_fields = {
            PlatformType.YOUTUBE: [
                'Title', 'Description', 'Channel Bio', 'Comments'
            ],
            PlatformType.INSTAGRAM: [
                'Post Caption', 'Bio', 'Username', 'Profile Name', 'Comments', 'Hashtags'
            ],
            PlatformType.FACEBOOK: [
                'Post Text', 'Page Description', 'Ad Headline', 'Ad Text'
            ],
            PlatformType.TIKTOK: [
                'Video Caption', 'Bio', 'Username', 'Comments', 'Hashtags'
            ],
            PlatformType.X_TWITTER: [
                'Post', 'Bio', 'Username', 'Profile Name', 'Hashtags'
            ],
            PlatformType.LINKEDIN: [
                'Post', 'Headline', 'About Section', 'Comments', 'Connection Message'
            ],
            PlatformType.TWITCH: [
                'Stream Title', 'Bio/About', 'Stream Category'
            ]
        }
        
        missing_fields = {}
        
        for platform, fields in required_fields.items():
            platform_missing = []
            
            for field in fields:
                # Look for field in table format
                field_patterns = [
                    f"| **{field}** |",
                    f"| {field} |",
                    f"**{field}**",
                ]
                
                field_found = False
                for pattern in field_patterns:
                    if pattern in content:
                        field_found = True
                        break
                
                if not field_found:
                    platform_missing.append(field)
            
            if platform_missing:
                missing_fields[platform.value] = platform_missing
        
        assert not missing_fields, (
            f"Missing required text fields in documentation: {missing_fields}"
        )
    
    def test_character_limits_documented(self):
        """Test that character limits are documented for text fields."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract table rows (simplified parsing)
        table_rows = []
        in_table = False
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('| Platform | Field Type'):
                in_table = True
                continue
            elif line.startswith('|---') or not line.startswith('|'):
                if not line.startswith('|') and in_table:
                    break
                continue
            elif in_table and line.startswith('|'):
                table_rows.append(line)
        
        rows_without_limits = []
        
        for row in table_rows:
            columns = [col.strip() for col in row.split('|')[1:-1]]  # Remove empty first/last
            if len(columns) >= 3:
                platform, field_type, max_length = columns[0], columns[1], columns[2]
                
                # Skip header rows or separator rows
                if 'Platform' in platform or '---' in platform:
                    continue
                
                # Check if max_length is empty or just dashes
                if not max_length or max_length in ['-', '']:
                    # Some fields like "Stream Category" might not have character limits
                    if 'Category' not in field_type and 'Hashtags' not in field_type:
                        rows_without_limits.append(f"{platform} - {field_type}")
        
        assert not rows_without_limits, (
            f"The following entries are missing character limits: {rows_without_limits}"
        )
    
    def test_source_urls_documented(self):
        """Test that source URLs are documented for verification."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for source URLs in table format
        source_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        sources = re.findall(source_pattern, content)
        
        assert len(sources) > 0, "No source URLs found in documentation"
        
        # Check that we have sources for each major platform
        source_text = ' '.join([source[0] + ' ' + source[1] for source in sources])
        
        expected_sources = ['YouTube', 'Instagram', 'Facebook', 'TikTok', 'Twitter', 'LinkedIn']
        missing_sources = []
        
        for platform in expected_sources:
            if platform.lower() not in source_text.lower():
                missing_sources.append(platform)
        
        assert not missing_sources, (
            f"Missing source documentation for platforms: {missing_sources}"
        )
    
    def test_documentation_structure(self):
        """Test that the documentation has the required structural elements."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            "# Platform Text Field Requirements",
            "## Platform Requirements Table",
            "## Platform-Specific Notes",
            "## Character Counting Rules",
            "## Optimal Length Guidelines",
            "## Sources and References"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        assert not missing_sections, (
            f"Missing required documentation sections: {missing_sections}"
        )
    
    def test_last_updated_date(self):
        """Test that the documentation includes a last updated date."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for last updated pattern
        date_patterns = [
            r'Last [Uu]pdated.*\d{4}',
            r'last updated.*\d{4}',
            r'Updated.*\d{4}'
        ]
        
        date_found = False
        for pattern in date_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                date_found = True
                break
        
        assert date_found, "Documentation is missing a 'Last Updated' date"
    
    def test_platform_rules_consistency(self):
        """Test that documented limits are consistent with current platform rules."""
        with open(self.docs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test specific platform rules for consistency
        consistency_checks = []
        
        # Check specific known mappings between docs and current rules
        known_mappings = {
            PlatformType.YOUTUBE: ("Title", 100),
            PlatformType.TWITCH: ("Stream Title", 140),
        }
        
        for platform, (field_name, expected_limit) in known_mappings.items():
            rules = get_platform_rules(platform)
            
            # Look for the specific field in the platform section
            platform_display = platform.value.replace('_', ' ').title()
            if platform == PlatformType.X_TWITTER:
                platform_display = "X (Twitter)"
            
            # Use more specific regex that matches table format
            pattern = rf'\|\s*\*\*{re.escape(platform_display)}\*\*\s*\|\s*{re.escape(field_name)}\s*\|\s*(\d+)\s*chars'
            match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                documented_limit = int(match.group(1))
                if documented_limit != rules.title_max_length:
                    consistency_checks.append(
                        f"{platform.value}: {field_name} limit mismatch - "
                        f"documented: {documented_limit}, actual: {rules.title_max_length}"
                    )
        
        # Note: For other platforms, the documentation covers multiple field types
        # while platform rules currently only track "title_max_length"
        # This will be resolved in Section 2 when we expand the model
        
        assert not consistency_checks, (
            f"Documentation inconsistencies found: {consistency_checks}"
        )


def run_platform_text_rules_tests():
    """Run all platform text rules validation tests."""
    print("🧪 Running Platform Text Rules Documentation Tests...\n")
    
    try:
        test_class = TestPlatformTextRulesDocumentation()
        
        print("Testing documentation file exists...")
        test_class.test_platform_text_rules_file_exists()
        print("✅ Documentation file exists")
        
        print("Testing documentation file is not empty...")
        test_class.test_platform_text_rules_file_not_empty()
        print("✅ Documentation file has content")
        
        print("Testing all platforms are documented...")
        test_class.test_all_supported_platforms_documented()
        print("✅ All supported platforms documented")
        
        print("Testing required text fields are documented...")
        test_class.test_required_text_fields_documented()
        print("✅ Required text fields documented")
        
        print("Testing character limits are documented...")
        test_class.test_character_limits_documented()
        print("✅ Character limits documented")
        
        print("Testing source URLs are documented...")
        test_class.test_source_urls_documented()
        print("✅ Source URLs documented")
        
        print("Testing documentation structure...")
        test_class.test_documentation_structure()
        print("✅ Documentation structure valid")
        
        print("Testing last updated date...")
        test_class.test_last_updated_date()
        print("✅ Last updated date present")
        
        print("Testing platform rules consistency...")
        test_class.test_platform_rules_consistency()
        print("✅ Platform rules consistency validated")
        
        print("\n🎉 All Platform Text Rules Documentation Tests PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Platform Text Rules Documentation Tests - FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_platform_text_rules_tests()
    if not success:
        exit(1) 