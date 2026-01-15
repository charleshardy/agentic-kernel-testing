import React from 'react';
import { Row, Col } from 'antd';
import { getDeviceType } from '../../styles/responsive';

interface ResponsiveCardGridProps {
  children: React.ReactNode;
  gutter?: number | [number, number];
  minCardWidth?: number;
}

/**
 * Responsive card grid that automatically adjusts columns based on device type
 */
const ResponsiveCardGrid: React.FC<ResponsiveCardGridProps> = ({
  children,
  gutter = [16, 16],
  minCardWidth = 300
}) => {
  const deviceType = getDeviceType();

  // Calculate responsive column spans
  const getColSpan = () => {
    switch (deviceType) {
      case 'mobile':
        return { xs: 24, sm: 24, md: 24, lg: 24, xl: 24 };
      case 'tablet':
        return { xs: 24, sm: 12, md: 12, lg: 12, xl: 12 };
      default:
        return { xs: 24, sm: 12, md: 8, lg: 6, xl: 6 };
    }
  };

  const colSpan = getColSpan();

  return (
    <Row gutter={gutter}>
      {React.Children.map(children, (child) => (
        <Col {...colSpan}>{child}</Col>
      ))}
    </Row>
  );
};

export default ResponsiveCardGrid;
