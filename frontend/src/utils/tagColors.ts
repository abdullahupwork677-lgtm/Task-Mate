/**
 * Tag Color Generation Utilities
 *
 * Provides deterministic color generation for tags using MD5 hashing.
 * This matches the backend Python implementation to ensure consistent
 * colors across the application.
 *
 * Phase V - Task Tags & Categories (003-task-tags)
 */

/**
 * Generate a deterministic hex color from a tag name using MD5 hashing.
 *
 * This implementation matches the backend Python algorithm:
 * 1. MD5 hash the tag name
 * 2. Take first 6 hex characters as color
 * 3. Ensure brightness >= 128 for readability
 *
 * @param tagName - Tag name (should be normalized lowercase)
 * @returns Hex color string (e.g., "#3a7bd5")
 *
 * @example
 * ```typescript
 * const color = generateTagColor("work");  // Always same color for "work"
 * const color2 = generateTagColor("urgent");  // Different color
 * ```
 */
export function generateTagColor(tagName: string): string {
  // Generate MD5 hash
  const hash = md5(tagName);

  // Extract first 6 characters as base color
  let r = parseInt(hash.substring(0, 2), 16);
  let g = parseInt(hash.substring(2, 4), 16);
  let b = parseInt(hash.substring(4, 6), 16);

  // Calculate brightness using relative luminance formula
  // Formula: (299*R + 587*G + 114*B) / 1000
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;

  // Ensure minimum brightness for readability on light backgrounds
  if (brightness < 128) {
    r = Math.min(255, r + 80);
    g = Math.min(255, g + 80);
    b = Math.min(255, b + 80);
  }

  // Convert back to hex
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Simple MD5 hash implementation
 *
 * This is a lightweight MD5 implementation for browser environments.
 * It produces the same output as Python's hashlib.md5().
 *
 * @param str - String to hash
 * @returns MD5 hash as hex string
 */
function md5(str: string): string {
  // Convert string to UTF-8 bytes
  const utf8Bytes = new TextEncoder().encode(str);

  // MD5 state
  let a = 0x67452301;
  let b = 0xefcdab89;
  let c = 0x98badcfe;
  let d = 0x10325476;

  // Padding
  const msgLength = utf8Bytes.length;
  const paddedLength = ((msgLength + 8) >> 6) + 1;
  const blocks = new Array(paddedLength * 16).fill(0);

  // Copy message bytes
  for (let i = 0; i < msgLength; i++) {
    blocks[i >> 2] |= utf8Bytes[i] << ((i % 4) * 8);
  }

  // Append padding bit
  blocks[msgLength >> 2] |= 0x80 << ((msgLength % 4) * 8);

  // Append message length
  blocks[paddedLength * 16 - 2] = msgLength << 3;
  blocks[paddedLength * 16 - 1] = msgLength >>> 29;

  // MD5 constants
  const k = [
    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a,
    0xa8304613, 0xfd469501, 0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
    0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821, 0xf61e2562, 0xc040b340,
    0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed, 0xa9e3e905, 0xfcefa3f8,
    0x676f02d9, 0x8d2a4c8a, 0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
    0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70, 0x289b7ec6, 0xeaa127fa,
    0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92,
    0xffeff47d, 0x85845dd1, 0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
    0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
  ];

  const s = [
    7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
    5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
    4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
    6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21
  ];

  // Process blocks
  for (let i = 0; i < paddedLength * 16; i += 16) {
    const aa = a;
    const bb = b;
    const cc = c;
    const dd = d;

    for (let j = 0; j < 64; j++) {
      let f: number, g: number;

      if (j < 16) {
        f = (b & c) | (~b & d);
        g = j;
      } else if (j < 32) {
        f = (d & b) | (~d & c);
        g = (5 * j + 1) % 16;
      } else if (j < 48) {
        f = b ^ c ^ d;
        g = (3 * j + 5) % 16;
      } else {
        f = c ^ (b | ~d);
        g = (7 * j) % 16;
      }

      const temp = d;
      d = c;
      c = b;
      b = add32(b, rotateLeft(add32(add32(a, f), add32(k[j], blocks[i + g])), s[j]));
      a = temp;
    }

    a = add32(a, aa);
    b = add32(b, bb);
    c = add32(c, cc);
    d = add32(d, dd);
  }

  // Convert to hex string (little-endian)
  return (
    toHex32(a) +
    toHex32(b) +
    toHex32(c) +
    toHex32(d)
  );
}

/**
 * Helper: 32-bit addition with overflow
 */
function add32(x: number, y: number): number {
  return ((x + y) & 0xffffffff) >>> 0;
}

/**
 * Helper: Left rotate 32-bit integer
 */
function rotateLeft(x: number, n: number): number {
  return ((x << n) | (x >>> (32 - n))) >>> 0;
}

/**
 * Helper: Convert number to 2-digit hex string
 */
function toHex(n: number): string {
  return n.toString(16).padStart(2, '0');
}

/**
 * Helper: Convert 32-bit integer to 8-digit hex string (little-endian)
 */
function toHex32(n: number): string {
  return (
    toHex((n >>> 0) & 0xff) +
    toHex((n >>> 8) & 0xff) +
    toHex((n >>> 16) & 0xff) +
    toHex((n >>> 24) & 0xff)
  );
}

/**
 * Calculate brightness of a hex color (0-255)
 *
 * Uses relative luminance formula for human perception:
 * (299*R + 587*G + 114*B) / 1000
 *
 * @param hexColor - Hex color string (with or without #)
 * @returns Brightness value (0-255)
 *
 * @example
 * ```typescript
 * const brightness = calculateBrightness("#3a7bd5");
 * if (brightness < 128) {
 *   // Use white text
 * }
 * ```
 */
export function calculateBrightness(hexColor: string): number {
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  return (r * 299 + g * 587 + b * 114) / 1000;
}

/**
 * Convert hex color to RGB object
 *
 * @param hexColor - Hex color string (with or without #)
 * @returns RGB object with r, g, b properties (0-255)
 *
 * @example
 * ```typescript
 * const rgb = hexToRgb("#3a7bd5");
 * // { r: 58, g: 123, b: 213 }
 * ```
 */
export function hexToRgb(hexColor: string): { r: number; g: number; b: number } {
  const hex = hexColor.replace('#', '');
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16)
  };
}

/**
 * Convert RGB values to hex color string
 *
 * @param r - Red value (0-255)
 * @param g - Green value (0-255)
 * @param b - Blue value (0-255)
 * @returns Hex color string (e.g., "#3a7bd5")
 *
 * @example
 * ```typescript
 * const hex = rgbToHex(58, 123, 213);
 * // "#3a7bd5"
 * ```
 */
export function rgbToHex(r: number, g: number, b: number): string {
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Determine if a hex color is light or dark
 *
 * @param hexColor - Hex color string (with or without #)
 * @returns True if light (brightness >= 128), false if dark
 *
 * @example
 * ```typescript
 * const isLight = isLightColor("#3a7bd5");
 * const textColor = isLight ? 'text-black' : 'text-white';
 * ```
 */
export function isLightColor(hexColor: string): boolean {
  return calculateBrightness(hexColor) >= 128;
}

/**
 * Get contrasting text color (black or white) for a background color
 *
 * @param hexColor - Hex background color (with or without #)
 * @returns "#000000" for light backgrounds, "#FFFFFF" for dark backgrounds
 *
 * @example
 * ```typescript
 * const textColor = getContrastingTextColor("#3a7bd5");
 * // "#FFFFFF" (white text on dark blue background)
 * ```
 */
export function getContrastingTextColor(hexColor: string): string {
  return isLightColor(hexColor) ? '#000000' : '#FFFFFF';
}
