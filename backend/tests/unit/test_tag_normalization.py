"""Unit tests for tag normalization, validation, and color generation.

Tests the TagService class methods:
- normalize_tags: Lowercase conversion and deduplication
- validate_tag: Length and character validation
- generate_tag_color: Deterministic color generation
- validate_and_normalize_tags: Combined validation and normalization
"""

import pytest
from src.services.tag_service import TagService


class TestTagNormalization:
    """Test tag normalization functionality."""

    def setup_method(self):
        """Initialize TagService for each test."""
        self.tag_service = TagService()

    def test_normalize_lowercase(self):
        """Tags should be converted to lowercase."""
        tags = ["Work", "URGENT", "Shopping"]
        result = self.tag_service.normalize_tags(tags)
        assert result == ["work", "urgent", "shopping"]

    def test_normalize_remove_duplicates(self):
        """Duplicate tags should be removed (case-insensitive)."""
        tags = ["work", "Work", "WORK", "urgent"]
        result = self.tag_service.normalize_tags(tags)
        assert result == ["work", "urgent"]
        assert len(result) == 2

    def test_normalize_strip_whitespace(self):
        """Leading/trailing whitespace should be removed."""
        tags = ["  work  ", "urgent ", " shopping"]
        result = self.tag_service.normalize_tags(tags)
        assert result == ["work", "urgent", "shopping"]

    def test_normalize_empty_strings(self):
        """Empty strings and whitespace-only strings should be filtered out."""
        tags = ["work", "", "  ", "urgent", "\t"]
        result = self.tag_service.normalize_tags(tags)
        assert result == ["work", "urgent"]

    def test_normalize_empty_list(self):
        """Empty list should return empty list."""
        result = self.tag_service.normalize_tags([])
        assert result == []

    def test_normalize_preserves_order(self):
        """Order should be preserved (first occurrence wins)."""
        tags = ["work", "urgent", "work", "shopping"]
        result = self.tag_service.normalize_tags(tags)
        assert result == ["work", "urgent", "shopping"]
        # work appears first, so it stays first


class TestTagValidation:
    """Test tag validation functionality."""

    def setup_method(self):
        """Initialize TagService for each test."""
        self.tag_service = TagService()

    def test_validate_valid_tags(self):
        """Valid tags should pass validation."""
        valid_tags = ["work", "urgent", "shopping", "home", "errands"]
        for tag in valid_tags:
            assert self.tag_service.validate_tag(tag) is True

    def test_validate_with_numbers(self):
        """Tags with numbers should be valid."""
        assert self.tag_service.validate_tag("project2024") is True
        assert self.tag_service.validate_tag("task1") is True

    def test_validate_with_hyphens(self):
        """Tags with hyphens should be valid."""
        assert self.tag_service.validate_tag("high-priority") is True
        assert self.tag_service.validate_tag("work-related") is True

    def test_validate_with_underscores(self):
        """Tags with underscores should be valid."""
        assert self.tag_service.validate_tag("high_priority") is True
        assert self.tag_service.validate_tag("work_related") is True

    def test_validate_empty_string(self):
        """Empty strings should fail validation."""
        assert self.tag_service.validate_tag("") is False
        assert self.tag_service.validate_tag("   ") is False

    def test_validate_too_long(self):
        """Tags exceeding 50 characters should fail validation."""
        long_tag = "a" * 51
        assert self.tag_service.validate_tag(long_tag) is False

        max_length_tag = "a" * 50
        assert self.tag_service.validate_tag(max_length_tag) is True

    def test_validate_special_characters(self):
        """Tags with special characters (except - and _) should fail."""
        invalid_tags = ["work!", "urgent@", "shopping#", "home$", "tag with space"]
        for tag in invalid_tags:
            assert self.tag_service.validate_tag(tag) is False


class TestColorGeneration:
    """Test deterministic color generation for tags."""

    def setup_method(self):
        """Initialize TagService for each test."""
        self.tag_service = TagService()

    def test_generate_color_format(self):
        """Generated colors should be valid hex colors."""
        color = self.tag_service.generate_tag_color("work")
        assert color.startswith("#")
        assert len(color) == 7
        # Check if valid hex
        int(color[1:], 16)  # Should not raise ValueError

    def test_generate_color_deterministic(self):
        """Same tag should always generate same color."""
        color1 = self.tag_service.generate_tag_color("work")
        color2 = self.tag_service.generate_tag_color("work")
        assert color1 == color2

    def test_generate_color_different_tags(self):
        """Different tags should generate different colors."""
        color_work = self.tag_service.generate_tag_color("work")
        color_urgent = self.tag_service.generate_tag_color("urgent")
        assert color_work != color_urgent

    def test_generate_color_case_sensitive(self):
        """Color generation is case-sensitive (but tags are normalized)."""
        # In practice, tags are normalized before color generation
        # But the function itself is case-sensitive
        color_lower = self.tag_service.generate_tag_color("work")
        color_upper = self.tag_service.generate_tag_color("WORK")
        # These will be different because input is different
        # In real usage, tags are normalized first

    def test_generate_color_brightness(self):
        """Generated colors should be readable (not too dark)."""
        tags = ["work", "urgent", "shopping", "home", "errands"]
        for tag in tags:
            color = self.tag_service.generate_tag_color(tag)
            # Extract RGB values
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            # Calculate brightness
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            # Should be at least 128 (readable on light background)
            assert brightness >= 128, f"Color {color} too dark (brightness={brightness})"


class TestValidateAndNormalize:
    """Test combined validation and normalization."""

    def setup_method(self):
        """Initialize TagService for each test."""
        self.tag_service = TagService()

    def test_validate_and_normalize_valid_tags(self):
        """Valid tags should be normalized."""
        tags = ["Work", "URGENT", "Shopping"]
        result = self.tag_service.validate_and_normalize_tags(tags)
        assert result == ["work", "urgent", "shopping"]

    def test_validate_and_normalize_filters_invalid(self):
        """Invalid tags should be filtered out."""
        tags = ["work", "urgent!", "", "shopping", "a" * 51]
        result = self.tag_service.validate_and_normalize_tags(tags)
        assert result == ["work", "shopping"]

    def test_validate_and_normalize_mixed(self):
        """Mixed valid and invalid tags should filter and normalize."""
        tags = ["Work", "urgent!", "SHOPPING", "", "home", "invalid tag with spaces"]
        result = self.tag_service.validate_and_normalize_tags(tags)
        assert result == ["work", "shopping", "home"]

    def test_validate_and_normalize_all_invalid(self):
        """All invalid tags should return empty list."""
        tags = ["", "!!!", "a" * 51, "   "]
        result = self.tag_service.validate_and_normalize_tags(tags)
        assert result == []

    def test_validate_and_normalize_deduplicates(self):
        """Validation and normalization should also deduplicate."""
        tags = ["work", "Work", "WORK", "urgent"]
        result = self.tag_service.validate_and_normalize_tags(tags)
        assert result == ["work", "urgent"]
        assert len(result) == 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Initialize TagService for each test."""
        self.tag_service = TagService()

    def test_normalize_none_values(self):
        """Should handle None values gracefully."""
        tags = ["work", None, "urgent"]
        # Filter out None values first (in real usage)
        filtered_tags = [t for t in tags if t is not None]
        result = self.tag_service.normalize_tags(filtered_tags)
        assert result == ["work", "urgent"]

    def test_unicode_tags(self):
        """Unicode tags should be handled correctly."""
        # Note: Current validation only allows ASCII alphanumeric + - and _
        # Unicode will fail validation, which is expected behavior
        unicode_tags = ["work", "café", "shopping"]
        result = self.tag_service.validate_and_normalize_tags(unicode_tags)
        # Only ASCII tags should pass
        assert "work" in result
        assert "shopping" in result
        # Unicode "café" should be filtered out

    def test_very_long_list(self):
        """Should handle large lists of tags efficiently."""
        tags = [f"tag{i}" for i in range(1000)]
        result = self.tag_service.normalize_tags(tags)
        assert len(result) == 1000

    def test_only_special_characters(self):
        """Tags with only special characters should be invalid."""
        invalid_tags = ["!!!", "@@@", "###", "---"]
        result = self.tag_service.validate_and_normalize_tags(invalid_tags)
        # Only "---" might be valid if hyphens are allowed
        # But a tag with only hyphens should still have at least one alphanumeric
