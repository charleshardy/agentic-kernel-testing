import { io, Socket } from 'socket.io-client'

export interface WebSocketEvent {
  type: 'test_status_update' | 'execution_complete' | 'system_metrics' | 'coverage_update' | 'performance_update'
  data: any
  timestamp: string
}

export type EventHandler = (event: WebSocketEvent) => void

class WebSocketService {
  private socket: Socket | null = null
  private eventHandlers: Map<string, EventHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(): void {
    if (this.socket?.connected) {
      return
    }

    const token = localStorage.getItem('auth_token')
    
    this.socket = io('ws://localhost:8000', {
      auth: {
        token: token
      },
      transports: ['websocket'],
      upgrade: true,
      rememberUpgrade: true
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      
      // Subscribe to all relevant events
      this.socket?.emit('subscribe', {
        events: ['test_status_update', 'execution_complete', 'system_metrics', 'coverage_update', 'performance_update']
      })
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect automatically
        return
      }
      
      // Attempt to reconnect
      this.attemptReconnect()
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.attemptReconnect()
    })

    // Handle incoming events
    this.socket.on('test_status_update', (data) => {
      this.handleEvent({
        type: 'test_status_update',
        data,
        timestamp: new Date().toISOString()
      })
    })

    this.socket.on('execution_complete', (data) => {
      this.handleEvent({
        type: 'execution_complete',
        data,
        timestamp: new Date().toISOString()
      })
    })

    this.socket.on('system_metrics', (data) => {
      this.handleEvent({
        type: 'system_metrics',
        data,
        timestamp: new Date().toISOString()
      })
    })

    this.socket.on('coverage_update', (data) => {
      this.handleEvent({
        type: 'coverage_update',
        data,
        timestamp: new Date().toISOString()
      })
    })

    this.socket.on('performance_update', (data) => {
      this.handleEvent({
        type: 'performance_update',
        data,
        timestamp: new Date().toISOString()
      })
    })
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.eventHandlers.clear()
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      this.connect()
    }, delay)
  }

  private handleEvent(event: WebSocketEvent): void {
    const handlers = this.eventHandlers.get(event.type) || []
    handlers.forEach(handler => {
      try {
        handler(event)
      } catch (error) {
        console.error('Error handling WebSocket event:', error)
      }
    })
  }

  subscribe(eventType: string, handler: EventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, [])
    }
    
    this.eventHandlers.get(eventType)!.push(handler)
    
    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  // Emit events to server
  emit(eventType: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(eventType, data)
    }
  }
}

export const webSocketService = new WebSocketService()
export default webSocketService