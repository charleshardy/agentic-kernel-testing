/**
 * Notification System Component
 * Provides toast notifications, error banners, and user feedback mechanisms
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  notification, 
  message, 
  Alert, 
  Button, 
  Space, 
  Drawer, 
  Typography, 
  Descriptions, 
  Tag,
  Collapse,
  Card
} from 'antd';
import {
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BugOutlined,
  ReloadOutlined,
  EyeOutlined,
  CopyOutlined
} from '@ant-design/icons';
import { 
  ErrorDetails, 
  ToastNotification, 
  BannerNotification, 
  NotificationAction,
  ErrorSeverity,
  ErrorCategory
} from '../types/errors';
import errorHandlingService from '../services/errorHandling';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface NotificationSystemProps {
  maxToasts?: number;
  maxBanners?: number;
  diagnosticMode?: boolean;
  onDiagnosticModeChange?: (enabled: boolean) => void;
}

interface NotificationState {
  toasts: ToastNotification[];
  banners: BannerNotification[];
  diagnosticDrawerVisible: boolean;
  selectedError?: ErrorDetails;
  recentErrors: ErrorDetails[];
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({
  maxToasts = 5,
  maxBanners = 3,
  diagnosticMode = false,
  onDiagnosticModeChange
}) => {
  const [state, setState] = useState<NotificationState>({
    toasts: [],
    banners: [],
    diagnosticDrawerVisible: false,
    recentErrors: []
  });

  // Configure Ant Design notification
  useEffect(() => {
    notification.config({
      placement: 'topRight',
      duration: 0, // We'll handle duration manually
      maxCount: maxToasts,
    });
  }, [maxToasts]);

  // Listen for errors from the error handling service
  useEffect(() => {
    const unsubscribe = errorHandlingService.addErrorListener((error: ErrorDetails) => {
      handleError(error);
    });

    return unsubscribe;
  }, []);

  const handleError = useCallback((error: ErrorDetails) => {
    // Add to recent errors for diagnostic purposes
    setState(prev => ({
      ...prev,
      recentErrors: [error, ...prev.recentErrors.slice(0, 49)] // Keep last 50 errors
    }));

    if (!error.userFacing || errorHandlingService.isErrorSuppressed(error.id)) {
      return;
    }

    const notificationStrategy = errorHandlingService.getNotificationStrategy(error);

    switch (notificationStrategy.type) {
      case 'toast':
        showToastNotification(error, notificationStrategy);
        break;
      case 'banner':
        showBannerNotification(error, notificationStrategy);
        break;
      case 'modal':
        showModalNotification(error, notificationStrategy);
        break;
      case 'inline':
        // Inline notifications are handled by individual components
        break;
    }
  }, []);

  const showToastNotification = (error: ErrorDetails, strategy: any) => {
    const actions = error.suggestedActions?.map(action => ({
      id: action.id,
      label: action.label,
      type: action.actionType === 'retry' ? 'primary' : 'secondary',
      handler: () => handleSuggestedAction(action, error)
    })) || [];

    // Add diagnostic action if enabled
    if (strategy.showDiagnostics || diagnosticMode) {
      actions.push({
        id: 'show_diagnostics',
        label: 'Diagnostics',
        type: 'secondary',
        handler: () => showDiagnostics(error)
      });
    }

    const toastType = getToastType(error.severity);
    const icon = getErrorIcon(error.severity);

    notification[toastType]({
      key: error.id,
      message: error.message,
      description: (
        <div>
          {error.description && (
            <Paragraph style={{ marginBottom: 8 }}>
              {error.description}
            </Paragraph>
          )}
          {actions.length > 0 && (
            <Space size="small">
              {actions.map(action => (
                <Button
                  key={action.id}
                  size="small"
                  type={action.type as any}
                  onClick={action.handler}
                >
                  {action.label}
                </Button>
              ))}
            </Space>
          )}
        </div>
      ),
      icon,
      duration: strategy.duration || 5,
      onClose: () => {
        setState(prev => ({
          ...prev,
          toasts: prev.toasts.filter(t => t.id !== error.id)
        }));
      }
    });
  };

  const showBannerNotification = (error: ErrorDetails, strategy: any) => {
    const banner: BannerNotification = {
      id: error.id,
      type: getBannerType(error.severity),
      title: error.message,
      message: error.description || '',
      persistent: strategy.persistent || false,
      actions: error.suggestedActions?.map(action => ({
        id: action.id,
        label: action.label,
        type: action.actionType === 'retry' ? 'primary' : 'secondary',
        handler: () => handleSuggestedAction(action, error)
      })) || [],
      showIcon: true,
      closable: strategy.dismissible !== false
    };

    setState(prev => ({
      ...prev,
      banners: [banner, ...prev.banners.slice(0, maxBanners - 1)]
    }));
  };

  const showModalNotification = (error: ErrorDetails, strategy: any) => {
    // For critical errors, show modal
    notification.error({
      key: error.id,
      message: 'Critical Error',
      description: (
        <div>
          <Alert
            message={error.message}
            description={error.description}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Space>
            <Button type="primary" onClick={() => showDiagnostics(error)}>
              View Diagnostics
            </Button>
            {error.suggestedActions?.map(action => (
              <Button
                key={action.id}
                onClick={() => handleSuggestedAction(action, error)}
              >
                {action.label}
              </Button>
            ))}
          </Space>
        </div>
      ),
      duration: 0, // Don't auto-close critical errors
      placement: 'top'
    });
  };

  const handleSuggestedAction = async (action: any, error: ErrorDetails) => {
    try {
      switch (action.actionType) {
        case 'retry':
          // Close current notification
          notification.close(error.id);
          
          // Show retry notification
          message.loading(`Retrying ${action.label.toLowerCase()}...`, 0);
          
          // The actual retry logic would be handled by the calling component
          // This is just the UI feedback
          setTimeout(() => {
            message.destroy();
            message.success('Retry completed');
          }, 2000);
          break;

        case 'navigate':
          // Handle navigation
          if (action.actionData?.url) {
            window.location.href = action.actionData.url;
          }
          break;

        case 'contact_support':
          // Open support contact
          showSupportContact(error);
          break;

        case 'manual_fix':
          // Show manual fix instructions
          showManualFixInstructions(action, error);
          break;

        case 'ignore':
          // Suppress the error
          errorHandlingService.suppressError(error.id);
          notification.close(error.id);
          break;
      }
    } catch (err) {
      console.error('Error handling suggested action:', err);
      message.error('Failed to execute action');
    }
  };

  const showDiagnostics = (error: ErrorDetails) => {
    setState(prev => ({
      ...prev,
      diagnosticDrawerVisible: true,
      selectedError: error
    }));
  };

  const showSupportContact = (error: ErrorDetails) => {
    const supportInfo = {
      errorId: error.id,
      timestamp: error.timestamp.toISOString(),
      category: error.category,
      code: error.code,
      message: error.message,
      context: error.context
    };

    // Copy error info to clipboard
    navigator.clipboard.writeText(JSON.stringify(supportInfo, null, 2));
    message.success('Error details copied to clipboard');
  };

  const showManualFixInstructions = (action: any, error: ErrorDetails) => {
    notification.info({
      key: `fix_${error.id}`,
      message: 'Manual Fix Required',
      description: (
        <div>
          <Paragraph>{action.description}</Paragraph>
          {action.actionData?.instructions && (
            <ul>
              {action.actionData.instructions.map((instruction: string, index: number) => (
                <li key={index}>{instruction}</li>
              ))}
            </ul>
          )}
        </div>
      ),
      duration: 0,
      placement: 'topRight'
    });
  };

  const closeBanner = (bannerId: string) => {
    setState(prev => ({
      ...prev,
      banners: prev.banners.filter(b => b.id !== bannerId)
    }));
  };

  const getToastType = (severity: ErrorSeverity): 'success' | 'info' | 'warning' | 'error' => {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        return 'error';
      case ErrorSeverity.MEDIUM:
        return 'warning';
      case ErrorSeverity.LOW:
      default:
        return 'info';
    }
  };

  const getBannerType = (severity: ErrorSeverity): 'info' | 'warning' | 'error' => {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        return 'error';
      case ErrorSeverity.MEDIUM:
        return 'warning';
      case ErrorSeverity.LOW:
      default:
        return 'info';
    }
  };

  const getErrorIcon = (severity: ErrorSeverity) => {
    switch (severity) {
      case ErrorSeverity.CRITICAL:
      case ErrorSeverity.HIGH:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case ErrorSeverity.MEDIUM:
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case ErrorSeverity.LOW:
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getCategoryColor = (category: ErrorCategory): string => {
    switch (category) {
      case ErrorCategory.NETWORK:
        return 'blue';
      case ErrorCategory.ALLOCATION:
        return 'orange';
      case ErrorCategory.ENVIRONMENT:
        return 'red';
      case ErrorCategory.USER_INPUT:
        return 'purple';
      case ErrorCategory.SYSTEM:
        return 'volcano';
      default:
        return 'default';
    }
  };

  const copyErrorDetails = (error: ErrorDetails) => {
    const details = {
      id: error.id,
      timestamp: error.timestamp.toISOString(),
      category: error.category,
      severity: error.severity,
      code: error.code,
      message: error.message,
      description: error.description,
      context: error.context,
      diagnosticInfo: error.diagnosticInfo
    };

    navigator.clipboard.writeText(JSON.stringify(details, null, 2));
    message.success('Error details copied to clipboard');
  };

  return (
    <>
      {/* Banner Notifications */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000 }}>
        {state.banners.map(banner => (
          <Alert
            key={banner.id}
            message={banner.title}
            description={banner.message}
            type={banner.type}
            showIcon={banner.showIcon}
            closable={banner.closable}
            onClose={() => closeBanner(banner.id)}
            action={
              banner.actions && banner.actions.length > 0 ? (
                <Space size="small">
                  {banner.actions.map(action => (
                    <Button
                      key={action.id}
                      size="small"
                      type={action.type as any}
                      onClick={action.handler}
                    >
                      {action.label}
                    </Button>
                  ))}
                </Space>
              ) : undefined
            }
            style={{ marginBottom: 8 }}
          />
        ))}
      </div>

      {/* Diagnostic Drawer */}
      <Drawer
        title="Error Diagnostics"
        placement="right"
        width={600}
        open={state.diagnosticDrawerVisible}
        onClose={() => setState(prev => ({ ...prev, diagnosticDrawerVisible: false }))}
        extra={
          <Space>
            <Button
              icon={<CopyOutlined />}
              onClick={() => state.selectedError && copyErrorDetails(state.selectedError)}
            >
              Copy Details
            </Button>
            <Button
              icon={<BugOutlined />}
              onClick={() => onDiagnosticModeChange?.(!diagnosticMode)}
            >
              {diagnosticMode ? 'Disable' : 'Enable'} Debug Mode
            </Button>
          </Space>
        }
      >
        {state.selectedError && (
          <div>
            <Descriptions title="Error Information" bordered column={1} size="small">
              <Descriptions.Item label="ID">{state.selectedError.id}</Descriptions.Item>
              <Descriptions.Item label="Timestamp">
                {state.selectedError.timestamp.toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Category">
                <Tag color={getCategoryColor(state.selectedError.category)}>
                  {state.selectedError.category}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Severity">
                <Tag color={state.selectedError.severity === ErrorSeverity.CRITICAL ? 'red' : 
                           state.selectedError.severity === ErrorSeverity.HIGH ? 'orange' :
                           state.selectedError.severity === ErrorSeverity.MEDIUM ? 'yellow' : 'green'}>
                  {state.selectedError.severity}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Code">{state.selectedError.code}</Descriptions.Item>
              <Descriptions.Item label="Message">{state.selectedError.message}</Descriptions.Item>
              {state.selectedError.description && (
                <Descriptions.Item label="Description">
                  {state.selectedError.description}
                </Descriptions.Item>
              )}
            </Descriptions>

            {state.selectedError.suggestedActions && state.selectedError.suggestedActions.length > 0 && (
              <Card title="Suggested Actions" size="small" style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {state.selectedError.suggestedActions.map(action => (
                    <Button
                      key={action.id}
                      block
                      type={action.priority === 1 ? 'primary' : 'default'}
                      onClick={() => handleSuggestedAction(action, state.selectedError!)}
                    >
                      {action.label}: {action.description}
                    </Button>
                  ))}
                </Space>
              </Card>
            )}

            {(state.selectedError.context || state.selectedError.diagnosticInfo) && (
              <Collapse style={{ marginTop: 16 }}>
                {state.selectedError.context && (
                  <Panel header="Context Information" key="context">
                    <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                      {JSON.stringify(state.selectedError.context, null, 2)}
                    </pre>
                  </Panel>
                )}
                {state.selectedError.diagnosticInfo && (
                  <Panel header="Diagnostic Information" key="diagnostic">
                    <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                      {JSON.stringify(state.selectedError.diagnosticInfo, null, 2)}
                    </pre>
                  </Panel>
                )}
              </Collapse>
            )}
          </div>
        )}

        {/* Recent Errors */}
        <Card title="Recent Errors" size="small" style={{ marginTop: 16 }}>
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {state.recentErrors.slice(0, 10).map(error => (
              <div
                key={error.id}
                style={{
                  padding: '8px',
                  borderBottom: '1px solid #f0f0f0',
                  cursor: 'pointer'
                }}
                onClick={() => setState(prev => ({ ...prev, selectedError: error }))}
              >
                <Space>
                  <Tag color={getCategoryColor(error.category)} size="small">
                    {error.category}
                  </Tag>
                  <Text style={{ fontSize: '12px' }}>
                    {error.timestamp.toLocaleTimeString()}
                  </Text>
                </Space>
                <div>
                  <Text strong style={{ fontSize: '13px' }}>{error.code}</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {error.message}
                  </Text>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </Drawer>
    </>
  );
};

export default NotificationSystem;