import React from 'react'
import { Tabs } from 'antd'
import {
  DashboardOutlined,
  BuildOutlined,
  DesktopOutlined,
  CloudServerOutlined,
  DeploymentUnitOutlined,
  FolderOutlined,
  GroupOutlined,
  SettingOutlined
} from '@ant-design/icons'
import {
  InfrastructureDashboard,
  BuildServerPanel,
  BuildJobDashboard,
  ArtifactBrowser,
  HostManagementPanel,
  BoardManagementPanel,
  PipelineDashboard,
  ResourceGroupPanel,
  InfrastructureSettings
} from '../components/infrastructure'

/**
 * Infrastructure Management Page
 * 
 * Main entry point for test infrastructure management including:
 * - Build servers and build jobs
 * - QEMU hosts
 * - Physical boards
 * - Pipelines
 * - Artifacts
 * - Resource groups
 * - Settings
 */
const Infrastructure: React.FC = () => {
  const tabItems = [
    {
      key: 'overview',
      label: <span><DashboardOutlined /> Overview</span>,
      children: <InfrastructureDashboard />
    },
    {
      key: 'build-servers',
      label: <span><BuildOutlined /> Build Servers</span>,
      children: <BuildServerPanel />
    },
    {
      key: 'build-jobs',
      label: <span><BuildOutlined /> Build Jobs</span>,
      children: <BuildJobDashboard />
    },
    {
      key: 'artifacts',
      label: <span><FolderOutlined /> Artifacts</span>,
      children: <ArtifactBrowser />
    },
    {
      key: 'hosts',
      label: <span><DesktopOutlined /> QEMU Hosts</span>,
      children: <HostManagementPanel />
    },
    {
      key: 'boards',
      label: <span><CloudServerOutlined /> Physical Boards</span>,
      children: <BoardManagementPanel />
    },
    {
      key: 'pipelines',
      label: <span><DeploymentUnitOutlined /> Pipelines</span>,
      children: <PipelineDashboard />
    },
    {
      key: 'groups',
      label: <span><GroupOutlined /> Resource Groups</span>,
      children: <ResourceGroupPanel />
    },
    {
      key: 'settings',
      label: <span><SettingOutlined /> Settings</span>,
      children: <InfrastructureSettings />
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Tabs
        defaultActiveKey="overview"
        items={tabItems}
        size="large"
        tabPosition="left"
        style={{ minHeight: 'calc(100vh - 150px)' }}
      />
    </div>
  )
}

export default Infrastructure
