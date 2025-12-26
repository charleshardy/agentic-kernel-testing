/**
 * Custom hook for managing Server-Sent Events (SSE) connections
 * Provides real-time allocation event streaming
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import apiService from '../services/api'

export interface SSEMessage {
  type: string
  data: any
  timestamp: string
}

export interface SSEConnectionState {
  isConnected: boolean
  isConnecting: boolean
  lastMessage: SSEMessage | null
  connectionAttempts: number
  lastError: string | null
}

export interface UseSSEOptions {
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectInterval?: number
  onMessage?: (message: SSEMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

export const useServerSentEvents = (options: UseSSEOptions = {}) => {
  const {
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  const [connectionState, setConnectionState] = useState<SSEConnectionState>({
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    connectionAttempts: 0,
    lastError: null
  })

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isManuallyClosedRef = useRef(false)

  const connect = useCallback(() => {
    if (eventSourceRef.current?.readyState === EventSource.OPEN) {
      return // Already connected
    }

    setConnectionState(prev => ({
      ...prev,
      isConnecting: true,
      lastError: null
    }))

    try {
      const eventSource = apiService.createAllocationEventStream()
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        console.log('📡 SSE connected')
        setConnectionState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          connectionAttempts: 0,
          lastError: null
        }))
        onConnect?.()
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const message: SSEMessage = {
            type: data.type || 'message',
            data: data,
            timestamp: data.timestamp || new Date().toISOString()
          }
          
          console.log('📨 SSE message received:', message)
          
          setConnectionState(prev => ({
            ...prev,
            lastMessage: message
          }))
          
          onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse SSE message:', error)
        }
      }

      eventSource.onerror = (error) => {
        console.error('❌ SSE error:', error)
        
        setConnectionState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false
        }))
        
        onDisconnect?.()

        // Attempt reconnection if not manually closed and auto-reconnect is enabled
        if (!isManuallyClosedRef.current && autoReconnect) {
          setConnectionState(prev => {
            const newAttempts = prev.connectionAttempts + 1
            
            if (newAttempts <= maxReconnectAttempts) {
              console.log(`🔄 Attempting to reconnect SSE (${newAttempts}/${maxReconnectAttempts})...`)
              
              reconnectTimeoutRef.current = setTimeout(() => {
                connect()
              }, reconnectInterval)
              
              return {
                ...prev,
                connectionAttempts: newAttempts
              }
            } else {
              const errorMsg = `Max SSE reconnection attempts (${maxReconnectAttempts}) reached`
              console.error('❌', errorMsg)
              onError?.(errorMsg)
              
              return {
                ...prev,
                lastError: errorMsg
              }
            }
          })
        }
      }

    } catch (error) {
      console.error('❌ Failed to create SSE connection:', error)
      const errorMsg = `Failed to create SSE: ${error}`
      
      setConnectionState(prev => ({
        ...prev,
        isConnecting: false,
        lastError: errorMsg
      }))
      
      onError?.(errorMsg)
    }
  }, [autoReconnect, maxReconnectAttempts, reconnectInterval, onMessage, onConnect, onDisconnect, onError])

  const disconnect = useCallback(() => {
    isManuallyClosedRef.current = true
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setConnectionState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      connectionAttempts: 0
    }))
  }, [])

  const reconnect = useCallback(() => {
    disconnect()
    isManuallyClosedRef.current = false
    
    // Reset connection attempts for manual reconnect
    setConnectionState(prev => ({
      ...prev,
      connectionAttempts: 0,
      lastError: null
    }))
    
    setTimeout(connect, 100)
  }, [connect, disconnect])

  // Initialize connection on mount
  useEffect(() => {
    isManuallyClosedRef.current = false
    connect()

    // Cleanup on unmount
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    ...connectionState,
    connect,
    disconnect,
    reconnect
  }
}

export default useServerSentEvents