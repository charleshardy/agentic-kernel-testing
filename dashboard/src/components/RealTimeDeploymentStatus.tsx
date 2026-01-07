import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Pause,
  Play,
  AlertTriangle,
  Zap,
  Server,
  Cpu,
  HardDrive,
  Network,
  Shield,
  Eye,
  RotateCcw,
  Download,
  Settings,
  Bell,
  BellOff
} from 'lucide-react';

// Types for real-time deployment status
interface LiveDeploymentStep {
  step_id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  progress_percentage: number;
  current_operation?: string;
  sub_operations: {
    name: string;
    status: string;
    progress: number;
  }[];
  resource_usage?: {
    cpu_percent: number;
    memory_mb: number;
    disk_io_mb: number;
    network_io_mb: number;
  };
  logs: {
    timestamp: string;
    level: 'info' | 'warning' | 'error' | 'debug';
    message: string;
  }[];
}

interface LiveDeploymentStatus {
  deployment_id: string;
  plan_id: string;
  environment_id: string;
  status: 'pending' | 'preparing' | 'connecting' | 'installing_dependencies' | 
          'deploying_scripts' | 'configuring_instrumentation' | 'validating' | 
          'completed' | 'failed' | 'cancelled';
  start_time: string;
  current_step?: string;
  completion_percentage: number;
  estimated_completion_time?: string;
  steps: LiveDeploymentStep[];
  environment_info: {
    type: string;
    architecture: string;
    kernel_version?: string;
    resource_usage: {
      cpu_percent: number;
      memory_percent: number;
      disk_percent: number;
      network_throughput_mbps: number;
    };
  };
  artifacts_info: {
    total_artifacts: number;
    deployed_artifacts: number;
    total_size_mb: number;
    deployed_size_mb: number;
  };
  instrumentation_status: {
    kasan_enabled: boolean;
    coverage_enabled: boolean;
    performance_monitoring_enabled: boolean;
    security_fuzzing_enabled: boolean;
  };
}

interface RealTimeDeploymentStatusProps {
  deploymentId: string;
  onClose?: () => void;
  showNotifications?: boolean;
}

const RealTimeDeploymentStatus: React.FC<RealTimeDeploymentStatusProps> = ({
  deploymentId,
  onClose,
  showNotifications = true
}) => {
  const [deployment, setDeployment] = useState<LiveDeploymentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState(showNotifications);
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // WebSocket connection for real-time updates
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Connect to WebSocket for real-time updates
  const connectWebSocket = useCallback(() => {
    const token = localStorage.getItem('token');
    const wsUrl = `ws://localhost:8000/api/v1/deployments/${deploymentId}/status/live?token=${token}`;
    
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setDeployment(data);
        setLoading(false);
        
        // Show notification for status changes
        if (notifications && data.status && deployment?.status !== data.status) {
          showStatusNotification(data.status, data.deployment_id);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Real-time connection failed');
      setIsConnected(false);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
          connectWebSocket();
        }
      }, 3000);
    };
    
    setWs(websocket);
  }, [deploymentId, notifications, deployment?.status]);

  // Show browser notification
  const showStatusNotification = (status: string, deploymentId: string) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      const title = `Deployment ${deploymentId}`;
      const body = `Status changed to: ${status.toUpperCase()}`;
      const icon = status === 'completed' ? '✅' : status === 'failed' ? '❌' : '🔄';
      
      new Notification(title, {
        body: `${icon} ${body}`,
        icon: '/favicon.ico'
      });
    }
  };

  // Request notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  useEffect(() => {
    connectWebSocket();
    if (notifications) {
      requestNotificationPermission();
    }
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket, notifications]);

  // Get status icon with animation
  const getStatusIcon = (status: string, animated: boolean = false) => {
    const className = `h-4 w-4 ${animated ? 'animate-spin' : ''}`;
    
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled': return <Pause className="h-4 w-4 text-gray-500" />;
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <Activity className={`${className} text-blue-500`} />;
    }
  };

  // Get step status color
  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'failed': return 'text-red-600 bg-red-50 border-red-200';
      case 'running': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'pending': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Format bytes
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get resource usage color
  const getResourceUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-500';
    if (percentage >= 75) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Activity className="h-6 w-6 animate-spin mr-2" />
            Connecting to deployment stream...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={connectWebSocket} className="mt-4">
            <RotateCcw className="h-4 w-4 mr-2" />
            Reconnect
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!deployment) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            No deployment data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Real-time Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(deployment.status, !['completed', 'failed', 'cancelled'].includes(deployment.status))}
              <div>
                <h2 className="text-xl font-bold">
                  Live Deployment: {deployment.deployment_id}
                </h2>
                <p className="text-sm text-gray-500">
                  {deployment.plan_id} → {deployment.environment_id}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-xs text-gray-500">
                  {isConnected ? 'Live' : 'Disconnected'}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setNotifications(!notifications)}
              >
                {notifications ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
              </Button>
              {onClose && (
                <Button variant="outline" size="sm" onClick={onClose}>
                  <XCircle className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Overall Progress */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-gray-500">
                {Math.round(deployment.completion_percentage)}%
                {deployment.estimated_completion_time && (
                  <span className="ml-2">
                    ETA: {new Date(deployment.estimated_completion_time).toLocaleTimeString()}
                  </span>
                )}
              </span>
            </div>
            <Progress value={deployment.completion_percentage} className="h-3" />
          </div>

          {/* Environment & Resource Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Server className="h-4 w-4" />
                  <span className="font-medium text-sm">Environment</span>
                </div>
                <div className="text-xs text-gray-600 space-y-1">
                  <div>Type: {deployment.environment_info.type}</div>
                  <div>Arch: {deployment.environment_info.architecture}</div>
                  {deployment.environment_info.kernel_version && (
                    <div>Kernel: {deployment.environment_info.kernel_version}</div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="border">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="h-4 w-4" />
                  <span className="font-medium text-sm">Resources</span>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span>CPU</span>
                    <span className={getResourceUsageColor(deployment.environment_info.resource_usage.cpu_percent)}>
                      {deployment.environment_info.resource_usage.cpu_percent}%
                    </span>
                  </div>
                  <Progress value={deployment.environment_info.resource_usage.cpu_percent} className="h-1" />
                  
                  <div className="flex items-center justify-between text-xs">
                    <span>Memory</span>
                    <span className={getResourceUsageColor(deployment.environment_info.resource_usage.memory_percent)}>
                      {deployment.environment_info.resource_usage.memory_percent}%
                    </span>
                  </div>
                  <Progress value={deployment.environment_info.resource_usage.memory_percent} className="h-1" />
                </div>
              </CardContent>
            </Card>

            <Card className="border">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <HardDrive className="h-4 w-4" />
                  <span className="font-medium text-sm">Artifacts</span>
                </div>
                <div className="text-xs text-gray-600 space-y-1">
                  <div>
                    Deployed: {deployment.artifacts_info.deployed_artifacts}/{deployment.artifacts_info.total_artifacts}
                  </div>
                  <div>
                    Size: {formatBytes(deployment.artifacts_info.deployed_size_mb * 1024 * 1024)}/
                    {formatBytes(deployment.artifacts_info.total_size_mb * 1024 * 1024)}
                  </div>
                  <Progress 
                    value={(deployment.artifacts_info.deployed_artifacts / deployment.artifacts_info.total_artifacts) * 100} 
                    className="h-1" 
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Live Deployment Steps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Zap className="h-5 w-5 mr-2" />
            Live Deployment Steps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {deployment.steps.map((step, index) => (
              <div 
                key={step.step_id} 
                className={`border rounded-lg p-4 transition-all ${getStepStatusColor(step.status)} ${
                  selectedStep === step.step_id ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(step.status, step.status === 'running')}
                    <div>
                      <h4 className="font-medium">{step.name}</h4>
                      <p className="text-sm opacity-75">
                        Step {index + 1} of {deployment.steps.length}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="text-xs">
                      {step.status.toUpperCase()}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedStep(selectedStep === step.step_id ? null : step.step_id)}
                    >
                      <Eye className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {/* Step Progress */}
                {step.progress_percentage > 0 && (
                  <div className="mb-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm">Progress</span>
                      <span className="text-sm">{Math.round(step.progress_percentage)}%</span>
                    </div>
                    <Progress value={step.progress_percentage} className="h-2" />
                  </div>
                )}

                {/* Current Operation */}
                {step.current_operation && (
                  <div className="mb-3 p-2 bg-white bg-opacity-50 rounded text-sm">
                    <span className="font-medium">Current:</span> {step.current_operation}
                  </div>
                )}

                {/* Sub-operations */}
                {step.sub_operations.length > 0 && (
                  <div className="mb-3">
                    <h5 className="text-sm font-medium mb-2">Sub-operations:</h5>
                    <div className="space-y-1">
                      {step.sub_operations.map((subOp, subIndex) => (
                        <div key={subIndex} className="flex items-center justify-between text-sm">
                          <span>{subOp.name}</span>
                          <div className="flex items-center space-x-2">
                            <Progress value={subOp.progress} className="w-16 h-1" />
                            <Badge variant="outline" className="text-xs">
                              {subOp.status}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Resource Usage */}
                {step.resource_usage && (
                  <div className="mb-3">
                    <h5 className="text-sm font-medium mb-2">Resource Usage:</h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>CPU: {step.resource_usage.cpu_percent}%</div>
                      <div>Memory: {formatBytes(step.resource_usage.memory_mb * 1024 * 1024)}</div>
                      <div>Disk I/O: {formatBytes(step.resource_usage.disk_io_mb * 1024 * 1024)}</div>
                      <div>Network: {formatBytes(step.resource_usage.network_io_mb * 1024 * 1024)}</div>
                    </div>
                  </div>
                )}

                {/* Timing Info */}
                <div className="flex items-center justify-between text-sm opacity-75">
                  <div>
                    {step.start_time && (
                      <span>Started: {new Date(step.start_time).toLocaleTimeString()}</span>
                    )}
                  </div>
                  <div>
                    Duration: {formatDuration(step.duration_seconds)}
                  </div>
                </div>

                {/* Expanded Step Details */}
                {selectedStep === step.step_id && (
                  <div className="mt-4 border-t pt-4">
                    <h5 className="text-sm font-medium mb-2">Live Logs:</h5>
                    <div className="bg-black text-green-400 p-3 rounded text-xs font-mono max-h-40 overflow-y-auto">
                      {step.logs.length > 0 ? (
                        step.logs.slice(-20).map((log, logIndex) => (
                          <div key={logIndex} className="mb-1">
                            <span className="text-gray-400">
                              [{new Date(log.timestamp).toLocaleTimeString()}]
                            </span>{' '}
                            <span className={
                              log.level === 'error' ? 'text-red-400' :
                              log.level === 'warning' ? 'text-yellow-400' :
                              log.level === 'info' ? 'text-blue-400' : 'text-gray-400'
                            }>
                              {log.level.toUpperCase()}:
                            </span>{' '}
                            {log.message}
                          </div>
                        ))
                      ) : (
                        <div className="text-gray-400">No logs available</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Instrumentation Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            Instrumentation Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${deployment.instrumentation_status.kasan_enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className="text-sm">KASAN</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${deployment.instrumentation_status.coverage_enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className="text-sm">Coverage</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${deployment.instrumentation_status.performance_monitoring_enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className="text-sm">Performance</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${deployment.instrumentation_status.security_fuzzing_enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className="text-sm">Security Fuzzing</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RealTimeDeploymentStatus;