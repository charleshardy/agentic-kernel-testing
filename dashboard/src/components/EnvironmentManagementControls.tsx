import React, { useState } from 'react'
import { 
  Button, 
  Modal, 
  Form, 
  Select, 
  InputNumber, 
  Switch, 
  Space, 
  Typography, 
  Alert, 
  Progress, 
  Descriptions,
  Popconfirm,
  notification,
  Divider
} from 'antd'
import { 
  PlusOutlined, 
  ToolOutlined, 
  StopOutlined, 
  ReloadOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentAction 
} from '../types/environment'

const { Title, Text } = Typography
const { Option } = Select

export interface EnvironmentManagementControlsProps {
  selectedEnvironments: Environment[]
  onEnvironmentAction: (envId: string, action: EnvironmentAction) => Promise<void>
  onCreateEnvironment: (config: EnvironmentCreationConfig) => Promise<void>
  onBulkAction: (envIds: string[], action: EnvironmentAction) => Promise<void>
  isLoading?: boolean
}

export interface EnvironmentCreationConfig {
  type: EnvironmentType
  architecture: string
  cpuCores: number
  memoryMB: number
  storageGB: number
  enableKVM?: boolean
  enableNestedVirtualization?: boolean
  customKernelVersion?: string
  additionalFeatures?: string[]
}

interface ActionProgress {
  envId: string
  action: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message?: string
}

/**
 * Environment Management Controls Component
 * Provides controls for creating, managing, and performing actions on environments
 */
const EnvironmentManagementControls: React.FC<EnvironmentManagementControlsProps> = ({
  selectedEnvironments,
  onEnvironmentAction,
  onCreateEnvironment,
  onBulkAction,
  isLoading = false
}) => {
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [actionProgress, setActionProgress] = useState<ActionProgress[]>([])
  const [form] = Form.useForm()

  // Handle single environment actions with confirmation
  const handleEnvironmentAction = async (environment: Environment, actionType: string) => {
    const action: EnvironmentAction = { type: actionType as any }
    
    try {
      // Add progress tracking
      const progressId = `${environment.id}-${actionType}`
      setActionProgress(prev => [...prev, {
        envId: environment.id,
        action: actionType,
        status: 'running',
        progress: 0,
        message: `Starting ${actionType}...`
      }])

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setActionProgress(prev => prev.map(p => 
          p.envId === environment.id && p.action === actionType
            ? { ...p, progress: Math.min(p.progress + 20, 90) }
            : p
        ))
      }, 500)

      await onEnvironmentAction(environment.id, action)

      // Complete progress
      clearInterval(progressInterval)
      setActionProgress(prev => prev.map(p => 
        p.envId === environment.id && p.action === actionType
          ? { ...p, status: 'completed', progress: 100, message: `${actionType} completed successfully` }
          : p
      ))

      notification.success({
        message: 'Action Completed',
        description: `Environment ${environment.id.slice(0, 8)}... ${actionType} completed successfully`,
        duration: 3
      })

      // Remove progress after delay
      setTimeout(() => {
        setActionProgress(prev => prev.filter(p => 
          !(p.envId === environment.id && p.action === actionType)
        ))
      }, 3000)

    } catch (error) {
      setActionProgress(prev => prev.map(p => 
        p.envId === environment.id && p.action === actionType
          ? { ...p, status: 'failed', progress: 100, message: `${actionType} failed: ${error}` }
          : p
      ))

      notification.error({
        message: 'Action Failed',
        description: `Failed to ${actionType} environment: ${error}`,
        duration: 5
      })
    }
  }

  // Handle bulk actions with confirmation
  const handleBulkAction = async (actionType: string) => {
    if (selectedEnvironments.length === 0) {
      notification.warning({
        message: 'No Environments Selected',
        description: 'Please select one or more environments to perform bulk actions.',
        duration: 3
      })
      return
    }

    const action: EnvironmentAction = { type: actionType as any }
    const envIds = selectedEnvironments.map(env => env.id)

    try {
      await onBulkAction(envIds, action)
      
      notification.success({
        message: 'Bulk Action Completed',
        description: `${actionType} completed for ${envIds.length} environments`,
        duration: 3
      })
    } catch (error) {
      notification.error({
        message: 'Bulk Action Failed',
        description: `Failed to ${actionType} environments: ${error}`,
        duration: 5
      })
    }
  }

  // Handle environment creation
  const handleCreateEnvironment = async () => {
    try {
      const values = await form.validateFields()
      
      const config: EnvironmentCreationConfig = {
        type: values.type,
        architecture: values.architecture,
        cpuCores: values.cpuCores,
        memoryMB: values.memoryMB,
        storageGB: values.storageGB,
        enableKVM: values.enableKVM || false,
        enableNestedVirtualization: values.enableNestedVirtualization || false,
        customKernelVersion: values.customKernelVersion,
        additionalFeatures: values.additionalFeatures || []
      }

      await onCreateEnvironment(config)
      
      notification.success({
        message: 'Environment Creation Started',
        description: 'New environment is being provisioned. This may take several minutes.',
        duration: 5
      })

      setCreateModalVisible(false)
      form.resetFields()
    } catch (error) {
      notification.error({
        message: 'Environment Creation Failed',
        description: `Failed to create environment: ${error}`,
        duration: 5
      })
    }
  }

  // Get action button props based on environment status
  const getActionButtonProps = (environment: Environment, actionType: string) => {
    const progress = actionProgress.find(p => p.envId === environment.id && p.action === actionType)
    
    if (progress) {
      return {
        loading: progress.status === 'running',
        disabled: true,
        icon: progress.status === 'completed' ? <CheckCircleOutlined /> : 
              progress.status === 'failed' ? <CloseCircleOutlined /> : undefined
      }
    }

    switch (actionType) {
      case 'reset':
        return {
          disabled: environment.status === EnvironmentStatus.RUNNING || 
                   environment.status === EnvironmentStatus.ALLOCATING,
          danger: true
        }
      case 'maintenance':
        return {
          disabled: environment.status === EnvironmentStatus.MAINTENANCE,
          type: 'default' as const
        }
      case 'offline':
        return {
          disabled: environment.status === EnvironmentStatus.OFFLINE,
          danger: true
        }
      case 'cleanup':
        return {
          disabled: environment.status === EnvironmentStatus.CLEANUP,
          type: 'primary' as const
        }
      default:
        return {}
    }
  }

  return (
    <div style={{ padding: '16px', background: '#fafafa', borderRadius: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <Title level={4} style={{ margin: 0 }}>
          Environment Management
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
          loading={isLoading}
        >
          Create Environment
        </Button>
      </div>

      {/* Single Environment Actions */}
      {selectedEnvironments.length === 1 && (
        <div style={{ marginBottom: '16px' }}>
          <Text strong>Actions for: {selectedEnvironments[0].id.slice(0, 12)}...</Text>
          <div style={{ marginTop: '8px' }}>
            <Space wrap>
              <Popconfirm
                title="Reset Environment"
                description="This will reset the environment to a clean state. All running tests will be terminated."
                onConfirm={() => handleEnvironmentAction(selectedEnvironments[0], 'reset')}
                okText="Reset"
                cancelText="Cancel"
                icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
              >
                <Button
                  icon={<ReloadOutlined />}
                  {...getActionButtonProps(selectedEnvironments[0], 'reset')}
                >
                  Reset
                </Button>
              </Popconfirm>

              <Button
                icon={<ToolOutlined />}
                onClick={() => handleEnvironmentAction(selectedEnvironments[0], 'maintenance')}
                {...getActionButtonProps(selectedEnvironments[0], 'maintenance')}
              >
                Maintenance
              </Button>

              <Popconfirm
                title="Take Environment Offline"
                description="This will take the environment offline and prevent new test allocations."
                onConfirm={() => handleEnvironmentAction(selectedEnvironments[0], 'offline')}
                okText="Take Offline"
                cancelText="Cancel"
                icon={<ExclamationCircleOutlined style={{ color: 'orange' }} />}
              >
                <Button
                  icon={<StopOutlined />}
                  {...getActionButtonProps(selectedEnvironments[0], 'offline')}
                >
                  Take Offline
                </Button>
              </Popconfirm>

              <Button
                icon={<DeleteOutlined />}
                onClick={() => handleEnvironmentAction(selectedEnvironments[0], 'cleanup')}
                {...getActionButtonProps(selectedEnvironments[0], 'cleanup')}
              >
                Force Cleanup
              </Button>
            </Space>
          </div>

          {/* Show progress for current environment */}
          {actionProgress
            .filter(p => p.envId === selectedEnvironments[0].id)
            .map(progress => (
              <div key={`${progress.envId}-${progress.action}`} style={{ marginTop: '12px' }}>
                <Text type="secondary">{progress.message}</Text>
                <Progress
                  percent={progress.progress}
                  status={progress.status === 'failed' ? 'exception' : 
                          progress.status === 'completed' ? 'success' : 'active'}
                  size="small"
                />
              </div>
            ))}
        </div>
      )}

      {/* Bulk Actions */}
      {selectedEnvironments.length > 1 && (
        <div style={{ marginBottom: '16px' }}>
          <Text strong>Bulk Actions ({selectedEnvironments.length} environments selected)</Text>
          <div style={{ marginTop: '8px' }}>
            <Space wrap>
              <Popconfirm
                title={`Reset ${selectedEnvironments.length} Environments`}
                description="This will reset all selected environments. All running tests will be terminated."
                onConfirm={() => handleBulkAction('reset')}
                okText="Reset All"
                cancelText="Cancel"
                icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
              >
                <Button icon={<ReloadOutlined />} danger>
                  Bulk Reset
                </Button>
              </Popconfirm>

              <Button
                icon={<ToolOutlined />}
                onClick={() => handleBulkAction('maintenance')}
              >
                Bulk Maintenance
              </Button>

              <Popconfirm
                title={`Take ${selectedEnvironments.length} Environments Offline`}
                description="This will take all selected environments offline."
                onConfirm={() => handleBulkAction('offline')}
                okText="Take All Offline"
                cancelText="Cancel"
                icon={<ExclamationCircleOutlined style={{ color: 'orange' }} />}
              >
                <Button icon={<StopOutlined />} danger>
                  Bulk Offline
                </Button>
              </Popconfirm>

              <Button
                icon={<DeleteOutlined />}
                onClick={() => handleBulkAction('cleanup')}
                type="primary"
              >
                Bulk Cleanup
              </Button>
            </Space>
          </div>
        </div>
      )}

      {/* Environment Creation Modal */}
      <Modal
        title="Create New Environment"
        open={createModalVisible}
        onOk={handleCreateEnvironment}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        width={600}
        okText="Create Environment"
        cancelText="Cancel"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            type: EnvironmentType.QEMU_X86,
            architecture: 'x86_64',
            cpuCores: 2,
            memoryMB: 4096,
            storageGB: 20,
            enableKVM: true,
            enableNestedVirtualization: false,
            additionalFeatures: []
          }}
        >
          <Form.Item
            name="type"
            label="Environment Type"
            rules={[{ required: true, message: 'Please select environment type' }]}
          >
            <Select>
              <Option value={EnvironmentType.QEMU_X86}>QEMU x86_64</Option>
              <Option value={EnvironmentType.QEMU_ARM}>QEMU ARM64</Option>
              <Option value={EnvironmentType.DOCKER}>Docker Container</Option>
              <Option value={EnvironmentType.PHYSICAL}>Physical Hardware</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="architecture"
            label="Architecture"
            rules={[{ required: true, message: 'Please select architecture' }]}
          >
            <Select>
              <Option value="x86_64">x86_64</Option>
              <Option value="arm64">ARM64</Option>
              <Option value="riscv64">RISC-V 64</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="cpuCores"
            label="CPU Cores"
            rules={[{ required: true, message: 'Please specify CPU cores' }]}
          >
            <InputNumber min={1} max={32} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="memoryMB"
            label="Memory (MB)"
            rules={[{ required: true, message: 'Please specify memory size' }]}
          >
            <InputNumber min={512} max={32768} step={512} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="storageGB"
            label="Storage (GB)"
            rules={[{ required: true, message: 'Please specify storage size' }]}
          >
            <InputNumber min={10} max={500} step={10} style={{ width: '100%' }} />
          </Form.Item>

          <Divider />

          <Form.Item name="enableKVM" valuePropName="checked">
            <Switch /> Enable KVM Acceleration (x86_64 only)
          </Form.Item>

          <Form.Item name="enableNestedVirtualization" valuePropName="checked">
            <Switch /> Enable Nested Virtualization
          </Form.Item>

          <Form.Item
            name="customKernelVersion"
            label="Custom Kernel Version (optional)"
          >
            <Select allowClear placeholder="Use default kernel">
              <Option value="6.1.0">6.1.0</Option>
              <Option value="6.0.0">6.0.0</Option>
              <Option value="5.19.0">5.19.0</Option>
              <Option value="5.15.0">5.15.0 LTS</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="additionalFeatures"
            label="Additional Features"
          >
            <Select mode="multiple" placeholder="Select additional features">
              <Option value="gdb">GDB Debugging</Option>
              <Option value="perf">Performance Profiling</Option>
              <Option value="strace">System Call Tracing</Option>
              <Option value="tcpdump">Network Packet Capture</Option>
              <Option value="valgrind">Memory Debugging</Option>
            </Select>
          </Form.Item>
        </Form>

        <Alert
          message="Environment Provisioning"
          description="Creating a new environment may take 5-10 minutes depending on the configuration. You will be notified when the environment is ready."
          type="info"
          showIcon
          style={{ marginTop: '16px' }}
        />
      </Modal>

      {/* Selected Environments Summary */}
      {selectedEnvironments.length > 0 && (
        <div style={{ marginTop: '16px', padding: '12px', background: '#f0f2f5', borderRadius: '4px' }}>
          <Text strong>Selected Environments ({selectedEnvironments.length})</Text>
          <div style={{ marginTop: '8px' }}>
            {selectedEnvironments.map(env => (
              <div key={env.id} style={{ marginBottom: '4px' }}>
                <Text code>{env.id.slice(0, 12)}...</Text>
                <Text type="secondary" style={{ marginLeft: '8px' }}>
                  {env.type} - {env.status}
                </Text>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EnvironmentManagementControls