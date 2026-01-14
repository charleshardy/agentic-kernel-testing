// Sidebar Service Implementation

import {
  SidebarService,
  NotificationService,
  PermissionService,
  UserPreferences,
  NotificationCounts,
  NotificationCountUpdate,
  Notification,
  Role,
  PermissionContext,
  SearchResult,
  FilterOptions,
  SidebarItem,
  SidebarSection,
  DEFAULT_USER_PREFERENCES,
  DEFAULT_NOTIFICATION_COUNTS
} from '../types/sidebar'

/**
 * Mock implementation of SidebarService for development
 * In production, this would connect to actual backend APIs
 */
export class MockSidebarService implements SidebarService {
  private userPreferencesCache = new Map<string, UserPreferences>()
  private notificationCountsCache = new Map<string, NotificationCounts>()
  private permissionsCache = new Map<string, string[]>()

  async getUserPreferences(userId: string): Promise<UserPreferences> {
    // Try to get from cache first
    if (this.userPreferencesCache.has(userId)) {
      return this.userPreferencesCache.get(userId)!
    }

    // Try to get from localStorage
    const stored = localStorage.getItem(`sidebar-preferences-${userId}`)
    if (stored) {
      try {
        const preferences = JSON.parse(stored)
        this.userPreferencesCache.set(userId, preferences)
        return preferences
      } catch (error) {
        console.warn('Failed to parse stored preferences:', error)
      }
    }

    // Return defaults
    const defaultPrefs = { ...DEFAULT_USER_PREFERENCES }
    this.userPreferencesCache.set(userId, defaultPrefs)
    return defaultPrefs
  }

  async updateUserPreferences(userId: string, preferences: Partial<UserPreferences>): Promise<void> {
    const current = await this.getUserPreferences(userId)
    const updated = { ...current, ...preferences }
    
    this.userPreferencesCache.set(userId, updated)
    localStorage.setItem(`sidebar-preferences-${userId}`, JSON.stringify(updated))
  }

  async getNotificationCounts(userId: string): Promise<NotificationCounts> {
    if (this.notificationCountsCache.has(userId)) {
      return this.notificationCountsCache.get(userId)!
    }

    // Mock notification counts - in production, fetch from API
    const mockCounts: NotificationCounts = {
      security: Math.floor(Math.random() * 5),
      vulnerabilities: Math.floor(Math.random() * 10),
      defects: Math.floor(Math.random() * 8),
      aiModels: Math.floor(Math.random() * 3),
      resources: Math.floor(Math.random() * 6),
      integrations: Math.floor(Math.random() * 4),
      notifications: Math.floor(Math.random() * 15),
      total: 0,
      unread: Math.floor(Math.random() * 20),
      acknowledged: Math.floor(Math.random() * 50),
      byPriority: {
        critical: Math.floor(Math.random() * 2),
        high: Math.floor(Math.random() * 5),
        medium: Math.floor(Math.random() * 10),
        low: Math.floor(Math.random() * 15)
      },
      byCategory: {
        security: Math.floor(Math.random() * 5),
        performance: Math.floor(Math.random() * 8),
        system: Math.floor(Math.random() * 12)
      }
    }

    // Calculate total
    mockCounts.total = (mockCounts.security || 0) + (mockCounts.vulnerabilities || 0) + 
                     (mockCounts.defects || 0) + (mockCounts.aiModels || 0) + 
                     (mockCounts.resources || 0) + (mockCounts.integrations || 0) + 
                     (mockCounts.notifications || 0)

    this.notificationCountsCache.set(userId, mockCounts)
    return mockCounts
  }

  async updateNotificationCount(userId: string, update: NotificationCountUpdate): Promise<void> {
    const current = await this.getNotificationCounts(userId)
    const updated = { ...current }
    
    // Update specific category
    if (update.itemKey in updated) {
      (updated as any)[update.itemKey] = update.count
    }

    // Recalculate total
    updated.total = (updated.security || 0) + (updated.vulnerabilities || 0) + 
                   (updated.defects || 0) + (updated.aiModels || 0) + 
                   (updated.resources || 0) + (updated.integrations || 0) + 
                   (updated.notifications || 0)

    this.notificationCountsCache.set(userId, updated)
  }

  async getUserPermissions(userId: string): Promise<string[]> {
    if (this.permissionsCache.has(userId)) {
      return this.permissionsCache.get(userId)!
    }

    // Mock permissions - in production, fetch from API based on user roles
    const mockPermissions = [
      'dashboard.read',
      'dashboard.write',
      'security.read',
      'security.vulnerabilities.read',
      'ai.models.read',
      'users.read',
      'teams.read',
      'audit.read',
      'compliance.read',
      'notifications.read',
      'knowledge.read',
      'settings.read',
      'test-cases.read',
      'test-plans.read',
      'test-execution.read',
      'test-results.read',
      'coverage.read',
      'performance.read',
      'environment.read',
      'infrastructure.read',
      'deployment.read',
      'resources.read',
      'integrations.read',
      'backup.read'
    ]

    this.permissionsCache.set(userId, mockPermissions)
    return mockPermissions
  }

  async validatePermission(userId: string, permission: string): Promise<boolean> {
    const userPermissions = await this.getUserPermissions(userId)
    return userPermissions.includes(permission)
  }

  async logAnalyticsEvent(userId: string, event: string, data: any): Promise<void> {
    // Mock analytics logging - in production, send to analytics service
    console.log(`Analytics Event [${userId}]: ${event}`, data)
    
    // Store in localStorage for development
    const analyticsKey = `sidebar-analytics-${userId}`
    const stored = localStorage.getItem(analyticsKey)
    let analytics = stored ? JSON.parse(stored) : { events: [] }
    
    analytics.events.push({
      event,
      data,
      timestamp: new Date().toISOString()
    })

    // Keep only last 100 events
    if (analytics.events.length > 100) {
      analytics.events = analytics.events.slice(-100)
    }

    localStorage.setItem(analyticsKey, JSON.stringify(analytics))
  }

  async searchItems(query: string, filters: FilterOptions): Promise<SearchResult[]> {
    // Mock search implementation - in production, use proper search service
    const mockSections: SidebarSection[] = [] // Would get from configuration
    const results: SearchResult[] = []

    mockSections.forEach(section => {
      section.items.forEach(item => {
        const matchesQuery = !query || 
          item.label.toLowerCase().includes(query.toLowerCase()) ||
          item.path.toLowerCase().includes(query.toLowerCase())

        const matchesFilters = !filters.permissions || 
          !item.permissions || 
          item.permissions.some(p => filters.permissions!.includes(p))

        if (matchesQuery && matchesFilters) {
          results.push({
            item,
            section,
            matchType: item.label.toLowerCase().includes(query.toLowerCase()) ? 'label' : 'path',
            score: calculateSearchScore(item, query)
          })
        }
      })
    })

    return results.sort((a, b) => b.score - a.score)
  }
}

/**
 * Mock implementation of NotificationService
 */
export class MockNotificationService implements NotificationService {
  private notifications = new Map<string, Notification[]>()
  private subscribers = new Map<string, ((counts: NotificationCounts) => void)[]>()

  async getUnreadCount(userId: string): Promise<number> {
    const userNotifications = this.notifications.get(userId) || []
    return userNotifications.filter(n => !n.readAt).length
  }

  async markAsRead(userId: string, notificationIds: string[]): Promise<void> {
    const userNotifications = this.notifications.get(userId) || []
    const now = new Date()
    
    userNotifications.forEach(notification => {
      if (notificationIds.includes(notification.id)) {
        notification.readAt = now
      }
    })

    this.notifications.set(userId, userNotifications)
    await this.notifySubscribers(userId)
  }

  subscribe(userId: string, callback: (counts: NotificationCounts) => void): () => void {
    if (!this.subscribers.has(userId)) {
      this.subscribers.set(userId, [])
    }
    
    this.subscribers.get(userId)!.push(callback)
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(userId) || []
      const index = callbacks.indexOf(callback)
      if (index !== -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  async getNotificationsByCategory(userId: string, category: string): Promise<Notification[]> {
    const userNotifications = this.notifications.get(userId) || []
    return userNotifications.filter(n => n.category === category)
  }

  async createNotification(notification: Omit<Notification, 'id' | 'createdAt'>): Promise<Notification> {
    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date()
    }

    // Add to user's notifications (assuming userId is in metadata)
    const userId = notification.metadata?.userId || 'default'
    const userNotifications = this.notifications.get(userId) || []
    userNotifications.push(newNotification)
    this.notifications.set(userId, userNotifications)

    await this.notifySubscribers(userId)
    return newNotification
  }

  private async notifySubscribers(userId: string): Promise<void> {
    const callbacks = this.subscribers.get(userId) || []
    const counts = await this.calculateNotificationCounts(userId)
    
    callbacks.forEach(callback => {
      try {
        callback(counts)
      } catch (error) {
        console.error('Error in notification subscriber callback:', error)
      }
    })
  }

  private async calculateNotificationCounts(userId: string): Promise<NotificationCounts> {
    const userNotifications = this.notifications.get(userId) || []
    
    const counts: NotificationCounts = {
      total: userNotifications.length,
      unread: userNotifications.filter(n => !n.readAt).length,
      acknowledged: userNotifications.filter(n => n.acknowledgedAt).length,
      byPriority: {
        critical: userNotifications.filter(n => n.priority === 'urgent').length,
        high: userNotifications.filter(n => n.priority === 'high').length,
        medium: userNotifications.filter(n => n.priority === 'medium').length,
        low: userNotifications.filter(n => n.priority === 'low').length
      },
      byCategory: {}
    }

    // Calculate by category
    userNotifications.forEach(notification => {
      if (!counts.byCategory![notification.category]) {
        counts.byCategory![notification.category] = 0
      }
      counts.byCategory![notification.category]++
    })

    return counts
  }
}

/**
 * Mock implementation of PermissionService
 */
export class MockPermissionService implements PermissionService {
  private roleCache = new Map<string, Role[]>()
  private permissionCache = new Map<string, { permissions: string[], expiry: number }>()

  async checkPermission(userId: string, permission: string, context?: PermissionContext): Promise<boolean> {
    const userPermissions = await this.getEffectivePermissions(userId)
    
    // Basic permission check
    if (userPermissions.includes(permission)) {
      return true
    }

    // Check for wildcard permissions
    const wildcardPermission = permission.split('.').slice(0, -1).join('.') + '.*'
    if (userPermissions.includes(wildcardPermission)) {
      return true
    }

    // Check for admin permissions
    if (userPermissions.includes('admin.*') || userPermissions.includes('*')) {
      return true
    }

    return false
  }

  async getUserRoles(userId: string): Promise<Role[]> {
    if (this.roleCache.has(userId)) {
      return this.roleCache.get(userId)!
    }

    // Mock roles - in production, fetch from API
    const mockRoles: Role[] = [
      {
        id: 'user',
        name: 'User',
        description: 'Standard user role',
        isSystem: true,
        permissions: [
          { id: 'dashboard.read', resource: 'dashboard', action: 'read' },
          { id: 'test-cases.read', resource: 'test-cases', action: 'read' }
        ]
      },
      {
        id: 'tester',
        name: 'Tester',
        description: 'Testing role with extended permissions',
        isSystem: false,
        permissions: [
          { id: 'test-execution.read', resource: 'test-execution', action: 'read' },
          { id: 'test-results.read', resource: 'test-results', action: 'read' }
        ]
      }
    ]

    this.roleCache.set(userId, mockRoles)
    return mockRoles
  }

  async getEffectivePermissions(userId: string): Promise<string[]> {
    // Check cache first
    const cached = this.permissionCache.get(userId)
    if (cached && cached.expiry > Date.now()) {
      return cached.permissions
    }

    const roles = await this.getUserRoles(userId)
    const permissions = new Set<string>()

    roles.forEach(role => {
      role.permissions.forEach(permission => {
        permissions.add(permission.id)
      })
    })

    const permissionArray = Array.from(permissions)
    
    // Cache for 5 minutes
    this.permissionCache.set(userId, {
      permissions: permissionArray,
      expiry: Date.now() + 5 * 60 * 1000
    })

    return permissionArray
  }

  async validateAccess(userId: string, resource: string, action: string): Promise<boolean> {
    const permission = `${resource}.${action}`
    return this.checkPermission(userId, permission)
  }

  async cachePermissions(userId: string, permissions: string[], ttl?: number): Promise<void> {
    const expiry = Date.now() + (ttl || 5 * 60 * 1000) // Default 5 minutes
    this.permissionCache.set(userId, { permissions, expiry })
  }

  async invalidateCache(userId: string): Promise<void> {
    this.permissionCache.delete(userId)
    this.roleCache.delete(userId)
  }
}

// Helper functions
function calculateSearchScore(item: SidebarItem, query: string): number {
  if (!query) return 0
  
  const queryLower = query.toLowerCase()
  let score = 0

  // Exact label match gets highest score
  if (item.label.toLowerCase() === queryLower) {
    score += 100
  }
  // Label starts with query
  else if (item.label.toLowerCase().startsWith(queryLower)) {
    score += 80
  }
  // Label contains query
  else if (item.label.toLowerCase().includes(queryLower)) {
    score += 60
  }

  // Path matches
  if (item.path.toLowerCase().includes(queryLower)) {
    score += 40
  }

  // Metadata matches
  if (item.metadata?.description?.toLowerCase().includes(queryLower)) {
    score += 20
  }

  return score
}

// Export singleton instances
export const sidebarService = new MockSidebarService()
export const notificationService = new MockNotificationService()
export const permissionService = new MockPermissionService()