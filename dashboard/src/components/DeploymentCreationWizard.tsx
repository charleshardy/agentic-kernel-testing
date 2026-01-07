import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  X,
  Plus,
  Trash2,
  Upload,
  FileText,
  Settings,
  Server,
  Cpu,
  HardDrive,
  Shield,
  Activity,
  CheckCircle,
  AlertTriangle,
  Eye,
  Download,
  Rocket
} from 'lucide-react';

// Types for deployment creation
interface TestArtifact {
  id: string;
  name: string;
  type: 'script' | 'config' | 'data' | 'binary';
  content?: string;
  file?: File;
  target_path: string;
  permissions: string;
  dependencies: string[];
}

interface InstrumentationConfig {
  enable_kasan: boolean;
  enable_ktsan: boolean;
  enable_lockdep: boolean;
  enable_coverage: boolean;
  enable_performance_monitoring: boolean;
  enable_security_fuzzing: boolean;
  enable_static_analysis: boolean;
  custom_options: Record<string, any>;
}

interface EnvironmentOption {
  id: string;
  name: string;
  type: 'qemu' | 'physical' | 'cloud';
  architecture: string;
  status: 'available' | 'busy' | 'maintenance';
  capabilities: string[];
  resource_limits: {
    max_cpu: number;
    max_memory_gb: number;
    max_disk_gb: number;
  };
}

interface DeploymentConfig {
  test_plan_id: string;
  environment_id: string;
  artifacts: TestArtifact[];
  instrumentation: InstrumentationConfig;
  timeout_minutes: number;
  retry_count: number;
  priority: 'low' | 'normal' | 'high' | 'critical';
  notifications: {
    on_completion: boolean;
    on_failure: boolean;
    email_addresses: string[];
  };
}

interface DeploymentCreationWizardProps {
  onClose: () => void;
  onDeploymentCreated: (deploymentId: string) => void;
}

const DeploymentCreationWizard: React.FC<DeploymentCreationWizardProps> = ({
  onClose,
  onDeploymentCreated
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<DeploymentConfig>({
    test_plan_id: '',
    environment_id: '',
    artifacts: [],
    instrumentation: {
      enable_kasan: false,
      enable_ktsan: false,
      enable_lockdep: false,
      enable_coverage: true,
      enable_performance_monitoring: false,
      enable_security_fuzzing: false,
      enable_static_analysis: false,
      custom_options: {}
    },
    timeout_minutes: 30,
    retry_count: 2,
    priority: 'normal',
    notifications: {
      on_completion: true,
      on_failure: true,
      email_addresses: []
    }
  });
  const [environments, setEnvironments] = useState<EnvironmentOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [isCreating, setIsCreating] = useState(false);

  // Fetch available environments
  const fetchEnvironments = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/environments/available', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch environments');
      }

      const data = await response.json();
      setEnvironments(data.environments || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch environments');
    }
  }, []);

  useEffect(() => {
    fetchEnvironments();
  }, [fetchEnvironments]);

  // Add artifact
  const addArtifact = () => {
    const newArtifact: TestArtifact = {
      id: `artifact_${Date.now()}`,
      name: '',
      type: 'script',
      target_path: '/opt/testing/',
      permissions: '0755',
      dependencies: []
    };
    setConfig(prev => ({
      ...prev,
      artifacts: [...prev.artifacts, newArtifact]
    }));
  };

  // Remove artifact
  const removeArtifact = (id: string) => {
    setConfig(prev => ({
      ...prev,
      artifacts: prev.artifacts.filter(a => a.id !== id)
    }));
  };

  // Update artifact
  const updateArtifact = (id: string, updates: Partial<TestArtifact>) => {
    setConfig(prev => ({
      ...prev,
      artifacts: prev.artifacts.map(a => 
        a.id === id ? { ...a, ...updates } : a
      )
    }));
  };

  // Handle file upload
  const handleFileUpload = (artifactId: string, file: File) => {
    updateArtifact(artifactId, { file, name: file.name });
  };

  // Validate current step
  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!config.test_plan_id.trim()) {
          errors.test_plan_id = 'Test Plan ID is required';
        }
        if (!config.environment_id) {
          errors.environment_id = 'Environment selection is required';
        }
        break;
      
      case 2:
        if (config.artifacts.length === 0) {
          errors.artifacts = 'At least one artifact is required';
        }
        config.artifacts.forEach((artifact, index) => {
          if (!artifact.name.trim()) {
            errors[`artifact_${index}_name`] = 'Artifact name is required';
          }
          if (!artifact.target_path.trim()) {
            errors[`artifact_${index}_path`] = 'Target path is required';
          }
        });
        break;
      
      case 3:
        // Instrumentation validation is optional
        break;
      
      case 4:
        if (config.timeout_minutes < 1 || config.timeout_minutes > 480) {
          errors.timeout = 'Timeout must be between 1 and 480 minutes';
        }
        if (config.retry_count < 0 || config.retry_count > 5) {
          errors.retry_count = 'Retry count must be between 0 and 5';
        }
        break;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Navigate to next step
  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 5));
    }
  };

  // Navigate to previous step
  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  // Create deployment
  const createDeployment = async () => {
    if (!validateStep(4)) return;

    setIsCreating(true);
    setError(null);

    try {
      // Prepare form data for file uploads
      const formData = new FormData();
      formData.append('config', JSON.stringify({
        test_plan_id: config.test_plan_id,
        environment_id: config.environment_id,
        instrumentation: config.instrumentation,
        timeout_minutes: config.timeout_minutes,
        retry_count: config.retry_count,
        priority: config.priority,
        notifications: config.notifications
      }));

      // Add artifacts
      config.artifacts.forEach((artifact, index) => {
        if (artifact.file) {
          formData.append(`artifact_${index}_file`, artifact.file);
        }
        formData.append(`artifact_${index}_config`, JSON.stringify({
          name: artifact.name,
          type: artifact.type,
          target_path: artifact.target_path,
          permissions: artifact.permissions,
          dependencies: artifact.dependencies,
          content: artifact.content
        }));
      });

      const response = await fetch('/api/v1/deployments', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create deployment');
      }

      const result = await response.json();
      onDeploymentCreated(result.deployment_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create deployment');
    } finally {
      setIsCreating(false);
    }
  };

  // Get environment type icon
  const getEnvironmentTypeIcon = (type: string) => {
    switch (type) {
      case 'qemu': return <Server className="h-4 w-4" />;
      case 'physical': return <Cpu className="h-4 w-4" />;
      case 'cloud': return <HardDrive className="h-4 w-4" />;
      default: return <Server className="h-4 w-4" />;
    }
  };

  // Get artifact type icon
  const getArtifactTypeIcon = (type: string) => {
    switch (type) {
      case 'script': return <FileText className="h-4 w-4" />;
      case 'config': return <Settings className="h-4 w-4" />;
      case 'data': return <HardDrive className="h-4 w-4" />;
      case 'binary': return <Activity className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const steps = [
    { number: 1, title: 'Basic Configuration', description: 'Test plan and environment' },
    { number: 2, title: 'Artifacts', description: 'Upload test files and scripts' },
    { number: 3, title: 'Instrumentation', description: 'Configure monitoring tools' },
    { number: 4, title: 'Advanced Options', description: 'Timeout, retries, notifications' },
    { number: 5, title: 'Review & Deploy', description: 'Confirm and start deployment' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto w-full mx-4">
        <div className="sticky top-0 bg-white border-b p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Create New Deployment</h2>
              <p className="text-gray-500">Deploy test scripts and configurations to target environments</p>
            </div>
            <Button variant="outline" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Progress Steps */}
          <div className="mt-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.number} className="flex items-center">
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                    currentStep >= step.number 
                      ? 'bg-blue-500 border-blue-500 text-white' 
                      : 'border-gray-300 text-gray-500'
                  }`}>
                    {currentStep > step.number ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      step.number
                    )}
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-16 h-0.5 mx-2 ${
                      currentStep > step.number ? 'bg-blue-500' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2">
              {steps.map((step) => (
                <div key={step.number} className="text-center" style={{ width: '120px' }}>
                  <p className="text-xs font-medium">{step.title}</p>
                  <p className="text-xs text-gray-500">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="p-6">
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Step 1: Basic Configuration */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <Label htmlFor="test_plan_id">Test Plan ID *</Label>
                <Input
                  id="test_plan_id"
                  value={config.test_plan_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, test_plan_id: e.target.value }))}
                  placeholder="e.g., kernel_security_test_001"
                  className={validationErrors.test_plan_id ? 'border-red-500' : ''}
                />
                {validationErrors.test_plan_id && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.test_plan_id}</p>
                )}
              </div>

              <div>
                <Label>Target Environment *</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                  {environments.map((env) => (
                    <Card 
                      key={env.id}
                      className={`cursor-pointer transition-colors ${
                        config.environment_id === env.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'hover:bg-gray-50'
                      } ${env.status !== 'available' ? 'opacity-50' : ''}`}
                      onClick={() => env.status === 'available' && setConfig(prev => ({ ...prev, environment_id: env.id }))}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getEnvironmentTypeIcon(env.type)}
                            <span className="font-medium">{env.name}</span>
                          </div>
                          <Badge variant={env.status === 'available' ? 'default' : 'secondary'}>
                            {env.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-500">
                          <p>Architecture: {env.architecture}</p>
                          <p>CPU: {env.resource_limits.max_cpu} cores</p>
                          <p>Memory: {env.resource_limits.max_memory_gb}GB</p>
                          <p>Disk: {env.resource_limits.max_disk_gb}GB</p>
                        </div>
                        <div className="mt-2">
                          <div className="flex flex-wrap gap-1">
                            {env.capabilities.slice(0, 3).map((cap) => (
                              <Badge key={cap} variant="outline" className="text-xs">
                                {cap}
                              </Badge>
                            ))}
                            {env.capabilities.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{env.capabilities.length - 3} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                {validationErrors.environment_id && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.environment_id}</p>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Artifacts */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium">Test Artifacts</h3>
                  <p className="text-gray-500">Upload scripts, configurations, and test data</p>
                </div>
                <Button onClick={addArtifact}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Artifact
                </Button>
              </div>

              {validationErrors.artifacts && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{validationErrors.artifacts}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-4">
                {config.artifacts.map((artifact, index) => (
                  <Card key={artifact.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-2">
                          {getArtifactTypeIcon(artifact.type)}
                          <span className="font-medium">Artifact {index + 1}</span>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => removeArtifact(artifact.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label>Name *</Label>
                          <Input
                            value={artifact.name}
                            onChange={(e) => updateArtifact(artifact.id, { name: e.target.value })}
                            placeholder="e.g., test_script.py"
                            className={validationErrors[`artifact_${index}_name`] ? 'border-red-500' : ''}
                          />
                          {validationErrors[`artifact_${index}_name`] && (
                            <p className="text-red-500 text-sm mt-1">{validationErrors[`artifact_${index}_name`]}</p>
                          )}
                        </div>

                        <div>
                          <Label>Type</Label>
                          <select
                            value={artifact.type}
                            onChange={(e) => updateArtifact(artifact.id, { type: e.target.value as any })}
                            className="w-full border rounded px-3 py-2"
                          >
                            <option value="script">Script</option>
                            <option value="config">Configuration</option>
                            <option value="data">Test Data</option>
                            <option value="binary">Binary</option>
                          </select>
                        </div>

                        <div>
                          <Label>Target Path *</Label>
                          <Input
                            value={artifact.target_path}
                            onChange={(e) => updateArtifact(artifact.id, { target_path: e.target.value })}
                            placeholder="e.g., /opt/testing/"
                            className={validationErrors[`artifact_${index}_path`] ? 'border-red-500' : ''}
                          />
                          {validationErrors[`artifact_${index}_path`] && (
                            <p className="text-red-500 text-sm mt-1">{validationErrors[`artifact_${index}_path`]}</p>
                          )}
                        </div>

                        <div>
                          <Label>Permissions</Label>
                          <select
                            value={artifact.permissions}
                            onChange={(e) => updateArtifact(artifact.id, { permissions: e.target.value })}
                            className="w-full border rounded px-3 py-2"
                          >
                            <option value="0755">0755 (Executable)</option>
                            <option value="0644">0644 (Read/Write)</option>
                            <option value="0600">0600 (Owner only)</option>
                            <option value="0777">0777 (Full access)</option>
                          </select>
                        </div>
                      </div>

                      <div className="mt-4">
                        <Label>File Upload</Label>
                        <div className="mt-2 border-2 border-dashed border-gray-300 rounded-lg p-4">
                          <input
                            type="file"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleFileUpload(artifact.id, file);
                            }}
                            className="hidden"
                            id={`file-${artifact.id}`}
                          />
                          <label 
                            htmlFor={`file-${artifact.id}`}
                            className="cursor-pointer flex flex-col items-center"
                          >
                            <Upload className="h-8 w-8 text-gray-400 mb-2" />
                            <p className="text-sm text-gray-500">
                              {artifact.file ? artifact.file.name : 'Click to upload file'}
                            </p>
                          </label>
                        </div>
                      </div>

                      <div className="mt-4">
                        <Label>Content (Alternative to file upload)</Label>
                        <Textarea
                          value={artifact.content || ''}
                          onChange={(e) => updateArtifact(artifact.id, { content: e.target.value })}
                          placeholder="Paste content here or upload a file above"
                          rows={4}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {config.artifacts.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No artifacts added yet</p>
                  <p className="text-sm">Click "Add Artifact" to get started</p>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Instrumentation */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium">Instrumentation Configuration</h3>
                <p className="text-gray-500">Enable monitoring and debugging tools</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-base">
                      <Shield className="h-4 w-4 mr-2" />
                      Kernel Debugging
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="kasan"
                        checked={config.instrumentation.enable_kasan}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_kasan: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="kasan">KASAN (Kernel Address Sanitizer)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="ktsan"
                        checked={config.instrumentation.enable_ktsan}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_ktsan: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="ktsan">KTSAN (Kernel Thread Sanitizer)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="lockdep"
                        checked={config.instrumentation.enable_lockdep}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_lockdep: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="lockdep">Lockdep (Lock Dependency Checker)</Label>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-base">
                      <Activity className="h-4 w-4 mr-2" />
                      Performance & Coverage
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="coverage"
                        checked={config.instrumentation.enable_coverage}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_coverage: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="coverage">Code Coverage (gcov/lcov)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="performance"
                        checked={config.instrumentation.enable_performance_monitoring}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_performance_monitoring: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="performance">Performance Monitoring (perf)</Label>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-base">
                      <Shield className="h-4 w-4 mr-2" />
                      Security Testing
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="fuzzing"
                        checked={config.instrumentation.enable_security_fuzzing}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_security_fuzzing: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="fuzzing">Security Fuzzing (Syzkaller)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="static_analysis"
                        checked={config.instrumentation.enable_static_analysis}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            instrumentation: { ...prev.instrumentation, enable_static_analysis: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="static_analysis">Static Analysis (Coccinelle)</Label>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* Step 4: Advanced Options */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium">Advanced Configuration</h3>
                <p className="text-gray-500">Timeout, retries, and notification settings</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Execution Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="timeout">Timeout (minutes)</Label>
                      <Input
                        id="timeout"
                        type="number"
                        min="1"
                        max="480"
                        value={config.timeout_minutes}
                        onChange={(e) => setConfig(prev => ({ ...prev, timeout_minutes: parseInt(e.target.value) || 30 }))}
                        className={validationErrors.timeout ? 'border-red-500' : ''}
                      />
                      {validationErrors.timeout && (
                        <p className="text-red-500 text-sm mt-1">{validationErrors.timeout}</p>
                      )}
                    </div>

                    <div>
                      <Label htmlFor="retry_count">Retry Count</Label>
                      <Input
                        id="retry_count"
                        type="number"
                        min="0"
                        max="5"
                        value={config.retry_count}
                        onChange={(e) => setConfig(prev => ({ ...prev, retry_count: parseInt(e.target.value) || 0 }))}
                        className={validationErrors.retry_count ? 'border-red-500' : ''}
                      />
                      {validationErrors.retry_count && (
                        <p className="text-red-500 text-sm mt-1">{validationErrors.retry_count}</p>
                      )}
                    </div>

                    <div>
                      <Label htmlFor="priority">Priority</Label>
                      <select
                        id="priority"
                        value={config.priority}
                        onChange={(e) => setConfig(prev => ({ ...prev, priority: e.target.value as any }))}
                        className="w-full border rounded px-3 py-2"
                      >
                        <option value="low">Low</option>
                        <option value="normal">Normal</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Notifications</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="notify_completion"
                        checked={config.notifications.on_completion}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, on_completion: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="notify_completion">Notify on completion</Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="notify_failure"
                        checked={config.notifications.on_failure}
                        onCheckedChange={(checked) => 
                          setConfig(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, on_failure: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="notify_failure">Notify on failure</Label>
                    </div>

                    <div>
                      <Label htmlFor="email_addresses">Email Addresses (comma-separated)</Label>
                      <Textarea
                        id="email_addresses"
                        value={config.notifications.email_addresses.join(', ')}
                        onChange={(e) => 
                          setConfig(prev => ({
                            ...prev,
                            notifications: { 
                              ...prev.notifications, 
                              email_addresses: e.target.value.split(',').map(email => email.trim()).filter(Boolean)
                            }
                          }))
                        }
                        placeholder="user1@example.com, user2@example.com"
                        rows={3}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* Step 5: Review & Deploy */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium">Review Configuration</h3>
                <p className="text-gray-500">Verify settings before starting deployment</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Basic Configuration</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><strong>Test Plan ID:</strong> {config.test_plan_id}</div>
                      <div><strong>Environment:</strong> {environments.find(e => e.id === config.environment_id)?.name}</div>
                      <div><strong>Priority:</strong> {config.priority}</div>
                      <div><strong>Timeout:</strong> {config.timeout_minutes} minutes</div>
                      <div><strong>Retries:</strong> {config.retry_count}</div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Artifacts ({config.artifacts.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {config.artifacts.map((artifact, index) => (
                        <div key={artifact.id} className="flex items-center space-x-2">
                          {getArtifactTypeIcon(artifact.type)}
                          <span>{artifact.name}</span>
                          <Badge variant="outline" className="text-xs">{artifact.type}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Instrumentation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1 text-sm">
                      {config.instrumentation.enable_kasan && <div>✓ KASAN enabled</div>}
                      {config.instrumentation.enable_ktsan && <div>✓ KTSAN enabled</div>}
                      {config.instrumentation.enable_lockdep && <div>✓ Lockdep enabled</div>}
                      {config.instrumentation.enable_coverage && <div>✓ Code coverage enabled</div>}
                      {config.instrumentation.enable_performance_monitoring && <div>✓ Performance monitoring enabled</div>}
                      {config.instrumentation.enable_security_fuzzing && <div>✓ Security fuzzing enabled</div>}
                      {config.instrumentation.enable_static_analysis && <div>✓ Static analysis enabled</div>}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Notifications</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1 text-sm">
                      {config.notifications.on_completion && <div>✓ Completion notifications</div>}
                      {config.notifications.on_failure && <div>✓ Failure notifications</div>}
                      {config.notifications.email_addresses.length > 0 && (
                        <div>📧 {config.notifications.email_addresses.length} email recipient(s)</div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t p-6">
          <div className="flex items-center justify-between">
            <div>
              {currentStep > 1 && (
                <Button variant="outline" onClick={prevStep}>
                  Previous
                </Button>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {currentStep < 5 ? (
                <Button onClick={nextStep}>
                  Next
                </Button>
              ) : (
                <Button 
                  onClick={createDeployment} 
                  disabled={isCreating}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isCreating ? (
                    <>
                      <Activity className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Rocket className="h-4 w-4 mr-2" />
                      Start Deployment
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeploymentCreationWizard;