// Sidebar Type Definitions for Enhanced Navigation

export interface BadgeConfig {
  count?: number
  status?: 'success' | 'warning' | 'error' | 'info'
  pulse?: boolean
}

export interface SidebarItem {
  key: string
  icon: React.ComponentType
  label: string
  path: string
  badge?: BadgeConfig
  permissions?: string[]
  children?: SidebarItem[]
  metadata?: Record<string, any>
}

export interface SidebarSection {
  id: string
  title: string
  icon: React.ComponentType
  items: SidebarItem[]
  collapsible: boolean
  defaultCollapsed?: boolean
  permissions?: string[]
  order?: number
}

// Sidebar customization and preference interfaces
export interface SidebarCustomization {
  layout: 'vertical' | 'horizontal' | 'mini'
  width: number
  collapsedWidth: number
  position: 'left' | 'right'
  autoCollapse: boolean
  showLabels: boolean
  showIcons: boolean
  groupSeparators: boolean
}

export interface UserPreferences {
  collapsedSections: string[]
  sidebarOrder: string[]
  hiddenItems: string[]
  theme?: 'light' | 'dark'
  compactMode?: boolean
  customization?: SidebarCustomization
  searchHistory?: string[]
  favoriteItems?: string[]
  recentlyAccessed?: Array<{
    itemKey: string
    timestamp: Date
    frequency: number
  }>
}

// Enhanced notification count tracking interfaces
export interface NotificationCounts {
  security?: number
  vulnerabilities?: number
  defects?: number
  aiModels?: number
  resources?: number
  integrations?: number
  notifications?: number
  total?: number
  byPriority?: {
    critical: number
    high: number
    medium: number
    low: number
  }
  byCategory?: Record<string, number>
  unread?: number
  acknowledged?: number
}

export interface NotificationCountUpdate {
  itemKey: string
  count: number
  priority?: 'critical' | 'high' | 'medium' | 'low'
  category?: string
  timestamp: Date
  source: string
}

// Role-based access control interfaces
export interface RoleBasedAccess {
  userId: string
  roles: string[]
  permissions: string[]
  restrictions: AccessRestriction[]
  effectivePermissions: string[]
  lastUpdated: Date
}

export interface AccessRestriction {
  type: 'time' | 'location' | 'resource' | 'condition'
  rule: string
  value: any
  active: boolean
  expiresAt?: Date
}

export interface PermissionGroup {
  id: string
  name: string
  description: string
  permissions: string[]
  inherits?: string[]
  conditions?: PermissionCondition[]
}

// Advanced permission system interfaces
export interface DynamicPermission {
  id: string
  resource: string
  action: string
  condition: (context: PermissionContext) => boolean
  priority: number
  cacheable: boolean
  ttl?: number
}

export interface PermissionContext {
  user: User
  resource: any
  environment: 'development' | 'staging' | 'production'
  timestamp: Date
  metadata: Record<string, any>
}

export interface PermissionCache {
  userId: string
  permissions: Map<string, boolean>
  lastUpdated: Date
  ttl: number
}

// Sidebar state management interfaces
export interface SidebarState {
  collapsed: boolean
  activeSection: string | null
  activeItem: string | null
  searchTerm: string
  filterOptions: FilterOptions
  userPreferences: UserPreferences
  notificationCounts: NotificationCounts
  loading: boolean
  error: string | null
}

export interface SidebarAction {
  type: 'TOGGLE_COLLAPSE' | 'SET_ACTIVE_SECTION' | 'SET_ACTIVE_ITEM' | 
        'UPDATE_SEARCH' | 'UPDATE_FILTERS' | 'UPDATE_PREFERENCES' | 
        'UPDATE_NOTIFICATIONS' | 'SET_LOADING' | 'SET_ERROR' | 'RESET'
  payload?: any
}

// Sidebar configuration interfaces
export interface SidebarConfiguration {
  sections: SidebarSection[]
  defaultPreferences: UserPreferences
  permissionProvider: (userId: string) => Promise<string[]>
  notificationProvider: (userId: string) => Promise<NotificationCounts>
  analyticsProvider?: (event: string, data: any) => void
  theme: SidebarTheme
  features: {
    search: boolean
    notifications: boolean
    customization: boolean
    analytics: boolean
    accessibility: boolean
  }
}

export interface EnhancedSidebarProps {
  collapsed: boolean
  onCollapse: (collapsed: boolean) => void
  userPermissions: string[]
  notificationCounts: NotificationCounts
  theme?: 'light' | 'dark'
  onPreferencesChange?: (preferences: UserPreferences) => void
}

// Permission system types
export interface Permission {
  id: string
  resource: string
  action: 'create' | 'read' | 'update' | 'delete' | 'execute'
  conditions?: PermissionCondition[]
}

export interface PermissionCondition {
  field: string
  operator: 'equals' | 'contains' | 'in' | 'not_in'
  value: any
}

export interface Role {
  id: string
  name: string
  description: string
  permissions: Permission[]
  isSystem: boolean
}

export interface User {
  id: string
  username: string
  email: string
  firstName: string
  lastName: string
  roles: Role[]
  permissions: Permission[]
  preferences: UserPreferences
  lastLogin: Date
  status: 'active' | 'inactive' | 'suspended'
  createdAt: Date
}

// Navigation context types
export interface NavigationContext {
  currentPath: string
  breadcrumbs: BreadcrumbItem[]
  pageTitle: string
  pageDescription?: string
  actions?: NavigationAction[]
}

export interface BreadcrumbItem {
  title: string
  path?: string
  icon?: React.ComponentType
}

export interface NavigationAction {
  key: string
  label: string
  icon?: React.ComponentType
  onClick: () => void
  type?: 'primary' | 'default' | 'dashed' | 'link'
  danger?: boolean
}

// Search and filtering types
export interface SearchResult {
  item: SidebarItem
  section: SidebarSection
  matchType: 'label' | 'path' | 'description'
  score: number
}

export interface FilterOptions {
  searchTerm?: string
  permissions?: string[]
  sections?: string[]
  hasNotifications?: boolean
}

// Analytics and tracking types
export interface SidebarAnalytics {
  itemClicks: Record<string, number>
  searchQueries: string[]
  sectionToggleCount: Record<string, number>
  timeSpentInSections: Record<string, number>
  lastAccessed: Record<string, Date>
}

// Theme and styling types
export interface SidebarTheme {
  primaryColor: string
  backgroundColor: string
  textColor: string
  hoverColor: string
  activeColor: string
  borderColor: string
  shadowColor: string
}

// Integration with external systems
export interface ExternalIntegration {
  id: string
  name: string
  type: 'webhook' | 'api' | 'sso' | 'notification'
  status: 'active' | 'inactive' | 'error'
  lastSync?: Date
  config: Record<string, any>
}

// Notification system types
export interface Notification {
  id: string
  type: 'alert' | 'info' | 'warning' | 'success' | 'system'
  title: string
  message: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: string
  targetPath?: string
  metadata?: Record<string, any>
  createdAt: Date
  readAt?: Date
  acknowledgedAt?: Date
}

// Security and audit types
export interface AuditEvent {
  id: string
  userId: string
  action: string
  resource: string
  details: Record<string, any>
  timestamp: Date
  ipAddress?: string
  userAgent?: string
}

// Performance monitoring types
export interface PerformanceMetrics {
  loadTime: number
  renderTime: number
  interactionTime: number
  memoryUsage: number
  errorCount: number
  timestamp: Date
}

// Feature flags and configuration
export interface FeatureFlag {
  key: string
  enabled: boolean
  conditions?: FeatureFlagCondition[]
  rolloutPercentage?: number
}

export interface FeatureFlagCondition {
  type: 'user' | 'role' | 'permission' | 'custom'
  operator: 'equals' | 'in' | 'contains'
  value: any
}

// Service interfaces for sidebar functionality
export interface SidebarService {
  getUserPreferences(userId: string): Promise<UserPreferences>
  updateUserPreferences(userId: string, preferences: Partial<UserPreferences>): Promise<void>
  getNotificationCounts(userId: string): Promise<NotificationCounts>
  updateNotificationCount(userId: string, update: NotificationCountUpdate): Promise<void>
  getUserPermissions(userId: string): Promise<string[]>
  validatePermission(userId: string, permission: string): Promise<boolean>
  logAnalyticsEvent(userId: string, event: string, data: any): Promise<void>
  searchItems(query: string, filters: FilterOptions): Promise<SearchResult[]>
}

export interface NotificationService {
  getUnreadCount(userId: string): Promise<number>
  markAsRead(userId: string, notificationIds: string[]): Promise<void>
  subscribe(userId: string, callback: (counts: NotificationCounts) => void): () => void
  getNotificationsByCategory(userId: string, category: string): Promise<Notification[]>
  createNotification(notification: Omit<Notification, 'id' | 'createdAt'>): Promise<Notification>
}

export interface PermissionService {
  checkPermission(userId: string, permission: string, context?: PermissionContext): Promise<boolean>
  getUserRoles(userId: string): Promise<Role[]>
  getEffectivePermissions(userId: string): Promise<string[]>
  validateAccess(userId: string, resource: string, action: string): Promise<boolean>
  cachePermissions(userId: string, permissions: string[], ttl?: number): Promise<void>
  invalidateCache(userId: string): Promise<void>
}

// Data persistence interfaces
export interface SidebarRepository {
  saveUserPreferences(userId: string, preferences: UserPreferences): Promise<void>
  loadUserPreferences(userId: string): Promise<UserPreferences | null>
  saveNotificationCounts(userId: string, counts: NotificationCounts): Promise<void>
  loadNotificationCounts(userId: string): Promise<NotificationCounts | null>
  saveAnalyticsData(userId: string, analytics: SidebarAnalytics): Promise<void>
  loadAnalyticsData(userId: string): Promise<SidebarAnalytics | null>
}

// Event system interfaces
export interface SidebarEvent {
  type: string
  userId: string
  data: any
  timestamp: Date
  source: 'user' | 'system' | 'external'
}

export interface SidebarEventHandler {
  handle(event: SidebarEvent): Promise<void>
  canHandle(eventType: string): boolean
}

export interface SidebarEventBus {
  emit(event: SidebarEvent): Promise<void>
  subscribe(eventType: string, handler: SidebarEventHandler): () => void
  unsubscribe(eventType: string, handler: SidebarEventHandler): void
}

// Accessibility interfaces
export interface AccessibilityOptions {
  highContrast: boolean
  reducedMotion: boolean
  screenReaderOptimized: boolean
  keyboardNavigation: boolean
  focusIndicators: boolean
  ariaLabels: Record<string, string>
}

export interface KeyboardShortcut {
  key: string
  modifiers: ('ctrl' | 'alt' | 'shift' | 'meta')[]
  action: string
  description: string
  enabled: boolean
}

// Internationalization interfaces
export interface SidebarTranslations {
  [key: string]: string | SidebarTranslations
}

export interface LocalizationConfig {
  locale: string
  translations: SidebarTranslations
  rtl: boolean
  dateFormat: string
  numberFormat: Intl.NumberFormatOptions
}

// Performance monitoring interfaces
export interface SidebarPerformanceMetrics extends PerformanceMetrics {
  sidebarSpecific: {
    itemRenderTime: number
    searchResponseTime: number
    permissionCheckTime: number
    notificationUpdateTime: number
    preferencesSaveTime: number
  }
}

export interface PerformanceMonitor {
  startTiming(operation: string): string
  endTiming(timingId: string): number
  recordMetric(name: string, value: number, tags?: Record<string, string>): void
  getMetrics(): SidebarPerformanceMetrics
  reset(): void
}

// Export additional utility types
export type SidebarEventType = 'item_click' | 'section_toggle' | 'search' | 'preference_change' | 'notification_update'
export type NotificationPriority = 'critical' | 'high' | 'medium' | 'low'
export type AccessLevel = 'none' | 'read' | 'write' | 'admin'

// Enhanced constants
export const SIDEBAR_EVENTS = {
  ITEM_CLICKED: 'item_click',
  SECTION_TOGGLED: 'section_toggle',
  SEARCH_PERFORMED: 'search',
  PREFERENCES_CHANGED: 'preference_change',
  NOTIFICATIONS_UPDATED: 'notification_update',
  PERMISSIONS_CHANGED: 'permissions_change',
  THEME_CHANGED: 'theme_change'
} as const

export const NOTIFICATION_PRIORITIES = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
} as const

export const ACCESS_LEVELS = {
  NONE: 'none',
  READ: 'read',
  WRITE: 'write',
  ADMIN: 'admin'
} as const

// Constants for default values
export const DEFAULT_NOTIFICATION_COUNTS: NotificationCounts = {
  security: 0,
  vulnerabilities: 0,
  defects: 0,
  aiModels: 0,
  resources: 0,
  integrations: 0,
  notifications: 0,
  total: 0
}

export const DEFAULT_USER_PREFERENCES: UserPreferences = {
  collapsedSections: [],
  sidebarOrder: [],
  hiddenItems: [],
  theme: 'light',
  compactMode: false
}

// Permission constants
export const PERMISSIONS = {
  DASHBOARD: {
    READ: 'dashboard.read',
    WRITE: 'dashboard.write'
  },
  SECURITY: {
    READ: 'security.read',
    WRITE: 'security.write',
    VULNERABILITIES_READ: 'security.vulnerabilities.read',
    VULNERABILITIES_WRITE: 'security.vulnerabilities.write'
  },
  AI_MODELS: {
    READ: 'ai.models.read',
    WRITE: 'ai.models.write',
    CONFIGURE: 'ai.models.configure'
  },
  USERS: {
    READ: 'users.read',
    WRITE: 'users.write',
    DELETE: 'users.delete'
  },
  TEAMS: {
    READ: 'teams.read',
    WRITE: 'teams.write',
    DELETE: 'teams.delete'
  },
  AUDIT: {
    READ: 'audit.read',
    EXPORT: 'audit.export'
  },
  COMPLIANCE: {
    READ: 'compliance.read',
    WRITE: 'compliance.write'
  },
  NOTIFICATIONS: {
    READ: 'notifications.read',
    WRITE: 'notifications.write'
  },
  KNOWLEDGE: {
    READ: 'knowledge.read',
    WRITE: 'knowledge.write'
  },
  SETTINGS: {
    READ: 'settings.read',
    WRITE: 'settings.write'
  }
} as const