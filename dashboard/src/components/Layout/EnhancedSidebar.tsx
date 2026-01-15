import React, { useState, useMemo, useEffect } from 'react'
import { Layout, Menu, Input, Badge, Divider, Typography, Tooltip, Button } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import UnifiedSearch from '../Navigation/UnifiedSearch'
import {
  // Core Testing Icons
  DashboardOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  ScheduleOutlined,
  CloudServerOutlined,
  DeploymentUnitOutlined,
  ClusterOutlined,
  FileTextOutlined,
  BugOutlined,
  
  // Security & Quality Icons
  SecurityScanOutlined,
  SafetyCertificateOutlined,
  
  // AI & Analytics Icons
  RobotOutlined,
  FundOutlined,
  ThunderboltOutlined,
  
  // Infrastructure Icons
  MonitorOutlined,
  
  // Management Icons
  TeamOutlined,
  ApiOutlined,
  AuditOutlined,
  DatabaseOutlined,
  
  // Communication Icons
  BellOutlined,
  BookOutlined,
  SettingOutlined,
  
  // Utility Icons
  SearchOutlined,
  DownOutlined,
  RightOutlined,
  FilterOutlined,
} from '@ant-design/icons'

const { Sider } = Layout
const { Text } = Typography
const { Search } = Input

// Type definitions
interface BadgeConfig {
  count?: number
  status?: 'success' | 'warning' | 'error' | 'info'
  pulse?: boolean
}

interface SidebarItem {
  key: string
  icon: React.ComponentType
  label: string
  path: string
  badge?: BadgeConfig
  permissions?: string[]
  children?: SidebarItem[]
}

interface SidebarSection {
  id: string
  title: string
  icon: React.ComponentType
  items: SidebarItem[]
  collapsible: boolean
  defaultCollapsed?: boolean
}

interface EnhancedSidebarProps {
  collapsed: boolean
  onCollapse: (collapsed: boolean) => void
  userPermissions: string[]
  notificationCounts: Record<string, number>
}

interface UserPreferences {
  collapsedSections: string[]
  sidebarOrder: string[]
  hiddenItems: string[]
}

const EnhancedSidebar: React.FC<EnhancedSidebarProps> = ({
  collapsed,
  onCollapse,
  userPermissions,
  notificationCounts
}) => {
  const navigate = useNavigate()
  const location = useLocation()
  
  // State management
  const [searchTerm, setSearchTerm] = useState('')
  const [searchModalVisible, setSearchModalVisible] = useState(false)
  const [collapsedSections, setCollapsedSections] = useState<string[]>([])
  const [userPreferences, setUserPreferences] = useState<UserPreferences>({
    collapsedSections: [],
    sidebarOrder: [],
    hiddenItems: []
  })

  // Load user preferences from localStorage
  useEffect(() => {
    const savedPreferences = localStorage.getItem('sidebar-preferences')
    if (savedPreferences) {
      try {
        const preferences = JSON.parse(savedPreferences)
        setUserPreferences(preferences)
        setCollapsedSections(preferences.collapsedSections || [])
      } catch (error) {
        console.warn('Failed to load sidebar preferences:', error)
      }
    }
  }, [])

  // Save user preferences to localStorage
  const savePreferences = (newPreferences: Partial<UserPreferences>) => {
    const updatedPreferences = { ...userPreferences, ...newPreferences }
    setUserPreferences(updatedPreferences)
    localStorage.setItem('sidebar-preferences', JSON.stringify(updatedPreferences))
  }

  // Define sidebar sections with all new functionality
  const sidebarSections: SidebarSection[] = [
    {
      id: 'core-testing',
      title: 'Core Testing',
      icon: ExperimentOutlined,
      collapsible: true,
      defaultCollapsed: false,
      items: [
        {
          key: '/',
          icon: DashboardOutlined,
          label: 'Dashboard',
          path: '/',
          permissions: ['dashboard.read']
        },
        {
          key: '/test-specifications',
          icon: FileTextOutlined,
          label: 'Test Specifications',
          path: '/test-specifications',
          permissions: ['specifications.read']
        },
        {
          key: '/test-cases',
          icon: ExperimentOutlined,
          label: 'Test Cases',
          path: '/test-cases',
          permissions: ['test-cases.read']
        },
        {
          key: '/test-plans',
          icon: ScheduleOutlined,
          label: 'Test Plans',
          path: '/test-plans',
          permissions: ['test-plans.read']
        },
        {
          key: '/test-execution',
          icon: ExperimentOutlined,
          label: 'Test Execution',
          path: '/test-execution',
          permissions: ['test-execution.read']
        },
        {
          key: '/results',
          icon: BarChartOutlined,
          label: 'Test Results',
          path: '/results',
          permissions: ['test-results.read']
        }
      ]
    },
    {
      id: 'security-quality',
      title: 'Security & Quality',
      icon: SecurityScanOutlined,
      collapsible: true,
      defaultCollapsed: false,
      items: [
        {
          key: '/security-dashboard',
          icon: SecurityScanOutlined,
          label: 'Security Dashboard',
          path: '/security-dashboard',
          permissions: ['security.read'],
          badge: notificationCounts.security ? {
            count: notificationCounts.security,
            status: 'error',
            pulse: true
          } : undefined
        },
        {
          key: '/vulnerability-management',
          icon: SafetyCertificateOutlined,
          label: 'Vulnerability Management',
          path: '/vulnerability-management',
          permissions: ['security.vulnerabilities.read'],
          badge: notificationCounts.vulnerabilities ? {
            count: notificationCounts.vulnerabilities,
            status: 'warning'
          } : undefined
        },
        {
          key: '/defects',
          icon: BugOutlined,
          label: 'Defect Management',
          path: '/defects',
          permissions: ['defects.read'],
          badge: notificationCounts.defects ? {
            count: notificationCounts.defects,
            status: 'error'
          } : undefined
        },
        {
          key: '/coverage',
          icon: PieChartOutlined,
          label: 'Coverage Analysis',
          path: '/coverage',
          permissions: ['coverage.read']
        }
      ]
    },
    {
      id: 'ai-analytics',
      title: 'AI & Analytics',
      icon: RobotOutlined,
      collapsible: true,
      defaultCollapsed: false,
      items: [
        {
          key: '/ai-model-management',
          icon: RobotOutlined,
          label: 'AI Model Management',
          path: '/ai-model-management',
          permissions: ['ai.models.read'],
          badge: notificationCounts.aiModels ? {
            count: notificationCounts.aiModels,
            status: 'warning'
          } : undefined
        },
        {
          key: '/analytics-insights',
          icon: FundOutlined,
          label: 'Analytics & Insights',
          path: '/analytics-insights',
          permissions: ['analytics.read']
        },
        {
          key: '/performance',
          icon: LineChartOutlined,
          label: 'Performance Monitoring',
          path: '/performance',
          permissions: ['performance.read']
        }
      ]
    },
    {
      id: 'infrastructure',
      title: 'Infrastructure',
      icon: ClusterOutlined,
      collapsible: true,
      defaultCollapsed: false,
      items: [
        {
          key: '/test-environment',
          icon: CloudServerOutlined,
          label: 'Test Environment',
          path: '/test-environment',
          permissions: ['environment.read']
        },
        {
          key: '/test-infrastructure',
          icon: ClusterOutlined,
          label: 'Test Infrastructure',
          path: '/test-infrastructure',
          permissions: ['infrastructure.read']
        },
        {
          key: '/test-deployment',
          icon: DeploymentUnitOutlined,
          label: 'Test Deployment',
          path: '/test-deployment',
          permissions: ['deployment.read']
        },
        {
          key: '/resource-monitoring',
          icon: MonitorOutlined,
          label: 'Resource Monitoring',
          path: '/resource-monitoring',
          permissions: ['resources.read'],
          badge: notificationCounts.resources ? {
            count: notificationCounts.resources,
            status: 'warning'
          } : undefined
        }
      ]
    },
    {
      id: 'management',
      title: 'Management',
      icon: TeamOutlined,
      collapsible: true,
      defaultCollapsed: false,
      items: [
        {
          key: '/user-team-management',
          icon: TeamOutlined,
          label: 'User & Team Management',
          path: '/user-team-management',
          permissions: ['users.read', 'teams.read']
        },
        {
          key: '/integration-hub',
          icon: ApiOutlined,
          label: 'Integration Hub',
          path: '/integration-hub',
          permissions: ['integrations.read'],
          badge: notificationCounts.integrations ? {
            count: notificationCounts.integrations,
            status: 'error'
          } : undefined
        },
        {
          key: '/audit-compliance',
          icon: AuditOutlined,
          label: 'Audit & Compliance',
          path: '/audit-compliance',
          permissions: ['audit.read', 'compliance.read']
        },
        {
          key: '/backup-recovery',
          icon: DatabaseOutlined,
          label: 'Backup & Recovery',
          path: '/backup-recovery',
          permissions: ['backup.read']
        }
      ]
    },
    {
      id: 'communication',
      title: 'Communication',
      icon: BellOutlined,
      collapsible: true,
      defaultCollapsed: false,
      items: [
        {
          key: '/notification-center',
          icon: BellOutlined,
          label: 'Notification Center',
          path: '/notification-center',
          permissions: ['notifications.read'],
          badge: notificationCounts.notifications ? {
            count: notificationCounts.notifications,
            status: 'info',
            pulse: true
          } : undefined
        },
        {
          key: '/knowledge-base',
          icon: BookOutlined,
          label: 'Knowledge Base',
          path: '/knowledge-base',
          permissions: ['knowledge.read']
        },
        {
          key: '/settings',
          icon: SettingOutlined,
          label: 'Settings',
          path: '/settings',
          permissions: ['settings.read']
        }
      ]
    }
  ]

  // Check if user has permission for a specific item
  const hasPermission = (permissions?: string[]): boolean => {
    if (!permissions || permissions.length === 0) return true
    return permissions.some(permission => userPermissions.includes(permission))
  }

  // Filter items based on permissions
  const filterItemsByPermissions = (items: SidebarItem[]): SidebarItem[] => {
    return items.filter(item => {
      if (!hasPermission(item.permissions)) return false
      if (userPreferences.hiddenItems.includes(item.key)) return false
      return true
    })
  }

  // Filter items based on search term
  const filterItemsBySearch = (items: SidebarItem[]): SidebarItem[] => {
    if (!searchTerm) return items
    
    return items.filter(item =>
      item.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.path.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  // Get filtered sections based on permissions and search
  const filteredSections = useMemo(() => {
    return sidebarSections.map(section => ({
      ...section,
      items: filterItemsBySearch(filterItemsByPermissions(section.items))
    })).filter(section => section.items.length > 0)
  }, [sidebarSections, userPermissions, searchTerm, userPreferences.hiddenItems])

  // Toggle section collapse
  const toggleSection = (sectionId: string) => {
    const newCollapsedSections = collapsedSections.includes(sectionId)
      ? collapsedSections.filter(id => id !== sectionId)
      : [...collapsedSections, sectionId]
    
    setCollapsedSections(newCollapsedSections)
    savePreferences({ collapsedSections: newCollapsedSections })
  }

  // Handle menu item click
  const handleMenuClick = (path: string) => {
    navigate(path)
  }

  // Render badge for menu item
  const renderBadge = (badge?: BadgeConfig) => {
    if (!badge) return null
    
    return (
      <Badge
        count={badge.count}
        status={badge.status}
        size="small"
        style={{
          animation: badge.pulse ? 'pulse 2s infinite' : undefined
        }}
      />
    )
  }

  // Render menu item
  const renderMenuItem = (item: SidebarItem) => {
    const IconComponent = item.icon
    const isActive = location.pathname === item.path
    
    return (
      <div
        key={item.key}
        className={`sidebar-menu-item ${isActive ? 'active' : ''}`}
        onClick={() => handleMenuClick(item.path)}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 16px',
          cursor: 'pointer',
          borderRadius: '6px',
          margin: '2px 8px',
          backgroundColor: isActive ? '#e6f7ff' : 'transparent',
          borderLeft: isActive ? '3px solid #1890ff' : '3px solid transparent',
          transition: 'all 0.2s ease'
        }}
      >
        <IconComponent style={{ fontSize: '16px', marginRight: collapsed ? 0 : '12px' }} />
        {!collapsed && (
          <>
            <span style={{ flex: 1, fontSize: '14px' }}>{item.label}</span>
            {renderBadge(item.badge)}
          </>
        )}
      </div>
    )
  }

  // Render section
  const renderSection = (section: SidebarSection) => {
    const isCollapsed = collapsedSections.includes(section.id)
    const SectionIcon = section.icon
    
    if (section.items.length === 0) return null
    
    return (
      <div key={section.id} style={{ marginBottom: '16px' }}>
        {!collapsed && section.collapsible && (
          <div
            className="sidebar-section-header"
            onClick={() => toggleSection(section.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '8px 16px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              color: '#8c8c8c',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              transition: 'color 0.2s ease'
            }}
          >
            <SectionIcon style={{ fontSize: '14px', marginRight: '8px' }} />
            <span style={{ flex: 1 }}>{section.title}</span>
            {isCollapsed ? <RightOutlined /> : <DownOutlined />}
          </div>
        )}
        
        {(!section.collapsible || !isCollapsed) && (
          <div className="sidebar-section-items">
            {section.items.map(renderMenuItem)}
          </div>
        )}
        
        {!collapsed && <Divider style={{ margin: '8px 0', borderColor: '#f0f0f0' }} />}
      </div>
    )
  }

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      theme="light"
      width={280}
      collapsedWidth={64}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        borderRight: '1px solid #f0f0f0',
        boxShadow: '2px 0 8px rgba(0,0,0,0.05)'
      }}
    >
      {/* Logo Section */}
      <div style={{ 
        padding: '16px', 
        textAlign: 'center',
        borderBottom: '1px solid #f0f0f0',
        backgroundColor: '#fafafa'
      }}>
        <div className="dashboard-logo" style={{
          fontSize: collapsed ? '14px' : '16px',
          fontWeight: 'bold',
          color: '#1890ff'
        }}>
          {collapsed ? 'ATS' : 'Agentic Testing System'}
        </div>
      </div>

      {/* Search Section */}
      {!collapsed && (
        <div style={{ padding: '16px 12px' }}>
          <Search
            placeholder="Search features..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => setSearchModalVisible(true)}
            prefix={<SearchOutlined />}
            allowClear
            size="small"
            style={{ borderRadius: '6px' }}
          />
        </div>
      )}

      {/* Navigation Sections */}
      <div style={{ padding: '8px 0' }}>
        {filteredSections.map(renderSection)}
      </div>

      {/* Search Results Info */}
      {searchTerm && !collapsed && (
        <div style={{ 
          padding: '8px 16px', 
          fontSize: '12px', 
          color: '#8c8c8c',
          borderTop: '1px solid #f0f0f0'
        }}>
          <Text type="secondary">
            {filteredSections.reduce((total, section) => total + section.items.length, 0)} results found
          </Text>
        </div>
      )}

      {/* Customization Hint */}
      {!collapsed && (
        <div style={{ 
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          right: '16px',
          fontSize: '11px',
          color: '#bfbfbf',
          textAlign: 'center'
        }}>
          <Tooltip title="Click section headers to collapse/expand">
            <FilterOutlined /> Customizable Layout
          </Tooltip>
        </div>
      )}

      {/* Custom Styles */}
      <style jsx>{`
        .sidebar-menu-item:hover {
          background-color: #f5f5f5 !important;
        }
        
        .sidebar-menu-item.active {
          background-color: #e6f7ff !important;
          color: #1890ff;
        }
        
        .sidebar-section-header:hover {
          color: #595959 !important;
        }
        
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        
        .ant-layout-sider-light .ant-layout-sider-trigger {
          background: #fafafa;
          border-top: 1px solid #f0f0f0;
          color: #595959;
        }
        
        .ant-layout-sider-light .ant-layout-sider-trigger:hover {
          background: #e6f7ff;
          color: #1890ff;
        }
      `}</style>

      {/* Unified Search Modal */}
      <UnifiedSearch 
        visible={searchModalVisible} 
        onClose={() => {
          setSearchModalVisible(false)
          setSearchTerm('')
        }} 
      />
    </Sider>
  )
}

export default EnhancedSidebar