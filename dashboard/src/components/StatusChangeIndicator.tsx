/**
 * Status Change Indicator Component
 * Provides visual feedback and animations for environment status changes
 */

import React, { useEffect, useState } from 'react'
import { Badge, Tooltip, Typography } from 'antd'
import { 
  CheckCircleOutlined, 
  LoadingOutlined, 
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ToolOutlined,
  PoweroffOutlined
} from '@ant-design/icons'
import { EnvironmentStatus } from '../types/environment'

const { Text } = Typography

export interface StatusChangeIndicatorProps {
  status: EnvironmentStatus
  previousStatus?: EnvironmentStatus
  isUpdating?: boolean
  showAnimation?: boolean
  size?: 'small' | 'default' | 'large'
  showText?: boolean
  lastUpdated?: Date
}

const StatusChangeIndicator: React.FC<StatusChangeIndicatorProps> = ({
  status,
  previousStatus,
  isUpdating = false,
  showAnimation = true,
  size = 'default',
  showText = true,
  lastUpdated
}) => {
  const [isAnimating, setIsAnimating] = useState(false)
  const [showPulse, setShowPulse] = useState(false)

  // Trigger animation when status changes
  useEffect(() => {
    if (previousStatus && previousStatus !== status && showAnimation) {
      setIsAnimating(true)
      setShowPulse(true)
      
      // Stop animation after 2 seconds
      const timer = setTimeout(() => {
        setIsAnimating(false)
        setShowPulse(false)
      }, 2000)
      
      return () => clearTimeout(timer)
    }
  }, [status, previousStatus, showAnimation])

  // Get status configuration
  const getStatusConfig = (envStatus: EnvironmentStatus) => {
    switch (envStatus) {
      case EnvironmentStatus.READY:
        return {
          status: 'success' as const,
          text: 'READY',
          icon: <CheckCircleOutlined />,
          color: '#52c41a',
          description: 'Environment is ready for allocation'
        }
      case EnvironmentStatus.RUNNING:
        return {
          status: 'processing' as const,
          text: 'RUNNING',
          icon: <LoadingOutlined />,
          color: '#1890ff',
          description: 'Environment is currently running tests'
        }
      case EnvironmentStatus.ALLOCATING:
        return {
          status: 'warning' as const,
          text: 'ALLOCATING',
          icon: <LoadingOutlined spin />,
          color: '#faad14',
          description: 'Environment is being allocated'
        }
      case EnvironmentStatus.CLEANUP:
        return {
          status: 'processing' as const,
          text: 'CLEANUP',
          icon: <LoadingOutlined spin />,
          color: '#722ed1',
          description: 'Environment is being cleaned up'
        }
      case EnvironmentStatus.MAINTENANCE:
        return {
          status: 'default' as const,
          text: 'MAINTENANCE',
          icon: <ToolOutlined />,
          color: '#8c8c8c',
          description: 'Environment is under maintenance'
        }
      case EnvironmentStatus.ERROR:
        return {
          status: 'error' as const,
          text: 'ERROR',
          icon: <ExclamationCircleOutlined />,
          color: '#ff4d4f',
          description: 'Environment has encountered an error'
        }
      case EnvironmentStatus.OFFLINE:
        return {
          status: 'default' as const,
          text: 'OFFLINE',
          icon: <PoweroffOutlined />,
          color: '#bfbfbf',
          description: 'Environment is offline'
        }
      default:
        return {
          status: 'default' as const,
          text: String(envStatus).toUpperCase(),
          icon: <CloseCircleOutlined />,
          color: '#d9d9d9',
          description: 'Unknown status'
        }
    }
  }

  const currentConfig = getStatusConfig(status)
  const previousConfig = previousStatus ? getStatusConfig(previousStatus) : null

  // Animation styles
  const animationStyles: React.CSSProperties = {
    transition: 'all 0.3s ease-in-out',
    ...(isAnimating && {
      transform: 'scale(1.1)',
    }),
    ...(showPulse && {
      animation: 'pulse 1s infinite'
    })
  }

  // Pulse animation keyframes (injected via style tag)
  useEffect(() => {
    if (showPulse) {
      const style = document.createElement('style')
      style.textContent = `
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.6; }
          100% { opacity: 1; }
        }
      `
      document.head.appendChild(style)
      
      return () => {
        document.head.removeChild(style)
      }
    }
  }, [showPulse])

  // Tooltip content
  const tooltipContent = (
    <div>
      <div>{currentConfig.description}</div>
      {previousStatus && previousStatus !== status && (
        <div style={{ marginTop: 4, fontSize: '12px', opacity: 0.8 }}>
          Changed from: {previousConfig?.text}
        </div>
      )}
      {lastUpdated && (
        <div style={{ marginTop: 4, fontSize: '11px', opacity: 0.7 }}>
          Updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
      {isUpdating && (
        <div style={{ marginTop: 4, fontSize: '11px', color: '#1890ff' }}>
          Updating...
        </div>
      )}
    </div>
  )

  const badgeElement = (
    <div style={animationStyles}>
      <Badge 
        status={currentConfig.status} 
        text={showText ? currentConfig.text : undefined}
        style={{
          ...(size === 'small' && { fontSize: '12px' }),
          ...(size === 'large' && { fontSize: '16px' })
        }}
      />
    </div>
  )

  // Show loading overlay if updating
  if (isUpdating) {
    return (
      <Tooltip title={tooltipContent}>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          {badgeElement}
          <div 
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.8)',
              borderRadius: '4px'
            }}
          >
            <LoadingOutlined style={{ fontSize: '12px', color: '#1890ff' }} />
          </div>
        </div>
      </Tooltip>
    )
  }

  return (
    <Tooltip title={tooltipContent}>
      {badgeElement}
    </Tooltip>
  )
}

export default StatusChangeIndicator