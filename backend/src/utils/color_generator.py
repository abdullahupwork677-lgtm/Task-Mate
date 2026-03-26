"""Utility functions for deterministic color generation."""

import hashlib


def generate_color_from_string(input_str: str, min_brightness: int = 128) -> str:
    """
    Generate a deterministic hex color from any string using MD5 hashing.

    The same input string always produces the same color. Brightness can be
    adjusted to ensure readability on light or dark backgrounds.

    Args:
        input_str: Input string to hash (e.g., tag name, user name, category)
        min_brightness: Minimum brightness threshold (0-255). Colors darker than
                       this will be brightened. Default 128 for light backgrounds.

    Returns:
        Hex color string in format "#RRGGBB" (e.g., "#3b82f6")

    Examples:
        >>> color = generate_color_from_string("work")
        >>> color.startswith("#") and len(color) == 7
        True
        >>> generate_color_from_string("work") == generate_color_from_string("work")
        True
        >>> generate_color_from_string("work") != generate_color_from_string("home")
        True
    """
    # Generate MD5 hash (128-bit output, 32 hex characters)
    hash_obj = hashlib.md5(input_str.encode())
    hash_hex = hash_obj.hexdigest()

    # Take first 6 characters as RGB hex color
    r = int(hash_hex[0:2], 16)
    g = int(hash_hex[2:4], 16)
    b = int(hash_hex[4:6], 16)

    # Calculate brightness using ITU-R BT.601 formula
    # Human eye is more sensitive to green, less to blue
    brightness = (r * 299 + g * 587 + b * 114) / 1000

    # Brighten if below minimum threshold
    if brightness < min_brightness:
        adjustment = min_brightness - brightness
        r = min(255, int(r + adjustment))
        g = min(255, int(g + adjustment))
        b = min(255, int(b + adjustment))

    return f"#{r:02x}{g:02x}{b:02x}"


def generate_tag_color(tag_name: str) -> str:
    """
    Generate deterministic color for a tag name.

    Convenience wrapper around generate_color_from_string() specifically for tags.
    Uses default brightness for light backgrounds.

    Args:
        tag_name: Tag name to generate color for

    Returns:
        Hex color string (e.g., "#3b82f6")

    Examples:
        >>> color = generate_tag_color("urgent")
        >>> color.startswith("#")
        True
    """
    return generate_color_from_string(tag_name.lower(), min_brightness=128)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (with or without # prefix)

    Returns:
        RGB tuple (r, g, b) with values 0-255

    Examples:
        >>> hex_to_rgb("#3b82f6")
        (59, 130, 246)
        >>> hex_to_rgb("3b82f6")
        (59, 130, 246)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB tuple to hex color string.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Hex color string with # prefix

    Examples:
        >>> rgb_to_hex(59, 130, 246)
        '#3b82f6'
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def calculate_brightness(r: int, g: int, b: int) -> float:
    """
    Calculate perceived brightness of RGB color using ITU-R BT.601 formula.

    Human eye perceives colors differently:
    - Green: 58.7% contribution to perceived brightness
    - Red: 29.9% contribution
    - Blue: 11.4% contribution

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Brightness value (0-255)

    Examples:
        >>> calculate_brightness(255, 255, 255)  # White
        255.0
        >>> calculate_brightness(0, 0, 0)  # Black
        0.0
        >>> calculate_brightness(128, 128, 128)  # Mid gray
        128.0
    """
    return (r * 299 + g * 587 + b * 114) / 1000
