import React, { useState, useMemo } from 'react'
import {
  Card,
  Table,
  Tag,
  Space,
  Typography,
  Tooltip,
  Badge,
  Progress,
  Row,
  Col,
  Statistic,
  Alert,
  Button,
  Tabs,
  List,
  Empty,
  Divider,
} from 'antd'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  LinkOutlined,
  FileTextOutlined,
  BulbOutlined,
  CodeOutlined,
  QuestionCircleOutlined,
  ExportOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography
const { TabPane } = Tabs

interface Requirement {
  id: string
  text: string
  pattern?: string
}

interface Property {
  id: string
  name: string
  requirement_ids: string[]
}

interface Test {
  id: string
  name: string
  property_id: string
  requirement_ids: string[]
  status?: 'passed' | 'failed' | 'pending' | 'not_run'
}

interface TraceabilityLink {
  requirement_id: string
  property_ids: string[]
  test_ids: string[]
  coverage_status: 'covered' | 'partial' | 'uncovered'
}

interface TraceabilityMatrixProps {
  requirements: Requirement[]
  properties: Property[]
  tests: Test[]
  links?: TraceabilityLink[]
  onExport?: (format: 'csv' | 'html' | 'markdown') => void
}

const TraceabilityMatrix: React.FC<TraceabilityMatrixProps> = ({
  requirements,
  properties,
  tests,
  links,
  onExport,
}) => {
  const [activeTab, setActiveTab] = useState('matrix')

  // Calculate traceability links if not provided
  const calculatedLinks = useMemo(() => {
    if (links) return links

    return requirements.map(req => {
      const linkedProperties = properties.filter(p => 
        p.requirement_ids.includes(req.id)
      )
      const linkedTests = tests.filter(t => 
        t.requirement_ids.includes(req.id)
      )
      
      let coverage_status: 'covered' | 'partial' | 'uncovered' = 'uncovered'
      if (linkedTests.length > 0) {
        const hasPassingTest = linkedTests.some(t => t.status === 'passed')
        coverage_status = hasPassingTest ? 'covered' : 'partial'
      } else if (linkedProperties.length > 0) {
        coverage_status = 'partial'
      }

      return {
        requirement_id: req.id,
        property_ids: linkedProperties.map(p => p.id),
        test_ids: linkedTests.map(t => t.id),
        coverage_status,
      }
    })
  }, [requirements, properties, tests, links])

  // Calculate statistics
  const stats = useMemo(() => {
    const covered = calculatedLinks.filter(l => l.coverage_status === 'covered').length
    const partial = calculatedLinks.filter(l => l.coverage_status === 'partial').length
    const uncovered = calculatedLinks.filter(l => l.coverage_status === 'uncovered').length
    const total = requirements.length

    // Find orphaned tests (tests not linked to any requirement)
    const linkedTestIds = new Set(calculatedLinks.flatMap(l => l.test_ids))
    const orphanedTests = tests.filter(t => !linkedTestIds.has(t.id))

    return {
      covered,
      partial,
      uncovered,
      total,
      coveragePercent: total > 0 ? Math.round((covered / total) * 100) : 0,
      orphanedTests,
    }
  }, [calculatedLinks, requirements, tests])

  const getCoverageIcon = (status: string) => {
    switch (status) {
      case 'covered':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'partial':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
      default:
        return <WarningOutlined style={{ color: '#ff4d4f' }} />
    }
  }

  const getCoverageColor = (status: string) => {
    const colors: Record<string, string> = {
      covered: 'success',
      partial: 'warning',
      uncovered: 'error',
    }
    return colors[status] || 'default'
  }

  const getTestStatusColor = (status?: string) => {
    const colors: Record<string, string> = {
      passed: 'success',
      failed: 'error',
      pending: 'processing',
      not_run: 'default',
    }
    return colors[status || 'not_run'] || 'default'
  }

  // Matrix columns
  const matrixColumns = [
    {
      title: 'Requirement',
      dataIndex: 'requirement_id',
      key: 'requirement',
      width: 150,
      fixed: 'left' as const,
      render: (reqId: string) => {
        const req = requirements.find(r => r.id === reqId)
        return (
          <Tooltip title={req?.text}>
            <Space>
              <FileTextOutlined />
              <Text code>{reqId}</Text>
            </Space>
          </Tooltip>
        )
      },
    },
    {
      title: 'Coverage',
      dataIndex: 'coverage_status',
      key: 'coverage',
      width: 120,
      render: (status: string) => (
        <Space>
          {getCoverageIcon(status)}
          <Tag color={getCoverageColor(status)}>{status.toUpperCase()}</Tag>
        </Space>
      ),
    },
    {
      title: 'Properties',
      dataIndex: 'property_ids',
      key: 'properties',
      width: 200,
      render: (propIds: string[]) => (
        <Space wrap>
          {propIds.length > 0 ? (
            propIds.map(id => {
              const prop = properties.find(p => p.id === id)
              return (
                <Tooltip key={id} title={prop?.name}>
                  <Tag color="purple" icon={<BulbOutlined />}>
                    {id}
                  </Tag>
                </Tooltip>
              )
            })
          ) : (
            <Text type="secondary">-</Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Tests',
      dataIndex: 'test_ids',
      key: 'tests',
      render: (testIds: string[]) => (
        <Space wrap>
          {testIds.length > 0 ? (
            testIds.map(id => {
              const test = tests.find(t => t.id === id)
              return (
                <Tooltip key={id} title={test?.name}>
                  <Tag 
                    color={getTestStatusColor(test?.status)} 
                    icon={<CodeOutlined />}
                  >
                    {id}
                  </Tag>
                </Tooltip>
              )
            })
          ) : (
            <Text type="secondary">No tests</Text>
          )}
        </Space>
      ),
    },
  ]

  // Untested requirements
  const untestedRequirements = calculatedLinks
    .filter(l => l.coverage_status === 'uncovered')
    .map(l => requirements.find(r => r.id === l.requirement_id))
    .filter(Boolean) as Requirement[]

  return (
    <div className="traceability-matrix">
      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={5}>
          <Card>
            <Statistic
              title="Total Requirements"
              value={stats.total}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="Covered"
              value={stats.covered}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="Partial"
              value={stats.partial}
              valueStyle={{ color: '#faad14' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="Uncovered"
              value={stats.uncovered}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Coverage"
              value={stats.coveragePercent}
              suffix="%"
              valueStyle={{ 
                color: stats.coveragePercent >= 80 ? '#52c41a' : 
                       stats.coveragePercent >= 50 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Coverage Progress */}
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" gutter={16}>
          <Col flex="auto">
            <Text strong>Requirements Coverage</Text>
            <Progress
              percent={stats.coveragePercent}
              status={
                stats.coveragePercent >= 80 ? 'success' :
                stats.coveragePercent >= 50 ? 'normal' : 'exception'
              }
              strokeWidth={20}
              style={{ marginTop: 8 }}
            />
          </Col>
          {onExport && (
            <Col>
              <Space>
                <Button icon={<ExportOutlined />} onClick={() => onExport('csv')}>
                  CSV
                </Button>
                <Button icon={<ExportOutlined />} onClick={() => onExport('html')}>
                  HTML
                </Button>
                <Button icon={<ExportOutlined />} onClick={() => onExport('markdown')}>
                  Markdown
                </Button>
              </Space>
            </Col>
          )}
        </Row>
      </Card>

      {/* Alerts */}
      {stats.uncovered > 0 && (
        <Alert
          message={`${stats.uncovered} requirement(s) have no test coverage`}
          description="These requirements need property-based tests to ensure correctness."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {stats.orphanedTests.length > 0 && (
        <Alert
          message={`${stats.orphanedTests.length} orphaned test(s) found`}
          description="These tests are not linked to any requirement and may be obsolete."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Tabs */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="Coverage Matrix" key="matrix">
            <Table
              columns={matrixColumns}
              dataSource={calculatedLinks}
              rowKey="requirement_id"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 800 }}
              rowClassName={record => 
                record.coverage_status === 'uncovered' ? 'uncovered-row' : ''
              }
            />
          </TabPane>

          <TabPane 
            tab={
              <Badge count={stats.uncovered} offset={[10, 0]}>
                Untested Requirements
              </Badge>
            } 
            key="untested"
          >
            {untestedRequirements.length > 0 ? (
              <List
                dataSource={untestedRequirements}
                renderItem={req => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<WarningOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />}
                      title={<Text code>{req.id}</Text>}
                      description={req.text}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="All requirements have test coverage!"
              />
            )}
          </TabPane>

          <TabPane 
            tab={
              <Badge count={stats.orphanedTests.length} offset={[10, 0]}>
                Orphaned Tests
              </Badge>
            } 
            key="orphaned"
          >
            {stats.orphanedTests.length > 0 ? (
              <List
                dataSource={stats.orphanedTests}
                renderItem={test => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<QuestionCircleOutlined style={{ color: '#faad14', fontSize: 20 }} />}
                      title={<Text code>{test.name}</Text>}
                      description={`Property: ${test.property_id} | Status: ${test.status || 'not_run'}`}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No orphaned tests found"
              />
            )}
          </TabPane>
        </Tabs>
      </Card>

      <style>{`
        .uncovered-row {
          background-color: #fff2f0;
        }
        .uncovered-row:hover > td {
          background-color: #ffccc7 !important;
        }
      `}</style>
    </div>
  )
}

export default TraceabilityMatrix
