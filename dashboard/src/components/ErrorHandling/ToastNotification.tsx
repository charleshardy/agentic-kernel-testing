import React, { useEffect, useState } from 'react'
import { notification } from 'antd'
import { 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  BugOutlined
} from '@ant-design/icons'

export type NotificationType = 'success' | 'info' | 'warning' | 'error'

export interface NotificationConfig {
  type: NotificationType
  message: string
  description?: string
  duration?: number
  placement?: 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight'
  key?: string
  onClose?: () => void
  onClick?: () => void
  showProgress?: boolean
  actions?: Array<{
    label: string
    onClick: () => void
    type?: 'primary' | 'default'
    icon?: React.ReactNode
  }>
}

class ToastNotificationManager {
  private static instance: ToastNotificationManager
  private notifications: Map<string, any> = new Map()

  static getInstance(): ToastNotificationManager {
    if (!ToastNotificationManager.instance) {
      ToastNotificationManager.instance = new ToastNotificationManager()
    }
    return ToastNotificationManager.instance
  }

  private getIcon(type: NotificationType) {
    switch (type) {
      case 'success': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'info': return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      case 'warning': return <WarningOutlined style={{ color: '#faad14' }} />
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <InfoCircleOutlined />
    }
  }

  show(config: NotificationConfig) {
    const key = config.key || `notification-${Date.now()}-${Math.random()}`
    
    const notificationConfig = {
      key,
      message: config.message,
      description: config.description,
      duration: config.duration ?? (config.type === 'error' ? 0 : 4.5),
      placement: config.placement ?? 'topRight',
      icon: this.getIcon(config.type),
      onClose: () => {
        this.notifications.delete(key)
        if (config.onClose) {
          config.onClose()
        }
      },
      onClick: config.onClick,
      style: {
        cursor: config.onClick ? 'pointer' : 'default'
      }
    }

    // Add action buttons if provided
    if (config.actions && config.actions.length > 0) {
      notificationConfig.btn = (
        <div style={{ marginTop: '8px' }}>
          {config.actions.map((action, index) => (
            <button
              key={index}
              onClick={action.onClick}
              style={{
                marginRight: '8px',
                padding: '4px 8px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px',
                background: action.type === 'primary' ? '#1890ff' : 'white',
                color: action.type === 'primary' ? 'white' : '#000',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              {action.icon && <span style={{ marginRight: '4px' }}>{action.icon}</span>}
              {action.label}
            </button>
          ))}
        </div>
      )
    }

    this.notifications.set(key, notificationConfig)
    notification[config.type](notificationConfig)
    
    return key
  }

  success(message: string, description?: string, options?: Partial<NotificationConfig>) {
    return this.show({
      type: 'success',
      message,
      description,
      ...options
    })
  }

  info(message: string, description?: string, options?: Partial<NotificationConfig>) {
    return this.show({
      type: 'info',
      message,
      description,
      ...options
    })
  }

  warning(message: string, description?: string, options?: Partial<NotificationConfig>) {
    return this.show({
      type: 'warning',
      message,
      description,
      ...options
    })
  }

  error(message: string, description?: string, options?: Partial<NotificationConfig>) {
    return this.show({
      type: 'error',
      message,
      description,
      duration: 0, // Don't auto-hide errors
      ...options
    })
  }

  // Specialized methods for common use cases
  networkError(endpoint: string, statusCode?: number, options?: Partial<NotificationConfig>) {
    return this.error(
      'Network Error',
      `Failed to connect to ${endpoint}${statusCode ? ` (Status: ${statusCode})` : ''}`,
      {
        actions: [
          {
            label: 'Retry',
            onClick: () => window.location.reload(),
            type: 'primary',
            icon: <ReloadOutlined />
          }
        ],
        ...options
      }
    )
  }

  allocationError(environmentId?: string, reason?: string, options?: Partial<NotificationConfig>) {
    return this.error(
      'Environment Allocation Failed',
      `${environmentId ? `Environment ${environmentId}: ` : ''}${reason || 'Unknown allocation error'}`,
      {
        actions: [
          {
            label: 'View Details',
            onClick: () => console.log('View allocation details'),
            icon: <BugOutlined />
          }
        ],
        ...options
      }
    )
  }

  environmentError(environmentId: string, error: string, options?: Partial<NotificationConfig>) {
    return this.error(
      'Environment Error',
      `Environment ${environmentId}: ${error}`,
      {
        actions: [
          {
            label: 'Diagnose',
            onClick: () => console.log('Open diagnostics'),
            icon: <BugOutlined />
          }
        ],
        ...options
      }
    )
  }

  allocationSuccess(environmentId: string, testId?: string, options?: Partial<NotificationConfig>) {
    return this.success(
      'Environment Allocated',
      `Environment ${environmentId}${testId ? ` allocated to test ${testId}` : ' is ready'}`,
      options
    )
  }

  environmentStatusChange(environmentId: string, status: string, options?: Partial<NotificationConfig>) {
    const type = status === 'error' ? 'error' : status === 'ready' ? 'success' : 'info'
    return this.show({
      type,
      message: 'Environment Status Changed',
      description: `Environment ${environmentId} is now ${status}`,
      ...options
    })
  }

  close(key: string) {
    notification.close(key)
    this.notifications.delete(key)
  }

  closeAll() {
    notification.destroy()
    this.notifications.clear()
  }

  update(key: string, config: Partial<NotificationConfig>) {
    const existing = this.notifications.get(key)
    if (existing) {
      const updatedConfig = { ...existing, ...config }
      this.notifications.set(key, updatedConfig)
      notification.open(updatedConfig)
    }
  }
}

// Export singleton instance
export const toast = ToastNotificationManager.getInstance()

// React hook for using toast notifications
export const useToast = () => {
  return {
    success: toast.success.bind(toast),
    info: toast.info.bind(toast),
    warning: toast.warning.bind(toast),
    error: toast.error.bind(toast),
    networkError: toast.networkError.bind(toast),
    allocationError: toast.allocationError.bind(toast),
    environmentError: toast.environmentError.bind(toast),
    allocationSuccess: toast.allocationSuccess.bind(toast),
    environmentStatusChange: toast.environmentStatusChange.bind(toast),
    close: toast.close.bind(toast),
    closeAll: toast.closeAll.bind(toast),
    update: toast.update.bind(toast)
  }
}

// Progress notification component
export const ProgressNotification: React.FC<{
  message: string
  progress: number
  onCancel?: () => void
}> = ({ message, progress, onCancel }) => {
  const [key, setKey] = useState<string>()

  useEffect(() => {
    const notificationKey = toast.info(
      message,
      `Progress: ${Math.round(progress)}%`,
      {
        duration: 0,
        key: key || `progress-${Date.now()}`,
        actions: onCancel ? [
          {
            label: 'Cancel',
            onClick: onCancel
          }
        ] : undefined
      }
    )
    
    if (!key) {
      setKey(notificationKey)
    }

    // Auto-close when complete
    if (progress >= 100) {
      setTimeout(() => {
        if (notificationKey) {
          toast.close(notificationKey)
        }
      }, 2000)
    }
  }, [message, progress, onCancel, key])

  return null
}

export default ToastNotificationManager