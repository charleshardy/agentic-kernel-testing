// Security and privacy utilities

/**
 * Data encryption utilities using Web Crypto API
 */
export class DataEncryption {
  private static algorithm = 'AES-GCM';
  private static keyLength = 256;

  /**
   * Generate encryption key
   */
  static async generateKey(): Promise<CryptoKey> {
    return await crypto.subtle.generateKey(
      {
        name: this.algorithm,
        length: this.keyLength
      },
      true,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Export key to string
   */
  static async exportKey(key: CryptoKey): Promise<string> {
    const exported = await crypto.subtle.exportKey('jwk', key);
    return JSON.stringify(exported);
  }

  /**
   * Import key from string
   */
  static async importKey(keyString: string): Promise<CryptoKey> {
    const keyData = JSON.parse(keyString);
    return await crypto.subtle.importKey(
      'jwk',
      keyData,
      {
        name: this.algorithm,
        length: this.keyLength
      },
      true,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Encrypt data
   */
  static async encrypt(data: string, key: CryptoKey): Promise<string> {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    
    // Generate random IV
    const iv = crypto.getRandomValues(new Uint8Array(12));
    
    const encryptedBuffer = await crypto.subtle.encrypt(
      {
        name: this.algorithm,
        iv
      },
      key,
      dataBuffer
    );

    // Combine IV and encrypted data
    const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(encryptedBuffer), iv.length);

    // Convert to base64
    return btoa(String.fromCharCode(...combined));
  }

  /**
   * Decrypt data
   */
  static async decrypt(encryptedData: string, key: CryptoKey): Promise<string> {
    // Convert from base64
    const combined = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
    
    // Extract IV and encrypted data
    const iv = combined.slice(0, 12);
    const data = combined.slice(12);

    const decryptedBuffer = await crypto.subtle.decrypt(
      {
        name: this.algorithm,
        iv
      },
      key,
      data
    );

    const decoder = new TextDecoder();
    return decoder.decode(decryptedBuffer);
  }

  /**
   * Hash data using SHA-256
   */
  static async hash(data: string): Promise<string> {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}

/**
 * Data masking utilities for sensitive information
 */
export class DataMasking {
  /**
   * Mask email address
   */
  static maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    if (!domain) return email;
    
    const maskedLocal = local.length > 2
      ? local[0] + '*'.repeat(local.length - 2) + local[local.length - 1]
      : local[0] + '*';
    
    return `${maskedLocal}@${domain}`;
  }

  /**
   * Mask phone number
   */
  static maskPhone(phone: string): string {
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 4) return phone;
    
    const lastFour = digits.slice(-4);
    const masked = '*'.repeat(digits.length - 4) + lastFour;
    return masked;
  }

  /**
   * Mask credit card number
   */
  static maskCreditCard(cardNumber: string): string {
    const digits = cardNumber.replace(/\D/g, '');
    if (digits.length < 4) return cardNumber;
    
    const lastFour = digits.slice(-4);
    return '**** **** **** ' + lastFour;
  }

  /**
   * Mask API key
   */
  static maskAPIKey(apiKey: string): string {
    if (apiKey.length < 8) return apiKey;
    return apiKey.slice(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.slice(-4);
  }

  /**
   * Mask generic sensitive data
   */
  static maskGeneric(data: string, visibleChars = 4): string {
    if (data.length <= visibleChars) return '*'.repeat(data.length);
    return data.slice(0, visibleChars) + '*'.repeat(data.length - visibleChars);
  }

  /**
   * Mask object fields recursively
   */
  static maskObject(
    obj: any,
    sensitiveFields: string[] = ['password', 'token', 'apiKey', 'secret', 'ssn']
  ): any {
    if (typeof obj !== 'object' || obj === null) {
      return obj;
    }

    if (Array.isArray(obj)) {
      return obj.map(item => this.maskObject(item, sensitiveFields));
    }

    const masked: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = sensitiveFields.some(field => 
        lowerKey.includes(field.toLowerCase())
      );

      if (isSensitive && typeof value === 'string') {
        masked[key] = this.maskGeneric(value);
      } else if (typeof value === 'object') {
        masked[key] = this.maskObject(value, sensitiveFields);
      } else {
        masked[key] = value;
      }
    }

    return masked;
  }
}

/**
 * Secure session management
 */
export class SecureSession {
  private static readonly SESSION_KEY = 'secure_session';
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly REFRESH_KEY = 'refresh_token';

  /**
   * Store session data securely
   */
  static async setSession(data: any, encryptionKey?: CryptoKey): Promise<void> {
    try {
      const serialized = JSON.stringify(data);
      
      if (encryptionKey) {
        const encrypted = await DataEncryption.encrypt(serialized, encryptionKey);
        sessionStorage.setItem(this.SESSION_KEY, encrypted);
      } else {
        sessionStorage.setItem(this.SESSION_KEY, serialized);
      }
    } catch (error) {
      console.error('Failed to set session:', error);
    }
  }

  /**
   * Get session data
   */
  static async getSession(encryptionKey?: CryptoKey): Promise<any | null> {
    try {
      const stored = sessionStorage.getItem(this.SESSION_KEY);
      if (!stored) return null;

      if (encryptionKey) {
        const decrypted = await DataEncryption.decrypt(stored, encryptionKey);
        return JSON.parse(decrypted);
      } else {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to get session:', error);
      return null;
    }
  }

  /**
   * Clear session
   */
  static clearSession(): void {
    sessionStorage.removeItem(this.SESSION_KEY);
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_KEY);
  }

  /**
   * Set authentication token
   */
  static setToken(token: string): void {
    sessionStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Get authentication token
   */
  static getToken(): string | null {
    return sessionStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Set refresh token
   */
  static setRefreshToken(token: string): void {
    sessionStorage.setItem(this.REFRESH_KEY, token);
  }

  /**
   * Get refresh token
   */
  static getRefreshToken(): string | null {
    return sessionStorage.getItem(this.REFRESH_KEY);
  }

  /**
   * Check if session is valid
   */
  static isValid(): boolean {
    return this.getToken() !== null;
  }
}

/**
 * Input sanitization
 */
export class InputSanitizer {
  /**
   * Sanitize HTML to prevent XSS
   */
  static sanitizeHTML(html: string): string {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }

  /**
   * Sanitize SQL input
   */
  static sanitizeSQL(input: string): string {
    return input.replace(/['";\\]/g, '');
  }

  /**
   * Sanitize file path
   */
  static sanitizePath(path: string): string {
    return path.replace(/[^a-zA-Z0-9._/-]/g, '');
  }

  /**
   * Validate email format
   */
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate URL format
   */
  static isValidURL(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Remove dangerous characters
   */
  static removeDangerousChars(input: string): string {
    return input.replace(/[<>'"&]/g, '');
  }
}

/**
 * Content Security Policy helper
 */
export class CSPHelper {
  /**
   * Generate nonce for inline scripts
   */
  static generateNonce(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode(...array));
  }

  /**
   * Validate CSP directive
   */
  static validateDirective(directive: string, value: string): boolean {
    const validDirectives = [
      'default-src', 'script-src', 'style-src', 'img-src',
      'connect-src', 'font-src', 'object-src', 'media-src',
      'frame-src', 'worker-src', 'manifest-src'
    ];
    return validDirectives.includes(directive);
  }
}

/**
 * Data retention policy manager
 */
export class DataRetention {
  private static readonly RETENTION_KEY = 'data_retention_policy';

  /**
   * Set retention policy
   */
  static setPolicy(policy: {
    auditLogs: number; // days
    userSessions: number;
    testResults: number;
    backups: number;
  }): void {
    localStorage.setItem(this.RETENTION_KEY, JSON.stringify(policy));
  }

  /**
   * Get retention policy
   */
  static getPolicy(): any {
    const stored = localStorage.getItem(this.RETENTION_KEY);
    return stored ? JSON.parse(stored) : null;
  }

  /**
   * Check if data should be deleted
   */
  static shouldDelete(timestamp: number, retentionDays: number): boolean {
    const now = Date.now();
    const age = now - timestamp;
    const maxAge = retentionDays * 24 * 60 * 60 * 1000;
    return age > maxAge;
  }
}

/**
 * Secure API client with encryption
 */
export class SecureAPIClient {
  private baseURL: string;
  private encryptionKey?: CryptoKey;

  constructor(baseURL: string, encryptionKey?: CryptoKey) {
    this.baseURL = baseURL;
    this.encryptionKey = encryptionKey;
  }

  /**
   * Make secure API request
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    encrypt = false
  ): Promise<T> {
    const token = SecureSession.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    };

    let body = options.body;
    if (encrypt && body && this.encryptionKey) {
      const encrypted = await DataEncryption.encrypt(
        typeof body === 'string' ? body : JSON.stringify(body),
        this.encryptionKey
      );
      body = JSON.stringify({ encrypted });
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
      body
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Decrypt response if needed
    if (data.encrypted && this.encryptionKey) {
      const decrypted = await DataEncryption.decrypt(data.encrypted, this.encryptionKey);
      return JSON.parse(decrypted);
    }

    return data;
  }
}

export default {
  DataEncryption,
  DataMasking,
  SecureSession,
  InputSanitizer,
  CSPHelper,
  DataRetention,
  SecureAPIClient
};
