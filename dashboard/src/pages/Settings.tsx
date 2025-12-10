import React, { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  message,
  InputNumber,
  Alert,
} from 'antd'
import {
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography
const { TextArea } = Input

interface SettingsProps {}

const Settings: React.FC<SettingsProps> = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSave = async (values: any) => {
    setLoading(true)
    try {
      // Simulate API call to save settings
      await new Promise(resolve => setTimeout(resolve, 1000))
      message.success('Settings saved successfully')
    } catch (error) {
      message.error('Failed to save settings')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    form.resetFields()
    message.info('Settings reset to defaults')
  }

  return (
    <div>
      <Title level={2}>Settings</Title>
      
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          // System settings
          max_concurrent_tests: 50,
          test_timeout: 3600,
          retry_attempts: 3,
          cleanup_interval: 300,
          
          // Notification settings
          email_notifications: true,
          slack_notifications: false,
          webhook_notifications: true,
          notification_threshold: 'critical',
          
          // Performance settings
          performance_monitoring: true,
          coverage_tracking: true,
          security_scanning: true,
          auto_retry_failed: true,
          
          // API settings
          api_rate_limit: 1000,
          api_timeout: 30,
          
          // Dashboard settings
          refresh_interval: 30,
          chart_animation: true,
          dark_mode: false,
        }}
      >
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            {/* System Configuration */}
            <Card title="System Configuration" style={{ marginBottom: 24 }}>
              <Form.Item
                name="max_concurrent_tests"
                label="Maximum Concurrent Tests"
                help="Maximum number of tests that can run simultaneously"
              >
                <InputNumber min={1} max={200} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="test_timeout"
                label="Default Test Timeout (seconds)"
                help="Default timeout for test execution"
              >
                <InputNumber min={60} max={7200} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="retry_attempts"
                label="Retry Attempts"
                help="Number of times to retry failed tests"
              >
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="cleanup_interval"
                label="Cleanup Interval (seconds)"
                help="How often to clean up idle resources"
              >
                <InputNumber min={60} max={3600} style={{ width: '100%' }} />
              </Form.Item>
            </Card>

            {/* Performance Settings */}
            <Card title="Performance & Monitoring" style={{ marginBottom: 24 }}>
              <Form.Item
                name="performance_monitoring"
                label="Performance Monitoring"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="coverage_tracking"
                label="Coverage Tracking"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="security_scanning"
                label="Security Scanning"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="auto_retry_failed"
                label="Auto-retry Failed Tests"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            {/* Notification Settings */}
            <Card title="Notification Settings" style={{ marginBottom: 24 }}>
              <Form.Item
                name="email_notifications"
                label="Email Notifications"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="slack_notifications"
                label="Slack Notifications"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="webhook_notifications"
                label="Webhook Notifications"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="notification_threshold"
                label="Notification Threshold"
                help="Minimum severity level for notifications"
              >
                <Select
                  options={[
                    { label: 'All', value: 'all' },
                    { label: 'Info', value: 'info' },
                    { label: 'Warning', value: 'warning' },
                    { label: 'Error', value: 'error' },
                    { label: 'Critical', value: 'critical' },
                  ]}
                />
              </Form.Item>

              <Form.Item
                name="email_recipients"
                label="Email Recipients"
                help="Comma-separated list of email addresses"
              >
                <TextArea rows={3} placeholder="admin@example.com, dev@example.com" />
              </Form.Item>

              <Form.Item
                name="slack_webhook"
                label="Slack Webhook URL"
              >
                <Input placeholder="https://hooks.slack.com/services/..." />
              </Form.Item>
            </Card>

            {/* API Settings */}
            <Card title="API Configuration" style={{ marginBottom: 24 }}>
              <Form.Item
                name="api_rate_limit"
                label="API Rate Limit (requests/hour)"
              >
                <InputNumber min={100} max={10000} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="api_timeout"
                label="API Timeout (seconds)"
              >
                <InputNumber min={5} max={300} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="cors_origins"
                label="CORS Origins"
                help="Allowed origins for CORS (one per line)"
              >
                <TextArea 
                  rows={3} 
                  placeholder="http://localhost:3000&#10;https://dashboard.example.com" 
                />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        {/* Dashboard Settings */}
        <Card title="Dashboard Settings" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <Form.Item
                name="refresh_interval"
                label="Refresh Interval (seconds)"
                help="How often to refresh dashboard data"
              >
                <Select
                  options={[
                    { label: '10 seconds', value: 10 },
                    { label: '30 seconds', value: 30 },
                    { label: '1 minute', value: 60 },
                    { label: '5 minutes', value: 300 },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item
                name="chart_animation"
                label="Chart Animations"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item
                name="dark_mode"
                label="Dark Mode"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Environment Configuration */}
        <Card title="Environment Configuration" style={{ marginBottom: 24 }}>
          <Alert
            message="Environment Settings"
            description="Configure default settings for test execution environments. These can be overridden per test submission."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="default_architecture"
                label="Default Architecture"
              >
                <Select
                  options={[
                    { label: 'x86_64', value: 'x86_64' },
                    { label: 'arm64', value: 'arm64' },
                    { label: 'riscv64', value: 'riscv64' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="default_memory"
                label="Default Memory (MB)"
              >
                <InputNumber min={512} max={32768} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="environment_cleanup_policy"
            label="Environment Cleanup Policy"
          >
            <Select
              options={[
                { label: 'Immediate', value: 'immediate' },
                { label: 'After 5 minutes', value: '5min' },
                { label: 'After 30 minutes', value: '30min' },
                { label: 'Manual', value: 'manual' },
              ]}
            />
          </Form.Item>
        </Card>

        {/* Security Settings */}
        <Card title="Security Settings" style={{ marginBottom: 24 }}>
          <Form.Item
            name="require_authentication"
            label="Require Authentication"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="session_timeout"
            label="Session Timeout (minutes)"
          >
            <InputNumber min={15} max={1440} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="allowed_ip_ranges"
            label="Allowed IP Ranges"
            help="CIDR notation, one per line (leave empty to allow all)"
          >
            <TextArea 
              rows={3} 
              placeholder="192.168.1.0/24&#10;10.0.0.0/8" 
            />
          </Form.Item>
        </Card>

        {/* Action Buttons */}
        <Card>
          <Space>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              htmlType="submit"
              loading={loading}
            >
              Save Settings
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              Reset to Defaults
            </Button>
          </Space>
        </Card>
      </Form>
    </div>
  )
}

export default Settings