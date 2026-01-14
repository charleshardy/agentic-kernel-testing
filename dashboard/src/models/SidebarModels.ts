// Sidebar Data Models and Business Logic

import { 
  SidebarItem, 
  SidebarSection, 
  UserPreferences, 
  NotificationCounts,
  Permission,
  Role,
  SidebarAnalytics,
  DEFAULT_USER_PREFERENCES,
  DEFAULT_NOTIFICATION_COUNTS
} from '../types/sidebar'

/**
 * SidebarItemModel - Business logic for sidebar items
 */
export class SidebarItemModel {
  constructor(private item: SidebarItem) {}

  get key(): string {
    return this.item.key
  }

  get label(): string {
    return this.item.label
  }

  get path(): string {
    return this.item.path
  }

  hasPermission(userPermissions: string[]): boolean {
    if (!this.item.permissions || this.item.permissions.length === 0) {
      return true
    }
    return this.item.permissions.some(permission => userPermissions.includes(permission))
  }

  hasNotification(): boolean {
    return this.item.badge !== undefined && (this.item.badge.count ?? 0) > 0
  }

  getNotificationCount(): number {
    return this.item.badge?.count ?? 0
  }

  matchesSearch(searchTerm: string): boolean {
    const term = searchTerm.toLowerCase()
    return (
      this.item.label.toLowerCase().includes(term) ||
      this.item.path.toLowerCase().includes(term) ||
      (this.item.metadata?.description?.toLowerCase().includes(term) ?? false)
    )
  }

  toJSON(): SidebarItem {
    return { ...this.item }
  }
}

/**
 * SidebarSectionModel - Business logic for sidebar sections
 */
export class SidebarSectionModel {
  private items: SidebarItemModel[]

  constructor(private section: SidebarSection) {
    this.items = section.items.map(item => new SidebarItemModel(item))
  }

  get id(): string {
    return this.section.id
  }

  get title(): string {
    return this.section.title
  }

  get collapsible(): boolean {
    return this.section.collapsible
  }

  getVisibleItems(userPermissions: string[]): SidebarItemModel[] {
    return this.items.filter(item => item.hasPermission(userPermissions))
  }

  getItemsWithNotifications(): SidebarItemModel[] {
    return this.items.filter(item => item.hasNotification())
  }

  getTotalNotificationCount(): number {
    return this.items.reduce((total, item) => total + item.getNotificationCount(), 0)
  }

  searchItems(searchTerm: string, userPermissions: string[]): SidebarItemModel[] {
    return this.getVisibleItems(userPermissions).filter(item => 
      item.matchesSearch(searchTerm)
    )
  }

  hasPermission(userPermissions: string[]): boolean {
    if (!this.section.permissions || this.section.permissions.length === 0) {
      return true
    }
    return this.section.permissions.some(permission => userPermissions.includes(permission))
  }

  toJSON(): SidebarSection {
    return {
      ...this.section,
      items: this.items.map(item => item.toJSON())
    }
  }
}

/**
 * UserPreferencesModel - Business logic for user preferences
 */
export class UserPreferencesModel {
  private preferences: UserPreferences

  constructor(preferences?: Partial<UserPreferences>) {
    this.preferences = {
      ...DEFAULT_USER_PREFERENCES,
      ...preferences
    }
  }

  isSectionCollapsed(sectionId: string): boolean {
    return this.preferences.collapsedSections.includes(sectionId)
  }

  toggleSection(sectionId: string): void {
    const index = this.preferences.collapsedSections.indexOf(sectionId)
    if (index === -1) {
      this.preferences.collapsedSections.push(sectionId)
    } else {
      this.preferences.collapsedSections.splice(index, 1)
    }
  }

  isItemHidden(itemKey: string): boolean {
    return this.preferences.hiddenItems.includes(itemKey)
  }

  hideItem(itemKey: string): void {
    if (!this.preferences.hiddenItems.includes(itemKey)) {
      this.preferences.hiddenItems.push(itemKey)
    }
  }

  showItem(itemKey: string): void {
    const index = this.preferences.hiddenItems.indexOf(itemKey)
    if (index !== -1) {
      this.preferences.hiddenItems.splice(index, 1)
    }
  }

  addToSearchHistory(searchTerm: string): void {
    if (!this.preferences.searchHistory) {
      this.preferences.searchHistory = []
    }
    
    // Remove if already exists
    const index = this.preferences.searchHistory.indexOf(searchTerm)
    if (index !== -1) {
      this.preferences.searchHistory.splice(index, 1)
    }
    
    // Add to beginning
    this.preferences.searchHistory.unshift(searchTerm)
    
    // Keep only last 10 searches
    this.preferences.searchHistory = this.preferences.searchHistory.slice(0, 10)
  }

  addToFavorites(itemKey: string): void {
    if (!this.preferences.favoriteItems) {
      this.preferences.favoriteItems = []
    }
    
    if (!this.preferences.favoriteItems.includes(itemKey)) {
      this.preferences.favoriteItems.push(itemKey)
    }
  }

  removeFromFavorites(itemKey: string): void {
    if (!this.preferences.favoriteItems) return
    
    const index = this.preferences.favoriteItems.indexOf(itemKey)
    if (index !== -1) {
      this.preferences.favoriteItems.splice(index, 1)
    }
  }

  updateRecentlyAccessed(itemKey: string): void {
    if (!this.preferences.recentlyAccessed) {
      this.preferences.recentlyAccessed = []
    }
    
    const existing = this.preferences.recentlyAccessed.find(item => item.itemKey === itemKey)
    if (existing) {
      existing.timestamp = new Date()
      existing.frequency += 1
    } else {
      this.preferences.recentlyAccessed.push({
        itemKey,
        timestamp: new Date(),
        frequency: 1
      })
    }
    
    // Sort by frequency and timestamp, keep only top 20
    this.preferences.recentlyAccessed.sort((a, b) => {
      if (a.frequency !== b.frequency) {
        return b.frequency - a.frequency
      }
      return b.timestamp.getTime() - a.timestamp.getTime()
    })
    
    this.preferences.recentlyAccessed = this.preferences.recentlyAccessed.slice(0, 20)
  }

  toJSON(): UserPreferences {
    return { ...this.preferences }
  }

  static fromJSON(data: any): UserPreferencesModel {
    return new UserPreferencesModel(data)
  }
}

/**
 * NotificationCountsModel - Business logic for notification counts
 */
export class NotificationCountsModel {
  private counts: NotificationCounts

  constructor(counts?: Partial<NotificationCounts>) {
    this.counts = {
      ...DEFAULT_NOTIFICATION_COUNTS,
      ...counts
    }
  }

  getTotalCount(): number {
    return this.counts.total ?? 0
  }

  getCountForCategory(category: string): number {
    const value = this.counts[category as keyof NotificationCounts]
    return typeof value === 'number' ? value : 0
  }

  updateCount(category: string, count: number): void {
    if (category === 'byPriority' || category === 'byCategory') {
      // Skip complex nested objects
      return
    }
    (this.counts as any)[category] = count
    this.recalculateTotal()
  }

  incrementCount(category: string, increment: number = 1): void {
    const current = this.getCountForCategory(category)
    this.updateCount(category, current + increment)
  }

  decrementCount(category: string, decrement: number = 1): void {
    const current = this.getCountForCategory(category)
    this.updateCount(category, Math.max(0, current - decrement))
  }

  resetCount(category: string): void {
    this.updateCount(category, 0)
  }

  resetAllCounts(): void {
    const simpleKeys = ['security', 'vulnerabilities', 'defects', 'aiModels', 'resources', 'integrations', 'notifications', 'total', 'unread', 'acknowledged']
    simpleKeys.forEach(key => {
      (this.counts as any)[key] = 0
    })
  }

  private recalculateTotal(): void {
    const simpleKeys = ['security', 'vulnerabilities', 'defects', 'aiModels', 'resources', 'integrations', 'notifications', 'unread', 'acknowledged']
    this.counts.total = simpleKeys.reduce((sum, key) => {
      const value = (this.counts as any)[key]
      return sum + (typeof value === 'number' ? value : 0)
    }, 0)
  }

  hasCriticalNotifications(): boolean {
    return (this.counts.byPriority?.critical ?? 0) > 0
  }

  hasUnreadNotifications(): boolean {
    return (this.counts.unread ?? 0) > 0
  }

  toJSON(): NotificationCounts {
    return { ...this.counts }
  }

  static fromJSON(data: any): NotificationCountsModel {
    return new NotificationCountsModel(data)
  }
}

/**
 * PermissionModel - Business logic for permissions
 */
export class PermissionModel {
  constructor(private permission: Permission) {}

  get id(): string {
    return this.permission.id
  }

  get resource(): string {
    return this.permission.resource
  }

  get action(): string {
    return this.permission.action
  }

  matches(resource: string, action: string): boolean {
    return this.permission.resource === resource && this.permission.action === action
  }

  checkConditions(context: any): boolean {
    if (!this.permission.conditions || this.permission.conditions.length === 0) {
      return true
    }

    return this.permission.conditions.every(condition => {
      const value = context[condition.field]
      switch (condition.operator) {
        case 'equals':
          return value === condition.value
        case 'contains':
          return Array.isArray(value) ? value.includes(condition.value) : 
                 typeof value === 'string' ? value.includes(condition.value) : false
        case 'in':
          return Array.isArray(condition.value) ? condition.value.includes(value) : false
        case 'not_in':
          return Array.isArray(condition.value) ? !condition.value.includes(value) : true
        default:
          return false
      }
    })
  }

  toJSON(): Permission {
    return { ...this.permission }
  }
}

/**
 * RoleModel - Business logic for roles
 */
export class RoleModel {
  private permissions: PermissionModel[]

  constructor(private role: Role) {
    this.permissions = role.permissions.map(p => new PermissionModel(p))
  }

  get id(): string {
    return this.role.id
  }

  get name(): string {
    return this.role.name
  }

  get isSystem(): boolean {
    return this.role.isSystem
  }

  hasPermission(resource: string, action: string, context?: any): boolean {
    return this.permissions.some(permission => 
      permission.matches(resource, action) && permission.checkConditions(context ?? {})
    )
  }

  getPermissions(): PermissionModel[] {
    return [...this.permissions]
  }

  toJSON(): Role {
    return {
      ...this.role,
      permissions: this.permissions.map(p => p.toJSON())
    }
  }
}

/**
 * SidebarAnalyticsModel - Business logic for sidebar analytics
 */
export class SidebarAnalyticsModel {
  private analytics: SidebarAnalytics

  constructor(analytics?: Partial<SidebarAnalytics>) {
    this.analytics = {
      itemClicks: {},
      searchQueries: [],
      sectionToggleCount: {},
      timeSpentInSections: {},
      lastAccessed: {},
      ...analytics
    }
  }

  recordItemClick(itemKey: string): void {
    this.analytics.itemClicks[itemKey] = (this.analytics.itemClicks[itemKey] ?? 0) + 1
    this.analytics.lastAccessed[itemKey] = new Date()
  }

  recordSearchQuery(query: string): void {
    this.analytics.searchQueries.push(query)
    // Keep only last 100 queries
    if (this.analytics.searchQueries.length > 100) {
      this.analytics.searchQueries = this.analytics.searchQueries.slice(-100)
    }
  }

  recordSectionToggle(sectionId: string): void {
    this.analytics.sectionToggleCount[sectionId] = (this.analytics.sectionToggleCount[sectionId] ?? 0) + 1
  }

  recordTimeInSection(sectionId: string, timeMs: number): void {
    this.analytics.timeSpentInSections[sectionId] = (this.analytics.timeSpentInSections[sectionId] ?? 0) + timeMs
  }

  getMostClickedItems(limit: number = 10): Array<{ itemKey: string; clicks: number }> {
    return Object.entries(this.analytics.itemClicks)
      .map(([itemKey, clicks]) => ({ itemKey, clicks }))
      .sort((a, b) => b.clicks - a.clicks)
      .slice(0, limit)
  }

  getMostSearchedQueries(limit: number = 10): Array<{ query: string; count: number }> {
    const queryCount: Record<string, number> = {}
    this.analytics.searchQueries.forEach(query => {
      queryCount[query] = (queryCount[query] ?? 0) + 1
    })
    
    return Object.entries(queryCount)
      .map(([query, count]) => ({ query, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit)
  }

  getRecentlyAccessedItems(limit: number = 10): Array<{ itemKey: string; lastAccessed: Date }> {
    return Object.entries(this.analytics.lastAccessed)
      .map(([itemKey, lastAccessed]) => ({ itemKey, lastAccessed }))
      .sort((a, b) => b.lastAccessed.getTime() - a.lastAccessed.getTime())
      .slice(0, limit)
  }

  toJSON(): SidebarAnalytics {
    return { ...this.analytics }
  }

  static fromJSON(data: any): SidebarAnalyticsModel {
    return new SidebarAnalyticsModel(data)
  }
}