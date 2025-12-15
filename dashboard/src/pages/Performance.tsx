import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Select,
  Button,
  Space,
  Table,
  Tag,
  Statistic,
  Alert,
  Tooltip,
} from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  ReloadOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Legend,
  ScatterChart,
  Scatter,
} from 'recharts'
import apiService from '../services/api'

const { Title, Text } = Typography

interface PerformanceProps {}

const Performance: React.FC<PerformanceProps> = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('30')
  const [selectedMetric, setSelectedMetric] = useState('all')

  // Fetch performance metrics
  const { data: performanceMetrics, isLoading: metricsLoading } = useQuery(
    ['performanceMetrics', selectedTimeRange, selectedMetric],
    () => apiService.getPerformanceMetrics({
      start_date: new Date(Date.now() - parseInt(selectedTimeRange) * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date().toISOString(),
      metric_type: selectedMetric === 'all' ? undefined : selectedMetric,
    }),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  // Fetch performance trends
  const { data: performanceTrends, isLoading: trendsLoading } = useQuery(
    ['performanceTrends', selectedTimeRange],
    () => apiService.getPerformanceTrends(parseInt(selectedTimeRange)),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  // Mock performance data (replace with real API data)
  const benchmarkResults = [
    {
      benchmark: 'System Call Latency',
      current: 1.2,
      baseline: 1.1,
      unit: 'μs',
      trend: 'up',
      change: 9.1,
      status: 'regression',
    },
    {
      benchmark: 'Context Switch',
      current: 2.8,
      baseline: 2.9,
      unit: 'μs',
      trend: 'down',
      change: -3.4,
      status: 'improvement',
    },
    {
      benchmark: 'Memory Bandwidth',
      current: 45.2,
      baseline: 45.0,
      unit: 'GB/s',
      trend: 'up',
      change: 0.4,
      status: 'stable',
    },
    {
      benchmark: 'Network Throughput',
      current: 9.8,
      baseline: 9.5,
      unit: 'Gbps',
      trend: 'up',
      change: 3.2,
      status: 'improvement',
    },
    {
      benchmark: 'Disk I/O Sequential Read',
      current: 520,
      baseline: 525,
      unit: 'MB/s',
      trend: 'down',
      change: -0.95,
      status: 'stable',
    },
    {
      benchmark: 'Disk I/O Random Read',
      current: 85,
      baseline: 90,
      unit: 'MB/s',
      trend: 'down',
      change: -5.6,
      status: 'regression',
    },
  ]

  // Mock trend data
  const trendData = [
    { date: '2024-01-01', syscall: 1.1, context: 2.9, memory: 44.8, network: 9.2 },
    { date: '2024-01-02', syscall: 1.0, context: 2.8, memory: 45.1, network: 9.4 },
    { date: '2024-01-03', syscall: 1.2, context: 2.7, memory: 45.0, network: 9.6 },
    { date: '2024-01-04', syscall: 1.1, context: 2.8, memory: 45.2, network: 9.8 },
    { date: '2024-01-05', syscall: 1.3, context: 2.9, memory: 44.9, network: 9.5 },
    { date: '2024-01-06', syscall: 1.2, context: 2.8, memory: 45.2, network: 9.8 },
  ]

  // Mock regression data
  const regressions = [
    {
      commit: 'a1b2c3d4',
      date: '2024-01-05',
      benchmark: 'System Call Latency',
      impact: '+15.2%',
      severity: 'high',
      author: 'john.doe',
      message: 'Optimize memory allocation in syscall path',
    },
    {
      commit: 'e5f6g7h8',
      date: '2024-01-04',
      benchmark: 'Disk I/O Random Read',
      impact: '-8.3%',
      severity: 'medium',
      author: 'jane.smith',
      message: 'Refactor block layer scheduling',
    },
  ]

  const benchmarkColumns = [
    {
      title: 'Benchmark',
      dataIndex: 'benchmark',
      key: 'benchmark',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Current',
      dataIndex: 'current',
      key: 'current',
      render: (value: number, record: any) => (
        <Space>
          <Text>{value}</Text>
          <Text type="secondary">{record.unit}</Text>
        </Space>
      ),
    },
    {
      title: 'Baseline',
      dataIndex: 'baseline',
      key: 'baseline',
      render: (value: number, record: any) => (
        <Space>
          <Text>{value}</Text>
          <Text type="secondary">{record.unit}</Text>
        </Space>
      ),
    },
    {
      title: 'Change',
      dataIndex: 'change',
      key: 'change',
      render: (change: number, record: any) => {
        const isPositive = change > 0
        const isImprovement = record.status === 'improvement'
        const color = isImprovement ? '#52c41a' : record.status === 'regression' ? '#ff4d4f' : '#1890ff'
        
        return (
          <Space>
            {isPositive ? <ArrowUpOutlined style={{ color }} /> : 
             change < 0 ? <ArrowDownOutlined style={{ color }} /> : 
             <MinusOutlined style={{ color }} />}
            <Text style={{ color }}>
              {isPositive ? '+' : ''}{change.toFixed(1)}%
            </Text>
          </Space>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          improvement: 'green',
          regression: 'red',
          stable: 'blue',
        }
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>
      },
    },
  ]

  const regressionColumns = [
    {
      title: 'Commit',
      dataIndex: 'commit',
      key: 'commit',
      render: (commit: string) => <Text code>{commit}</Text>,
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Benchmark',
      dataIndex: 'benchmark',
      key: 'benchmark',
    },
    {
      title: 'Impact',
      dataIndex: 'impact',
      key: 'impact',
      render: (impact: string, record: any) => (
        <Tag color={record.severity === 'high' ? 'red' : 'orange'}>
          {impact}
        </Tag>
      ),
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => {
        const colors = { high: 'red', medium: 'orange', low: 'blue' }
        return <Tag color={colors[severity as keyof typeof colors]}>{severity.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Author',
      dataIndex: 'author',
      key: 'author',
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      render: (text: string) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 200 }}>{text}</Text>
        </Tooltip>
      ),
    },
  ]

  // Calculate summary statistics
  const totalBenchmarks = benchmarkResults.length
  const regressionCount = benchmarkResults.filter(b => b.status === 'regression').length
  const improvementCount = benchmarkResults.filter(b => b.status === 'improvement').length
  const stableCount = benchmarkResults.filter(b => b.status === 'stable').length

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Performance Monitoring</Title>
        <Space>
          <Select
            value={selectedTimeRange}
            onChange={setSelectedTimeRange}
            options={[
              { label: 'Last 7 days', value: '7' },
              { label: 'Last 30 days', value: '30' },
              { label: 'Last 90 days', value: '90' },
            ]}
          />
          <Select
            value={selectedMetric}
            onChange={setSelectedMetric}
            options={[
              { label: 'All Metrics', value: 'all' },
              { label: 'System Calls', value: 'syscall' },
              { label: 'Memory', value: 'memory' },
              { label: 'Network', value: 'network' },
              { label: 'Disk I/O', value: 'disk' },
            ]}
          />
          <Button icon={<ReloadOutlined />}>
            Refresh
          </Button>
          <Button icon={<DownloadOutlined />}>
            Export Report
          </Button>
        </Space>
      </div>

      {/* Performance Summary */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Benchmarks"
              value={totalBenchmarks}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Improvements"
              value={improvementCount}
              valueStyle={{ color: '#52c41a' }}
              prefix={<ArrowUpOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Regressions"
              value={regressionCount}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Stable"
              value={stableCount}
              valueStyle={{ color: '#1890ff' }}
              prefix={<MinusOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Performance Alerts */}
      {regressionCount > 0 && (
        <Alert
          message={`${regressionCount} performance regression${regressionCount > 1 ? 's' : ''} detected`}
          description="Recent changes have caused performance degradation in some benchmarks. Review the regressions table below for details."
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Performance Trends */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card 
            title="Performance Trends" 
            extra={
              <Tooltip title="Performance metrics over time">
                <InfoCircleOutlined />
              </Tooltip>
            }
          >
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="syscall" stroke="#1890ff" name="System Call Latency (μs)" strokeWidth={2} />
                <Line type="monotone" dataKey="context" stroke="#52c41a" name="Context Switch (μs)" strokeWidth={2} />
                <Line type="monotone" dataKey="memory" stroke="#faad14" name="Memory Bandwidth (GB/s)" strokeWidth={2} />
                <Line type="monotone" dataKey="network" stroke="#722ed1" name="Network Throughput (Gbps)" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Benchmark Results */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Current Benchmark Results">
            <Table
              columns={benchmarkColumns}
              dataSource={benchmarkResults}
              rowKey="benchmark"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* Performance Distribution */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Benchmark Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={benchmarkResults}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="benchmark" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="current" fill="#1890ff" name="Current Value" />
                <Bar dataKey="baseline" fill="#52c41a" name="Baseline Value" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Performance vs Baseline">
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart data={benchmarkResults}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="baseline" name="Baseline" />
                <YAxis dataKey="current" name="Current" />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter dataKey="current" fill="#1890ff" />
              </ScatterChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Performance Regressions */}
      {regressions.length > 0 && (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="Recent Performance Regressions">
              <Table
                columns={regressionColumns}
                dataSource={regressions}
                rowKey="commit"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default Performance