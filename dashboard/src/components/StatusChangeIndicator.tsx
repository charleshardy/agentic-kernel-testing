/**
 * Enhanced Status Change Indicator Component
 * Provides advanced visual feedback and animations for environment status changes
 * with real-time update capabilities
 */

import React, { useEffect, useState, useRef } from 'react'
import { Badge, Tooltip, Typography, notification } from 'antd'
import { 
  CheckCircleOutlined, 
  LoadingOutlined, 
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ToolOutlined,
  PoweroffOutlined,
  SyncOutlined,
  WarningOutlined
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
  environmentId?: string
  onStatusChange?: (newStatus: EnvironmentStatus, previousStatus?: EnvironmentStatus) => void
  enableNotifications?: boolean
  animationDuration?: number
}

const StatusChangeIndicator: React.FC<StatusChangeIndicatorProps> = ({
  status,
  previousStatus,
  isUpdating = false,
  showAnimation = true,
  size = 'default',
  showText = true,
  lastUpdated,
  environmentId,
  onStatusChange,
  enableNotifications = true,
  animationDuration = 2000
}) => {
  const [isAnimating, setIsAnimating] = useState(false)
  const [showPulse, setShowPulse] = useState(false)
  const [showGlow, setShowGlow] = useState(false)
  const [animationPhase, setAnimationPhase] = useState<'none' | 'transition' | 'highlight' | 'settle'>('none')
  const previousStatusRef = useRef<EnvironmentStatus | undefined>(previousStatus)
  const animationTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Trigger animation and notifications when status changes
  useEffect(() => {
    if (previousStatusRef.current && previousStatusRef.current !== status && showAnimation) {
      console.log(`🎨 Status change animation: ${previousStatusRef.current} → ${status}`)
      
      // Start animation sequence
      setAnimationPhase('transition')
      setIsAnimating(true)
      setShowPulse(true)
      
      // Show glow effect for significant status changes
      const significantChanges = [
        EnvironmentStatus.ERROR,
        EnvironmentStatus.READY,
        EnvironmentStatus.RUNNING,
        EnvironmentStatus.OFFLINE
      ]
      
      if (significantChanges.includes(status)) {
        setShowGlow(true)
      }
      
      // Trigger callback
      onStatusChange?.(status, previousStatusRef.current)
      
      // Show notification for important status changes
      if (enableNotifications && environmentId) {
        showStatusChangeNotification(status, previousStatusRef.current, environmentId)
      }
      
      // Animation phases
      const phaseTimeout1 = setTimeout(() => {
        setAnimationPhase('highlight')
      }, animationDuration * 0.3)
      
      const phaseTimeout2 = setTimeout(() => {
        setAnimationPhase('settle')
        setShowPulse(false)
      }, animationDuration * 0.7)
      
      // Stop animation after duration
      animationTimeoutRef.current = setTimeout(() => {
        setIsAnimating(false)
        setShowGlow(false)
        setAnimationPhase('none')
      }, animationDuration)
      
      // Cleanup timeouts
      return () => {
        clearTimeout(phaseTimeout1)
        clearTimeout(phaseTimeout2)
        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current)
        }
      }
    }
    
    // Update previous status ref
    previousStatusRef.current = status
  }, [status, showAnimation, onStatusChange, enableNotifications, environmentId, animationDuration])

  // Show status change notifications
  const showStatusChangeNotification = (
    newStatus: EnvironmentStatus, 
    oldStatus: EnvironmentStatus, 
    envId: string
  ) => {
    const envIdShort = envId.slice(0, 8)
    
    switch (newStatus) {
      case EnvironmentStatus.READY:
        if (oldStatus === EnvironmentStatus.ALLOCATING || oldStatus === EnvironmentStatus.CLEANUP) {
          notification.success({
            message: 'Environment Ready',
            description: `Environment ${envIdShort}... is now ready for allocation`,
            duration: 3,
            placement: 'topRight'
          })
        }
        break
        
      case EnvironmentStatus.RUNNING:
        notification.info({
          message: 'Environment Running',
          description: `Environment ${envIdShort}... is now running tests`,
          duration: 3,
          placement: 'topRight'
        })
        break
        
      case EnvironmentStatus.ERROR:
        notification.error({
          message: 'Environment Error',
          description: `Environment ${envIdShort}... has encountered an error`,
          duration: 5,
          placement: 'topRight'
        })
        break
        
      case EnvironmentStatus.OFFLINE:
        notification.warning({
          message: 'Environment Offline',
          description: `Environment ${envIdShort}... has gone offline`,
          duration: 4,
          placement: 'topRight'
        })
        break
        
      case EnvironmentStatus.MAINTENANCE:
        notification.info({
          message: 'Environment Maintenance',
          description: `Environment ${envIdShort}... is now under maintenance`,
          duration: 3,
          placement: 'topRight'
        })
        break
    }
  }

  // Get status configuration with enhanced visual feedback
  const getStatusConfig = (envStatus: EnvironmentStatus) => {
    switch (envStatus) {
      case EnvironmentStatus.READY:
        return {
          status: 'success' as const,
          text: 'READY',
          icon: <CheckCircleOutlined />,
          color: '#52c41a',
          glowColor: '#52c41a',
          description: 'Environment is ready for allocation',
          priority: 'high'
        }
      case EnvironmentStatus.RUNNING:
        return {
          status: 'processing' as const,
          text: 'RUNNING',
          icon: <SyncOutlined spin />,
          color: '#1890ff',
          glowColor: '#1890ff',
          description: 'Environment is currently running tests',
          priority: 'high'
        }
      case EnvironmentStatus.ALLOCATING:
        return {
          status: 'warning' as const,
          text: 'ALLOCATING',
          icon: <LoadingOutlined spin />,
          color: '#faad14',
          glowColor: '#faad14',
          description: 'Environment is being allocated',
          priority: 'medium'
        }
      case EnvironmentStatus.CLEANUP:
        return {
          status: 'processing' as const,
          text: 'CLEANUP',
          icon: <LoadingOutlined spin />,
          color: '#722ed1',
          glowColor: '#722ed1',
          description: 'Environment is being cleaned up',
          priority: 'medium'
        }
      case EnvironmentStatus.MAINTENANCE:
        return {
          status: 'default' as const,
          text: 'MAINTENANCE',
          icon: <ToolOutlined />,
          color: '#8c8c8c',
          glowColor: '#faad14',
          description: 'Environment is under maintenance',
          priority: 'medium'
        }
      case EnvironmentStatus.ERROR:
        return {
          status: 'error' as const,
          text: 'ERROR',
          icon: <ExclamationCircleOutlined />,
          color: '#ff4d4f',
          glowColor: '#ff4d4f',
          description: 'Environment has encountered an error',
          priority: 'critical'
        }
      case EnvironmentStatus.OFFLINE:
        return {
          status: 'default' as const,
          text: 'OFFLINE',
          icon: <PoweroffOutlined />,
          color: '#bfbfbf',
          glowColor: '#ff4d4f',
          description: 'Environment is offline',
          priority: 'high'
        }
      default:
        return {
          status: 'default' as const,
          text: String(envStatus).toUpperCase(),
          icon: <WarningOutlined />,
          color: '#d9d9d9',
          glowColor: '#faad14',
          description: 'Unknown status',
          priority: 'low'
        }
    }
  }

  const currentConfig = getStatusConfig(status)
  const previousConfig = previousStatusRef.current ? getStatusConfig(previousStatusRef.current) : null

  // Enhanced animation styles with multiple phases
  const getAnimationStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      position: 'relative',
      display: 'inline-block'
    }

    if (!isAnimating) return baseStyles

    switch (animationPhase) {
      case 'transition':
        return {
          ...baseStyles,
          transform: 'scale(1.15)',
          filter: showGlow ? `drop-shadow(0 0 8px ${currentConfig.glowColor}40)` : undefined
        }
      case 'highlight':
        return {
          ...baseStyles,
          transform: 'scale(1.1)',
          filter: showGlow ? `drop-shadow(0 0 12px ${currentConfig.glowColor}60)` : undefined
        }
      case 'settle':
        return {
          ...baseStyles,
          transform: 'scale(1.05)',
          filter: showGlow ? `drop-shadow(0 0 6px ${currentConfig.glowColor}30)` : undefined
        }
      default:
        return baseStyles
    }
  }

  // Pulse animation styles
  const getPulseStyles = (): React.CSSProperties => {
    if (!showPulse) return {}
    
    return {
      animation: `statusPulse ${animationDuration / 2}ms ease-in-out infinite`,
      animationDelay: '0ms'
    }
  }

  // Enhanced tooltip content with more information
  const tooltipContent = (
    <div>
      <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
        {currentConfig.description}
      </div>
      {previousStatusRef.current && previousStatusRef.current !== status && (
        <div style={{ marginTop: 4, fontSize: '12px', opacity: 0.8 }}>
          <strong>Previous:</strong> {previousConfig?.text}
        </div>
      )}
      {lastUpdated && (
        <div style={{ marginTop: 4, fontSize: '11px', opacity: 0.7 }}>
          <strong>Updated:</strong> {lastUpdated.toLocaleTimeString()}
        </div>
      )}
      {isUpdating && (
        <div style={{ marginTop: 4, fontSize: '11px', color: '#1890ff' }}>
          <LoadingOutlined /> Updating...
        </div>
      )}
      {isAnimating && (
        <div style={{ marginTop: 4, fontSize: '11px', color: currentConfig.color }}>
          🎨 Status changed
        </div>
      )}
      {environmentId && (
        <div style={{ marginTop: 4, fontSize: '10px', opacity: 0.6, fontFamily: 'monospace' }}>
          {environmentId.slice(0, 12)}...
        </div>
      )}
    </div>
  )

  // Inject enhanced CSS animations
  useEffect(() => {
    if (showPulse || isAnimating) {
      const style = document.createElement('style')
      style.textContent = `
        @keyframes statusPulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.05); }
          100% { opacity: 1; transform: scale(1); }
        }
        
        @keyframes statusGlow {
          0% { filter: drop-shadow(0 0 4px ${currentConfig.glowColor}30); }
          50% { filter: drop-shadow(0 0 12px ${currentConfig.glowColor}60); }
          100% { filter: drop-shadow(0 0 4px ${currentConfig.glowColor}30); }
        }
        
        .status-indicator-container {
          position: relative;
          display: inline-block;
        }
        
        .status-indicator-updating::after {
          content: '';
          position: absolute;
          top: -2px;
          left: -2px;
          right: -2px;
          bottom: -2px;
          border: 2px solid #1890ff;
          border-radius: 50%;
          animation: statusSpin 1s linear infinite;
          opacity: 0.6;
        }
        
        @keyframes statusSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `
      document.head.appendChild(style)
      
      return () => {
        if (document.head.contains(style)) {
          document.head.removeChild(style)
        }
      }
    }
  }, [showPulse, isAnimating, currentConfig.glowColor])

  const badgeElement = (
    <div 
      className={`status-indicator-container ${isUpdating ? 'status-indicator-updating' : ''}`}
      style={{
        ...getAnimationStyles(),
        ...getPulseStyles()
      }}
    >
      <Badge 
        status={currentConfig.status} 
        text={showText ? currentConfig.text : undefined}
        style={{
          ...(size === 'small' && { fontSize: '12px' }),
          ...(size === 'large' && { fontSize: '16px' }),
          fontWeight: isAnimating ? 'bold' : 'normal'
        }}
      />
    </div>
  )

  // Show enhanced loading overlay if updating
  if (isUpdating) {
    return (
      <Tooltip title={tooltipContent}>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          {badgeElement}
          <div 
            style={{
              position: 'absolute',
              top: -2,
              left: -2,
              right: -2,
              bottom: -2,
              border: '2px solid #1890ff',
              borderRadius: '4px',
              animation: 'statusSpin 1s linear infinite',
              opacity: 0.6,
              pointerEvents: 'none'
            }}
          />
        </div>
      </Tooltip>
    )
  }

  return (
    <Tooltip title={tooltipContent} placement="top">
      {badgeElement}
    </Tooltip>
  )
}

export default StatusChangeIndicator