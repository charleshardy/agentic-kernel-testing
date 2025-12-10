import React, { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  DatePicker,
  Typography,
  Row,
  Col,
  Statistic,
  Modal,
  Descriptions,
  Collapse,
  Alert,
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useQuery } from 'react-query'
import dayjs from 'dayjs'
import apiService, { TestResult } from '../services/api'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Panel } = Collapse

interface TestResultsProps {}

const TestResults: React.FC<TestResultsProps> = () => {
  const [filters, setFilters] = useState({
    status: undefined,
    test_type: undefined,
    start_date: undefined,
    end_date: undefined,
    search: '',
  })
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null)
  const [isDetailModalVisible, setIsDetailModalVisible] = useState(false)

  // Fetch test results with filters
  const { data: resultsData, isLoading, refetch } = useQuery(
    ['testResults', filters],
    () => apiService.getTestResults({
      page: 1,
      page_size: 50,
      status: filters.status,
      start_date: filters.start_date,
      end_date: filters.end_date,
    }),
    {
      keepPreviousData: true,
    }
  )

  const columns = [
    {
      title: 'Test ID',
      dataIndex: 'test_id',
      key: 'test_id',
      render: (id: string) => (
        <Button
          type="link"
          onClick={() => handleViewResult(id)}
          style={{ padding: 0 }}
        >
          {id.slice(0, 12)}...
        </Button>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          passed: 'green',
          failed: 'red',
          running: 'blue',
          pending: 'orange',
          skipped: 'default',
          timeout: 'red',
          error: 'red',
        }
        return <Tag color={colors[status as keyof typeof colors]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Execution Time',
      dataIndex: 'execution_time',
      key: 'execution_time',
      render: (time: number) => `${time.toFixed(2)}s`,
      sorter: (a: TestResult, b: TestResult) => a.execution_time - b.execution_time,
    },
    {
      title: 'Environment',
      dataIndex: 'environment',
      key: 'environment',
      render: (env: any) => (
        <Space direction="vertical" size="small">
          <Text>{env.config?.architecture || 'Unknown'}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {env.config?.cpu_model || 'N/A'}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Coverage',
      dataIndex: 'coverage_data',
      key: 'coverage',
      render: (coverage: any) => {
        if (!coverage) return <Text type="secondary">N/A</Text>
        const linePercent = Math.round(coverage.line_coverage * 100)
        return (
          <Space>
            <Text>{linePercent}%</Text>
            <Text type="secondary">lines</Text>
          </Space>
        )
      },
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (date: string) => dayjs(date).format('MMM DD, HH:mm'),
      sorter: (a: TestResult, b: TestResult) => 
        dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: TestResult) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewResult(record.test_id)}
          >
            View
          </Button>
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadArtifacts(record.test_id)}
          >
            Artifacts
          </Button>
        </Space>
      ),
    },
  ]

  const handleViewResult = async (testId: string) => {
    try {
      const result = await apiService.getTestResult(testId)
      setSelectedResult(result)
      setIsDetailModalVisible(true)
    } catch (error) {
      console.error('Failed to fetch test result:', error)
    }
  }

  const handleDownloadArtifacts = (testId: string) => {
    // Implement artifact download
    console.log('Download artifacts for:', testId)
  }

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleDateRangeChange = (dates: any) => {
    if (dates) {
      setFilters(prev => ({
        ...prev,
        start_date: dates[0].toISOString(),
        end_date: dates[1].toISOString(),
      }))
    } else {
      setFilters(prev => ({
        ...prev,
        start_date: undefined,
        end_date: undefined,
      }))
    }
  }

  // Calculate statistics
  const results = resultsData?.results || []
  const totalTests = results.length
  const passedTests = results.filter(r => r.status === 'passed').length
  const failedTests = results.filter(r => r.status === 'failed').length
  const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Test Results</Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {/* Export results */}}
          >
            Export
          </Button>
        </Space>
      </div>

      {/* Summary Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Tests"
              value={totalTests}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Passed"
              value={passedTests}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Failed"
              value={failedTests}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Pass Rate"
              value={passRate}
              suffix="%"
              valueStyle={{ 
                color: passRate >= 90 ? '#52c41a' : passRate >= 70 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card title="Filters" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Input
              placeholder="Search test ID..."
              prefix={<SearchOutlined />}
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </Col>
          <Col xs={24} sm={4}>
            <Select
              placeholder="Status"
              allowClear
              value={filters.status}
              onChange={(value) => handleFilterChange('status', value)}
              options={[
                { label: 'Passed', value: 'passed' },
                { label: 'Failed', value: 'failed' },
                { label: 'Running', value: 'running' },
                { label: 'Pending', value: 'pending' },
                { label: 'Skipped', value: 'skipped' },
                { label: 'Timeout', value: 'timeout' },
                { label: 'Error', value: 'error' },
              ]}
            />
          </Col>
          <Col xs={24} sm={4}>
            <Select
              placeholder="Test Type"
              allowClear
              value={filters.test_type}
              onChange={(value) => handleFilterChange('test_type', value)}
              options={[
                { label: 'Unit', value: 'unit' },
                { label: 'Integration', value: 'integration' },
                { label: 'Performance', value: 'performance' },
                { label: 'Security', value: 'security' },
                { label: 'Fuzz', value: 'fuzz' },
              ]}
            />
          </Col>
          <Col xs={24} sm={8}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={handleDateRangeChange}
              showTime
            />
          </Col>
        </Row>
      </Card>

      {/* Results Table */}
      <Card title="Test Results">
        <Table
          columns={columns}
          dataSource={results}
          loading={isLoading}
          rowKey="test_id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} results`,
          }}
        />
      </Card>

      {/* Result Detail Modal */}
      <Modal
        title="Test Result Details"
        open={isDetailModalVisible}
        onCancel={() => setIsDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedResult && (
          <div>
            <Descriptions bordered column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Test ID" span={2}>
                {selectedResult.test_id}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={selectedResult.status === 'passed' ? 'green' : 'red'}>
                  {selectedResult.status.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Execution Time">
                {selectedResult.execution_time.toFixed(2)}s
              </Descriptions.Item>
              <Descriptions.Item label="Environment">
                {selectedResult.environment.config?.architecture} - {selectedResult.environment.config?.cpu_model}
              </Descriptions.Item>
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedResult.timestamp).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            <Collapse>
              {selectedResult.coverage_data && (
                <Panel header="Coverage Data" key="coverage">
                  <Descriptions bordered size="small">
                    <Descriptions.Item label="Line Coverage">
                      {Math.round(selectedResult.coverage_data.line_coverage * 100)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="Branch Coverage">
                      {Math.round(selectedResult.coverage_data.branch_coverage * 100)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="Function Coverage">
                      {Math.round(selectedResult.coverage_data.function_coverage * 100)}%
                    </Descriptions.Item>
                  </Descriptions>
                </Panel>
              )}

              {selectedResult.failure_info && (
                <Panel header="Failure Information" key="failure">
                  <Alert
                    message="Test Failed"
                    description={selectedResult.failure_info.message || 'No failure message available'}
                    type="error"
                    showIcon
                  />
                  {selectedResult.failure_info.stack_trace && (
                    <div style={{ marginTop: 16 }}>
                      <Text strong>Stack Trace:</Text>
                      <pre style={{ 
                        background: '#f5f5f5', 
                        padding: '12px', 
                        borderRadius: '4px',
                        fontSize: '12px',
                        overflow: 'auto',
                        maxHeight: '300px'
                      }}>
                        {selectedResult.failure_info.stack_trace}
                      </pre>
                    </div>
                  )}
                </Panel>
              )}

              <Panel header="Artifacts" key="artifacts">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {Object.entries(selectedResult.artifacts).map(([key, value]) => (
                    <div key={key}>
                      <Text strong>{key}:</Text>
                      <Text style={{ marginLeft: 8 }}>{String(value)}</Text>
                    </div>
                  ))}
                </Space>
              </Panel>
            </Collapse>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default TestResults