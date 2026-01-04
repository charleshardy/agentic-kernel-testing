import React from 'react'
import { Card, Row, Col, Skeleton, Space } from 'antd'

interface ResourceChartsSkeletonProps {
  showAnalytics?: boolean
  showThresholds?: boolean
}

const ResourceChartsSkeleton: React.FC<ResourceChartsSkeletonProps> = ({
  showAnalytics = true,
  showThresholds = true
}) => {
  return (
    <div>
      {/* Alert Summary Skeleton */}
      <div style={{ marginBottom: 16 }}>
        <Skeleton.Input style={{ width: '100%', height: 60 }} active />
      </div>

      <Card
        title={
          <Space>
            <Skeleton.Avatar size="small" active />
            <Skeleton.Input style={{ width: 200, height: 20 }} active />
            <Skeleton.Avatar size="small" active />
            <Skeleton.Button style={{ width: 60, height: 22 }} active size="small" />
          </Space>
        }
        extra={
          <Space>
            <Skeleton.Input style={{ width: 200, height: 32 }} active />
            <Skeleton.Input style={{ width: 100, height: 32 }} active />
            <Skeleton.Button style={{ width: 80, height: 32 }} active />
            <Skeleton.Button style={{ width: 80, height: 32 }} active />
            <Skeleton.Button style={{ width: 100, height: 32 }} active />
          </Space>
        }
      >
        {/* Aggregate Statistics Skeleton */}
        {showAnalytics && (
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            {Array.from({ length: 4 }).map((_, index) => (
              <Col key={index} span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Skeleton.Avatar size={40} active />
                  <div style={{ marginTop: 8 }}>
                    <Skeleton.Input style={{ width: 80, height: 32 }} active />
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <Skeleton.Input style={{ width: 120, height: 16 }} active />
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        )}

        {/* Chart Skeleton */}
        <Card size="small" title={<Skeleton.Input style={{ width: 120, height: 16 }} active />} style={{ marginBottom: 16 }}>
          <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Skeleton.Image style={{ width: '100%', height: 280 }} active />
          </div>
        </Card>

        {/* Environment Filter Skeleton */}
        <Card size="small" title={<Skeleton.Input style={{ width: 140, height: 16 }} active />} style={{ marginBottom: 16 }}>
          <Skeleton.Input style={{ width: '100%', height: 32 }} active />
        </Card>

        {/* Threshold Configuration Skeleton */}
        {showThresholds && (
          <Card size="small" title={<Skeleton.Input style={{ width: 120, height: 16 }} active />} style={{ marginBottom: 16 }}>
            <Row gutter={[16, 16]}>
              {Array.from({ length: 4 }).map((_, index) => (
                <Col key={index} span={6}>
                  <div>
                    <Skeleton.Input style={{ width: 100, height: 16 }} active />
                    <div style={{ marginTop: 8 }}>
                      <Skeleton.Input style={{ width: 80, height: 16 }} active />
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Skeleton.Input style={{ width: '100%', height: 20 }} active />
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Skeleton.Input style={{ width: 80, height: 16 }} active />
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        )}

        {/* Environment Resource Cards Skeleton */}
        <Card size="small" title={<Skeleton.Input style={{ width: 180, height: 16 }} active />}>
          <Row gutter={[12, 12]}>
            {Array.from({ length: 8 }).map((_, index) => (
              <Col key={index} xs={24} sm={12} md={8} lg={6}>
                <Card size="small" style={{ minHeight: 160 }}>
                  <div style={{ marginBottom: 8 }}>
                    <Space>
                      <Skeleton.Input style={{ width: 80, height: 16 }} active />
                      <Skeleton.Button style={{ width: 60, height: 22 }} active size="small" />
                    </Space>
                  </div>
                  
                  {/* Progress bars skeleton */}
                  {Array.from({ length: 3 }).map((_, progressIndex) => (
                    <div key={progressIndex} style={{ marginBottom: 8 }}>
                      <Skeleton.Input style={{ width: 40, height: 12 }} active />
                      <div style={{ marginTop: 4 }}>
                        <Skeleton.Input style={{ width: '100%', height: 8 }} active />
                      </div>
                    </div>
                  ))}
                  
                  <div style={{ marginTop: 8 }}>
                    <Skeleton.Input style={{ width: 60, height: 12 }} active />
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      </Card>
    </div>
  )
}

export default ResourceChartsSkeleton