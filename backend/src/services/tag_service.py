"""Tag management service for task categorization and organization."""

import hashlib
from typing import List


class TagService:
    """
    Service for managing task tags with normalization and color generation.

    Features:
    - Case-insensitive tag normalization (stored as lowercase)
    - Duplicate removal
    - Deterministic color generation for consistent visual indicators
    - Tag validation (alphanumeric + basic punctuation)
    """

    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        """
        Normalize tags by converting to lowercase and removing duplicates.

        Args:
            tags: Raw list of tags from user input

        Returns:
            Normalized list with lowercase tags and no duplicates

        Examples:
            >>> TagService.normalize_tags(["Work", "work", "URGENT", "urgent"])
            ['work', 'urgent']
        """
        # Convert to lowercase, strip whitespace, and remove duplicates
        normalized = [tag.lower().strip() for tag in tags if tag and tag.strip()]
        # Remove duplicates while preserving order (Python 3.7+ dict insertion order)
        return list(dict.fromkeys(normalized))

    @staticmethod
    def validate_tag(tag: str) -> bool:
        """
        Validate a single tag meets requirements.

        Requirements:
        - Not empty
        - Max 50 characters
        - Alphanumeric + basic punctuation (-, _)

        Args:
            tag: Tag to validate

        Returns:
            True if valid, False otherwise

        Examples:
            >>> TagService.validate_tag("work")
            True
            >>> TagService.validate_tag("my-urgent-task")
            True
            >>> TagService.validate_tag("")
            False
            >>> TagService.validate_tag("a" * 51)
            False
        """
        if not tag or not tag.strip():
            return False

        tag = tag.strip()

        # Check length (max 50 characters)
        if len(tag) > 50:
            return False

        # Check alphanumeric + basic punctuation (-, _)
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        return all(c in allowed_chars for c in tag)

    @staticmethod
    def generate_tag_color(tag_name: str) -> str:
        """
        Generate deterministic, visually distinct color for a tag using hash function.

        The same tag always produces the same color. Brightness is adjusted to ensure
        readability on light backgrounds.

        Args:
            tag_name: Tag name to generate color for

        Returns:
            Hex color string (e.g., "#3b82f6")

        Examples:
            >>> color = TagService.generate_tag_color("work")
            >>> color.startswith("#") and len(color) == 7
            True
            >>> TagService.generate_tag_color("work") == TagService.generate_tag_color("work")
            True
        """
        # Generate MD5 hash of tag name (deterministic)
        hash_obj = hashlib.md5(tag_name.encode())
        hash_hex = hash_obj.hexdigest()

        # Take first 6 characters as hex color
        color = f"#{hash_hex[:6]}"

        # Brightness adjustment for readability
        # Convert hex to RGB
        r = int(hash_hex[0:2], 16)
        g = int(hash_hex[2:4], 16)
        b = int(hash_hex[4:6], 16)

        # Calculate brightness using formula: (299*R + 587*G + 114*B) / 1000
        brightness = (r * 299 + g * 587 + b * 114) / 1000

        # If too dark (brightness < 128), brighten it
        if brightness < 128:
            r = min(255, r + 80)
            g = min(255, g + 80)
            b = min(255, b + 80)
            color = f"#{r:02x}{g:02x}{b:02x}"

        return color

    @staticmethod
    def validate_and_normalize_tags(tags: List[str]) -> List[str]:
        """
        Convenience method that validates AND normalizes tags in one call.

        Invalid tags are filtered out silently.

        Args:
            tags: Raw list of tags from user input

        Returns:
            Normalized list with only valid tags

        Examples:
            >>> TagService.validate_and_normalize_tags(["Work", "URGENT", "", "a" * 51])
            ['work', 'urgent']
        """
        # Filter valid tags first, then normalize
        valid_tags = [tag for tag in tags if TagService.validate_tag(tag)]
        return TagService.normalize_tags(valid_tags)
