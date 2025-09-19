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
      const validEmails = [
        'test@example.com',
        'user.name@domain.co.uk',
        'first+last@subdomain.example.org',
        'user123@test-domain.com',
        'a@b.co',
      ];

      validEmails.forEach(email => {
        expect(isValidEmail(email)).toBe(true);
      });
    });

    it('returns false for invalid email addresses', () => {
      const invalidEmails = [
        'invalid',
        'invalid@',
        '@invalid.com',
        'invalid.com',
        'invalid@.com',
        'invalid@com.',
        '',
        'user@',
        '@domain.com',
        'user name@domain.com', // space
        'user@domain',
      ];

      invalidEmails.forEach(email => {
        expect(isValidEmail(email)).toBe(false);
      });
    });

    it('handles non-string inputs', () => {
      expect(isValidEmail(null)).toBe(false);
      expect(isValidEmail(undefined)).toBe(false);
      expect(isValidEmail(123)).toBe(false);
      expect(isValidEmail({})).toBe(false);
      expect(isValidEmail([])).toBe(false);
      expect(isValidEmail(true)).toBe(false);
    });

    it('trims whitespace before validation', () => {
      expect(isValidEmail('  test@example.com  ')).toBe(true);
      expect(isValidEmail('\n\tuser@domain.com\n')).toBe(true);
      expect(isValidEmail('   invalid@   ')).toBe(false);
    });

    it('handles empty and whitespace-only strings', () => {
      expect(isValidEmail('')).toBe(false);
      expect(isValidEmail('   ')).toBe(false);
      expect(isValidEmail('\t\n')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('validates strong passwords correctly', () => {
      const strongPasswords = [
        'StrongPass123!',
        'MyS3cur3P@ssw0rd',
        'C0mpl3x!P@$$w0rd',
        'Secure123#',
      ];

      strongPasswords.forEach(password => {
        const result = validatePassword(password);
        expect(result.isValid).toBe(true);
        expect(result.requirements.minLength).toBe(true);
        expect(result.requirements.hasUppercase).toBe(true);
        expect(result.requirements.hasLowercase).toBe(true);
        expect(result.requirements.hasNumber).toBe(true);
        expect(result.requirements.hasSpecialChar).toBe(true);
      });
    });

    it('identifies weak passwords', () => {
      const weakPassword = 'weak';
      const result = validatePassword(weakPassword);

      expect(result.isValid).toBe(false);
      expect(result.requirements.minLength).toBe(false);
      expect(result.requirements.hasUppercase).toBe(false);
      expect(result.requirements.hasNumber).toBe(false);
      expect(result.requirements.hasSpecialChar).toBe(false);
    });

    it('checks individual requirements', () => {
      expect(validatePassword('short1!').requirements.minLength).toBe(false);
      expect(validatePassword('longenoughpass1!').requirements.minLength).toBe(
        true
      );

      expect(validatePassword('nouppercase1!').requirements.hasUppercase).toBe(
        false
      );
      expect(validatePassword('HasUppercase1!').requirements.hasUppercase).toBe(
        true
      );

      expect(validatePassword('NOLOWERCASE1!').requirements.hasLowercase).toBe(
        false
      );
      expect(validatePassword('HasLowercase1!').requirements.hasLowercase).toBe(
        true
      );

      expect(validatePassword('NoNumbers!A').requirements.hasNumber).toBe(
        false
      );
      expect(validatePassword('HasNumbers1!').requirements.hasNumber).toBe(
        true
      );

      expect(validatePassword('NoSpecial1A').requirements.hasSpecialChar).toBe(
        false
      );
      expect(validatePassword('HasSpecial1!').requirements.hasSpecialChar).toBe(
        true
      );
    });

    it('handles non-string inputs', () => {
      const invalidInputs = [null, undefined, 123, {}, [], true];

      invalidInputs.forEach(input => {
        const result = validatePassword(input);
        expect(result.isValid).toBe(false);
        expect(
          Object.values(result.requirements).every(req => req === false)
        ).toBe(true);
      });
    });

    it('handles edge cases', () => {
      expect(validatePassword('').isValid).toBe(false);
      expect(validatePassword('A1!').isValid).toBe(false); // too short
      expect(validatePassword('Abcdefgh').isValid).toBe(false); // no number or special char
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

    it('handles ISO date strings', () => {
      const isoDate = '2023-12-25T10:30:00.000Z';
      const formatted = formatDate(isoDate);
      expect(formatted).toMatch(/December \d{1,2}, 2023/);
    });

    it('handles various date formats', () => {
      // Test valid date parsing with timezone considerations
      const result1 = formatDate('2023-01-01'); // This might show Dec 31, 2022 due to timezone
      const result2 = formatDate('2023/01/01'); // This should show Jan 1, 2023
      const result3 = formatDate('January 1, 2023'); // This should show Jan 1, 2023

      // Check that all return valid formatted dates
      expect(result1).toMatch(/(December 31, 2022|January 1, 2023)/);
      expect(result2).toMatch(/January 1, 2023/);
      expect(result3).toMatch(/January 1, 2023/);

      // All should be valid dates, not "Invalid Date"
      [result1, result2, result3].forEach(result => {
        expect(result).not.toBe('Invalid Date');
      });
    });

    it('returns "Invalid Date" for invalid date strings', () => {
      const invalidDates = ['invalid-date', 'not-a-date', '', 'abc'];

      invalidDates.forEach(date => {
        expect(formatDate(date)).toBe('Invalid Date');
      });
    });

    it('handles timestamp numbers', () => {
      // formatDate expects a string, so timestamp strings should be handled differently
      const validDateString = '2023-12-25';
      const result = formatDate(validDateString);
      expect(result).toMatch(/December \d{1,2}, 2023/);

      // Test that pure number strings are treated as invalid
      const numberString = '1703548800000';
      expect(formatDate(numberString)).toBe('Invalid Date');
    });
  });

  describe('truncateText', () => {
    it('returns original text when under max length', () => {
      const text = 'Short text';
      expect(truncateText(text, 20)).toBe('Short text');
      expect(truncateText(text, 10)).toBe('Short text');
      expect(truncateText('Hi', 5)).toBe('Hi');
    });

    it('truncates text when over max length', () => {
      const text = 'This is a very long text that should be truncated';
      const result = truncateText(text, 20);
      expect(result).toBe('This is a very long...');
      expect(result.length).toBe(22); // 19 + 3 for '...' (trimmed)
    });

    it('handles exact length boundaries', () => {
      expect(truncateText('Exactly20Characters!', 20)).toBe(
        'Exactly20Characters!'
      );
      expect(truncateText('ExactlyTwentyOneChars', 20)).toBe(
        'ExactlyTwentyOneChar...'
      );
    });

    it('handles empty strings', () => {
      expect(truncateText('', 10)).toBe('');
      expect(truncateText('', 0)).toBe('');
    });

    it('handles non-string inputs', () => {
      expect(truncateText(null, 10)).toBe('');
      expect(truncateText(undefined, 10)).toBe('');
      expect(truncateText(123, 10)).toBe('');
      expect(truncateText({}, 10)).toBe('');
      expect(truncateText([], 10)).toBe('');
    });

    it('trims whitespace before adding ellipsis', () => {
      const text = 'Text with trailing spaces   ';
      const result = truncateText(text, 10);
      expect(result).toBe('Text with...');
      expect(result).not.toContain('   ');
    });

    it('handles zero and negative max lengths', () => {
      // With length 0, it takes 0 characters then adds '...'
      expect(truncateText('Any text', 0)).toBe('...');
      // With negative length, it still takes some characters
      expect(truncateText('Any text', -5)).toBe('Any...');
    });

    it('handles very small max lengths', () => {
      expect(truncateText('Hello', 1)).toBe('H...');
      expect(truncateText('Hello', 2)).toBe('He...');
    });
  });
});
