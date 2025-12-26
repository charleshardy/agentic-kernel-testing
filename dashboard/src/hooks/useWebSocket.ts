/**
 * Custom hook for managing WebSocket connections with automatic reconnection
 * Provides real-time updates for environment allocation status
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import apiService from '../services/api'

export interface WebSocketMessage {
  type: string
  timestamp: string
  data?: any
  environment_id?: string
  request_id?: string
}

export interface WebSocketConnectionState {
  isConnected: boolean
  isConnecting: boolean
  lastMessage: WebSocketMessage | null
  connectionAttempts: number
  lastError: string | null
}

export interface UseWebSocketOptions {
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectInterval?: number
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  const [connectionState, setConnectionState] = useState<WebSocketConnectionState>({
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    connectionAttempts: 0,
    lastError: null
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isManuallyClosedRef = useRef(false)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    setConnectionState(prev => ({
      ...prev,
      isConnecting: true,
      lastError: null
    }))

    try {
      const ws = apiService.createEnvironmentWebSocket()
      wsRef.current = ws

      ws.onopen = () => {
        console.log('🔗 WebSocket connected')
        setConnectionState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          connectionAttempts: 0,
          lastError: null
        }))
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('📨 WebSocket message received:', message)
          
          setConnectionState(prev => ({
            ...prev,
            lastMessage: message
          }))
          
          onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        
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
              console.log(`🔄 Attempting to reconnect (${newAttempts}/${maxReconnectAttempts})...`)
              
              reconnectTimeoutRef.current = setTimeout(() => {
                connect()
              }, reconnectInterval)
              
              return {
                ...prev,
                connectionAttempts: newAttempts
              }
            } else {
              const errorMsg = `Max reconnection attempts (${maxReconnectAttempts}) reached`
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

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        const errorMsg = 'WebSocket connection error'
        
        setConnectionState(prev => ({
          ...prev,
          isConnecting: false,
          lastError: errorMsg
        }))
        
        onError?.(errorMsg)
      }

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error)
      const errorMsg = `Failed to create WebSocket: ${error}`
      
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

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setConnectionState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      connectionAttempts: 0
    }))
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    } else {
      console.warn('⚠️ Cannot send message: WebSocket not connected')
      return false
    }
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
    reconnect,
    sendMessage
  }
}

export default useWebSocket