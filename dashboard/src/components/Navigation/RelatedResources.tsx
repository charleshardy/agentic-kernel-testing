import React from 'react';
import { Card, List, Space, Tag } from 'antd';
import { Link } from 'react-router-dom';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  BugOutlined,
  SafetyOutlined,
  LinkOutlined,
  ProjectOutlined,
  CloudServerOutlined,
  BarChartOutlined,
  TeamOutlined,
  AuditOutlined,
  LineChartOutlined,
  DashboardOutlined
} from '@ant-design/icons';
import NavigationService, { NavigationLink } from '../../services/NavigationService';

interface RelatedResourcesProps {
  resourceType: 'security-finding' | 'user' | 'team' | 'test-case' | 'notification';
  resourceId: string;
  resource: any;
  style?: React.CSSProperties;
}

const iconMap: Record<string, React.ReactNode> = {
  'FileTextOutlined': <FileTextOutlined />,
  'CheckCircleOutlined': <CheckCircleOutlined />,
  'BugOutlined': <BugOutlined />,
  'SafetyOutlined': <SafetyOutlined />,
  'LinkOutlined': <LinkOutlined />,
  'ProjectOutlined': <ProjectOutlined />,
  'CloudServerOutlined': <CloudServerOutlined />,
  'BarChartOutlined': <BarChartOutlined />,
  'TeamOutlined': <TeamOutlined />,
  'AuditOutlined': <AuditOutlined />,
  'LineChartOutlined': <LineChartOutlined />,
  'DashboardOutlined': <DashboardOutlined />
};

const RelatedResources: React.FC<RelatedResourcesProps> = ({ 
  resourceType, 
  resourceId, 
  resource,
  style 
}) => {
  const getLinks = (): NavigationLink[] => {
    switch (resourceType) {
      case 'security-finding':
        return NavigationService.getSecurityFindingLinks(resourceId, resource);
      case 'user':
      case 'team':
        return NavigationService.getUserTeamLinks(resourceId, resource);
      case 'notification':
        const link = NavigationService.getNotificationLink(resource);
        return link ? [link] : [];
      default:
        return [];
    }
  };

  const links = getLinks();

  if (links.length === 0) {
    return null;
  }

  return (
    <Card 
      title="Related Resources" 
      size="small"
      style={style}
    >
      <List
        size="small"
        dataSource={links}
        renderItem={(link) => (
          <List.Item>
            <Link to={link.path} style={{ width: '100%' }}>
              <Space>
                {link.icon && iconMap[link.icon]}
                <span>{link.label}</span>
              </Space>
            </Link>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default RelatedResources;
