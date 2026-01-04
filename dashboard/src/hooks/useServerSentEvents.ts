/**
 * Server-Sent Events Hook for Real-time Environment Updates
 * Provides SSE connection management with automatic reconnection
 */

import { useCallback, useEffect, useRef, useState } from 'react'

export interface SSEMessage {
  type: string
  data?: any
  id?: string
  timestamp?: string
}

export interface UseServerSentEventsOptions {
  url?: string
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectInterval?: number
  onMessage?: (message: SSEMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

export interface UseServerSentEventsReturn {
  isConnected: boolean
  isConnecting: boolean
  connectionAttempts: number
  lastError: string | null
  reconnect: () => void
  disconnect: () => void
}

export const useServerSentEvents = (options: UseServerSentEventsOptions = {}): UseServerSentEventsReturn => {
  const {
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  // Build URL with authentication token
  const token = localStorage.getItem('auth_token')
  const url = `http://localhost:8000/api/v1/environments/allocation/events${token ? `?token=${token}` : ''}`

  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const optionsRef = useRef(options)

  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  // Connect to Server-Sent Events
  const connect = useCallback(() => {
    // Don't connect if URL indicates disabled
    if (url.startsWith('disabled://')) {
      console.log('📡 SSE connection disabled')
      return
    }
    
    if (eventSourceRef.current?.readyState === EventSource.CONNECTING || 
        eventSourceRef.current?.readyState === EventSource.OPEN) {
      return
    }

    setIsConnecting(true)
    setLastError(null)

    try {
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        console.log('📡 SSE connected to:', url)
        setIsConnected(true)
        setIsConnecting(false)
        setConnectionAttempts(0)
        setLastError(null)
        optionsRef.current.onConnect?.()
      }

      eventSource.onmessage = (event) => {
        try {
          const message: SSEMessage = {
            type: 'message',
            data: JSON.parse(event.data),
            id: event.lastEventId,
            timestamp: new Date().toISOString()
          }
          console.log('📨 SSE message received:', message)
          optionsRef.current.onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse SSE message:', error)
          const errorMsg = 'Failed to parse SSE message'
          setLastError(errorMsg)
          optionsRef.current.onError?.(errorMsg)
        }
      }

      eventSource.onerror = (event) => {
        console.error('❌ SSE error:', event)
        setIsConnected(false)
        setIsConnecting(false)
        
        const errorMsg = 'SSE connection error'
        setLastError(errorMsg)
        optionsRef.current.onError?.(errorMsg)
        optionsRef.current.onDisconnect?.()

        // Attempt reconnection if enabled
        if (autoReconnect && connectionAttempts < maxReconnectAttempts) {
          const nextAttempt = connectionAttempts + 1
          setConnectionAttempts(nextAttempt)
          
          console.log(`🔄 Attempting SSE reconnection ${nextAttempt}/${maxReconnectAttempts} in ${reconnectInterval}ms`)
          
          // Close current connection before reconnecting
          if (eventSourceRef.current) {
            eventSourceRef.current.close()
            eventSourceRef.current = null
          }
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (connectionAttempts >= maxReconnectAttempts) {
          const maxAttemptsErrorMsg = `SSE reconnection failed after ${maxReconnectAttempts} attempts`
          setLastError(maxAttemptsErrorMsg)
          optionsRef.current.onError?.(maxAttemptsErrorMsg)
        }
      }

      // Listen for specific event types
      eventSource.addEventListener('connected', (event) => {
        const message: SSEMessage = {
          type: 'connected',
          data: event.data ? JSON.parse(event.data) : null,
          id: event.lastEventId,
          timestamp: new Date().toISOString()
        }
        optionsRef.current.onMessage?.(message)
      })

      eventSource.addEventListener('environment_update', (event) => {
        try {
          const message: SSEMessage = {
            type: 'environment_update',
            data: JSON.parse(event.data),
            id: event.lastEventId,
            timestamp: new Date().toISOString()
          }
          optionsRef.current.onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse environment_update SSE message:', error)
        }
      })

      eventSource.addEventListener('allocation_event', (event) => {
        try {
          const message: SSEMessage = {
            type: 'allocation_event',
            data: JSON.parse(event.data),
            id: event.lastEventId,
            timestamp: new Date().toISOString()
          }
          optionsRef.current.onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse allocation_event SSE message:', error)
        }
      })

      eventSource.addEventListener('queue_status', (event) => {
        try {
          const message: SSEMessage = {
            type: 'queue_status',
            data: JSON.parse(event.data),
            id: event.lastEventId,
            timestamp: new Date().toISOString()
          }
          optionsRef.current.onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse queue_status SSE message:', error)
        }
      })

    } catch (error) {
      console.error('❌ Failed to create SSE connection:', error)
      setIsConnecting(false)
      const errorMsg = `Failed to create SSE connection: ${error}`
      setLastError(errorMsg)
      optionsRef.current.onError?.(errorMsg)
    }
  }, [url, autoReconnect, maxReconnectAttempts, reconnectInterval, connectionAttempts])

  // Manual reconnection
  const reconnect = useCallback(() => {
    console.log('🔄 Manual SSE reconnection requested')
    
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    // Reset connection attempts for manual reconnection
    setConnectionAttempts(0)
    
    // Connect after a short delay
    setTimeout(() => {
      connect()
    }, 100)
  }, [connect])

  // Disconnect SSE
  const disconnect = useCallback(() => {
    console.log('📡 SSE disconnect requested')
    
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setIsConnected(false)
    setIsConnecting(false)
    setConnectionAttempts(0)
  }, [])

  // Initial connection
  useEffect(() => {
    connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [connect])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    isConnected,
    isConnecting,
    connectionAttempts,
    lastError,
    reconnect,
    disconnect
  }
}

export default useServerSentEvents