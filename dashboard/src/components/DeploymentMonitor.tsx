import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Pause, 
  Play,
  RotateCcw,
  Eye,
  Download,
  Activity
} from 'lucide-react';

// Types for deployment monitoring
interface DeploymentStep {
  step_id: string;
  name: string;
  status: string;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  error_message?: string;
  progress_percentage: number;
  details: Record<string, any>;
}

interface DeploymentStatus {
  deployment_id: string;
  plan_id: string;
  environment_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  artifacts_deployed: number;
  dependencies_installed: number;
  error_message?: string;
  retry_count: number;
  completion_percentage: number;
  steps: DeploymentStep[];
}

interface DeploymentMonitorProps {
  deploymentId: string;
  onClose?: () => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const DeploymentMonitor: React.FC<DeploymentMonitorProps> = ({
  deploymentId,
  onClose,
  autoRefresh = true,
  refreshInterval = 2000
}) => {
  const [deployment, setDeployment] = useState<DeploymentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(autoRefresh);

  // Fetch deployment status
  const fetchDeploymentStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/deployments/${deploymentId}/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch deployment status: ${response.statusText}`);
      }

      const data = await response.json();
      setDeployment(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [deploymentId]);

  // Fetch deployment logs
  const fetchDeploymentLogs = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/deployments/${deploymentId}/logs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    }
  }, [deploymentId]);

  // Auto-refresh effect
  useEffect(() => {
    fetchDeploymentStatus();
    fetchDeploymentLogs();

    if (isRefreshing && deployment?.status && !['completed', 'failed', 'cancelled'].includes(deployment.status)) {
      const interval = setInterval(() => {
        fetchDeploymentStatus();
        fetchDeploymentLogs();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [fetchDeploymentStatus, fetchDeploymentLogs, isRefreshing, refreshInterval, deployment?.status]);

  // Cancel deployment
  const handleCancel = async () => {
    try {
      const response = await fetch(`/api/v1/deployments/${deploymentId}/cancel`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        await fetchDeploymentStatus();
      } else {
        throw new Error('Failed to cancel deployment');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel deployment');
    }
  };

  // Retry deployment
  const handleRetry = async () => {
    try {
      const response = await fetch(`/api/v1/deployments/${deploymentId}/retry`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        await fetchDeploymentStatus();
      } else {
        throw new Error('Failed to retry deployment');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry deployment');
    }
  };

  // Download logs
  const handleDownloadLogs = async () => {
    try {
      const response = await fetch(`/api/v1/deployments/${deploymentId}/logs?format=text`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deployment_${deploymentId}_logs.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Failed to download logs');
    }
  };

  // Get status badge variant
  const getStatusBadgeVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'default';
      case 'failed': return 'destructive';
      case 'cancelled': return 'secondary';
      case 'pending': return 'outline';
      default: return 'outline';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled': return <Pause className="h-4 w-4 text-gray-500" />;
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <Activity className="h-4 w-4 text-blue-500" />;
    }
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Get remediation suggestions
  const getRemediationSuggestions = (errorMessage?: string) => {
    if (!errorMessage) return [];
    
    const suggestions = [];
    if (errorMessage.includes('connection')) {
      suggestions.push('Check network connectivity to the target environment');
      suggestions.push('Verify environment is running and accessible');
    }
    if (errorMessage.includes('permission')) {
      suggestions.push('Check file permissions and user access rights');
      suggestions.push('Verify deployment user has necessary privileges');
    }
    if (errorMessage.includes('timeout')) {
      suggestions.push('Increase deployment timeout settings');
      suggestions.push('Check for resource constraints on target environment');
    }
    if (errorMessage.includes('artifact')) {
      suggestions.push('Verify artifact integrity and checksums');
      suggestions.push('Check artifact dependencies are available');
    }
    
    return suggestions;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Activity className="h-6 w-6 animate-spin mr-2" />
            Loading deployment status...
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
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={fetchDeploymentStatus} className="mt-4">
            <RotateCcw className="h-4 w-4 mr-2" />
            Retry
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
            Deployment not found
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(deployment.status)}
              <div>
                <CardTitle className="text-lg">
                  Deployment {deployment.deployment_id}
                </CardTitle>
                <p className="text-sm text-gray-500">
                  Plan: {deployment.plan_id} • Environment: {deployment.environment_id}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={getStatusBadgeVariant(deployment.status)}>
                {deployment.status.toUpperCase()}
              </Badge>
              {onClose && (
                <Button variant="outline" size="sm" onClick={onClose}>
                  <XCircle className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Duration</p>
              <p className="text-lg font-semibold">
                {formatDuration(deployment.duration_seconds)}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Artifacts</p>
              <p className="text-lg font-semibold">{deployment.artifacts_deployed}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Dependencies</p>
              <p className="text-lg font-semibold">{deployment.dependencies_installed}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Retries</p>
              <p className="text-lg font-semibold">{deployment.retry_count}</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-gray-500">
                {Math.round(deployment.completion_percentage)}%
              </span>
            </div>
            <Progress value={deployment.completion_percentage} className="h-2" />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsRefreshing(!isRefreshing)}
            >
              {isRefreshing ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
              {isRefreshing ? 'Pause' : 'Resume'} Auto-refresh
            </Button>
            
            {deployment.status === 'failed' && (
              <Button variant="outline" size="sm" onClick={handleRetry}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            )}
            
            {!['completed', 'failed', 'cancelled'].includes(deployment.status) && (
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <Pause className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            )}
            
            <Button variant="outline" size="sm" onClick={handleDownloadLogs}>
              <Download className="h-4 w-4 mr-2" />
              Download Logs
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display with Remediation */}
      {deployment.error_message && (
        <Card>
          <CardHeader>
            <CardTitle className="text-red-600 flex items-center">
              <XCircle className="h-5 w-5 mr-2" />
              Error Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{deployment.error_message}</AlertDescription>
            </Alert>
            
            {getRemediationSuggestions(deployment.error_message).length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Suggested Remediation:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  {getRemediationSuggestions(deployment.error_message).map((suggestion, index) => (
                    <li key={index}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Detailed Tabs */}
      <Tabs defaultValue="steps" className="w-full">
        <TabsList>
          <TabsTrigger value="steps">Deployment Steps</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>
        
        <TabsContent value="steps">
          <Card>
            <CardHeader>
              <CardTitle>Deployment Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {deployment.steps.map((step, index) => (
                  <div key={step.step_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(step.status)}
                        <div>
                          <h4 className="font-medium">{step.name}</h4>
                          <p className="text-sm text-gray-500">
                            Step {index + 1} of {deployment.steps.length}
                          </p>
                        </div>
                      </div>
                      <Badge variant={getStatusBadgeVariant(step.status)}>
                        {step.status.toUpperCase()}
                      </Badge>
                    </div>
                    
                    {step.progress_percentage > 0 && (
                      <div className="mb-2">
                        <Progress value={step.progress_percentage} className="h-1" />
                      </div>
                    )}
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Duration: </span>
                        {formatDuration(step.duration_seconds)}
                      </div>
                      {step.start_time && (
                        <div>
                          <span className="font-medium">Started: </span>
                          {new Date(step.start_time).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                    
                    {step.error_message && (
                      <Alert variant="destructive" className="mt-2">
                        <AlertDescription>{step.error_message}</AlertDescription>
                      </Alert>
                    )}
                    
                    {Object.keys(step.details).length > 0 && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-sm font-medium">
                          Step Details
                        </summary>
                        <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(step.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Deployment Logs</CardTitle>
                <Button variant="outline" size="sm" onClick={fetchDeploymentLogs}>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
                {logs.length > 0 ? (
                  logs.map((log, index) => (
                    <div key={index} className="mb-1">
                      <span className="text-gray-400">
                        [{log.timestamp}]
                      </span>{' '}
                      <span className="text-yellow-400">{log.event}:</span>{' '}
                      {log.message || JSON.stringify(log)}
                    </div>
                  ))
                ) : (
                  <div className="text-gray-400">No logs available</div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DeploymentMonitor;