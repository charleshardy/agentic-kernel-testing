import React from 'react'
import { Modal, Form, Select, InputNumber, Switch, Space, Button } from 'antd'
import { Environment, HardwareRequirements, AllocationPreferences } from '../types/environment'

interface EnvironmentPreferenceModalProps {
  visible: boolean
  onClose: () => void
  testId?: string
  availableEnvironments: Environment[]
  onApplyPreferences: (requirements: HardwareRequirements, preferences: AllocationPreferences) => void
}

const EnvironmentPreferenceModal: React.FC<EnvironmentPreferenceModalProps> = ({
  visible,
  onClose,
  testId,
  availableEnvironments,
  onApplyPreferences
}) => {
  const [form] = Form.useForm()

  const handleSubmit = (values: any) => {
    const requirements: HardwareRequirements = {
      architecture: values.architecture,
      minMemoryMB: values.minMemoryMB,
      minCpuCores: values.minCpuCores,
      requiredFeatures: values.requiredFeatures || [],
      preferredEnvironmentType: values.preferredEnvironmentType,
      isolationLevel: values.isolationLevel
    }

    const preferences: AllocationPreferences = {
      environmentType: values.environmentType,
      architecture: values.architecture,
      maxWaitTime: values.maxWaitTime,
      allowSharedEnvironment: values.allowSharedEnvironment,
      requireDedicatedResources: values.requireDedicatedResources
    }

    onApplyPreferences(requirements, preferences)
    onClose()
  }

  return (
    <Modal
      title="Environment Preferences"
      open={visible}
      onCancel={onClose}
      onOk={() => form.submit()}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          architecture: 'x86_64',
          minCpuCores: 1,
          minMemoryMB: 1024,
          isolationLevel: 'vm',
          allowSharedEnvironment: true,
          requireDedicatedResources: false
        }}
      >
        <Form.Item
          name="architecture"
          label="Architecture"
          rules={[{ required: true }]}
        >
          <Select>
            <Select.Option value="x86_64">x86_64</Select.Option>
            <Select.Option value="arm64">ARM64</Select.Option>
            <Select.Option value="riscv64">RISC-V 64</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="minCpuCores"
          label="Minimum CPU Cores"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} max={16} />
        </Form.Item>

        <Form.Item
          name="minMemoryMB"
          label="Minimum Memory (MB)"
          rules={[{ required: true }]}
        >
          <InputNumber min={512} max={32768} step={512} />
        </Form.Item>

        <Form.Item
          name="isolationLevel"
          label="Isolation Level"
          rules={[{ required: true }]}
        >
          <Select>
            <Select.Option value="none">None</Select.Option>
            <Select.Option value="process">Process</Select.Option>
            <Select.Option value="container">Container</Select.Option>
            <Select.Option value="vm">Virtual Machine</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item name="allowSharedEnvironment" valuePropName="checked">
          <Switch /> Allow Shared Environment
        </Form.Item>

        <Form.Item name="requireDedicatedResources" valuePropName="checked">
          <Switch /> Require Dedicated Resources
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default EnvironmentPreferenceModal