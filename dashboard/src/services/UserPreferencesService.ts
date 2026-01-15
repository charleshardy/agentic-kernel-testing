// User preferences service for cross-device consistency

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  sidebarCollapsed: boolean;
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    inApp: boolean;
    sound: boolean;
  };
  dashboard: {
    defaultView: string;
    refreshInterval: number;
    widgetsLayout: string[];
  };
  accessibility: {
    highContrast: boolean;
    fontSize: 'small' | 'medium' | 'large';
    reducedMotion: boolean;
  };
  mobile: {
    compactView: boolean;
    offlineMode: boolean;
    dataSync: 'wifi' | 'always' | 'manual';
  };
}

const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'auto',
  sidebarCollapsed: false,
  language: 'en',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  notifications: {
    email: true,
    push: true,
    inApp: true,
    sound: false
  },
  dashboard: {
    defaultView: 'overview',
    refreshInterval: 30000,
    widgetsLayout: ['security', 'ai-models', 'resources', 'notifications', 'analytics']
  },
  accessibility: {
    highContrast: false,
    fontSize: 'medium',
    reducedMotion: false
  },
  mobile: {
    compactView: true,
    offlineMode: false,
    dataSync: 'wifi'
  }
};

class UserPreferencesService {
  private static instance: UserPreferencesService;
  private preferences: UserPreferences;
  private listeners: Set<(prefs: UserPreferences) => void> = new Set();

  private constructor() {
    this.preferences = this.loadPreferences();
    this.applyPreferences();
  }

  static getInstance(): UserPreferencesService {
    if (!UserPreferencesService.instance) {
      UserPreferencesService.instance = new UserPreferencesService();
    }
    return UserPreferencesService.instance;
  }

  /**
   * Load preferences from localStorage and sync with server
   */
  private loadPreferences(): UserPreferences {
    try {
      const stored = localStorage.getItem('userPreferences');
      if (stored) {
        return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
    return DEFAULT_PREFERENCES;
  }

  /**
   * Save preferences to localStorage and sync with server
   */
  private savePreferences(): void {
    try {
      localStorage.setItem('userPreferences', JSON.stringify(this.preferences));
      this.syncWithServer();
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  }

  /**
   * Sync preferences with server for cross-device consistency
   */
  private async syncWithServer(): Promise<void> {
    try {
      await fetch('/api/user/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.preferences)
      });
    } catch (error) {
      console.error('Failed to sync preferences with server:', error);
    }
  }

  /**
   * Load preferences from server
   */
  async loadFromServer(): Promise<void> {
    try {
      const response = await fetch('/api/user/preferences');
      if (response.ok) {
        const serverPrefs = await response.json();
        this.preferences = { ...DEFAULT_PREFERENCES, ...serverPrefs };
        this.savePreferences();
        this.applyPreferences();
        this.notifyListeners();
      }
    } catch (error) {
      console.error('Failed to load preferences from server:', error);
    }
  }

  /**
   * Apply preferences to the application
   */
  private applyPreferences(): void {
    // Apply theme
    this.applyTheme();
    
    // Apply accessibility settings
    this.applyAccessibility();
    
    // Apply mobile settings
    this.applyMobileSettings();
  }

  private applyTheme(): void {
    const theme = this.preferences.theme === 'auto'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : this.preferences.theme;
    
    document.documentElement.setAttribute('data-theme', theme);
  }

  private applyAccessibility(): void {
    const { highContrast, fontSize, reducedMotion } = this.preferences.accessibility;
    
    document.documentElement.classList.toggle('high-contrast', highContrast);
    document.documentElement.setAttribute('data-font-size', fontSize);
    
    if (reducedMotion) {
      document.documentElement.style.setProperty('--animation-duration', '0.01ms');
    }
  }

  private applyMobileSettings(): void {
    if ('serviceWorker' in navigator && this.preferences.mobile.offlineMode) {
      navigator.serviceWorker.register('/service-worker.js');
    }
  }

  /**
   * Get current preferences
   */
  getPreferences(): UserPreferences {
    return { ...this.preferences };
  }

  /**
   * Update preferences
   */
  updatePreferences(updates: Partial<UserPreferences>): void {
    this.preferences = { ...this.preferences, ...updates };
    this.savePreferences();
    this.applyPreferences();
    this.notifyListeners();
  }

  /**
   * Reset to default preferences
   */
  resetToDefaults(): void {
    this.preferences = { ...DEFAULT_PREFERENCES };
    this.savePreferences();
    this.applyPreferences();
    this.notifyListeners();
  }

  /**
   * Subscribe to preference changes
   */
  subscribe(listener: (prefs: UserPreferences) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.preferences));
  }

  /**
   * Export preferences for backup
   */
  exportPreferences(): string {
    return JSON.stringify(this.preferences, null, 2);
  }

  /**
   * Import preferences from backup
   */
  importPreferences(json: string): boolean {
    try {
      const imported = JSON.parse(json);
      this.preferences = { ...DEFAULT_PREFERENCES, ...imported };
      this.savePreferences();
      this.applyPreferences();
      this.notifyListeners();
      return true;
    } catch (error) {
      console.error('Failed to import preferences:', error);
      return false;
    }
  }
}

export default UserPreferencesService.getInstance();
