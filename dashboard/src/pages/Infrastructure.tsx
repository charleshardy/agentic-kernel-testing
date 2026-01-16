import React, { useEffect, useState } from 'react'
import { Tabs } from 'antd'
import { useSearchParams } from 'react-router-dom'
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
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('overview');

  // Set active tab from URL query parameter
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) {
      setActiveTab(tab);
    }
  }, [searchParams]);

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
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
        tabPosition="left"
        style={{ minHeight: 'calc(100vh - 150px)' }}
      />
    </div>
  )
}

export default Infrastructure
