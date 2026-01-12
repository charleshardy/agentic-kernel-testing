import React, { useState } from 'react'
import {
  Card,
  List,
  Typography,
  Tag,
  Space,
  Button,
  Collapse,
  Tooltip,
  Badge,
  Modal,
  Form,
  Input,
  Select,
  Empty,
  Divider,
  Row,
  Col,
} from 'antd'
import {
  BulbOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CodeOutlined,
  LinkOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  EyeOutlined,
} from '@ant-design/icons'

const { Text, Paragraph, Title } = Typography
const { Panel } = Collapse
const { TextArea } = Input
const { Option } = Select

interface Property {
  id: string
  name: string
  description: string
  pattern: string
  universal_quantifier: string
  property_statement: string
  requirement_ids: string[]
  hypothesis_code?: string
}

interface PropertyViewerProps {
  properties: Property[]
  requirements?: Array<{ id: string; text: string }>
  onEdit?: (property: Property) => void
  onDelete?: (propertyId: string) => void
  onGenerateTest?: (propertyId: string) => void
  editable?: boolean
}

// Property pattern metadata
const PROPERTY_PATTERNS = {
  round_trip: {
    name: 'Round-Trip',
    icon: <SyncOutlined />,
    color: 'blue',
    description: 'Encode then decode returns original value',
  },
  invariant: {
    name: 'Invariant',
    icon: <CheckCircleOutlined />,
    color: 'green',
    description: 'Property that must always hold true',
  },
  idempotence: {
    name: 'Idempotence',
    icon: <CodeOutlined />,
    color: 'purple',
    description: 'Applying operation twice equals applying once',
  },
  metamorphic: {
    name: 'Metamorphic',
    icon: <BulbOutlined />,
    color: 'orange',
    description: 'Related inputs produce related outputs',
  },
  oracle: {
    name: 'Oracle',
    icon: <EyeOutlined />,
    color: 'cyan',
    description: 'Compare against reference implementation',
  },
}

const PropertyViewer: React.FC<PropertyViewerProps> = ({
  properties,
  requirements = [],
  onEdit,
  onDelete,
  onGenerateTest,
  editable = false,
}) => {
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [codeModalVisible, setCodeModalVisible] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [form] = Form.useForm()

  const getPatternInfo = (pattern: string) => {
    return PROPERTY_PATTERNS[pattern as keyof typeof PROPERTY_PATTERNS] || {
      name: pattern,
      icon: <BulbOutlined />,
      color: 'default',
      description: 'Custom property pattern',
    }
  }

  const getRequirementText = (reqId: string) => {
    const req = requirements.find(r => r.id === reqId)
    return req?.text || reqId
  }

  const handleEdit = (property: Property) => {
    setSelectedProperty(property)
    form.setFieldsValue(property)
    setEditModalVisible(true)
  }

  const handleViewCode = (property: Property) => {
    setSelectedProperty(property)
    setCodeModalVisible(true)
  }

  const handleSaveEdit = async () => {
    try {
      const values = await form.validateFields()
      if (selectedProperty && onEdit) {
        onEdit({ ...selectedProperty, ...values })
      }
      setEditModalVisible(false)
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  if (properties.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="No properties generated yet"
      />
    )
  }

  return (
    <div className="property-viewer">
      <Collapse accordion>
        {properties.map(property => {
          const patternInfo = getPatternInfo(property.pattern)
          
          return (
            <Panel
              key={property.id}
              header={
                <Space>
                  <span style={{ color: patternInfo.color === 'default' ? undefined : patternInfo.color }}>
                    {patternInfo.icon}
                  </span>
                  <Text strong>{property.name}</Text>
                  <Tag color={patternInfo.color}>{patternInfo.name}</Tag>
                  <Badge 
                    count={property.requirement_ids.length} 
                    style={{ backgroundColor: '#1890ff' }}
                    title={`Links to ${property.requirement_ids.length} requirement(s)`}
                  />
                </Space>
              }
              extra={
                editable && (
                  <Space onClick={e => e.stopPropagation()}>
                    <Tooltip title="View Hypothesis Code">
                      <Button
                        size="small"
                        icon={<CodeOutlined />}
                        onClick={() => handleViewCode(property)}
                      />
                    </Tooltip>
                    <Tooltip title="Edit Property">
                      <Button
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(property)}
                      />
                    </Tooltip>
                    {onGenerateTest && (
                      <Tooltip title="Generate Test">
                        <Button
                          size="small"
                          type="primary"
                          icon={<CodeOutlined />}
                          onClick={() => onGenerateTest(property.id)}
                        >
                          Test
                        </Button>
                      </Tooltip>
                    )}
                    {onDelete && (
                      <Tooltip title="Delete">
                        <Button
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => onDelete(property.id)}
                        />
                      </Tooltip>
                    )}
                  </Space>
                )
              }
            >
              <div style={{ padding: '8px 0' }}>
                {/* Description */}
                <Paragraph type="secondary">{property.description}</Paragraph>
                
                <Divider style={{ margin: '12px 0' }} />
                
                {/* Universal Quantifier */}
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Text strong>Universal Quantifier:</Text>
                    <Card size="small" style={{ marginTop: 8, background: '#f6ffed' }}>
                      <Text style={{ fontStyle: 'italic' }}>
                        ∀ {property.universal_quantifier}
                      </Text>
                    </Card>
                  </Col>
                </Row>

                {/* Property Statement */}
                <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                  <Col span={24}>
                    <Text strong>Property Statement:</Text>
                    <Card size="small" style={{ marginTop: 8, background: '#e6f7ff' }}>
                      <Text code>{property.property_statement}</Text>
                    </Card>
                  </Col>
                </Row>

                {/* Linked Requirements */}
                <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                  <Col span={24}>
                    <Text strong>
                      <LinkOutlined /> Validates Requirements:
                    </Text>
                    <div style={{ marginTop: 8 }}>
                      {property.requirement_ids.map(reqId => (
                        <Tooltip key={reqId} title={getRequirementText(reqId)}>
                          <Tag 
                            color="blue" 
                            style={{ marginBottom: 4, cursor: 'help' }}
                          >
                            {reqId}
                          </Tag>
                        </Tooltip>
                      ))}
                    </div>
                  </Col>
                </Row>

                {/* Pattern Info */}
                <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                  <Col span={24}>
                    <Text strong>Pattern Type:</Text>
                    <div style={{ marginTop: 8 }}>
                      <Tag color={patternInfo.color} icon={patternInfo.icon}>
                        {patternInfo.name}
                      </Tag>
                      <Text type="secondary" style={{ marginLeft: 8 }}>
                        {patternInfo.description}
                      </Text>
                    </div>
                  </Col>
                </Row>

                {/* Hypothesis Code Preview */}
                {property.hypothesis_code && (
                  <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                    <Col span={24}>
                      <Space>
                        <Text strong>Hypothesis Code:</Text>
                        <Button
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => copyToClipboard(property.hypothesis_code || '')}
                        >
                          Copy
                        </Button>
                      </Space>
                      <pre style={{ 
                        marginTop: 8, 
                        padding: 12, 
                        background: '#1e1e1e', 
                        color: '#d4d4d4',
                        borderRadius: 4,
                        overflow: 'auto',
                        maxHeight: 200,
                        fontSize: 12,
                      }}>
                        {property.hypothesis_code}
                      </pre>
                    </Col>
                  </Row>
                )}
              </div>
            </Panel>
          )
        })}
      </Collapse>

      {/* Edit Modal */}
      <Modal
        title="Edit Property"
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => setEditModalVisible(false)}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Property Name"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item
            name="pattern"
            label="Pattern Type"
            rules={[{ required: true }]}
          >
            <Select>
              {Object.entries(PROPERTY_PATTERNS).map(([key, info]) => (
                <Option key={key} value={key}>
                  <Space>
                    {info.icon}
                    {info.name}
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="universal_quantifier"
            label="Universal Quantifier"
            rules={[{ required: true }]}
          >
            <Input prefix="∀" placeholder="any valid input x" />
          </Form.Item>
          <Form.Item
            name="property_statement"
            label="Property Statement"
            rules={[{ required: true }]}
          >
            <TextArea rows={3} placeholder="decode(encode(x)) == x" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Code View Modal */}
      <Modal
        title={`Hypothesis Code: ${selectedProperty?.name}`}
        open={codeModalVisible}
        onCancel={() => setCodeModalVisible(false)}
        width={800}
        footer={[
          <Button
            key="copy"
            icon={<CopyOutlined />}
            onClick={() => copyToClipboard(selectedProperty?.hypothesis_code || '')}
          >
            Copy Code
          </Button>,
          <Button key="close" onClick={() => setCodeModalVisible(false)}>
            Close
          </Button>,
        ]}
      >
        {selectedProperty?.hypothesis_code ? (
          <pre style={{ 
            padding: 16, 
            background: '#1e1e1e', 
            color: '#d4d4d4',
            borderRadius: 4,
            overflow: 'auto',
            maxHeight: 500,
            fontSize: 13,
            lineHeight: 1.5,
          }}>
            {selectedProperty.hypothesis_code}
          </pre>
        ) : (
          <Empty description="No Hypothesis code generated yet" />
        )}
      </Modal>
    </div>
  )
}

export default PropertyViewer
