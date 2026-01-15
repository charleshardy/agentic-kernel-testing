import React from 'react';
import { Spin, Skeleton, Card } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface LoadingStateProps {
  loading?: boolean;
  children: React.ReactNode;
  type?: 'spin' | 'skeleton' | 'card';
  tip?: string;
  size?: 'small' | 'default' | 'large';
  minHeight?: number;
}

/**
 * Loading state component with multiple display options
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  loading = true,
  children,
  type = 'spin',
  tip = 'Loading...',
  size = 'large',
  minHeight = 200
}) => {
  if (!loading) {
    return <>{children}</>;
  }

  switch (type) {
    case 'skeleton':
      return (
        <div style={{ padding: '24px' }}>
          <Skeleton active paragraph={{ rows: 4 }} />
        </div>
      );

    case 'card':
      return (
        <div style={{ padding: '24px' }}>
          <Card loading={true}>
            <Skeleton active />
          </Card>
        </div>
      );

    case 'spin':
    default:
      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: minHeight,
            width: '100%'
          }}
        >
          <Spin size={size} tip={tip} />
        </div>
      );
  }
};

/**
 * Page loading skeleton
 */
export const PageLoadingSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Skeleton.Input active style={{ width: 200, marginBottom: 24 }} />
      <Skeleton active paragraph={{ rows: 2 }} style={{ marginBottom: 24 }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: 24 }}>
        <Card loading={true}><Skeleton active /></Card>
        <Card loading={true}><Skeleton active /></Card>
        <Card loading={true}><Skeleton active /></Card>
        <Card loading={true}><Skeleton active /></Card>
      </div>
      <Skeleton active paragraph={{ rows: 6 }} />
    </div>
  );
};

/**
 * Table loading skeleton
 */
export const TableLoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div style={{ padding: '24px' }}>
      <Skeleton.Input active style={{ width: '100%', marginBottom: 16 }} />
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} active paragraph={{ rows: 1 }} style={{ marginBottom: 8 }} />
      ))}
    </div>
  );
};

/**
 * Dashboard loading skeleton
 */
export const DashboardLoadingSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Skeleton.Input active style={{ width: 300, height: 40 }} />
      </div>

      {/* Stats cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: 24 }}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <Skeleton active paragraph={{ rows: 1 }} />
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px', marginBottom: 24 }}>
        <Card>
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
        <Card>
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
      </div>

      {/* Table */}
      <Card>
        <TableLoadingSkeleton rows={8} />
      </Card>
    </div>
  );
};

/**
 * Custom loading spinner
 */
export const CustomSpinner: React.FC<{ size?: number; color?: string }> = ({
  size = 40,
  color = '#1890ff'
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: size, color }} spin />;
  return <Spin indicator={antIcon} />;
};

/**
 * Inline loading indicator
 */
export const InlineLoading: React.FC<{ text?: string }> = ({ text = 'Loading...' }) => {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <Spin size="small" />
      <span>{text}</span>
    </span>
  );
};

/**
 * Full page loading overlay
 */
export const FullPageLoading: React.FC<{ tip?: string }> = ({ tip = 'Loading...' }) => {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'rgba(255, 255, 255, 0.9)',
        zIndex: 9999
      }}
    >
      <Spin size="large" tip={tip} />
    </div>
  );
};

/**
 * Suspense fallback component
 */
export const SuspenseFallback: React.FC<{ message?: string }> = ({
  message = 'Loading component...'
}) => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 300,
        width: '100%'
      }}
    >
      <Spin size="large" tip={message} />
    </div>
  );
};

export default LoadingState;
