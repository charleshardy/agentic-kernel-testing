import React from 'react'
import { Badge, Tooltip } from 'antd'

interface StatusIndicatorProps {
  status: 'healthy' | 'warning' | 'error' | 'unknown'
  text?: string
  tooltip?: string
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, text, tooltip }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'healthy':
        return { color: 'green', text: text || 'Healthy' }
      case 'warning':
        return { color: 'orange', text: text || 'Warning' }
      case 'error':
        return { color: 'red', text: text || 'Error' }
      default:
        return { color: 'gray', text: text || 'Unknown' }
    }
  }

  const config = getStatusConfig(status)
  
  const badge = <Badge color={config.color} text={config.text} />
  
  return tooltip ? (
    <Tooltip title={tooltip}>
      {badge}
    </Tooltip>
  ) : badge
}

export default StatusIndicator