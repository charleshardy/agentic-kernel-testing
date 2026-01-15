import React from 'react';
import { Breadcrumb } from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { generateBreadcrumbs, Breadcrumb as BreadcrumbItem } from '../utils/navigation';

const NavigationBreadcrumb: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const context = location.state as any;

  const breadcrumbs = generateBreadcrumbs(location.pathname, context);

  const handleClick = (path?: string) => {
    if (path) {
      navigate(path);
    }
  };

  return (
    <Breadcrumb style={{ margin: '16px 0' }}>
      {breadcrumbs.map((crumb, index) => (
        <Breadcrumb.Item
          key={index}
          onClick={() => handleClick(crumb.path)}
          style={{ cursor: crumb.path ? 'pointer' : 'default' }}
        >
          {index === 0 && <HomeOutlined />}
          {crumb.label}
        </Breadcrumb.Item>
      ))}
    </Breadcrumb>
  );
};

export default NavigationBreadcrumb;
