/**
 * Comprehensive hook for managing real-time environment allocation updates
 * Combines WebSocket and Server-Sent Events for robust real-time functionality
 */

import { useCallback, useEffect, useState } from 'react'
import { useQueryClient } from 'react-query'
import useWebSocket, { WebSocketMessage } from './useWebSocket'
import useServerSentEvents, { SSEMessage } from './useServerSentEvents'
import { Environment, AllocationRequest, AllocationEvent } from '../types/environment'

export interface RealTimeUpdateState {
  isConnected: boolean
  connectionHealth: 'healthy' | 'degraded' | 'disconnected'
  lastUpdate: Date | null
  updateCount: number
  errors: string[]
}

export interface UseRealTimeUpdatesOptions {
  enableWebSocket?: boolean
  enableSSE?: boolean
  onEnvironmentUpdate?: (environment: Environment) => void
  onAllocationUpdate?: (request: AllocationRequest) => void
  onAllocationEvent?: (event: AllocationEvent) => void
  onConnectionHealthChange?: (health: 'healthy' | 'degraded' | 'disconnected') => void
}

export const useRealTimeUpdates = (options: UseRealTimeUpdatesOptions = {}) => {
  const {
    enableWebSocket = true,
    enableSSE = true,
    onEnvironmentUpdate,
    onAllocationUpdate,
    onAllocationEvent,
    onConnectionHealthChange
  } = options

  const queryClient = useQueryClient()
  
  const [state, setState] = useState<RealTimeUpdateState>({
    isConnected: false,
    connectionHealth: 'disconnected',
    lastUpdate: null,
    updateCount: 0,
    errors: []
  })

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log('🔄 Processing WebSocket message:', message)
    
    setState(prev => ({
      ...prev,
      lastUpdate: new Date(),
      updateCount: prev.updateCount + 1
    }))

    switch (message.type) {
      case 'environment_status_changed':
      case 'environment_update':
        if (message.data?.environment) {
          onEnvironmentUpdate?.(message.data.environment)
          
          // Invalidate and refetch environment data
          queryClient.invalidateQueries(['environmentAllocation'])
        }
        break

      case 'allocation_status':
      case 'allocation_queued':
      case 'allocation_allocated':
      case 'allocation_cancelled':
        if (message.data) {
          onAllocationUpdate?.(message.data)
          
          // Invalidate allocation queue data
          queryClient.invalidateQueries(['environmentAllocation'])
        }
        break

      case 'resource_update':
        if (message.environment_id) {
          // Update specific environment resource data
          queryClient.setQueryData(['environmentAllocation'], (oldData: any) => {
            if (!oldData?.environments) return oldData
            
            return {
              ...oldData,
              environments: oldData.environments.map((env: Environment) =>
                env.id === message.environment_id
                  ? { ...env, resources: { ...env.resources, ...message.data?.resource_usage } }
                  : env
              )
            }
          })
        }
        break

      default:
        console.log('📝 Unhandled WebSocket message type:', message.type)
    }
  }, [queryClient, onEnvironmentUpdate, onAllocationUpdate])

  // Handle SSE messages
  const handleSSEMessage = useCallback((message: SSEMessage) => {
    console.log('🔄 Processing SSE message:', message)
    
    setState(prev => ({
      ...prev,
      lastUpdate: new Date(),
      updateCount: prev.updateCount + 1
    }))

    switch (message.type) {
      case 'connected':
        console.log('✅ SSE connection established')
        break

      case 'queue_status':
        // Update queue status without full refetch
        if (message.data) {
          queryClient.setQueryData(['environmentAllocation'], (oldData: any) => {
            if (!oldData) return oldData
            
            return {
              ...oldData,
              metrics: {
                ...oldData.metrics,
                queueLength: message.data.queue_length,
                utilizationRate: message.data.busy_environments / message.data.total_environments
              }
            }
          })
        }
        break

      case 'allocation_event':
        if (message.data) {
          onAllocationEvent?.(message.data)
          
          // Add to allocation history
          queryClient.setQueryData(['environmentAllocation'], (oldData: any) => {
            if (!oldData?.history) return oldData
            
            return {
              ...oldData,
              history: [message.data, ...oldData.history.slice(0, 19)] // Keep last 20 events
            }
          })
        }
        break

      default:
        console.log('📝 Unhandled SSE message type:', message.type)
    }
  }, [queryClient, onAllocationEvent])

  // WebSocket connection
  const webSocket = useWebSocket({
    autoReconnect: true,
    maxReconnectAttempts: 5,
    reconnectInterval: 3000,
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('✅ WebSocket connected')
      updateConnectionHealth()
    },
    onDisconnect: () => {
      console.log('❌ WebSocket disconnected')
      updateConnectionHealth()
    },
    onError: (error) => {
      console.error('❌ WebSocket error:', error)
      setState(prev => ({
        ...prev,
        errors: [...prev.errors.slice(-4), error] // Keep last 5 errors
      }))
      updateConnectionHealth()
    }
  })

  // Server-Sent Events connection
  const sse = useServerSentEvents({
    autoReconnect: true,
    maxReconnectAttempts: 5,
    reconnectInterval: 3000,
    onMessage: handleSSEMessage,
    onConnect: () => {
      console.log('✅ SSE connected')
      updateConnectionHealth()
    },
    onDisconnect: () => {
      console.log('❌ SSE disconnected')
      updateConnectionHealth()
    },
    onError: (error) => {
      console.error('❌ SSE error:', error)
      setState(prev => ({
        ...prev,
        errors: [...prev.errors.slice(-4), error] // Keep last 5 errors
      }))
      updateConnectionHealth()
    }
  })

  // Update connection health based on WebSocket and SSE status
  const updateConnectionHealth = useCallback(() => {
    const wsConnected = enableWebSocket ? webSocket.isConnected : true
    const sseConnected = enableSSE ? sse.isConnected : true
    
    let health: 'healthy' | 'degraded' | 'disconnected'
    let isConnected: boolean

    if (wsConnected && sseConnected) {
      health = 'healthy'
      isConnected = true
    } else if (wsConnected || sseConnected) {
      health = 'degraded'
      isConnected = true
    } else {
      health = 'disconnected'
      isConnected = false
    }

    setState(prev => {
      if (prev.connectionHealth !== health) {
        onConnectionHealthChange?.(health)
      }
      
      return {
        ...prev,
        isConnected,
        connectionHealth: health
      }
    })
  }, [enableWebSocket, enableSSE, webSocket.isConnected, sse.isConnected, onConnectionHealthChange])

  // Update connection health when connection states change
  useEffect(() => {
    updateConnectionHealth()
  }, [updateConnectionHealth])

  // Manual reconnection for both connections
  const reconnectAll = useCallback(() => {
    console.log('🔄 Manually reconnecting all real-time connections...')
    
    if (enableWebSocket) {
      webSocket.reconnect()
    }
    
    if (enableSSE) {
      sse.reconnect()
    }
    
    // Clear errors on manual reconnect
    setState(prev => ({
      ...prev,
      errors: []
    }))
  }, [enableWebSocket, enableSSE, webSocket.reconnect, sse.reconnect])

  // Disconnect all connections
  const disconnectAll = useCallback(() => {
    console.log('🔌 Disconnecting all real-time connections...')
    
    if (enableWebSocket) {
      webSocket.disconnect()
    }
    
    if (enableSSE) {
      sse.disconnect()
    }
  }, [enableWebSocket, enableSSE, webSocket.disconnect, sse.disconnect])

  return {
    // Connection state
    ...state,
    
    // Individual connection states
    webSocket: enableWebSocket ? {
      isConnected: webSocket.isConnected,
      isConnecting: webSocket.isConnecting,
      connectionAttempts: webSocket.connectionAttempts,
      lastError: webSocket.lastError
    } : null,
    
    sse: enableSSE ? {
      isConnected: sse.isConnected,
      isConnecting: sse.isConnecting,
      connectionAttempts: sse.connectionAttempts,
      lastError: sse.lastError
    } : null,
    
    // Control methods
    reconnectAll,
    disconnectAll,
    
    // Individual control methods
    reconnectWebSocket: enableWebSocket ? webSocket.reconnect : undefined,
    reconnectSSE: enableSSE ? sse.reconnect : undefined,
    sendWebSocketMessage: enableWebSocket ? webSocket.sendMessage : undefined
  }
}

export default useRealTimeUpdates