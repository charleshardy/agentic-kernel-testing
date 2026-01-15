import React from 'react';
import { getDeviceType, spacing } from '../../styles/responsive';

interface ResponsivePageContainerProps {
  children: React.ReactNode;
  maxWidth?: number;
  centered?: boolean;
}

/**
 * Responsive page container that adapts padding and layout based on device type
 */
const ResponsivePageContainer: React.FC<ResponsivePageContainerProps> = ({
  children,
  maxWidth,
  centered = false
}) => {
  const deviceType = getDeviceType();
  
  const getPadding = () => {
    switch (deviceType) {
      case 'mobile':
        return spacing.mobile.md;
      case 'tablet':
        return spacing.tablet.md;
      default:
        return spacing.desktop.md;
    }
  };

  return (
    <div
      style={{
        padding: `${getPadding()}px`,
        maxWidth: maxWidth || '100%',
        margin: centered ? '0 auto' : undefined,
        width: '100%'
      }}
    >
      {children}
    </div>
  );
};

export default ResponsivePageContainer;
