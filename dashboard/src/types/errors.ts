/**
 * Error handling types for Environment Allocation UI
 * Based on design document error categories and recovery strategies
 */

export enum ErrorCategory {
  NETWORK = 'network',
  ALLOCATION = 'allocation',
  ENVIRONMENT = 'environment',
  USER_INPUT = 'user_input',
  SYSTEM = 'system'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface ErrorDetails {
  id: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  code: string;
  message: string;
  description?: string;
  timestamp: Date;
  context?: Record<string, any>;
  suggestedActions?: SuggestedAction[];
  diagnosticInfo?: DiagnosticInfo;
  retryable: boolean;
  userFacing: boolean;
}

export interface SuggestedAction {
  id: string;
  label: string;
  description: string;
  actionType: 'retry' | 'navigate' | 'contact_support' | 'manual_fix' | 'ignore';
  actionData?: Record<string, any>;
  priority: number;
}

export interface DiagnosticInfo {
  environmentId?: string;
  testId?: string;
  allocationRequestId?: string;
  apiEndpoint?: string;
  httpStatus?: number;
  stackTrace?: string;
  systemState?: Record<string, any>;
  logs?: string[];
}

export interface RetryPolicy {
  maxAttempts: number;
  backoffStrategy: 'linear' | 'exponential';
  baseDelay: number;
  maxDelay: number;
  retryableErrors: string[];
}

export interface FallbackBehavior {
  type: 'cache' | 'mock_data' | 'degraded_mode' | 'offline_mode';
  data?: any;
  message?: string;
}

export interface ErrorRecoveryStrategy {
  errorType: string;
  retryPolicy: RetryPolicy;
  fallbackBehavior: FallbackBehavior;
  userNotification: NotificationStrategy;
}

export interface NotificationStrategy {
  type: 'toast' | 'banner' | 'modal' | 'inline';
  duration?: number;
  persistent?: boolean;
  dismissible?: boolean;
  showDiagnostics?: boolean;
}

// Specific error types for Environment Allocation
export interface AllocationError extends ErrorDetails {
  category: ErrorCategory.ALLOCATION;
  allocationRequestId?: string;
  environmentRequirements?: any;
  availableEnvironments?: any[];
  queuePosition?: number;
}

export interface EnvironmentError extends ErrorDetails {
  category: ErrorCategory.ENVIRONMENT;
  environmentId: string;
  environmentType?: string;
  healthStatus?: string;
  lastKnownState?: any;
}

export interface NetworkError extends ErrorDetails {
  category: ErrorCategory.NETWORK;
  endpoint?: string;
  httpStatus?: number;
  connectionType?: 'api' | 'websocket' | 'sse';
  isTimeout?: boolean;
}

export interface UserInputError extends ErrorDetails {
  category: ErrorCategory.USER_INPUT;
  fieldName?: string;
  inputValue?: any;
  validationRules?: string[];
}

export interface SystemError extends ErrorDetails {
  category: ErrorCategory.SYSTEM;
  serviceType?: 'api' | 'database' | 'orchestrator' | 'resource_manager';
  systemLoad?: number;
  memoryUsage?: number;
}

// Error state management
export interface ErrorState {
  errors: ErrorDetails[];
  activeError?: ErrorDetails;
  retryAttempts: Map<string, number>;
  suppressedErrors: Set<string>;
  diagnosticMode: boolean;
}

// Notification types
export interface ToastNotification {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  duration?: number;
  actions?: NotificationAction[];
  dismissible?: boolean;
}

export interface BannerNotification {
  id: string;
  type: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  persistent: boolean;
  actions?: NotificationAction[];
  showIcon?: boolean;
  closable?: boolean;
}

export interface NotificationAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary' | 'danger';
  handler: () => void | Promise<void>;
}

// Error context providers
export interface ErrorContextValue {
  errors: ErrorDetails[];
  addError: (error: Omit<ErrorDetails, 'id' | 'timestamp'>) => void;
  removeError: (errorId: string) => void;
  clearErrors: () => void;
  retryError: (errorId: string) => Promise<void>;
  suppressError: (errorId: string) => void;
  toggleDiagnosticMode: () => void;
  diagnosticMode: boolean;
}

// Predefined error configurations
export const ERROR_CONFIGS: Record<string, Partial<ErrorDetails>> = {
  // Network errors
  CONNECTION_TIMEOUT: {
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.MEDIUM,
    code: 'NET_001',
    message: 'Connection timeout',
    description: 'The request timed out while connecting to the server',
    retryable: true,
    userFacing: true,
    suggestedActions: [
      {
        id: 'retry_connection',
        label: 'Retry Connection',
        description: 'Try connecting again',
        actionType: 'retry',
        priority: 1
      },
      {
        id: 'check_network',
        label: 'Check Network',
        description: 'Verify your network connection',
        actionType: 'manual_fix',
        priority: 2
      }
    ]
  },
  
  API_UNAVAILABLE: {
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.HIGH,
    code: 'NET_002',
    message: 'API service unavailable',
    description: 'The backend API is currently unavailable',
    retryable: true,
    userFacing: true,
    suggestedActions: [
      {
        id: 'retry_api',
        label: 'Retry',
        description: 'Try the request again',
        actionType: 'retry',
        priority: 1
      },
      {
        id: 'contact_support',
        label: 'Contact Support',
        description: 'Report this issue to support',
        actionType: 'contact_support',
        priority: 3
      }
    ]
  },

  // Allocation errors
  NO_AVAILABLE_ENVIRONMENTS: {
    category: ErrorCategory.ALLOCATION,
    severity: ErrorSeverity.MEDIUM,
    code: 'ALLOC_001',
    message: 'No available environments',
    description: 'No environments match your requirements or all are currently in use',
    retryable: false,
    userFacing: true,
    suggestedActions: [
      {
        id: 'modify_requirements',
        label: 'Modify Requirements',
        description: 'Adjust your environment requirements',
        actionType: 'manual_fix',
        priority: 1
      },
      {
        id: 'wait_for_availability',
        label: 'Wait for Availability',
        description: 'Wait for environments to become available',
        actionType: 'ignore',
        priority: 2
      }
    ]
  },

  ALLOCATION_QUEUE_FULL: {
    category: ErrorCategory.ALLOCATION,
    severity: ErrorSeverity.MEDIUM,
    code: 'ALLOC_002',
    message: 'Allocation queue is full',
    description: 'The allocation queue has reached its maximum capacity',
    retryable: true,
    userFacing: true,
    suggestedActions: [
      {
        id: 'retry_later',
        label: 'Try Again Later',
        description: 'Wait for the queue to clear and try again',
        actionType: 'retry',
        priority: 1
      },
      {
        id: 'increase_priority',
        label: 'Increase Priority',
        description: 'Submit with higher priority',
        actionType: 'manual_fix',
        priority: 2
      }
    ]
  },

  // Environment errors
  ENVIRONMENT_PROVISIONING_FAILED: {
    category: ErrorCategory.ENVIRONMENT,
    severity: ErrorSeverity.HIGH,
    code: 'ENV_001',
    message: 'Environment provisioning failed',
    description: 'Failed to provision the requested environment',
    retryable: true,
    userFacing: true,
    suggestedActions: [
      {
        id: 'retry_provisioning',
        label: 'Retry Provisioning',
        description: 'Try provisioning the environment again',
        actionType: 'retry',
        priority: 1
      },
      {
        id: 'try_different_type',
        label: 'Try Different Type',
        description: 'Try a different environment type',
        actionType: 'manual_fix',
        priority: 2
      }
    ]
  },

  ENVIRONMENT_HEALTH_CHECK_FAILED: {
    category: ErrorCategory.ENVIRONMENT,
    severity: ErrorSeverity.HIGH,
    code: 'ENV_002',
    message: 'Environment health check failed',
    description: 'The environment failed its health check and may be unstable',
    retryable: true,
    userFacing: true,
    suggestedActions: [
      {
        id: 'reset_environment',
        label: 'Reset Environment',
        description: 'Reset the environment to a clean state',
        actionType: 'manual_fix',
        priority: 1
      },
      {
        id: 'use_different_environment',
        label: 'Use Different Environment',
        description: 'Switch to a different environment',
        actionType: 'manual_fix',
        priority: 2
      }
    ]
  },

  // User input errors
  INVALID_ENVIRONMENT_REQUIREMENTS: {
    category: ErrorCategory.USER_INPUT,
    severity: ErrorSeverity.LOW,
    code: 'INPUT_001',
    message: 'Invalid environment requirements',
    description: 'The specified environment requirements are invalid or incompatible',
    retryable: false,
    userFacing: true,
    suggestedActions: [
      {
        id: 'fix_requirements',
        label: 'Fix Requirements',
        description: 'Correct the environment requirements',
        actionType: 'manual_fix',
        priority: 1
      }
    ]
  },

  // System errors
  RESOURCE_EXHAUSTION: {
    category: ErrorCategory.SYSTEM,
    severity: ErrorSeverity.CRITICAL,
    code: 'SYS_001',
    message: 'System resources exhausted',
    description: 'The system has run out of available resources',
    retryable: true,
    userFacing: true,
    suggestedActions: [
      {
        id: 'wait_for_resources',
        label: 'Wait for Resources',
        description: 'Wait for system resources to become available',
        actionType: 'retry',
        priority: 1
      },
      {
        id: 'contact_admin',
        label: 'Contact Administrator',
        description: 'Contact system administrator',
        actionType: 'contact_support',
        priority: 2
      }
    ]
  }
};

// Default retry policies
export const DEFAULT_RETRY_POLICIES: Record<ErrorCategory, RetryPolicy> = {
  [ErrorCategory.NETWORK]: {
    maxAttempts: 3,
    backoffStrategy: 'exponential',
    baseDelay: 1000,
    maxDelay: 10000,
    retryableErrors: ['CONNECTION_TIMEOUT', 'API_UNAVAILABLE']
  },
  [ErrorCategory.ALLOCATION]: {
    maxAttempts: 2,
    backoffStrategy: 'linear',
    baseDelay: 5000,
    maxDelay: 15000,
    retryableErrors: ['ALLOCATION_QUEUE_FULL']
  },
  [ErrorCategory.ENVIRONMENT]: {
    maxAttempts: 2,
    backoffStrategy: 'exponential',
    baseDelay: 2000,
    maxDelay: 8000,
    retryableErrors: ['ENVIRONMENT_PROVISIONING_FAILED', 'ENVIRONMENT_HEALTH_CHECK_FAILED']
  },
  [ErrorCategory.USER_INPUT]: {
    maxAttempts: 0,
    backoffStrategy: 'linear',
    baseDelay: 0,
    maxDelay: 0,
    retryableErrors: []
  },
  [ErrorCategory.SYSTEM]: {
    maxAttempts: 1,
    backoffStrategy: 'linear',
    baseDelay: 30000,
    maxDelay: 30000,
    retryableErrors: ['RESOURCE_EXHAUSTION']
  }
};