import React, { useState } from 'react'
import { Card, Button, Space, Modal, Form, Select, InputNumber, Switch, message } from 'antd'
import { PlusOutlined, ReloadOutlined, SettingOutlined, DeleteOutlined } from '@ant-design/icons'
import { Environment, EnvironmentAction } from '../types/environment'

export interface EnvironmentCreationConfig {
  type: string
  architecture: string
  cpuCores: number
  memoryMB: number
  storageGB: number
  enableKVM?: boolean
  enableNestedVirtualization?: boolean
  customKernelVersion?: string
  additionalFeatures?: string[]
}

interface EnvironmentManagementControlsProps {
  selectedEnvironments: Environment[]
  onEnvironmentAction: (envId: string, action: EnvironmentAction) => Promise<void>
  onCreateEnvironment: (config: EnvironmentCreationConfig) => Promise<void>
  onBulkAction: (envIds: string[], action: EnvironmentAction) => Promise<void>
  isLoading: boolean
}

const EnvironmentManagementControls: React.FC<EnvironmentManagementControlsProps> = ({
  selectedEnvironments,
  onEnvironmentAction,
  onCreateEnvironment,
  onBulkAction,
  isLoading
}) => {
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  const handleCreateEnvironment = async (values: any) => {
    try {
      await onCreateEnvironment({
        type: values.type,
        architecture: values.architecture,
        cpuCores: values.cpuCores,
        memoryMB: values.memoryMB,
        storageGB: values.storageGB,
        enableKVM: values.enableKVM,
        enableNestedVirtualization: values.enableNestedVirtualization,
        customKernelVersion: values.customKernelVersion,
        additionalFeatures: values.additionalFeatures || []
      })
      setCreateModalVisible(false)
      form.resetFields()
      message.success('Environment creation initiated')
    } catch (error) {
      message.error('Failed to create environment')
    }
  }

  const handleBulkAction = async (actionType: string) => {
    if (selectedEnvironments.length === 0) {
      message.warning('Please select environments first')
      return
    }

    try {
      await onBulkAction(
        selectedEnvironments.map(env => env.id),
        { type: actionType as any }
      )
      message.success(`Bulk ${actionType} completed`)
    } catch (error) {
      message.error(`Failed to perform bulk ${actionType}`)
    }
  }

  return (
    <>
      <Card title="Environment Management" size="small">
        <Space wrap>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
            loading={isLoading}
          >
            Create Environment
          </Button>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={() => handleBulkAction('reset')}
            disabled={selectedEnvironments.length === 0}
            loading={isLoading}
          >
            Reset Selected ({selectedEnvironments.length})
          </Button>
          
          <Button
            icon={<SettingOutlined />}
            onClick={() => handleBulkAction('maintenance')}
            disabled={selectedEnvironments.length === 0}
            loading={isLoading}
          >
            Maintenance Mode
          </Button>
          
          <Button
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleBulkAction('offline')}
            disabled={selectedEnvironments.length === 0}
            loading={isLoading}
          >
            Take Offline
          </Button>
          
          <Button
            icon={<DeleteOutlined />}
            onClick={() => handleBulkAction('cleanup')}
            disabled={selectedEnvironments.length === 0}
            loading={isLoading}
            type="default"
          >
            Cleanup Selected ({selectedEnvironments.length})
          </Button>
        </Space>
      </Card>

      <Modal
        title="Create New Environment"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateEnvironment}
          initialValues={{
            type: 'qemu-x86',
            architecture: 'x86_64',
            cpuCores: 2,
            memoryMB: 2048,
            storageGB: 20,
            enableKVM: true,
            enableNestedVirtualization: false
          }}
        >
          <Form.Item
            name="type"
            label="Environment Type"
            rules={[{ required: true, message: 'Please select environment type' }]}
          >
            <Select>
              <Select.Option value="qemu-x86">QEMU x86_64</Select.Option>
              <Select.Option value="qemu-arm">QEMU ARM64</Select.Option>
              <Select.Option value="docker">Docker Container</Select.Option>
              <Select.Option value="physical">Physical Hardware</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="architecture"
            label="Architecture"
            rules={[{ required: true, message: 'Please select architecture' }]}
          >
            <Select>
              <Select.Option value="x86_64">x86_64</Select.Option>
              <Select.Option value="arm64">ARM64</Select.Option>
              <Select.Option value="riscv64">RISC-V 64</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="cpuCores"
            label="CPU Cores"
            rules={[{ required: true, message: 'Please specify CPU cores' }]}
          >
            <InputNumber min={1} max={16} />
          </Form.Item>

          <Form.Item
            name="memoryMB"
            label="Memory (MB)"
            rules={[{ required: true, message: 'Please specify memory' }]}
          >
            <InputNumber min={512} max={32768} step={512} />
          </Form.Item>

          <Form.Item
            name="storageGB"
            label="Storage (GB)"
            rules={[{ required: true, message: 'Please specify storage' }]}
          >
            <InputNumber min={10} max={500} step={10} />
          </Form.Item>

          <Form.Item name="enableKVM" valuePropName="checked">
            <Switch /> Enable KVM Acceleration
          </Form.Item>

          <Form.Item name="enableNestedVirtualization" valuePropName="checked">
            <Switch /> Enable Nested Virtualization
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default EnvironmentManagementControls