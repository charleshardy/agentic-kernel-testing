import React, { useState, useEffect } from 'react';
import { Layout } from 'antd';
import { getDeviceType, spacing, safeAreaInsets } from '../../styles/responsive';
import ResponsiveSidebar from './ResponsiveSidebar';
import NavigationBreadcrumb from '../NavigationBreadcrumb';

const { Header, Content, Footer } = Layout;

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  menuItems: any[];
  showBreadcrumb?: boolean;
}

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  menuItems,
  showBreadcrumb = true
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [deviceType, setDeviceType] = useState(getDeviceType());

  useEffect(() => {
    const handleResize = () => {
      const newDeviceType = getDeviceType();
      setDeviceType(newDeviceType);
      
      // Auto-collapse on mobile
      if (newDeviceType === 'mobile') {
        setCollapsed(true);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const getContentPadding = () => {
    switch (deviceType) {
      case 'mobile':
        return spacing.mobile.md;
      case 'tablet':
        return spacing.tablet.md;
      default:
        return spacing.desktop.md;
    }
  };

  const getMarginLeft = () => {
    if (deviceType === 'mobile') return 0;
    if (collapsed) return deviceType === 'tablet' ? 56 : 80;
    return deviceType === 'tablet' ? 240 : 256;
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <ResponsiveSidebar
        menuItems={menuItems}
        collapsed={collapsed}
        onCollapse={setCollapsed}
      />
      <Layout
        style={{
          marginLeft: getMarginLeft(),
          transition: 'margin-left 0.2s',
          // Add safe area padding for mobile devices with notches
          paddingTop: deviceType === 'mobile' ? safeAreaInsets.top : 0,
          paddingBottom: deviceType === 'mobile' ? safeAreaInsets.bottom : 0
        }}
      >
        {deviceType !== 'mobile' && (
          <Header
            style={{
              background: '#fff',
              padding: `0 ${getContentPadding()}px`,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          >
            {showBreadcrumb && <NavigationBreadcrumb />}
          </Header>
        )}
        <Content
          style={{
            margin: deviceType === 'mobile' ? '60px 0 0 0' : '24px 16px 0',
            padding: getContentPadding(),
            minHeight: 280,
            overflow: 'initial'
          }}
        >
          {deviceType === 'mobile' && showBreadcrumb && <NavigationBreadcrumb />}
          {children}
        </Content>
        <Footer
          style={{
            textAlign: 'center',
            padding: `${getContentPadding()}px`,
            fontSize: deviceType === 'mobile' ? 12 : 14
          }}
        >
          Agentic AI Testing System ©{new Date().getFullYear()}
        </Footer>
      </Layout>
    </Layout>
  );
};

export default ResponsiveLayout;
