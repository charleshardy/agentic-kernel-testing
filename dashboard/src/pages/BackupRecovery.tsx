import React from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space, Button, Progress, Alert } from 'antd'
import { 
  DatabaseOutlined, 
  CloudDownloadOutlined, 
  HistoryOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  SettingOutlined
} from '@ant-design/icons'

const BackupRecovery: React.FC = () => {
  // Mock backup data
  const stats = {
    totalBackups: 156,
    successfulBackups: 152,
    failedBackups: 4,
    storageUsed: 2.4,
    storageTotal: 10.0
  }

  const backupJobs = [
    {
      key: '1',
      name: 'Daily System Backup',
      type: 'Full',
      status: 'Completed',
      lastRun: '2024-01-13 02:00:00',
      nextRun: '2024-01-14 02:00:00',
      size: '1.2 GB',
      duration: '45 min'
    },
    {
      key: '2',
      name: 'Test Results Incremental',
      type: 'Incremental',
      status: 'Completed',
      lastRun: '2024-01-13 14:00:00',
      nextRun: '2024-01-13 18:00:00',
      size: '156 MB',
      duration: '8 min'
    },
    {
      key: '3',
      name: 'Configuration Backup',
      type: 'Configuration',
      status: 'Failed',
      lastRun: '2024-01-13 12:00:00',
      nextRun: '2024-01-13 16:00:00',
      size: '0 MB',
      duration: '0 min'
    }
  ]

  const recoveryPoints = [
    {
      key: '1',
      timestamp: '2024-01-13 02:00:00',
      type: 'Full Backup',
      size: '1.2 GB',
      retention: '90 days',
      status: 'Available',
      location: 'Primary Storage'
    },
    {
      key: '2',
      timestamp: '2024-01-12 14:00:00',
      type: 'Incremental',
      size: '234 MB',
      retention: '30 days',
      status: 'Available',
      location: 'Primary Storage'
    },
    {
      key: '3',
      timestamp: '2024-01-12 02:00:00',
      type: 'Full Backup',
      size: '1.1 GB',
      retention: '90 days',
      status: 'Available',
      location: 'Archive Storage'
    }
  ]

  const backupColumns = [
    {
      title: 'Backup Job',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: any) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.type} Backup</div>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors = {
          'Completed': 'green',
          'Running': 'blue',
          'Failed': 'red',
          'Scheduled': 'orange'
        }
        const icons = {
          'Completed': <CheckCircleOutlined />,
          'Running': <ClockCircleOutlined />,
          'Failed': <ExclamationCircleOutlined />,
          'Scheduled': <ClockCircleOutlined />
        }
        return (
          <Tag color={colors[status as keyof typeof colors]} icon={icons[status as keyof typeof icons]}>
            {status}
          </Tag>
        )
      }
    },
    {
      title: 'Last Run',
      dataIndex: 'lastRun',
      key: 'lastRun',
      render: (text: string) => <span style={{ fontSize: '12px', fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: 'Next Run',
      dataIndex: 'nextRun',
      key: 'nextRun',
      render: (text: string) => <span style={{ fontSize: '12px', fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size'
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: any) => (
        <Space>
          <Button size="small" icon={<PlayCircleOutlined />}>Run Now</Button>
          <Button size="small" icon={<SettingOutlined />}>Configure</Button>
        </Space>
      )
    }
  ]

  const recoveryColumns = [
    {
      title: 'Recovery Point',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string, record: any) => (
        <div>
          <div style={{ fontWeight: 'bold', fontFamily: 'monospace', fontSize: '12px' }}>{timestamp}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.type}</div>
        </div>
      )
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size'
    },
    {
      title: 'Retention',
      dataIndex: 'retention',
      key: 'retention'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'Available' ? 'green' : 'gray'}>{status}</Tag>
      )
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      render: (location: string) => <span style={{ fontSize: '12px' }}>{location}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <Space>
          <Button size="small" icon={<HistoryOutlined />}>Restore</Button>
          <Button size="small" icon={<CloudDownloadOutlined />}>Download</Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <DatabaseOutlined />
          Backup & Recovery
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Manage backup policies, monitor backup jobs, and perform data recovery operations
        </p>
      </div>

      <Alert
        message="Backup Failure"
        description="Configuration backup failed at 12:00. Check storage connectivity and retry the backup operation."
        type="error"
        showIcon
        style={{ marginBottom: '24px' }}
        action={
          <Button size="small" type="primary">
            Retry Backup
          </Button>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Backups"
              value={stats.totalBackups}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Successful"
              value={stats.successfulBackups}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Failed"
              value={stats.failedBackups}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Storage Used"
              value={stats.storageUsed}
              suffix={`/ ${stats.storageTotal} TB`}
              prefix={<CloudDownloadOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Storage Utilization" size="small">
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={Math.round((stats.storageUsed / stats.storageTotal) * 100)}
                format={(percent) => `${percent}%\nUsed`}
                strokeColor="#1890ff"
                size={120}
              />
              <div style={{ marginTop: '16px', fontSize: '14px', color: '#666' }}>
                {stats.storageUsed} TB of {stats.storageTotal} TB used
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Backup Success Rate" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span>Success Rate</span>
                  <span>{Math.round((stats.successfulBackups / stats.totalBackups) * 100)}%</span>
                </div>
                <Progress 
                  percent={Math.round((stats.successfulBackups / stats.totalBackups) * 100)} 
                  strokeColor="#52c41a"
                  showInfo={false}
                />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span>Successful Backups</span>
                  <span>{stats.successfulBackups}</span>
                </div>
                <Progress 
                  percent={Math.round((stats.successfulBackups / stats.totalBackups) * 100)} 
                  strokeColor="#52c41a"
                  showInfo={false}
                />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span>Failed Backups</span>
                  <span>{stats.failedBackups}</span>
                </div>
                <Progress 
                  percent={Math.round((stats.failedBackups / stats.totalBackups) * 100)} 
                  strokeColor="#ff4d4f"
                  showInfo={false}
                />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Backup Jobs" size="small">
            <Table
              columns={backupColumns}
              dataSource={backupJobs}
              pagination={false}
              size="small"
              scroll={{ x: true }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Recovery Points" size="small">
            <Table
              columns={recoveryColumns}
              dataSource={recoveryPoints}
              pagination={false}
              size="small"
              scroll={{ x: true }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default BackupRecovery