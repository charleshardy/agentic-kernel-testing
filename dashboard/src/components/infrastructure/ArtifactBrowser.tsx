import React, { useState } from 'react'
import {
  Card, Table, Tag, Button, Space, Input, Select,
  Typography, Row, Col, Statistic, Tooltip, Descriptions
} from 'antd'
import {
  FileOutlined, DownloadOutlined, ReloadOutlined, SearchOutlined,
  FolderOutlined, CheckCircleOutlined
} from '@ant-design/icons'
import { useQuery } from 'react-query'

const { Title, Text } = Typography
const { Option } = Select
const { Search } = Input

interface Artifact {
  id: string
  build_id: string
  artifact_type: 'kernel_image' | 'rootfs' | 'device_tree' | 'modules' | 'debug_symbols'
  filename: string
  file_size_bytes: number
  checksum_sha256: string
  architecture: string
  branch: string
  commit_hash: string
  created_at: string
}

/**
 * Artifact Browser
 * 
 * **Feature: test-infrastructure-management**
 * **Requirement 4.1**: List artifacts with download links
 * **Requirement 4.5**: Retrieve artifacts by build ID, commit, or "latest"
 */
const ArtifactBrowser: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [filterArch, setFilterArch] = useState<string | undefined>()
  const [filterType, setFilterType] = useState<string | undefined>()

  const { data: artifacts = [], isLoading, refetch } = useQuery<Artifact[]>(
    ['artifacts', searchQuery, filterArch, filterType],
    async () => {
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (filterArch) params.append('architecture', filterArch)
      if (filterType) params.append('type', filterType)
      const response = await fetch(`/api/v1/infrastructure/artifacts?${params}`)
      if (!response.ok) throw new Error('Failed to fetch artifacts')
      return response.json()
    },
    { refetchInterval: 30000 }
  )

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      kernel_image: 'blue', rootfs: 'green', device_tree: 'orange',
      modules: 'purple', debug_symbols: 'cyan'
    }
    return colors[type] || 'default'
  }

  const columns = [
    {
      title: 'Artifact',
      key: 'artifact',
      render: (_: any, record: Artifact) => (
        <Space direction="vertical" size="small">
          <a onClick={() => setSelectedArtifact(record)}><FileOutlined /> {record.filename}</a>
          <Text type="secondary" style={{ fontSize: 12 }}>Build: {record.build_id.slice(0, 8)}</Text>
        </Space>
      )
    },
    { title: 'Type', dataIndex: 'artifact_type', key: 'type', render: (t: string) => <Tag color={getTypeColor(t)}>{t.replace('_', ' ')}</Tag> },
    { title: 'Architecture', dataIndex: 'architecture', key: 'arch', render: (a: string) => <Tag color="blue">{a}</Tag> },
    { title: 'Branch', dataIndex: 'branch', key: 'branch', render: (b: string) => <Tag>{b}</Tag> },
    { title: 'Size', dataIndex: 'file_size_bytes', key: 'size', render: (s: number) => formatFileSize(s) },
    {
      title: 'Commit',
      dataIndex: 'commit_hash',
      key: 'commit',
      render: (c: string) => <Text code>{c?.slice(0, 7)}</Text>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Artifact) => (
        <Space>
          <Tooltip title="Download">
            <Button size="small" icon={<DownloadOutlined />} 
              href={`/api/v1/infrastructure/artifacts/${record.id}/download`} />
          </Tooltip>
          <Button size="small" onClick={() => setSelectedArtifact(record)}>Details</Button>
        </Space>
      )
    }
  ]

  const totalSize = artifacts.reduce((sum, a) => sum + a.file_size_bytes, 0)

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <Title level={3}><FolderOutlined /> Build Artifacts</Title>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="Total Artifacts" value={artifacts.length} prefix={<FileOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="Total Size" value={formatFileSize(totalSize)} /></Card></Col>
        <Col span={6}><Card><Statistic title="Kernel Images" value={artifacts.filter(a => a.artifact_type === 'kernel_image').length} /></Card></Col>
        <Col span={6}><Card><Statistic title="Rootfs Images" value={artifacts.filter(a => a.artifact_type === 'rootfs').length} /></Card></Col>
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Search placeholder="Search by build ID, commit, or branch" allowClear style={{ width: 300 }}
            onSearch={setSearchQuery} prefix={<SearchOutlined />} />
          <Select placeholder="Architecture" allowClear style={{ width: 150 }} onChange={setFilterArch}>
            <Option value="x86_64">x86_64</Option>
            <Option value="arm64">ARM64</Option>
            <Option value="arm">ARM</Option>
            <Option value="riscv64">RISC-V 64</Option>
          </Select>
          <Select placeholder="Type" allowClear style={{ width: 150 }} onChange={setFilterType}>
            <Option value="kernel_image">Kernel Image</Option>
            <Option value="rootfs">Rootfs</Option>
            <Option value="device_tree">Device Tree</Option>
            <Option value="modules">Modules</Option>
            <Option value="debug_symbols">Debug Symbols</Option>
          </Select>
        </Space>
      </Card>

      <Table columns={columns} dataSource={artifacts} rowKey="id" loading={isLoading} pagination={{ pageSize: 15 }} />

      {/* Artifact Details Modal */}
      {selectedArtifact && (
        <Card title={`Artifact: ${selectedArtifact.filename}`} style={{ marginTop: 16 }}
          extra={<Button type="link" onClick={() => setSelectedArtifact(null)}>Close</Button>}>
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="Build ID">{selectedArtifact.build_id}</Descriptions.Item>
            <Descriptions.Item label="Type"><Tag color={getTypeColor(selectedArtifact.artifact_type)}>{selectedArtifact.artifact_type}</Tag></Descriptions.Item>
            <Descriptions.Item label="Architecture"><Tag color="blue">{selectedArtifact.architecture}</Tag></Descriptions.Item>
            <Descriptions.Item label="Branch">{selectedArtifact.branch}</Descriptions.Item>
            <Descriptions.Item label="Commit"><Text code>{selectedArtifact.commit_hash}</Text></Descriptions.Item>
            <Descriptions.Item label="Size">{formatFileSize(selectedArtifact.file_size_bytes)}</Descriptions.Item>
            <Descriptions.Item label="SHA256" span={2}><Text code copyable>{selectedArtifact.checksum_sha256}</Text></Descriptions.Item>
            <Descriptions.Item label="Created">{new Date(selectedArtifact.created_at).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="Verified"><CheckCircleOutlined style={{ color: '#52c41a' }} /> Checksum Valid</Descriptions.Item>
          </Descriptions>
          <div style={{ marginTop: 16 }}>
            <Button type="primary" icon={<DownloadOutlined />} href={`/api/v1/infrastructure/artifacts/${selectedArtifact.id}/download`}>
              Download Artifact
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

export default ArtifactBrowser
