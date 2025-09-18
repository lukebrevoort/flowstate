import * as validation from '../validation';
import {
  isValidEmail,
  validatePassword,
  formatDate,
  truncateText,
} from '../validation';

describe('Validation Utilities', () => {
  describe('Module exports', () => {
    it('exports all validation functions', () => {
      expect(typeof validation.isValidEmail).toBe('function');
      expect(typeof validation.validatePassword).toBe('function');
      expect(typeof validation.formatDate).toBe('function');
      expect(typeof validation.truncateText).toBe('function');
    });
  });

  describe('isValidEmail', () => {
    it('returns true for valid email addresses', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true);
    });

    it('returns false for invalid email addresses', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('invalid@')).toBe(false);
      expect(isValidEmail('@invalid.com')).toBe(false);
    });

    it('handles non-string inputs', () => {
      expect(isValidEmail(null)).toBe(false);
      expect(isValidEmail(undefined)).toBe(false);
    });

    it('trims whitespace before validation', () => {
      expect(isValidEmail('  test@example.com  ')).toBe(true);
    });
  });

  describe('validatePassword', () => {
    it('validates strong passwords correctly', () => {
      const result = validatePassword('StrongPass123!');
      expect(result.isValid).toBe(true);
      expect(result.requirements.minLength).toBe(true);
    });

    it('identifies weak passwords', () => {
      const result = validatePassword('weak');
      expect(result.isValid).toBe(false);
      expect(result.requirements.minLength).toBe(false);
    });
  });

  describe('formatDate', () => {
    it('formats valid date strings correctly', () => {
      const formatted = formatDate('2023-12-25');
      // Check that it contains the year and month, but be flexible about the exact day due to timezone
      expect(formatted).toMatch(/December \d{1,2}, 2023/);
      expect(formatted).toContain('2023');
      expect(formatted).toContain('December');
    });

    it('returns "Invalid Date" for invalid date strings', () => {
      expect(formatDate('invalid-date')).toBe('Invalid Date');
    });
  });

  describe('truncateText', () => {
    it('returns original text when under max length', () => {
      expect(truncateText('Short text', 20)).toBe('Short text');
    });

    it('truncates text when over max length', () => {
      const result = truncateText(
        'This is a very long text that should be truncated',
        20
      );
      expect(result).toBe('This is a very long...');
    });

    it('handles empty strings', () => {
      expect(truncateText('', 10)).toBe('');
    });

    it('handles non-string inputs', () => {
      expect(truncateText(null, 10)).toBe('');
      expect(truncateText(undefined, 10)).toBe('');
    });
  });
});
