import React from 'react'
import { Card, Skeleton, Space } from 'antd'

interface EnvironmentTableSkeletonProps {
  rows?: number
  showResourceUsage?: boolean
}

const EnvironmentTableSkeleton: React.FC<EnvironmentTableSkeletonProps> = ({
  rows = 5,
  showResourceUsage = true
}) => {
  return (
    <Card
      title={
        <Space>
          <Skeleton.Input style={{ width: 120, height: 20 }} active />
          <Skeleton.Avatar size="small" active />
        </Space>
      }
      extra={
        <Space>
          <Skeleton.Input style={{ width: 200, height: 32 }} active />
          <Skeleton.Input style={{ width: 120, height: 32 }} active />
          <Skeleton.Input style={{ width: 120, height: 32 }} active />
        </Space>
      }
    >
      {/* Table Header Skeleton */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 16px',
          backgroundColor: '#fafafa',
          borderBottom: '2px solid #f0f0f0',
          marginBottom: '8px'
        }}
      >
        <div style={{ flex: '0 0 200px' }}>
          <Skeleton.Input style={{ width: 150, height: 16 }} active />
        </div>
        <div style={{ flex: '0 0 120px' }}>
          <Skeleton.Input style={{ width: 80, height: 16 }} active />
        </div>
        <div style={{ flex: '0 0 120px' }}>
          <Skeleton.Input style={{ width: 80, height: 16 }} active />
        </div>
        <div style={{ flex: '0 0 100px' }}>
          <Skeleton.Input style={{ width: 80, height: 16 }} active />
        </div>
        <div style={{ flex: '0 0 100px', textAlign: 'center' }}>
          <Skeleton.Input style={{ width: 60, height: 16 }} active />
        </div>
        {showResourceUsage && (
          <div style={{ flex: '0 0 300px' }}>
            <Skeleton.Input style={{ width: 200, height: 16 }} active />
          </div>
        )}
        <div style={{ flex: '1', textAlign: 'right' }}>
          <Skeleton.Input style={{ width: 80, height: 16 }} active />
        </div>
      </div>

      {/* Table Rows Skeleton */}
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px 16px',
            borderBottom: '1px solid #f0f0f0',
            marginBottom: '4px'
          }}
        >
          {/* Environment ID */}
          <div style={{ flex: '0 0 200px' }}>
            <Skeleton.Input 
              style={{ width: Math.random() * 50 + 120, height: 16 }} 
              active 
            />
          </div>

          {/* Type */}
          <div style={{ flex: '0 0 120px' }}>
            <Skeleton.Button 
              style={{ width: 80, height: 22 }} 
              active 
              size="small"
            />
          </div>

          {/* Status */}
          <div style={{ flex: '0 0 120px' }}>
            <Skeleton.Button 
              style={{ width: 70, height: 22 }} 
              active 
              size="small"
            />
          </div>

          {/* Architecture */}
          <div style={{ flex: '0 0 100px' }}>
            <Skeleton.Input style={{ width: 60, height: 16 }} active />
          </div>

          {/* Assigned Tests */}
          <div style={{ flex: '0 0 100px', textAlign: 'center' }}>
            <Skeleton.Button 
              style={{ width: 30, height: 22 }} 
              active 
              size="small"
            />
          </div>

          {/* Resource Usage */}
          {showResourceUsage && (
            <div style={{ flex: '0 0 300px' }}>
              <Space size="small">
                <Skeleton.Avatar size={24} active />
                <Skeleton.Avatar size={24} active />
                <Skeleton.Avatar size={24} active />
              </Space>
            </div>
          )}

          {/* Actions */}
          <div style={{ flex: '1', textAlign: 'right' }}>
            <Space size="small">
              <Skeleton.Button style={{ width: 28, height: 28 }} active size="small" />
              <Skeleton.Button style={{ width: 28, height: 28 }} active size="small" />
              <Skeleton.Button style={{ width: 28, height: 28 }} active size="small" />
              <Skeleton.Button style={{ width: 28, height: 28 }} active size="small" />
            </Space>
          </div>
        </div>
      ))}
    </Card>
  )
}

export default EnvironmentTableSkeleton