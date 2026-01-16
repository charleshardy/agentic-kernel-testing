import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Modal, Form, Input, Select,
  Typography, Row, Col, Statistic, Badge, Tooltip, Progress, Tabs
} from 'antd'
import {
  BuildOutlined, PlusOutlined, ReloadOutlined, StopOutlined,
  ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import BuildFlowVisualization from './BuildFlowVisualization'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input

interface BuildJob {
  id: string
  repository_url: string
  branch: string
  commit_hash?: string
  architecture: string
  build_server_id?: string
  status: 'queued' | 'building' | 'completed' | 'failed' | 'cancelled'
  progress_percent: number
  estimated_completion?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

interface BuildFlowStage {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  error_message?: string
}

interface BuildFlowData {
  job_id: string
  overall_status: string
  stages: BuildFlowStage[]
}

/**
 * Build Job Dashboard
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 3.1**: Submit build jobs with repository, branch, architecture
 * **Requirement 3.5**: View build logs and progress
 */
interface BuildTemplate {
  id: string
  name: string
  description?: string
  build_mode: string
  workspace_root?: string
  output_directory?: string
  keep_workspace: boolean
  git_depth?: number
  git_submodules: boolean
  kernel_config?: string
  extra_make_args?: string[]
  artifact_patterns?: string[]
  pre_build_commands?: string[]
  build_commands?: string[]
  post_build_commands?: string[]
  custom_env?: Record<string, string>
  created_at: string
  updated_at: string
}

const BuildJobDashboard: React.FC = () => {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedJob, setSelectedJob] = useState<BuildJob | null>(null)
  const [isSaveTemplateModalVisible, setIsSaveTemplateModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [templateForm] = Form.useForm()

  const { data: jobs = [], isLoading, refetch } = useQuery<BuildJob[]>(
    'build-jobs',
    async () => {
      const response = await fetch('/api/v1/infrastructure/build-jobs')
      if (!response.ok) throw new Error('Failed to fetch build jobs')
      return response.json()
    },
    { refetchInterval: 5000 }
  )

  const { data: buildServers = [] } = useQuery<any[]>('build-servers', async () => {
    const response = await fetch('/api/v1/infrastructure/build-servers')
    if (!response.ok) throw new Error('Failed to fetch build servers')
    return response.json()
  })

  // Fetch build templates
  const { data: templates = [] } = useQuery<BuildTemplate[]>('build-templates', async () => {
    const response = await fetch('/api/v1/infrastructure/build-templates')
    if (!response.ok) throw new Error('Failed to fetch build templates')
    return response.json()
  })

  // Fetch build flow data for selected job
  const { data: buildFlow } = useQuery<BuildFlowData>(
    ['build-flow', selectedJob?.id],
    async () => {
      if (!selectedJob) return null
      const response = await fetch(`/api/v1/infrastructure/build-jobs/${selectedJob.id}/flow`)
      if (!response.ok) throw new Error('Failed to fetch build flow')
      return response.json()
    },
    {
      enabled: !!selectedJob,
      refetchInterval: selectedJob?.status === 'building' ? 3000 : false
    }
  )

  const submitMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/build-jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to submit build job')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('build-jobs')
        setIsModalVisible(false)
        form.resetFields()
      }
    }
  )

  const cancelMutation = useMutation(
    async (jobId: string) => {
      const response = await fetch(`/api/v1/infrastructure/build-jobs/${jobId}/cancel`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to cancel build job')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('build-jobs') }
  )

  const saveTemplateMutation = useMutation(
    async (data: any) => {
      const response = await fetch('/api/v1/infrastructure/build-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to save template')
      return response.json()
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('build-templates')
        setIsSaveTemplateModalVisible(false)
        templateForm.resetFields()
      }
    }
  )

  const deleteTemplateMutation = useMutation(
    async (templateId: string) => {
      const response = await fetch(`/api/v1/infrastructure/build-templates/${templateId}`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Failed to delete template')
      return response.json()
    },
    { onSuccess: () => queryClient.invalidateQueries('build-templates') }
  )

  const loadTemplate = (template: BuildTemplate) => {
    // Convert template data to form values
    const formValues: any = {
      build_mode: template.build_mode,
      workspace_root: template.workspace_root,
      output_directory: template.output_directory,
      keep_workspace: template.keep_workspace,
      git_depth: template.git_depth,
      git_submodules: template.git_submodules
    }

    if (template.build_mode === 'kernel') {
      formValues.kernel_config = template.kernel_config
      formValues.extra_make_args = template.extra_make_args?.join(', ')
      formValues.artifact_patterns = template.artifact_patterns?.join('\n')
    } else {
      formValues.pre_build_commands = template.pre_build_commands?.join('\n')
      formValues.build_commands = template.build_commands?.join('\n')
      formValues.post_build_commands = template.post_build_commands?.join('\n')
    }

    if (template.custom_env) {
      formValues.custom_env = JSON.stringify(template.custom_env, null, 2)
    }

    form.setFieldsValue(formValues)
  }

  const saveCurrentAsTemplate = () => {
    const currentValues = form.getFieldsValue()
    templateForm.setFieldsValue({
      name: '',
      description: '',
      ...currentValues
    })
    setIsSaveTemplateModalVisible(true)
  }

  const getStatusBadge = (status: string) => {
    const config: Record<string, { status: any; text: string; icon: React.ReactNode }> = {
      queued: { status: 'default', text: 'Queued', icon: <ClockCircleOutlined /> },
      building: { status: 'processing', text: 'Building', icon: <BuildOutlined spin /> },
      completed: { status: 'success', text: 'Completed', icon: <CheckCircleOutlined /> },
      failed: { status: 'error', text: 'Failed', icon: <CloseCircleOutlined /> },
      cancelled: { status: 'warning', text: 'Cancelled', icon: <StopOutlined /> }
    }
    const c = config[status] || { status: 'default', text: status, icon: null }
    return <Badge status={c.status} text={<Space>{c.icon}{c.text}</Space>} />
  }

  const activeJobs = jobs.filter(j => j.status === 'building')
  const queuedJobs = jobs.filter(j => j.status === 'queued')

  const columns = [
    {
      title: 'Job',
      key: 'job',
      render: (_: any, record: BuildJob) => (
        <Space direction="vertical" size="small">
          <a onClick={() => setSelectedJob(record)}>{record.id.slice(0, 8)}</a>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.branch}</Text>
        </Space>
      )
    },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => getStatusBadge(s) },
    { title: 'Architecture', dataIndex: 'architecture', key: 'arch', render: (a: string) => <Tag color="blue">{a}</Tag> },
    {
      title: 'Progress',
      key: 'progress',
      render: (_: any, record: BuildJob) => (
        record.status === 'building' ? <Progress percent={record.progress_percent} size="small" /> : '-'
      )
    },
    {
      title: 'Repository',
      dataIndex: 'repository_url',
      key: 'repo',
      render: (url: string) => <Text ellipsis style={{ maxWidth: 200 }}>{url}</Text>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: BuildJob) => (
        <Space>
          {['queued', 'building'].includes(record.status) && (
            <Tooltip title="Cancel">
              <Button size="small" danger icon={<StopOutlined />} onClick={() => cancelMutation.mutate(record.id)} />
            </Tooltip>
          )}
          <Button size="small" onClick={() => setSelectedJob(record)}>View</Button>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><BuildOutlined /> Build Jobs</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>Submit Build</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="Active Builds" value={activeJobs.length} prefix={<BuildOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Queued" value={queuedJobs.length} prefix={<ClockCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Completed Today" 
              value={jobs.filter(j => j.status === 'completed').length} 
              valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Failed Today" 
              value={jobs.filter(j => j.status === 'failed').length} 
              valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="all" items={[
        { key: 'all', label: 'All Jobs', children: <Table columns={columns} dataSource={jobs} rowKey="id" loading={isLoading} pagination={{ pageSize: 10 }} /> },
        { key: 'active', label: `Active (${activeJobs.length})`, children: <Table columns={columns} dataSource={activeJobs} rowKey="id" loading={isLoading} /> },
        { key: 'queued', label: `Queued (${queuedJobs.length})`, children: <Table columns={columns} dataSource={queuedJobs} rowKey="id" loading={isLoading} /> }
      ]} />

      {/* Submit Build Modal */}
      <Modal title="Submit Build Job" open={isModalVisible} onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()} confirmLoading={submitMutation.isLoading} width={800}>
        <Form form={form} layout="vertical" onFinish={(values) => {
          // Transform form values to include build_config
          const buildConfig: any = {}
          
          // Build mode
          if (values.build_mode) buildConfig.build_mode = values.build_mode
          
          // Build path configuration
          if (values.workspace_root) buildConfig.workspace_root = values.workspace_root
          if (values.output_directory) buildConfig.output_directory = values.output_directory
          if (values.keep_workspace !== undefined) buildConfig.keep_workspace = values.keep_workspace
          
          // Repository configuration
          if (values.git_depth !== undefined) buildConfig.git_depth = values.git_depth
          if (values.git_submodules !== undefined) buildConfig.git_submodules = values.git_submodules
          
          // Build configuration (kernel mode)
          if (values.kernel_config) buildConfig.kernel_config = values.kernel_config
          if (values.extra_make_args) buildConfig.extra_make_args = values.extra_make_args.split(',').map((s: string) => s.trim()).filter(Boolean)
          if (values.artifact_patterns) buildConfig.artifact_patterns = values.artifact_patterns.split('\n').map((s: string) => s.trim()).filter(Boolean)
          
          // Custom build commands (custom mode)
          if (values.pre_build_commands) buildConfig.pre_build_commands = values.pre_build_commands.split('\n').map((s: string) => s.trim()).filter(Boolean)
          if (values.build_commands) buildConfig.build_commands = values.build_commands.split('\n').map((s: string) => s.trim()).filter(Boolean)
          if (values.post_build_commands) buildConfig.post_build_commands = values.post_build_commands.split('\n').map((s: string) => s.trim()).filter(Boolean)
          
          // Custom environment variables
          if (values.custom_env) {
            try {
              buildConfig.custom_env = JSON.parse(values.custom_env)
            } catch (e) {
              // If not valid JSON, treat as key=value pairs
              const envVars: any = {}
              values.custom_env.split('\n').forEach((line: string) => {
                const [key, ...valueParts] = line.split('=')
                if (key && valueParts.length > 0) {
                  envVars[key.trim()] = valueParts.join('=').trim()
                }
              })
              buildConfig.custom_env = envVars
            }
          }
          
          const payload = {
            source_repository: values.repository_url,
            branch: values.branch,
            commit_hash: values.commit_hash,
            target_architecture: values.architecture,
            server_id: values.build_server_id,
            build_config: buildConfig
          }
          
          submitMutation.mutate(payload)
        }}>
          <Title level={5}>Basic Settings</Title>
          
          {/* Template Management */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={16}>
              <Form.Item label="Load Template">
                <Select 
                  placeholder="Select a saved template to load" 
                  allowClear
                  onChange={(templateId) => {
                    if (templateId) {
                      const template = templates.find(t => t.id === templateId)
                      if (template) loadTemplate(template)
                    }
                  }}
                >
                  {templates.map(t => (
                    <Option key={t.id} value={t.id}>
                      <Tag color={t.build_mode === 'custom' ? 'blue' : 'green'} style={{ marginRight: 8 }}>
                        {t.build_mode === 'custom' ? 'Custom' : 'Kernel'}
                      </Tag>
                      {t.name} {t.description && `- ${t.description}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label=" ">
                <Button onClick={saveCurrentAsTemplate} block>Save as Template</Button>
              </Form.Item>
            </Col>
          </Row>

          {/* Build Mode Selection - Prominent */}
          <Form.Item name="build_mode" label="Build Mode" initialValue="custom" tooltip="Choose between custom commands or standard kernel build">
            <Select size="large">
              <Option value="custom">
                <Space>
                  <BuildOutlined />
                  <span><strong>Custom Build Commands</strong> - Run any build commands</span>
                </Space>
              </Option>
              <Option value="kernel">
                <Space>
                  <BuildOutlined />
                  <span><strong>Standard Kernel Build</strong> - Linux kernel build with make</span>
                </Space>
              </Option>
            </Select>
          </Form.Item>

          {/* Build Configuration - Dynamic based on build_mode */}
          <Title level={5} style={{ marginTop: 24 }}>Build Configuration</Title>
          <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.build_mode !== currentValues.build_mode}>
            {({ getFieldValue }) => {
              const buildMode = getFieldValue('build_mode') || 'custom'
              
              if (buildMode === 'custom') {
                return (
                  <>
                    <Form.Item name="pre_build_commands" label="Pre-Build Commands (Optional)" tooltip="Commands to run before build (one per line)">
                      <TextArea rows={3} placeholder="# Optional setup commands&#10;export CROSS_COMPILE=aarch64-linux-gnu-&#10;./apply-patches.sh" />
                    </Form.Item>
                    <Form.Item name="build_commands" label="Build Commands" rules={[{ required: true, message: 'Build commands are required for custom mode' }]} tooltip="Main build commands (one per line)">
                      <TextArea rows={6} placeholder="# Main build commands (required)&#10;make clean&#10;make defconfig&#10;make -j$(nproc)" />
                    </Form.Item>
                    <Form.Item name="post_build_commands" label="Post-Build Commands (Optional)" tooltip="Commands to run after build (one per line)">
                      <TextArea rows={3} placeholder="# Optional post-build commands&#10;./run-tests.sh&#10;./package-artifacts.sh" />
                    </Form.Item>
                    <Form.Item name="custom_env" label="Environment Variables (Optional)" tooltip="JSON object or KEY=VALUE pairs (one per line)">
                      <TextArea rows={4} placeholder='{"CC": "gcc-12", "CFLAGS": "-O2"}&#10;or&#10;CC=gcc-12&#10;CFLAGS=-O2' />
                    </Form.Item>
                  </>
                )
              } else {
                return (
                  <>
                    <Form.Item name="architecture" label="Architecture" rules={[{ required: true }]}>
                      <Select placeholder="Select architecture">
                        <Option value="x86_64">x86_64</Option>
                        <Option value="arm64">ARM64</Option>
                        <Option value="arm">ARM</Option>
                        <Option value="riscv64">RISC-V 64</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item name="kernel_config" label="Kernel Config" tooltip="defconfig name or path to config file">
                      <Input placeholder="defconfig" />
                    </Form.Item>
                    <Form.Item name="extra_make_args" label="Extra Make Arguments" tooltip="Comma-separated make arguments">
                      <Input placeholder="ARCH=arm64, CROSS_COMPILE=aarch64-linux-gnu-" />
                    </Form.Item>
                    <Form.Item name="artifact_patterns" label="Artifact Patterns" tooltip="One pattern per line (glob patterns)">
                      <TextArea rows={4} placeholder="arch/*/boot/Image&#10;vmlinux&#10;*.dtb" />
                    </Form.Item>
                    <Form.Item name="custom_env" label="Environment Variables (Optional)" tooltip="JSON object or KEY=VALUE pairs (one per line)">
                      <TextArea rows={4} placeholder='{"CC": "gcc-12", "CFLAGS": "-O2"}&#10;or&#10;CC=gcc-12&#10;CFLAGS=-O2' />
                    </Form.Item>
                  </>
                )
              }
            }}
          </Form.Item>

          {/* Repository Settings - After Build Configuration */}
          <Title level={5} style={{ marginTop: 24 }}>Repository Settings (Optional)</Title>
          <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.build_mode !== currentValues.build_mode}>
            {({ getFieldValue }) => {
              const buildMode = getFieldValue('build_mode') || 'custom'
              const isKernelMode = buildMode === 'kernel'
              
              return (
                <>
                  <Form.Item 
                    name="repository_url" 
                    label="Repository URL"
                    rules={isKernelMode ? [{ required: true, message: 'Repository URL is required for kernel builds' }] : []}
                    tooltip={isKernelMode ? "Git repository URL (required)" : "Optional: Git repository URL if you need to clone code"}
                  >
                    <Input placeholder="https://github.com/org/kernel.git" />
                  </Form.Item>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item 
                        name="branch" 
                        label="Branch"
                        rules={isKernelMode ? [{ required: true, message: 'Branch is required for kernel builds' }] : []}
                      >
                        <Input placeholder="main" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="commit_hash" label="Commit">
                        <Input placeholder="abc123..." />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="git_depth" label="Git Clone Depth" tooltip="Shallow clone depth (1 = latest commit only, empty = full clone)">
                        <Input type="number" placeholder="Full clone" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="git_submodules" label="Clone Submodules" valuePropName="checked" tooltip="Clone git submodules">
                        <input type="checkbox" style={{ marginTop: 8 }} />
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              )
            }}
          </Form.Item>

          {/* Build Server Settings */}
          <Title level={5} style={{ marginTop: 24 }}>Build Server Settings</Title>
          <Form.Item name="build_server_id" label="Build Server" rules={[{ required: true, message: 'Please select a build server' }]} tooltip="Select the build server to execute this build">
            <Select placeholder="Select a build server">
              {buildServers.filter(s => s.status === 'online').map(s => (
                <Option key={s.id} value={s.id}>{s.hostname}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="workspace_root" label="Workspace Root" tooltip="Root directory for builds on the build server">
                <Input placeholder="/tmp/builds" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="output_directory" label="Output Directory" tooltip="Where to place build artifacts">
                <Input placeholder="Auto-generated if not specified" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item name="keep_workspace" label="Keep Workspace" valuePropName="checked" tooltip="Keep workspace after build completes">
            <input type="checkbox" style={{ marginTop: 8 }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Job Details Modal */}
      <Modal title={`Build Job: ${selectedJob?.id.slice(0, 8)}`} open={!!selectedJob} 
        onCancel={() => setSelectedJob(null)} footer={null} width={900}>
        {selectedJob && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={6}><Statistic title="Status" value={selectedJob.status} /></Col>
              <Col span={6}><Statistic title="Architecture" value={selectedJob.architecture} /></Col>
              <Col span={6}><Statistic title="Progress" value={selectedJob.progress_percent} suffix="%" /></Col>
              <Col span={6}><Statistic title="Branch" value={selectedJob.branch} /></Col>
            </Row>
            
            {/* Build Flow Visualization */}
            <BuildFlowVisualization 
              jobId={selectedJob.id}
              status={selectedJob.status}
              stages={buildFlow?.stages}
            />
            
            <Card title="Build Logs" size="small" style={{ marginTop: 16 }}>
              <Paragraph code style={{ maxHeight: 300, overflow: 'auto', background: '#1e1e1e', color: '#d4d4d4', padding: 12 }}>
                Build logs will appear here when available...
              </Paragraph>
            </Card>
          </div>
        )}
      </Modal>

      {/* Save Template Modal */}
      <Modal 
        title="Save Build Configuration as Template" 
        open={isSaveTemplateModalVisible} 
        onCancel={() => setIsSaveTemplateModalVisible(false)}
        onOk={() => templateForm.submit()} 
        confirmLoading={saveTemplateMutation.isLoading}
      >
        <Form 
          form={templateForm} 
          layout="vertical" 
          onFinish={(values) => {
            // Get current form values
            const currentValues = form.getFieldsValue()
            
            // Build the template data
            const templateData: any = {
              name: values.name,
              description: values.description,
              build_mode: currentValues.build_mode || 'kernel',
              workspace_root: currentValues.workspace_root,
              output_directory: currentValues.output_directory,
              keep_workspace: currentValues.keep_workspace || false,
              git_depth: currentValues.git_depth,
              git_submodules: currentValues.git_submodules || false
            }
            
            // Add mode-specific fields
            if (currentValues.build_mode === 'custom') {
              if (currentValues.pre_build_commands) {
                templateData.pre_build_commands = currentValues.pre_build_commands.split('\n').map((s: string) => s.trim()).filter(Boolean)
              }
              if (currentValues.build_commands) {
                templateData.build_commands = currentValues.build_commands.split('\n').map((s: string) => s.trim()).filter(Boolean)
              }
              if (currentValues.post_build_commands) {
                templateData.post_build_commands = currentValues.post_build_commands.split('\n').map((s: string) => s.trim()).filter(Boolean)
              }
            } else {
              if (currentValues.kernel_config) templateData.kernel_config = currentValues.kernel_config
              if (currentValues.extra_make_args) {
                templateData.extra_make_args = currentValues.extra_make_args.split(',').map((s: string) => s.trim()).filter(Boolean)
              }
              if (currentValues.artifact_patterns) {
                templateData.artifact_patterns = currentValues.artifact_patterns.split('\n').map((s: string) => s.trim()).filter(Boolean)
              }
            }
            
            // Add environment variables
            if (currentValues.custom_env) {
              try {
                templateData.custom_env = JSON.parse(currentValues.custom_env)
              } catch (e) {
                const envVars: any = {}
                currentValues.custom_env.split('\n').forEach((line: string) => {
                  const [key, ...valueParts] = line.split('=')
                  if (key && valueParts.length > 0) {
                    envVars[key.trim()] = valueParts.join('=').trim()
                  }
                })
                templateData.custom_env = envVars
              }
            }
            
            saveTemplateMutation.mutate(templateData)
          }}
        >
          <Form.Item name="name" label="Template Name" rules={[{ required: true, message: 'Please enter a template name' }]}>
            <Input placeholder="e.g., U-Boot QEMU ARM64" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Optional description of this template" />
          </Form.Item>
          <Paragraph type="secondary" style={{ fontSize: 12 }}>
            This will save all current build configuration settings (build mode, commands, environment variables, etc.) as a reusable template.
          </Paragraph>
        </Form>
      </Modal>
    </div>
  )
}

export default BuildJobDashboard
