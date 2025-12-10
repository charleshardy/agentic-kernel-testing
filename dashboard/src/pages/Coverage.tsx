import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Progress,
  Typography,
  Select,
  Button,
  Space,
  Table,
  Tag,
  Tooltip,
  Alert,
} from 'antd'
import {
  LineChartOutlined,
  PieChartOutlined,
  DownloadOutlined,
  ReloadOutlined,
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
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts'
import apiService from '../services/api'

const { Title, Text } = Typography

interface CoverageProps {}

const Coverage: React.FC<CoverageProps> = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('30')
  const [selectedSubsystem, setSelectedSubsystem] = useState('all')

  // Fetch current coverage data
  const { data: coverageData, isLoading: coverageLoading } = useQuery(
    ['coverageReport', selectedSubsystem],
    () => apiService.getCoverageReport(),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  )

  // Fetch coverage trends
  const { data: coverageTrends, isLoading: trendsLoading } = useQuery(
    ['coverageTrends', selectedTimeRange],
    () => apiService.getCoverageTrends(parseInt(selectedTimeRange)),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  // Mock data for subsystem coverage (replace with real API call)
  const subsystemCoverage = [
    { subsystem: 'kernel/core', line: 85, branch: 78, function: 92 },
    { subsystem: 'kernel/mm', line: 72, branch: 65, function: 80 },
    { subsystem: 'kernel/fs', line: 68, branch: 60, function: 75 },
    { subsystem: 'kernel/net', line: 90, branch: 85, function: 95 },
    { subsystem: 'drivers/block', line: 55, branch: 48, function: 62 },
    { subsystem: 'drivers/char', line: 63, branch: 58, function: 70 },
    { subsystem: 'drivers/net', line: 88, branch: 82, function: 91 },
    { subsystem: 'arch/x86', line: 75, branch: 70, function: 82 },
    { subsystem: 'arch/arm64', line: 70, branch: 65, function: 78 },
  ]

  // Mock data for coverage gaps (replace with real API call)
  const coverageGaps = [
    {
      file: 'kernel/sched/core.c',
      function: 'schedule_timeout',
      lines: '1245-1267',
      priority: 'high',
      reason: 'Error handling path not covered',
    },
    {
      file: 'mm/page_alloc.c',
      function: 'alloc_pages_exact',
      lines: '4521-4535',
      priority: 'medium',
      reason: 'Edge case for large allocations',
    },
    {
      file: 'fs/ext4/inode.c',
      function: 'ext4_write_begin',
      lines: '2890-2910',
      priority: 'high',
      reason: 'Failure recovery not tested',
    },
    {
      file: 'net/core/dev.c',
      function: 'netdev_rx_handler_register',
      lines: '4123-4140',
      priority: 'low',
      reason: 'Rare configuration path',
    },
  ]

  const coverageColumns = [
    {
      title: 'Subsystem',
      dataIndex: 'subsystem',
      key: 'subsystem',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Line Coverage',
      dataIndex: 'line',
      key: 'line',
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          status={value >= 80 ? 'normal' : value >= 60 ? 'active' : 'exception'}
        />
      ),
      sorter: (a: any, b: any) => a.line - b.line,
    },
    {
      title: 'Branch Coverage',
      dataIndex: 'branch',
      key: 'branch',
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          status={value >= 70 ? 'normal' : value >= 50 ? 'active' : 'exception'}
        />
      ),
      sorter: (a: any, b: any) => a.branch - b.branch,
    },
    {
      title: 'Function Coverage',
      dataIndex: 'function',
      key: 'function',
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          status={value >= 85 ? 'normal' : value >= 70 ? 'active' : 'exception'}
        />
      ),
      sorter: (a: any, b: any) => a.function - b.function,
    },
  ]

  const gapColumns = [
    {
      title: 'File',
      dataIndex: 'file',
      key: 'file',
      render: (text: string) => <Text code style={{ fontSize: '12px' }}>{text}</Text>,
    },
    {
      title: 'Function',
      dataIndex: 'function',
      key: 'function',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Lines',
      dataIndex: 'lines',
      key: 'lines',
      render: (text: string) => <Text>{text}</Text>,
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => {
        const colors = { high: 'red', medium: 'orange', low: 'blue' }
        return <Tag color={colors[priority as keyof typeof colors]}>{priority.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      render: (text: string) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 200 }}>{text}</Text>
        </Tooltip>
      ),
    },
  ]

  // Prepare chart data
  const coverageChartData = coverageTrends?.map(trend => ({
    date: new Date(trend.date).toLocaleDateString(),
    line: Math.round(trend.line_coverage * 100),
    branch: Math.round(trend.branch_coverage * 100),
    function: Math.round(trend.function_coverage * 100),
  })) || []

  const coverageDistribution = [
    { name: 'Covered Lines', value: coverageData ? coverageData.covered_lines.length : 0, color: '#52c41a' },
    { name: 'Uncovered Lines', value: coverageData ? coverageData.uncovered_lines.length : 0, color: '#ff4d4f' },
  ]

  const currentCoverage = coverageData ? {
    line: Math.round(coverageData.line_coverage * 100),
    branch: Math.round(coverageData.branch_coverage * 100),
    function: Math.round(coverageData.function_coverage * 100),
  } : { line: 0, branch: 0, function: 0 }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Coverage Analysis</Title>
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
          <Button icon={<ReloadOutlined />}>
            Refresh
          </Button>
          <Button icon={<DownloadOutlined />}>
            Export Report
          </Button>
        </Space>
      </div>

      {/* Current Coverage Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <div className="metric-card">
              <div className="metric-value">{currentCoverage.line}%</div>
              <div className="metric-label">Line Coverage</div>
              <Progress
                percent={currentCoverage.line}
                showInfo={false}
                status={currentCoverage.line >= 80 ? 'normal' : 'exception'}
              />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="metric-card">
              <div className="metric-value">{currentCoverage.branch}%</div>
              <div className="metric-label">Branch Coverage</div>
              <Progress
                percent={currentCoverage.branch}
                showInfo={false}
                status={currentCoverage.branch >= 70 ? 'normal' : 'exception'}
              />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div className="metric-card">
              <div className="metric-value">{currentCoverage.function}%</div>
              <div className="metric-label">Function Coverage</div>
              <Progress
                percent={currentCoverage.function}
                showInfo={false}
                status={currentCoverage.function >= 85 ? 'normal' : 'exception'}
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Coverage Trends and Distribution */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card 
            title="Coverage Trends" 
            extra={
              <Tooltip title="Coverage percentage over time">
                <InfoCircleOutlined />
              </Tooltip>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={coverageChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="line" stroke="#1890ff" name="Line Coverage" strokeWidth={2} />
                <Line type="monotone" dataKey="branch" stroke="#52c41a" name="Branch Coverage" strokeWidth={2} />
                <Line type="monotone" dataKey="function" stroke="#faad14" name="Function Coverage" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Coverage Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={coverageDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {coverageDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Subsystem Coverage */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Coverage by Subsystem">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={subsystemCoverage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="subsystem" angle={-45} textAnchor="end" height={100} />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Legend />
                <Bar dataKey="line" fill="#1890ff" name="Line Coverage" />
                <Bar dataKey="branch" fill="#52c41a" name="Branch Coverage" />
                <Bar dataKey="function" fill="#faad14" name="Function Coverage" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Detailed Coverage Table */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Subsystem Coverage Details">
            <Table
              columns={coverageColumns}
              dataSource={subsystemCoverage}
              rowKey="subsystem"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* Coverage Gaps */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card 
            title="Coverage Gaps" 
            extra={
              <Alert
                message="High priority gaps should be addressed first"
                type="info"
                showIcon
                style={{ marginBottom: 0 }}
              />
            }
          >
            <Table
              columns={gapColumns}
              dataSource={coverageGaps}
              rowKey={(record) => `${record.file}-${record.function}`}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
              }}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Coverage