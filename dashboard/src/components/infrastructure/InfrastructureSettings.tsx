import React from 'react'
import {
  Card, Form, Input, InputNumber, Select, Switch, Button, Space,
  Typography, Row, Col, Divider, message
} from 'antd'
import {
  SettingOutlined, SaveOutlined, BellOutlined, ClockCircleOutlined,
  DeleteOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select

interface InfrastructureConfig {
  health_check_interval_seconds: number
  alert_thresholds: {
    build_server_disk_warning_percent: number
    host_cpu_warning_percent: number
    host_memory_warning_percent: number
    board_temperature_warning_celsius: number
  }
  notifications: {
    email_enabled: boolean
    email_recipients: string[]
    webhook_enabled: boolean
    webhook_url: string
  }
  artifact_retention: {
    max_age_days: number
    max_total_size_gb: number
    keep_latest_per_branch: number
  }
  selection_strategy: {
    default_build_server: 'load_balanced' | 'round_robin' | 'least_jobs'
    default_host: 'load_balanced' | 'round_robin' | 'most_available'
    default_board: 'round_robin' | 'least_used'
  }
}

/**
 * Infrastructure Settings Page
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 2.4**: Configure disk space warning thresholds
 * **Requirement 9.4**: Configure host utilization thresholds
 * **Requirement 16.1-16.5**: Configure alert notifications
 */
const InfrastructureSettings: React.FC = () => {
  const queryClient = useQueryClient()
  const [form] = Form.useForm()

  const { data: config, isLoading } = useQuery<InfrastructureConfig>(
    'infrastructure-config',
    async () => {
      const response = await fetch('/api/v1/infrastructure/config')
      if (!response.ok) throw new Error('Failed to fetch config')
      return response.json()
    },
    { onSuccess: (data) => form.setFieldsValue(flattenConfig(data)) }
  )

  const saveMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(unflattenConfig(data))
      })
      if (!response.ok) throw new Error('Failed to save config')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('infrastructure-config')
        message.success('Settings saved successfully')
      },
      onError: () => message.error('Failed to save settings')
    }
  )

  const flattenConfig = (cfg: InfrastructureConfig) => ({
    health_check_interval_seconds: cfg.health_check_interval_seconds,
    build_server_disk_warning_percent: cfg.alert_thresholds.build_server_disk_warning_percent,
    host_cpu_warning_percent: cfg.alert_thresholds.host_cpu_warning_percent,
    host_memory_warning_percent: cfg.alert_thresholds.host_memory_warning_percent,
    board_temperature_warning_celsius: cfg.alert_thresholds.board_temperature_warning_celsius,
    email_enabled: cfg.notifications.email_enabled,
    email_recipients: cfg.notifications.email_recipients.join(', '),
    webhook_enabled: cfg.notifications.webhook_enabled,
    webhook_url: cfg.notifications.webhook_url,
    max_age_days: cfg.artifact_retention.max_age_days,
    max_total_size_gb: cfg.artifact_retention.max_total_size_gb,
    keep_latest_per_branch: cfg.artifact_retention.keep_latest_per_branch,
    default_build_server: cfg.selection_strategy.default_build_server,
    default_host: cfg.selection_strategy.default_host,
    default_board: cfg.selection_strategy.default_board
  })

  const unflattenConfig = (data: any): InfrastructureConfig => ({
    health_check_interval_seconds: data.health_check_interval_seconds,
    alert_thresholds: {
      build_server_disk_warning_percent: data.build_server_disk_warning_percent,
      host_cpu_warning_percent: data.host_cpu_warning_percent,
      host_memory_warning_percent: data.host_memory_warning_percent,
      board_temperature_warning_celsius: data.board_temperature_warning_celsius
    },
    notifications: {
      email_enabled: data.email_enabled,
      email_recipients: data.email_recipients?.split(',').map((e: string) => e.trim()).filter(Boolean) || [],
      webhook_enabled: data.webhook_enabled,
      webhook_url: data.webhook_url || ''
    },
    artifact_retention: {
      max_age_days: data.max_age_days,
      max_total_size_gb: data.max_total_size_gb,
      keep_latest_per_branch: data.keep_latest_per_branch
    },
    selection_strategy: {
      default_build_server: data.default_build_server,
      default_host: data.default_host,
      default_board: data.default_board
    }
  })

  return (
    <div style={{ padding: '24px', maxWidth: 900 }}>
      <Title level={3}><SettingOutlined /> Infrastructure Settings</Title>
      
      <Form form={form} layout="vertical" onFinish={(values) => saveMutation.mutate(values)}>
        <Card title={<><ClockCircleOutlined /> Health Monitoring</>} style={{ marginBottom: 16 }}>
          <Form.Item name="health_check_interval_seconds" label="Health Check Interval (seconds)" initialValue={30}>
            <InputNumber min={10} max={300} style={{ width: 200 }} />
          </Form.Item>
        </Card>

        <Card title={<><BellOutlined /> Alert Thresholds</>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="build_server_disk_warning_percent" label="Build Server Disk Warning (%)" initialValue={80}>
                <InputNumber min={50} max={95} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="host_cpu_warning_percent" label="Host CPU Warning (%)" initialValue={85}>
                <InputNumber min={50} max={95} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="host_memory_warning_percent" label="Host Memory Warning (%)" initialValue={85}>
                <InputNumber min={50} max={95} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="board_temperature_warning_celsius" label="Board Temperature Warning (°C)" initialValue={70}>
                <InputNumber min={40} max={90} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title={<><BellOutlined /> Notifications</>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="email_enabled" label="Email Notifications" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="email_recipients" label="Email Recipients (comma-separated)">
                <Input placeholder="admin@example.com, ops@example.com" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="webhook_enabled" label="Webhook Notifications" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="webhook_url" label="Webhook URL">
                <Input placeholder="https://hooks.slack.com/..." />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title={<><DeleteOutlined /> Artifact Retention</>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="max_age_days" label="Max Age (days)" initialValue={30}>
                <InputNumber min={1} max={365} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_total_size_gb" label="Max Total Size (GB)" initialValue={500}>
                <InputNumber min={10} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="keep_latest_per_branch" label="Keep Latest Per Branch" initialValue={5}>
                <InputNumber min={1} max={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title={<><ThunderboltOutlined /> Selection Strategy</>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="default_build_server" label="Build Server Strategy" initialValue="load_balanced">
                <Select>
                  <Option value="load_balanced">Load Balanced</Option>
                  <Option value="round_robin">Round Robin</Option>
                  <Option value="least_jobs">Least Jobs</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="default_host" label="Host Strategy" initialValue="load_balanced">
                <Select>
                  <Option value="load_balanced">Load Balanced</Option>
                  <Option value="round_robin">Round Robin</Option>
                  <Option value="most_available">Most Available</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="default_board" label="Board Strategy" initialValue="round_robin">
                <Select>
                  <Option value="round_robin">Round Robin</Option>
                  <Option value="least_used">Least Used</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saveMutation.isLoading}>
            Save Settings
          </Button>
          <Button onClick={() => form.resetFields()}>Reset</Button>
        </Space>
      </Form>
    </div>
  )
}

export default InfrastructureSettings
