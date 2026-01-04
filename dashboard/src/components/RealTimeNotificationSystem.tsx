/**
 * Real-Time Notification System
 * Manages notifications for environment status changes and real-time events
 * with intelligent filtering and user preferences
 */

import React, { useEffect, useRef, useState } from 'react'
import { notification, Button, Space } from 'antd'
import { 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  BellOutlined,
  BellFilled,
  SettingOutlined
} from '@ant-design/icons'
import { Environment, AllocationEvent, EnvironmentStatus } from '../types/environment'

export interface NotificationPreferences {
  enableStatusChanges: boolean
  enableAllocationEvents: boolean
  enableConnectionEvents: boolean
  enableErrorNotifications: boolean
  soundEnabled: boolean
  maxNotificationsPerMinute: number
  importantStatusesOnly: boolean
  groupSimilarNotifications: boolean
}

export interface RealTimeNotificationSystemProps {
  preferences?: Partial<NotificationPreferences>
  onPreferencesChange?: (preferences: NotificationPreferences) => void
}

const defaultPreferences: NotificationPreferences = {
  enableStatusChanges: true,
  enableAllocationEvents: true,
  enableConnectionEvents: true,
  enableErrorNotifications: true,
  soundEnabled: false,
  maxNotificationsPerMinute: 10,
  importantStatusesOnly: true,
  groupSimilarNotifications: true
}

class NotificationManager {
  private static instance: NotificationManager
  private preferences: NotificationPreferences
  private notificationCount: number = 0
  private lastResetTime: number = Date.now()
  private groupedNotifications: Map<string, { count: number, lastTime: number }> = new Map()
  private soundContext: AudioContext | null = null

  private constructor(preferences: NotificationPreferences) {
    this.preferences = preferences
    this.initializeSound()
  }

  static getInstance(preferences?: NotificationPreferences): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager(preferences || defaultPreferences)
    } else if (preferences) {
      NotificationManager.instance.updatePreferences(preferences)
    }
    return NotificationManager.instance
  }

  updatePreferences(preferences: NotificationPreferences) {
    this.preferences = preferences
  }

  private initializeSound() {
    if (this.preferences.soundEnabled && typeof window !== 'undefined') {
      try {
        this.soundContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      } catch (error) {
        console.warn('Audio context not available:', error)
      }
    }
  }

  private playNotificationSound(type: 'success' | 'warning' | 'error' | 'info' = 'info') {
    if (!this.preferences.soundEnabled || !this.soundContext) return

    try {
      const oscillator = this.soundContext.createOscillator()
      const gainNode = this.soundContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(this.soundContext.destination)

      // Different frequencies for different notification types
      const frequencies = {
        success: 800,
        warning: 600,
        error: 400,
        info: 500
      }

      oscillator.frequency.setValueAtTime(frequencies[type], this.soundContext.currentTime)
      oscillator.type = 'sine'

      gainNode.gain.setValueAtTime(0.1, this.soundContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, this.soundContext.currentTime + 0.3)

      oscillator.start(this.soundContext.currentTime)
      oscillator.stop(this.soundContext.currentTime + 0.3)
    } catch (error) {
      console.warn('Failed to play notification sound:', error)
    }
  }

  private shouldShowNotification(): boolean {
    const now = Date.now()
    
    // Reset counter every minute
    if (now - this.lastResetTime > 60000) {
      this.notificationCount = 0
      this.lastResetTime = now
    }

    // Check rate limit
    if (this.notificationCount >= this.preferences.maxNotificationsPerMinute) {
      return false
    }

    this.notificationCount++
    return true
  }

  private getGroupKey(type: string, environmentId?: string): string {
    return `${type}-${environmentId || 'global'}`
  }

  private shouldGroupNotification(groupKey: string): boolean {
    if (!this.preferences.groupSimilarNotifications) return false

    const now = Date.now()
    const existing = this.groupedNotifications.get(groupKey)

    if (existing && now - existing.lastTime < 30000) { // Group within 30 seconds
      existing.count++
      existing.lastTime = now
      return true
    }

    this.groupedNotifications.set(groupKey, { count: 1, lastTime: now })
    return false
  }

  showEnvironmentStatusChange(
    environment: Environment, 
    previousStatus?: EnvironmentStatus,
    options?: { skipRateLimit?: boolean }
  ) {
    if (!this.preferences.enableStatusChanges) return
    if (!options?.skipRateLimit && !this.shouldShowNotification()) return

    const envIdShort = environment.id.slice(0, 8)
    const groupKey = this.getGroupKey('status-change', environment.id)

    // Check if this is an important status change
    const importantStatuses = [
      EnvironmentStatus.READY,
      EnvironmentStatus.ERROR,
      EnvironmentStatus.OFFLINE
    ]

    if (this.preferences.importantStatusesOnly && 
        !importantStatuses.includes(environment.status)) {
      return
    }

    // Check for grouping
    if (this.shouldGroupNotification(groupKey)) {
      const grouped = this.groupedNotifications.get(groupKey)!
      notification.info({
        key: groupKey,
        message: 'Multiple Environment Changes',
        description: `Environment ${envIdShort}... has changed status ${grouped.count} times`,
        duration: 3,
        placement: 'topRight'
      })
      return
    }

    let notificationType: 'success' | 'info' | 'warning' | 'error' = 'info'
    let message = 'Environment Status Changed'
    let description = `Environment ${envIdShort}... is now ${environment.status.toUpperCase()}`

    switch (environment.status) {
      case EnvironmentStatus.READY:
        notificationType = 'success'
        message = 'Environment Ready'
        description = `Environment ${envIdShort}... is ready for allocation`
        break
      case EnvironmentStatus.ERROR:
        notificationType = 'error'
        message = 'Environment Error'
        description = `Environment ${envIdShort}... has encountered an error`
        break
      case EnvironmentStatus.OFFLINE:
        notificationType = 'warning'
        message = 'Environment Offline'
        description = `Environment ${envIdShort}... has gone offline`
        break
      case EnvironmentStatus.RUNNING:
        notificationType = 'info'
        message = 'Environment Running'
        description = `Environment ${envIdShort}... is now running tests`
        break
    }

    if (previousStatus) {
      description += ` (was ${previousStatus.toUpperCase()})`
    }

    this.playNotificationSound(notificationType)

    notification[notificationType]({
      key: `env-${environment.id}-${environment.status}`,
      message,
      description,
      duration: notificationType === 'error' ? 6 : 4,
      placement: 'topRight',
      icon: this.getStatusIcon(environment.status)
    })
  }

  showAllocationEvent(event: AllocationEvent) {
    if (!this.preferences.enableAllocationEvents) return
    if (!this.shouldShowNotification()) return

    const envIdShort = event.environmentId.slice(0, 8)
    const testIdShort = event.testId?.slice(0, 8)

    let notificationType: 'success' | 'info' | 'warning' | 'error' = 'info'
    let message = 'Allocation Event'
    let description = `Event: ${event.type}`

    switch (event.type) {
      case 'allocated':
        notificationType = 'success'
        message = 'Environment Allocated'
        description = `Test ${testIdShort}... allocated to environment ${envIdShort}...`
        break
      case 'deallocated':
        notificationType = 'info'
        message = 'Environment Deallocated'
        description = `Environment ${envIdShort}... is now available`
        break
      case 'failed':
        notificationType = 'error'
        message = 'Allocation Failed'
        description = `Failed to allocate environment for test ${testIdShort}...`
        break
      case 'queued':
        notificationType = 'info'
        message = 'Test Queued'
        description = `Test ${testIdShort}... added to allocation queue`
        break
    }

    this.playNotificationSound(notificationType)

    notification[notificationType]({
      key: `alloc-${event.id}`,
      message,
      description,
      duration: 4,
      placement: 'topRight'
    })
  }

  showConnectionEvent(
    type: 'connected' | 'disconnected' | 'degraded' | 'recovered',
    details?: string
  ) {
    if (!this.preferences.enableConnectionEvents) return
    if (!this.shouldShowNotification()) return

    let notificationType: 'success' | 'info' | 'warning' | 'error' = 'info'
    let message = 'Connection Event'
    let description = details || `Connection ${type}`

    switch (type) {
      case 'connected':
      case 'recovered':
        notificationType = 'success'
        message = 'Connection Restored'
        description = 'Real-time updates are now available'
        break
      case 'disconnected':
        notificationType = 'error'
        message = 'Connection Lost'
        description = 'Real-time updates are unavailable'
        break
      case 'degraded':
        notificationType = 'warning'
        message = 'Connection Degraded'
        description = 'Some real-time features may be limited'
        break
    }

    this.playNotificationSound(notificationType)

    notification[notificationType]({
      key: `connection-${type}`,
      message,
      description,
      duration: type === 'disconnected' ? 8 : 5,
      placement: 'topRight'
    })
  }

  showError(error: string, context?: string) {
    if (!this.preferences.enableErrorNotifications) return
    if (!this.shouldShowNotification()) return

    this.playNotificationSound('error')

    notification.error({
      key: `error-${Date.now()}`,
      message: 'System Error',
      description: context ? `${context}: ${error}` : error,
      duration: 8,
      placement: 'topRight'
    })
  }

  private getStatusIcon(status: EnvironmentStatus) {
    switch (status) {
      case EnvironmentStatus.READY:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case EnvironmentStatus.ERROR:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case EnvironmentStatus.RUNNING:
        return <ThunderboltOutlined style={{ color: '#1890ff' }} />
      default:
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
    }
  }

  clearAll() {
    notification.destroy()
    this.groupedNotifications.clear()
  }
}

const RealTimeNotificationSystem: React.FC<RealTimeNotificationSystemProps> = ({
  preferences: userPreferences,
  onPreferencesChange
}) => {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    ...defaultPreferences,
    ...userPreferences
  })
  const [isEnabled, setIsEnabled] = useState(true)
  const managerRef = useRef<NotificationManager>()

  // Initialize notification manager
  useEffect(() => {
    managerRef.current = NotificationManager.getInstance(preferences)
  }, [])

  // Update preferences
  useEffect(() => {
    if (managerRef.current) {
      managerRef.current.updatePreferences(preferences)
    }
    onPreferencesChange?.(preferences)
  }, [preferences, onPreferencesChange])

  const toggleNotifications = () => {
    setIsEnabled(!isEnabled)
    if (isEnabled) {
      managerRef.current?.clearAll()
    }
  }

  // Expose notification methods globally
  useEffect(() => {
    if (typeof window !== 'undefined' && managerRef.current) {
      (window as any).notificationManager = managerRef.current
    }
  }, [])

  return (
    <Space>
      <Button
        size="small"
        icon={isEnabled ? <BellFilled /> : <BellOutlined />}
        onClick={toggleNotifications}
        type={isEnabled ? 'primary' : 'default'}
        title={isEnabled ? 'Disable notifications' : 'Enable notifications'}
      />
      <Button
        size="small"
        icon={<SettingOutlined />}
        onClick={() => {
          // TODO: Open notification preferences modal
          console.log('Open notification preferences')
        }}
        title="Notification settings"
      />
    </Space>
  )
}

export default RealTimeNotificationSystem
export { NotificationManager }