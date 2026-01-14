// Sidebar Context Provider

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import {
  SidebarState,
  SidebarAction,
  UserPreferences,
  NotificationCounts,
  FilterOptions,
  DEFAULT_USER_PREFERENCES,
  DEFAULT_NOTIFICATION_COUNTS
} from '../types/sidebar'
import { sidebarService, notificationService, permissionService } from '../services/SidebarService'

// Initial state
const initialState: SidebarState = {
  collapsed: false,
  activeSection: null,
  activeItem: null,
  searchTerm: '',
  filterOptions: {},
  userPreferences: DEFAULT_USER_PREFERENCES,
  notificationCounts: DEFAULT_NOTIFICATION_COUNTS,
  loading: false,
  error: null
}

// Reducer function
function sidebarReducer(state: SidebarState, action: SidebarAction): SidebarState {
  switch (action.type) {
    case 'TOGGLE_COLLAPSE':
      return {
        ...state,
        collapsed: !state.collapsed
      }

    case 'SET_ACTIVE_SECTION':
      return {
        ...state,
        activeSection: action.payload
      }

    case 'SET_ACTIVE_ITEM':
      return {
        ...state,
        activeItem: action.payload
      }

    case 'UPDATE_SEARCH':
      return {
        ...state,
        searchTerm: action.payload
      }

    case 'UPDATE_FILTERS':
      return {
        ...state,
        filterOptions: { ...state.filterOptions, ...action.payload }
      }

    case 'UPDATE_PREFERENCES':
      return {
        ...state,
        userPreferences: { ...state.userPreferences, ...action.payload }
      }

    case 'UPDATE_NOTIFICATIONS':
      return {
        ...state,
        notificationCounts: { ...state.notificationCounts, ...action.payload }
      }

    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload
      }

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false
      }

    case 'RESET':
      return initialState

    default:
      return state
  }
}

// Context type
interface SidebarContextType {
  state: SidebarState
  dispatch: React.Dispatch<SidebarAction>
  actions: {
    toggleCollapse: () => void
    setActiveSection: (sectionId: string | null) => void
    setActiveItem: (itemKey: string | null) => void
    updateSearch: (searchTerm: string) => void
    updateFilters: (filters: Partial<FilterOptions>) => void
    updatePreferences: (preferences: Partial<UserPreferences>) => Promise<void>
    refreshNotifications: () => Promise<void>
    loadUserData: (userId: string) => Promise<void>
    logAnalyticsEvent: (event: string, data: any) => Promise<void>
  }
}

// Create context
const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

// Provider props
interface SidebarProviderProps {
  children: ReactNode
  userId?: string
}

// Provider component
export const SidebarProvider: React.FC<SidebarProviderProps> = ({ 
  children, 
  userId = 'default-user' 
}) => {
  const [state, dispatch] = useReducer(sidebarReducer, initialState)

  // Action creators
  const actions = {
    toggleCollapse: () => {
      dispatch({ type: 'TOGGLE_COLLAPSE' })
    },

    setActiveSection: (sectionId: string | null) => {
      dispatch({ type: 'SET_ACTIVE_SECTION', payload: sectionId })
    },

    setActiveItem: (itemKey: string | null) => {
      dispatch({ type: 'SET_ACTIVE_ITEM', payload: itemKey })
    },

    updateSearch: (searchTerm: string) => {
      dispatch({ type: 'UPDATE_SEARCH', payload: searchTerm })
      
      // Log search analytics
      if (searchTerm) {
        actions.logAnalyticsEvent('search_performed', { query: searchTerm })
      }
    },

    updateFilters: (filters: Partial<FilterOptions>) => {
      dispatch({ type: 'UPDATE_FILTERS', payload: filters })
    },

    updatePreferences: async (preferences: Partial<UserPreferences>) => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true })
        
        await sidebarService.updateUserPreferences(userId, preferences)
        dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences })
        
        // Log preferences change
        await actions.logAnalyticsEvent('preferences_changed', preferences)
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to update preferences' })
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    },

    refreshNotifications: async () => {
      try {
        const notificationCounts = await sidebarService.getNotificationCounts(userId)
        dispatch({ type: 'UPDATE_NOTIFICATIONS', payload: notificationCounts })
      } catch (error) {
        console.error('Failed to refresh notifications:', error)
        dispatch({ type: 'SET_ERROR', payload: 'Failed to refresh notifications' })
      }
    },

    loadUserData: async (userId: string) => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true })
        dispatch({ type: 'SET_ERROR', payload: null })

        // Load user preferences
        const preferences = await sidebarService.getUserPreferences(userId)
        dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences })

        // Load notification counts
        const notificationCounts = await sidebarService.getNotificationCounts(userId)
        dispatch({ type: 'UPDATE_NOTIFICATIONS', payload: notificationCounts })

        // Set initial collapsed state from preferences
        if (preferences.customization?.autoCollapse) {
          dispatch({ type: 'TOGGLE_COLLAPSE' })
        }

      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to load user data' })
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    },

    logAnalyticsEvent: async (event: string, data: any) => {
      try {
        await sidebarService.logAnalyticsEvent(userId, event, data)
      } catch (error) {
        console.error('Failed to log analytics event:', error)
      }
    }
  }

  // Load initial data when userId changes
  useEffect(() => {
    if (userId) {
      actions.loadUserData(userId)
    }
  }, [userId])

  // Subscribe to notification updates
  useEffect(() => {
    const unsubscribe = notificationService.subscribe(userId, (counts) => {
      dispatch({ type: 'UPDATE_NOTIFICATIONS', payload: counts })
    })

    return unsubscribe
  }, [userId])

  // Auto-refresh notifications every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      actions.refreshNotifications()
    }, 30000)

    return () => clearInterval(interval)
  }, [userId])

  // Save preferences to localStorage when they change
  useEffect(() => {
    if (state.userPreferences !== DEFAULT_USER_PREFERENCES) {
      localStorage.setItem(`sidebar-preferences-${userId}`, JSON.stringify(state.userPreferences))
    }
  }, [state.userPreferences, userId])

  const contextValue: SidebarContextType = {
    state,
    dispatch,
    actions
  }

  return (
    <SidebarContext.Provider value={contextValue}>
      {children}
    </SidebarContext.Provider>
  )
}

// Hook to use sidebar context
export const useSidebarContext = (): SidebarContextType => {
  const context = useContext(SidebarContext)
  if (context === undefined) {
    throw new Error('useSidebarContext must be used within a SidebarProvider')
  }
  return context
}

// Hook for sidebar state only
export const useSidebarState = () => {
  const { state } = useSidebarContext()
  return state
}

// Hook for sidebar actions only
export const useSidebarActions = () => {
  const { actions } = useSidebarContext()
  return actions
}

// Hook for specific sidebar data
export const useSidebarData = () => {
  const { state } = useSidebarContext()
  return {
    collapsed: state.collapsed,
    searchTerm: state.searchTerm,
    userPreferences: state.userPreferences,
    notificationCounts: state.notificationCounts,
    loading: state.loading,
    error: state.error
  }
}

// Hook for notification counts with real-time updates
export const useNotificationCounts = () => {
  const { state, actions } = useSidebarContext()
  
  return {
    counts: state.notificationCounts,
    refresh: actions.refreshNotifications,
    loading: state.loading
  }
}

// Hook for user preferences with update functionality
export const useUserPreferences = () => {
  const { state, actions } = useSidebarContext()
  
  return {
    preferences: state.userPreferences,
    updatePreferences: actions.updatePreferences,
    loading: state.loading
  }
}

// Hook for search functionality
export const useSidebarSearch = () => {
  const { state, actions } = useSidebarContext()
  
  return {
    searchTerm: state.searchTerm,
    updateSearch: actions.updateSearch,
    filters: state.filterOptions,
    updateFilters: actions.updateFilters
  }
}

export default SidebarContext