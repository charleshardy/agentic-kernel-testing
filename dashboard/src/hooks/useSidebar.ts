// Custom Sidebar Hook

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  SidebarItem,
  SidebarSection,
  UserPreferences,
  NotificationCounts,
  SearchResult,
  FilterOptions,
  SidebarAnalytics,
  SIDEBAR_EVENTS
} from '../types/sidebar'
import { 
  SidebarItemModel, 
  SidebarSectionModel, 
  UserPreferencesModel, 
  NotificationCountsModel,
  SidebarAnalyticsModel
} from '../models/SidebarModels'
import { sidebarService, permissionService } from '../services/SidebarService'
import { useSidebarContext } from '../contexts/SidebarContext'

/**
 * Main sidebar hook that provides all sidebar functionality
 */
export const useSidebar = (userId: string = 'default-user') => {
  const { state, actions } = useSidebarContext()
  const location = useLocation()
  const navigate = useNavigate()

  // Local state for enhanced functionality
  const [userPermissions, setUserPermissions] = useState<string[]>([])
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [analytics, setAnalytics] = useState<SidebarAnalyticsModel>(new SidebarAnalyticsModel())

  // Load user permissions
  useEffect(() => {
    const loadPermissions = async () => {
      try {
        const permissions = await permissionService.getEffectivePermissions(userId)
        setUserPermissions(permissions)
      } catch (error) {
        console.error('Failed to load user permissions:', error)
      }
    }

    loadPermissions()
  }, [userId])

  // Track current page for analytics
  useEffect(() => {
    const currentItem = getCurrentActiveItem()
    if (currentItem) {
      analytics.recordItemClick(currentItem.key)
      actions.logAnalyticsEvent(SIDEBAR_EVENTS.ITEM_CLICKED, {
        itemKey: currentItem.key,
        path: location.pathname
      })
    }
  }, [location.pathname])

  // Get current active item based on location
  const getCurrentActiveItem = useCallback((): SidebarItem | null => {
    // This would be populated from your actual sidebar configuration
    // For now, return null as placeholder
    return null
  }, [location.pathname])

  // Enhanced search functionality
  const performSearch = useCallback(async (query: string, filters?: FilterOptions) => {
    if (!query.trim()) {
      setSearchResults([])
      return []
    }

    try {
      const results = await sidebarService.searchItems(query, filters || {})
      setSearchResults(results)
      
      // Record search analytics
      analytics.recordSearchQuery(query)
      actions.logAnalyticsEvent(SIDEBAR_EVENTS.SEARCH_PERFORMED, {
        query,
        resultsCount: results.length,
        filters
      })

      return results
    } catch (error) {
      console.error('Search failed:', error)
      return []
    }
  }, [analytics, actions])

  // Permission checking
  const hasPermission = useCallback((permission: string): boolean => {
    return userPermissions.includes(permission) || 
           userPermissions.includes('admin.*') || 
           userPermissions.includes('*')
  }, [userPermissions])

  // Navigation with analytics
  const navigateToItem = useCallback((item: SidebarItem) => {
    navigate(item.path)
    
    // Update analytics
    analytics.recordItemClick(item.key)
    actions.logAnalyticsEvent(SIDEBAR_EVENTS.ITEM_CLICKED, {
      itemKey: item.key,
      path: item.path,
      label: item.label
    })
  }, [navigate, analytics, actions])

  // Section management
  const toggleSection = useCallback(async (sectionId: string) => {
    const currentPreferences = new UserPreferencesModel(state.userPreferences)
    currentPreferences.toggleSection(sectionId)
    
    await actions.updatePreferences(currentPreferences.toJSON())
    
    // Record analytics
    analytics.recordSectionToggle(sectionId)
    actions.logAnalyticsEvent(SIDEBAR_EVENTS.SECTION_TOGGLED, {
      sectionId,
      collapsed: currentPreferences.isSectionCollapsed(sectionId)
    })
  }, [state.userPreferences, actions, analytics])

  // Favorites management
  const toggleFavorite = useCallback(async (itemKey: string) => {
    const currentPreferences = new UserPreferencesModel(state.userPreferences)
    const isFavorite = currentPreferences.toJSON().favoriteItems?.includes(itemKey)
    
    if (isFavorite) {
      currentPreferences.removeFromFavorites(itemKey)
    } else {
      currentPreferences.addToFavorites(itemKey)
    }
    
    await actions.updatePreferences(currentPreferences.toJSON())
  }, [state.userPreferences, actions])

  // Get filtered sections based on permissions and preferences
  const getFilteredSections = useCallback((sections: SidebarSection[]): SidebarSection[] => {
    const preferences = new UserPreferencesModel(state.userPreferences)
    
    return sections.map(section => {
      const sectionModel = new SidebarSectionModel(section)
      
      // Check section permissions
      if (!sectionModel.hasPermission(userPermissions)) {
        return null
      }
      
      // Get visible items
      const visibleItems = sectionModel.getVisibleItems(userPermissions)
        .filter(item => !preferences.isItemHidden(item.key))
        .map(item => item.toJSON())
      
      return {
        ...section,
        items: visibleItems
      }
    }).filter((section): section is SidebarSection => 
      section !== null && section.items.length > 0
    )
  }, [userPermissions, state.userPreferences])

  // Get notification summary
  const getNotificationSummary = useCallback(() => {
    const counts = new NotificationCountsModel(state.notificationCounts)
    
    return {
      total: counts.getTotalCount(),
      critical: counts.hasCriticalNotifications(),
      unread: counts.hasUnreadNotifications(),
      byCategory: counts.toJSON().byCategory || {}
    }
  }, [state.notificationCounts])

  // Get user preferences with helper methods
  const getUserPreferences = useCallback(() => {
    return new UserPreferencesModel(state.userPreferences)
  }, [state.userPreferences])

  // Get analytics data
  const getAnalyticsData = useCallback(() => {
    return {
      mostClicked: analytics.getMostClickedItems(5),
      recentSearches: analytics.getMostSearchedQueries(5),
      recentlyAccessed: analytics.getRecentlyAccessedItems(5)
    }
  }, [analytics])

  // Bulk operations
  const bulkUpdatePreferences = useCallback(async (updates: Partial<UserPreferences>) => {
    await actions.updatePreferences(updates)
    
    actions.logAnalyticsEvent(SIDEBAR_EVENTS.PREFERENCES_CHANGED, {
      updates,
      timestamp: new Date().toISOString()
    })
  }, [actions])

  // Reset to defaults
  const resetToDefaults = useCallback(async () => {
    const defaultPrefs = new UserPreferencesModel()
    await actions.updatePreferences(defaultPrefs.toJSON())
    
    actions.logAnalyticsEvent('preferences_reset', {
      timestamp: new Date().toISOString()
    })
  }, [actions])

  return {
    // State
    collapsed: state.collapsed,
    loading: state.loading,
    error: state.error,
    searchTerm: state.searchTerm,
    searchResults,
    userPermissions,
    
    // Data
    userPreferences: getUserPreferences(),
    notificationCounts: state.notificationCounts,
    notificationSummary: getNotificationSummary(),
    analyticsData: getAnalyticsData(),
    
    // Actions
    toggleCollapse: actions.toggleCollapse,
    updateSearch: actions.updateSearch,
    performSearch,
    navigateToItem,
    toggleSection,
    toggleFavorite,
    bulkUpdatePreferences,
    resetToDefaults,
    
    // Utilities
    hasPermission,
    getFilteredSections,
    getCurrentActiveItem,
    
    // Raw actions for advanced usage
    actions
  }
}

/**
 * Hook for sidebar section management
 */
export const useSidebarSections = (sections: SidebarSection[], userId: string = 'default-user') => {
  const { getFilteredSections, toggleSection, userPreferences, hasPermission } = useSidebar(userId)
  
  const filteredSections = useMemo(() => 
    getFilteredSections(sections), 
    [sections, getFilteredSections]
  )
  
  const sectionModels = useMemo(() => 
    filteredSections.map(section => new SidebarSectionModel(section)),
    [filteredSections]
  )
  
  return {
    sections: filteredSections,
    sectionModels,
    toggleSection,
    isCollapsed: (sectionId: string) => userPreferences.isSectionCollapsed(sectionId),
    hasPermission
  }
}

/**
 * Hook for sidebar item management
 */
export const useSidebarItems = (items: SidebarItem[], userId: string = 'default-user') => {
  const { navigateToItem, toggleFavorite, userPreferences, hasPermission } = useSidebar(userId)
  
  const itemModels = useMemo(() => 
    items.map(item => new SidebarItemModel(item)),
    [items]
  )
  
  const visibleItems = useMemo(() => 
    itemModels.filter(item => hasPermission(item.toJSON().permissions?.[0] || '')),
    [itemModels, hasPermission]
  )
  
  return {
    items: visibleItems.map(item => item.toJSON()),
    itemModels: visibleItems,
    navigateToItem,
    toggleFavorite,
    isFavorite: (itemKey: string) => userPreferences.toJSON().favoriteItems?.includes(itemKey) || false,
    isHidden: (itemKey: string) => userPreferences.isItemHidden(itemKey),
    hasPermission
  }
}

/**
 * Hook for sidebar search functionality
 */
export const useSidebarSearch = (userId: string = 'default-user') => {
  const { 
    searchTerm, 
    searchResults, 
    performSearch, 
    updateSearch,
    userPreferences 
  } = useSidebar(userId)
  
  const searchHistory = userPreferences.toJSON().searchHistory || []
  
  const clearSearch = useCallback(() => {
    updateSearch('')
  }, [updateSearch])
  
  const searchWithFilters = useCallback((query: string, filters: FilterOptions) => {
    return performSearch(query, filters)
  }, [performSearch])
  
  return {
    searchTerm,
    searchResults,
    searchHistory,
    performSearch,
    searchWithFilters,
    updateSearch,
    clearSearch
  }
}

/**
 * Hook for sidebar notifications
 */
export const useSidebarNotifications = (userId: string = 'default-user') => {
  const { 
    notificationCounts, 
    notificationSummary, 
    actions 
  } = useSidebar(userId)
  
  return {
    counts: notificationCounts,
    summary: notificationSummary,
    refresh: actions.refreshNotifications,
    hasUnread: notificationSummary.unread,
    hasCritical: notificationSummary.critical,
    totalCount: notificationSummary.total
  }
}

/**
 * Hook for sidebar analytics
 */
export const useSidebarAnalytics = (userId: string = 'default-user') => {
  const { analyticsData, actions } = useSidebar(userId)
  
  const logEvent = useCallback((event: string, data: any) => {
    actions.logAnalyticsEvent(event, data)
  }, [actions])
  
  return {
    data: analyticsData,
    logEvent,
    mostClicked: analyticsData.mostClicked,
    recentSearches: analyticsData.recentSearches,
    recentlyAccessed: analyticsData.recentlyAccessed
  }
}

export default useSidebar