import React from 'react'
import { Card, Row, Col, Statistic, Progress, Alert, Space, Button, Table, Tag } from 'antd'
import { 
  FundOutlined, 
  TrendingUpOutlined, 
  TrendingDownOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  BulbOutlined,
  BarChartOutlined
} from '@ant-design/icons'

const AnalyticsInsights: React.FC = () => {
  // Mock analytics data
  const analyticsStats = {
    totalTests: 15420,
    testTrend: 12.5,
    passRate: 94.2,
    passRateTrend: -2.1,
    avgExecutionTime: 145,
    timeTrend: -8.3,
    coverageIncrease: 5.7,
    defectReduction: 23.4
  }

  const insights = [
    {
      key: '1',
      type: 'Performance',
      title: 'Test Execution Time Improved',
      description: 'Average test execution time decreased by 8.3% this week',
      impact: 'High',
      confidence: 95,
      recommendation: 'Continue optimizing test parallelization'
    },
    {
      key: '2',
      type: 'Quality',
      title: 'Memory Leak Pattern Detected',
      description: 'AI detected recurring memory leak pattern in network drivers',
      impact: 'Critical',
      confidence: 87,
      recommendation: 'Review memory management in network subsystem'
    },
    {
      key: '3',
      type: 'Coverage',
      title: 'Code Coverage Gap Identified',
      description: 'Low coverage detected in error handling paths',
      impact: 'Medium',
      confidence: 92,
      recommendation: 'Add negative test cases for error scenarios'
    }
  ]

  const trendData = [
    { metric: 'Test Pass Rate', current: 94.2, previous: 96.3, trend: -2.1 },
    { metric: 'Code Coverage', current: 87.5, previous: 82.8, trend: 4.7 },
    { metric: 'Defect Density', current: 0.8, previous: 1.2, trend: -33.3 },
    { metric: 'Test Efficiency', current: 145, previous: 158, trend: -8.2 }
  ]

  const insightColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colors = {
          'Performance': 'blue',
          'Quality': 'red',
          'Coverage': 'green'
        }
        return <Tag color={colors[type as keyof typeof colors]}>{type}</Tag>
      }
    },
    {
      title: 'Insight',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: any) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{title}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: 'Impact',
      dataIndex: 'impact',
      key: 'impact',
      render: (impact: string) => {
        const colors = {
          'Critical': 'red',
          'High': 'orange',
          'Medium': 'yellow',
          'Low': 'green'
        }
        return <Tag color={colors[impact as keyof typeof colors]}>{impact}</Tag>
      }
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => (
        <Progress 
          percent={confidence} 
          size="small" 
          strokeColor={confidence > 90 ? '#52c41a' : confidence > 70 ? '#faad14' : '#ff4d4f'}
        />
      )
    },
    {
      title: 'Recommendation',
      dataIndex: 'recommendation',
      key: 'recommendation',
      render: (text: string) => <span style={{ fontSize: '12px' }}>{text}</span>
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <FundOutlined />
          Analytics & Insights
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          AI-powered analytics and predictive insights for test optimization
        </p>
      </div>

      <Alert
        message="New Insight Available"
        description="AI has detected a potential performance regression pattern. Review the insights below for recommendations."
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
        action={
          <Button size="small" type="primary">
            View Details
          </Button>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Tests Executed"
              value={analyticsStats.totalTests}
              prefix={<BarChartOutlined />}
              suffix={
                <span style={{ fontSize: '12px', color: analyticsStats.testTrend > 0 ? '#52c41a' : '#ff4d4f' }}>
                  {analyticsStats.testTrend > 0 ? <TrendingUpOutlined /> : <TrendingDownOutlined />}
                  {Math.abs(analyticsStats.testTrend)}%
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Pass Rate"
              value={analyticsStats.passRate}
              precision={1}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: analyticsStats.passRateTrend > 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Execution Time"
              value={analyticsStats.avgExecutionTime}
              suffix="s"
              prefix={<EyeOutlined />}
              valueStyle={{ color: analyticsStats.timeTrend < 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="AI Insights Generated"
              value={insights.length}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Key Metrics Trends" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {trendData.map((item, index) => (
                <div key={index}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>{item.metric}</span>
                    <Space>
                      <span>{item.current}{item.metric.includes('Time') ? 's' : item.metric.includes('Rate') || item.metric.includes('Coverage') ? '%' : ''}</span>
                      <span style={{ 
                        color: item.trend > 0 ? '#52c41a' : '#ff4d4f',
                        fontSize: '12px'
                      }}>
                        {item.trend > 0 ? <TrendingUpOutlined /> : <TrendingDownOutlined />}
                        {Math.abs(item.trend)}%
                      </span>
                    </Space>
                  </div>
                  <Progress 
                    percent={item.metric.includes('Density') ? (2 - item.current) * 50 : item.current} 
                    strokeColor={item.trend > 0 ? '#52c41a' : '#ff4d4f'}
                    showInfo={false}
                    size="small"
                  />
                </div>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Predictive Analytics" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Coverage Improvement Forecast</div>
                <Progress 
                  percent={87.5} 
                  strokeColor="#52c41a"
                  format={() => `87.5% → 92.2%`}
                />
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  Projected 30-day improvement: +4.7%
                </div>
              </div>
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Defect Reduction Trend</div>
                <Progress 
                  percent={76.6} 
                  strokeColor="#1890ff"
                  format={() => `23.4% reduction`}
                />
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  Expected continued improvement based on current patterns
                </div>
              </div>
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Resource Optimization</div>
                <Progress 
                  percent={91.7} 
                  strokeColor="#faad14"
                  format={() => `8.3% faster`}
                />
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  Test execution efficiency improvements
                </div>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="AI-Generated Insights" size="small">
        <Table
          columns={insightColumns}
          dataSource={insights}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  )
}

export default AnalyticsInsights