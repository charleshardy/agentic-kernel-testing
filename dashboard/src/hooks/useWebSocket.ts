/**
 * WebSocket Hook for Real-time Environment Updates
 * Provides WebSocket connection management with automatic reconnection
 */

import { useCallback, useEffect, useRef, useState } from 'react'

export interface WebSocketMessage {
  type: string
  data?: any
  environment_id?: string
  timestamp?: string
}

export interface UseWebSocketOptions {
  url?: string
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectInterval?: number
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

export interface UseWebSocketReturn {
  isConnected: boolean
  isConnecting: boolean
  connectionAttempts: number
  lastError: string | null
  sendMessage: (message: any) => void
  reconnect: () => void
  disconnect: () => void
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/environments/allocation`,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  const [lastError, setLastError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const optionsRef = useRef(options)

  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING || 
        wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setIsConnecting(true)
    setLastError(null)

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('🔌 WebSocket connected to:', url)
        setIsConnected(true)
        setIsConnecting(false)
        setConnectionAttempts(0)
        setLastError(null)
        optionsRef.current.onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('📨 WebSocket message received:', message)
          optionsRef.current.onMessage?.(message)
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error)
          const errorMsg = 'Failed to parse WebSocket message'
          setLastError(errorMsg)
          optionsRef.current.onError?.(errorMsg)
        }
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        setIsConnecting(false)
        wsRef.current = null
        optionsRef.current.onDisconnect?.()

        // Attempt reconnection if enabled and not a clean close
        if (autoReconnect && event.code !== 1000 && connectionAttempts < maxReconnectAttempts) {
          const nextAttempt = connectionAttempts + 1
          setConnectionAttempts(nextAttempt)
          
          console.log(`🔄 Attempting WebSocket reconnection ${nextAttempt}/${maxReconnectAttempts} in ${reconnectInterval}ms`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (connectionAttempts >= maxReconnectAttempts) {
          const errorMsg = `WebSocket reconnection failed after ${maxReconnectAttempts} attempts`
          setLastError(errorMsg)
          optionsRef.current.onError?.(errorMsg)
        }
      }

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event)
        const errorMsg = 'WebSocket connection error'
        setLastError(errorMsg)
        optionsRef.current.onError?.(errorMsg)
      }

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error)
      setIsConnecting(false)
      const errorMsg = `Failed to create WebSocket connection: ${error}`
      setLastError(errorMsg)
      optionsRef.current.onError?.(errorMsg)
    }
  }, [url, autoReconnect, maxReconnectAttempts, reconnectInterval, connectionAttempts])

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message)
        wsRef.current.send(messageStr)
        console.log('📤 WebSocket message sent:', message)
      } catch (error) {
        console.error('❌ Failed to send WebSocket message:', error)
        const errorMsg = `Failed to send WebSocket message: ${error}`
        setLastError(errorMsg)
        optionsRef.current.onError?.(errorMsg)
      }
    } else {
      console.warn('⚠️ Cannot send message: WebSocket not connected')
      const errorMsg = 'Cannot send message: WebSocket not connected'
      setLastError(errorMsg)
      optionsRef.current.onError?.(errorMsg)
    }
  }, [])

  // Manual reconnection
  const reconnect = useCallback(() => {
    console.log('🔄 Manual WebSocket reconnection requested')
    
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual reconnection')
    }

    // Reset connection attempts for manual reconnection
    setConnectionAttempts(0)
    
    // Connect after a short delay
    setTimeout(() => {
      connect()
    }, 100)
  }, [connect])

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    console.log('🔌 WebSocket disconnect requested')
    
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
    }

    setIsConnected(false)
    setIsConnecting(false)
    setConnectionAttempts(0)
    wsRef.current = null
  }, [])

  // Initial connection
  useEffect(() => {
    connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount')
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
    sendMessage,
    reconnect,
    disconnect
  }
}

export default useWebSocket