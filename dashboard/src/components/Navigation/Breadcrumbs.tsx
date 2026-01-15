import React from 'react';
import { Breadcrumb } from 'antd';
import { Link } from 'react-router-dom';
import {
  HomeOutlined,
  SafetyOutlined,
  RobotOutlined,
  AuditOutlined,
  DashboardOutlined,
  ApiOutlined,
  TeamOutlined,
  BellOutlined,
  BookOutlined,
  LineChartOutlined,
  DatabaseOutlined,
  FileOutlined
} from '@ant-design/icons';
import NavigationService, { BreadcrumbItem } from '../../services/NavigationService';

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  feature?: string;
  resourceId?: string;
  resourceType?: string;
}

const iconMap: Record<string, React.ReactNode> = {
  'HomeOutlined': <HomeOutlined />,
  'SafetyOutlined': <SafetyOutlined />,
  'RobotOutlined': <RobotOutlined />,
  'AuditOutlined': <AuditOutlined />,
  'DashboardOutlined': <DashboardOutlined />,
  'ApiOutlined': <ApiOutlined />,
  'TeamOutlined': <TeamOutlined />,
  'BellOutlined': <BellOutlined />,
  'BookOutlined': <BookOutlined />,
  'LineChartOutlined': <LineChartOutlined />,
  'DatabaseOutlined': <DatabaseOutlined />,
  'FileOutlined': <FileOutlined />
};

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, feature, resourceId, resourceType }) => {
  // Generate breadcrumbs from context if not provided
  const breadcrumbItems = items || (feature ? NavigationService.generateBreadcrumbs({
    feature,
    resourceId,
    resourceType
  }) : []);

  return (
    <Breadcrumb style={{ margin: '16px 0' }}>
      {breadcrumbItems.map((item, index) => (
        <Breadcrumb.Item key={index}>
          {item.path ? (
            <Link to={item.path}>
              {item.icon && iconMap[item.icon]}
              <span style={{ marginLeft: item.icon ? '8px' : 0 }}>{item.label}</span>
            </Link>
          ) : (
            <>
              {item.icon && iconMap[item.icon]}
              <span style={{ marginLeft: item.icon ? '8px' : 0 }}>{item.label}</span>
            </>
          )}
        </Breadcrumb.Item>
      ))}
    </Breadcrumb>
  );
};

export default Breadcrumbs;
