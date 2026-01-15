import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Result, Button } from 'antd';

interface RouteGuardProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  requireAuth?: boolean;
  fallbackPath?: string;
}

/**
 * Route guard component for permission-based access control
 */
export const RouteGuard: React.FC<RouteGuardProps> = ({
  children,
  requiredPermissions = [],
  requireAuth = true,
  fallbackPath = '/login'
}) => {
  const location = useLocation();

  // Check authentication
  const isAuthenticated = checkAuthentication();
  
  if (requireAuth && !isAuthenticated) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Check permissions
  if (requiredPermissions.length > 0) {
    const hasPermission = checkPermissions(requiredPermissions);
    
    if (!hasPermission) {
      return (
        <div style={{ padding: '50px' }}>
          <Result
            status="403"
            title="Access Denied"
            subTitle="You don't have permission to access this page."
            extra={
              <Button type="primary" onClick={() => window.location.href = '/'}>
                Go Home
              </Button>
            }
          />
        </div>
      );
    }
  }

  return <>{children}</>;
};

/**
 * Check if user is authenticated
 */
function checkAuthentication(): boolean {
  // TODO: Implement actual authentication check
  // For now, return true for demo mode
  const token = sessionStorage.getItem('auth_token');
  return true; // Demo mode - always authenticated
}

/**
 * Check if user has required permissions
 */
function checkPermissions(requiredPermissions: string[]): boolean {
  // TODO: Implement actual permission check
  // For now, return true for demo mode
  const userPermissions = getUserPermissions();
  
  return requiredPermissions.every(permission =>
    userPermissions.includes(permission) || userPermissions.includes('admin')
  );
}

/**
 * Get user permissions from session/storage
 */
function getUserPermissions(): string[] {
  // TODO: Implement actual permission retrieval
  // For now, return admin permissions for demo mode
  try {
    const stored = sessionStorage.getItem('user_permissions');
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to get user permissions:', error);
  }
  
  // Demo mode - return all permissions
  return ['admin', 'read', 'write', 'execute', 'manage_users', 'manage_security'];
}

/**
 * Role-based route guard
 */
interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: string[];
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  allowedRoles
}) => {
  const userRole = getUserRole();

  if (!allowedRoles.includes(userRole)) {
    return (
      <div style={{ padding: '50px' }}>
        <Result
          status="403"
          title="Access Denied"
          subTitle={`This page is only accessible to: ${allowedRoles.join(', ')}`}
          extra={
            <Button type="primary" onClick={() => window.location.href = '/'}>
              Go Home
            </Button>
          }
        />
      </div>
    );
  }

  return <>{children}</>;
};

/**
 * Get user role
 */
function getUserRole(): string {
  // TODO: Implement actual role retrieval
  try {
    const stored = sessionStorage.getItem('user_role');
    if (stored) {
      return stored;
    }
  } catch (error) {
    console.error('Failed to get user role:', error);
  }
  
  // Demo mode - return admin role
  return 'admin';
}

/**
 * Feature flag guard
 */
interface FeatureFlagGuardProps {
  children: React.ReactNode;
  featureFlag: string;
  fallback?: React.ReactNode;
}

export const FeatureFlagGuard: React.FC<FeatureFlagGuardProps> = ({
  children,
  featureFlag,
  fallback
}) => {
  const isEnabled = checkFeatureFlag(featureFlag);

  if (!isEnabled) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div style={{ padding: '50px' }}>
        <Result
          status="404"
          title="Feature Not Available"
          subTitle="This feature is currently not enabled."
          extra={
            <Button type="primary" onClick={() => window.location.href = '/'}>
              Go Home
            </Button>
          }
        />
      </div>
    );
  }

  return <>{children}</>;
};

/**
 * Check if feature flag is enabled
 */
function checkFeatureFlag(flag: string): boolean {
  // TODO: Implement actual feature flag check
  try {
    const stored = localStorage.getItem('feature_flags');
    if (stored) {
      const flags = JSON.parse(stored);
      return flags[flag] === true;
    }
  } catch (error) {
    console.error('Failed to check feature flag:', error);
  }
  
  // Demo mode - all features enabled
  return true;
}

export default RouteGuard;
