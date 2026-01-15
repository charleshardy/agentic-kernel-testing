import React, { useState, useEffect } from 'react';
import { Layout, Menu, Drawer, Button } from 'antd';
import { MenuOutlined, CloseOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { getDeviceType, isTouchDevice, touchTargets } from '../../styles/responsive';

const { Sider } = Layout;

interface ResponsiveSidebarProps {
  menuItems: any[];
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
}

const ResponsiveSidebar: React.FC<ResponsiveSidebarProps> = ({
  menuItems,
  collapsed,
  onCollapse
}) => {
  const [deviceType, setDeviceType] = useState(getDeviceType());
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const [isTouch, setIsTouch] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleResize = () => {
      setDeviceType(getDeviceType());
    };

    setIsTouch(isTouchDevice());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMenuClick = (path: string) => {
    navigate(path);
    if (deviceType === 'mobile') {
      setMobileDrawerVisible(false);
    }
  };

  // Mobile: Use drawer
  if (deviceType === 'mobile') {
    return (
      <>
        <Button
          type="primary"
          icon={<MenuOutlined />}
          onClick={() => setMobileDrawerVisible(true)}
          style={{
            position: 'fixed',
            top: 16,
            left: 16,
            zIndex: 1000,
            minWidth: touchTargets.recommended,
            minHeight: touchTargets.recommended
          }}
        />
        <Drawer
          placement="left"
          onClose={() => setMobileDrawerVisible(false)}
          open={mobileDrawerVisible}
          width="80%"
          bodyStyle={{ padding: 0 }}
          closeIcon={<CloseOutlined style={{ fontSize: 20 }} />}
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => handleMenuClick(key)}
            style={{
              height: '100%',
              borderRight: 0,
              // Increase touch targets for mobile
              fontSize: 16,
              lineHeight: `${touchTargets.recommended}px`
            }}
          />
        </Drawer>
      </>
    );
  }

  // Tablet: Collapsible sidebar with larger touch targets
  if (deviceType === 'tablet') {
    return (
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={onCollapse}
        width={240}
        collapsedWidth={isTouch ? touchTargets.comfortable : 80}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0
        }}
      >
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
          style={{
            // Larger touch targets for tablet
            fontSize: 15,
            lineHeight: isTouch ? `${touchTargets.recommended}px` : 'normal'
          }}
        />
      </Sider>
    );
  }

  // Desktop: Standard sidebar
  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      width={256}
      collapsedWidth={80}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0
      }}
    >
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => handleMenuClick(key)}
      />
    </Sider>
  );
};

export default ResponsiveSidebar;
