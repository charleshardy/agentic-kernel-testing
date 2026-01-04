import React, { useState, useEffect } from 'react';
import {
  Form,
  Select,
  InputNumber,
  Switch,
  Button,
  Card,
  Row,
  Col,
  Space,
  Tag,
  Alert,
  Tooltip,
  Progress,
  Typography,
  Divider,
  message
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import {
  EnvironmentType,
  HardwareRequirements,
  AllocationPreferences,
  Environment
} from '../types/environment';
import { apiService } from '../services/api';

const { Option } = Select;
const { Text } = Typography;

export interface PreferenceProfile {
  id: string;
  name: string;
  description?: string;
  requirements: HardwareRequirements;
  preferences: AllocationPreferences;
  createdAt: Date;
  updatedAt: Date;
}

export interface CompatibilityResult {
  compatible: boolean;
  compatibleEnvironments: Environment[];
  allocationLikelihood: number;
  issues: string[];
  suggestions: string[];
}

export interface EnvironmentPreferenceFormProps {
  testId?: string;
  initialRequirements?: Partial<HardwareRequirements>;
  initialPreferences?: Partial<AllocationPreferences>;
  availableEnvironments: Environment[];
  onSubmit: (requirements: HardwareRequirements, preferences: AllocationPreferences) => void;
  onValidationChange?: (isValid: boolean, compatibility: CompatibilityResult) => void;
  showProfileManagement?: boolean;
}

const EnvironmentPreferenceForm: React.FC<EnvironmentPreferenceFormProps> = ({
  testId,
  initialRequirements,
  initialPreferences,
  availableEnvironments,
  onSubmit,
  onValidationChange,
  showProfileManagement = true
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [compatibility, setCompatibility] = useState<CompatibilityResult | null>(null);
  const [savedProfiles, setSavedProfiles] = useState<PreferenceProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);

  // Load saved profiles on component mount
  useEffect(() => {
    loadSavedProfiles();
  }, []);

  // Validate compatibility when form values change
  useEffect(() => {
    const subscription = form.getFieldsValue();
    validateCompatibility();
  }, [form, availableEnvironments]);

  const loadSavedProfiles = async () => {
    try {
      // Load from localStorage for now - could be extended to API
      const profiles = localStorage.getItem('environment_preference_profiles');
      if (profiles) {
        setSavedProfiles(JSON.parse(profiles));
      }
    } catch (error) {
      console.error('Failed to load preference profiles:', error);
    }
  };

  const saveProfile = async (name: string, description?: string) => {
    try {
      const values = form.getFieldsValue();
      const requirements: HardwareRequirements = {
        architecture: values.architecture,
        minMemoryMB: values.minMemoryMB,
        minCpuCores: values.minCpuCores,
        requiredFeatures: values.requiredFeatures || [],
        preferredEnvironmentType: values.preferredEnvironmentType,
        isolationLevel: values.isolationLevel
      };

      const preferences: AllocationPreferences = {
        environmentType: values.environmentType,
        architecture: values.preferredArchitecture,
        maxWaitTime: values.maxWaitTime,
        allowSharedEnvironment: values.allowSharedEnvironment,
        requireDedicatedResources: values.requireDedicatedResources
      };

      const profile: PreferenceProfile = {
        id: Date.now().toString(),
        name,
        description,
        requirements,
        preferences,
        createdAt: new Date(),
        updatedAt: new Date()
      };

      const updatedProfiles = [...savedProfiles, profile];
      setSavedProfiles(updatedProfiles);
      localStorage.setItem('environment_preference_profiles', JSON.stringify(updatedProfiles));
      
      message.success(`Profile "${name}" saved successfully`);
    } catch (error) {
      console.error('Failed to save profile:', error);
      message.error('Failed to save profile');
    }
  };

  const loadProfile = (profileId: string) => {
    const profile = savedProfiles.find(p => p.id === profileId);
    if (profile) {
      form.setFieldsValue({
        architecture: profile.requirements.architecture,
        minMemoryMB: profile.requirements.minMemoryMB,
        minCpuCores: profile.requirements.minCpuCores,
        requiredFeatures: profile.requirements.requiredFeatures,
        preferredEnvironmentType: profile.requirements.preferredEnvironmentType,
        isolationLevel: profile.requirements.isolationLevel,
        environmentType: profile.preferences.environmentType,
        preferredArchitecture: profile.preferences.architecture,
        maxWaitTime: profile.preferences.maxWaitTime,
        allowSharedEnvironment: profile.preferences.allowSharedEnvironment,
        requireDedicatedResources: profile.preferences.requireDedicatedResources
      });
      setSelectedProfile(profileId);
      validateCompatibility();
      message.success(`Profile "${profile.name}" loaded`);
    }
  };

  const validateCompatibility = async () => {
    try {
      const values = form.getFieldsValue();
      
      // Skip validation if required fields are missing
      if (!values.architecture || !values.minMemoryMB || !values.minCpuCores) {
        return;
      }

      const requirements: HardwareRequirements = {
        architecture: values.architecture,
        minMemoryMB: values.minMemoryMB,
        minCpuCores: values.minCpuCores,
        requiredFeatures: values.requiredFeatures || [],
        preferredEnvironmentType: values.preferredEnvironmentType,
        isolationLevel: values.isolationLevel || 'container'
      };

      // Check compatibility against available environments
      const compatibleEnvironments = availableEnvironments.filter(env => {
        // Architecture match
        if (env.architecture !== requirements.architecture) return false;
        
        // Memory check (assuming metadata contains memory info)
        const envMemory = env.metadata.memoryMB || 0;
        if (envMemory < requirements.minMemoryMB) return false;
        
        // CPU cores check
        const envCores = env.metadata.cpuCores || 0;
        if (envCores < requirements.minCpuCores) return false;
        
        // Environment type preference
        if (requirements.preferredEnvironmentType && env.type !== requirements.preferredEnvironmentType) {
          return false;
        }
        
        return true;
      });

      const totalEnvironments = availableEnvironments.length;
      const allocationLikelihood = totalEnvironments > 0 ? 
        (compatibleEnvironments.length / totalEnvironments) * 100 : 0;

      const issues: string[] = [];
      const suggestions: string[] = [];

      if (compatibleEnvironments.length === 0) {
        issues.push('No compatible environments found');
        suggestions.push('Consider reducing memory or CPU requirements');
        suggestions.push('Try a different architecture or environment type');
      } else if (allocationLikelihood < 30) {
        issues.push('Low allocation likelihood');
        suggestions.push('Consider more flexible requirements');
      }

      const result: CompatibilityResult = {
        compatible: compatibleEnvironments.length > 0,
        compatibleEnvironments,
        allocationLikelihood,
        issues,
        suggestions
      };

      setCompatibility(result);
      onValidationChange?.(result.compatible, result);
    } catch (error) {
      console.error('Compatibility validation failed:', error);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      setLoading(true);
      
      const requirements: HardwareRequirements = {
        architecture: values.architecture,
        minMemoryMB: values.minMemoryMB,
        minCpuCores: values.minCpuCores,
        requiredFeatures: values.requiredFeatures || [],
        preferredEnvironmentType: values.preferredEnvironmentType,
        isolationLevel: values.isolationLevel
      };

      const preferences: AllocationPreferences = {
        environmentType: values.environmentType,
        architecture: values.preferredArchitecture,
        maxWaitTime: values.maxWaitTime,
        allowSharedEnvironment: values.allowSharedEnvironment ?? true,
        requireDedicatedResources: values.requireDedicatedResources ?? false
      };

      onSubmit(requirements, preferences);
    } catch (error) {
      console.error('Form submission failed:', error);
      message.error('Failed to submit preferences');
    } finally {
      setLoading(false);
    }
  };

  const renderCompatibilityStatus = () => {
    if (!compatibility) return null;

    const { compatible, allocationLikelihood, issues, suggestions, compatibleEnvironments } = compatibility;

    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={12}>
            <Space>
              {compatible ? (
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
              ) : (
                <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
              )}
              <Text strong>
                {compatible ? 'Compatible' : 'Incompatible'}
              </Text>
              <Text type="secondary">
                ({compatibleEnvironments.length} of {availableEnvironments.length} environments)
              </Text>
            </Space>
          </Col>
          <Col span={12}>
            <Space>
              <Text>Allocation Likelihood:</Text>
              <Progress
                percent={allocationLikelihood}
                size="small"
                status={allocationLikelihood > 70 ? 'success' : allocationLikelihood > 30 ? 'normal' : 'exception'}
                style={{ width: 100 }}
              />
              <Text>{allocationLikelihood.toFixed(0)}%</Text>
            </Space>
          </Col>
        </Row>
        
        {issues.length > 0 && (
          <Alert
            type="warning"
            message="Compatibility Issues"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            }
            style={{ marginTop: 8 }}
          />
        )}
        
        {suggestions.length > 0 && (
          <Alert
            type="info"
            message="Suggestions"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            }
            style={{ marginTop: 8 }}
          />
        )}
      </Card>
    );
  };

  return (
    <div>
      {showProfileManagement && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col span={12}>
              <Select
                placeholder="Load saved profile"
                value={selectedProfile}
                onChange={loadProfile}
                style={{ width: '100%' }}
                allowClear
                onClear={() => setSelectedProfile(null)}
              >
                {savedProfiles.map(profile => (
                  <Option key={profile.id} value={profile.id}>
                    {profile.name}
                    {profile.description && (
                      <Text type="secondary"> - {profile.description}</Text>
                    )}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={12}>
              <Button
                icon={<SaveOutlined />}
                onClick={() => {
                  const name = prompt('Profile name:');
                  if (name) {
                    const description = prompt('Profile description (optional):');
                    saveProfile(name, description || undefined);
                  }
                }}
              >
                Save Profile
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {renderCompatibilityStatus()}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          architecture: initialRequirements?.architecture || 'x86_64',
          minMemoryMB: initialRequirements?.minMemoryMB || 1024,
          minCpuCores: initialRequirements?.minCpuCores || 1,
          requiredFeatures: initialRequirements?.requiredFeatures || [],
          isolationLevel: initialRequirements?.isolationLevel || 'container',
          allowSharedEnvironment: initialPreferences?.allowSharedEnvironment ?? true,
          requireDedicatedResources: initialPreferences?.requireDedicatedResources ?? false,
          ...initialPreferences
        }}
        onValuesChange={validateCompatibility}
      >
        <Card title="Hardware Requirements" size="small">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="architecture"
                label="Architecture"
                rules={[{ required: true, message: 'Please select architecture' }]}
              >
                <Select placeholder="Select architecture">
                  <Option value="x86_64">x86_64</Option>
                  <Option value="arm64">ARM64</Option>
                  <Option value="riscv64">RISC-V 64</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="minMemoryMB"
                label="Minimum Memory (MB)"
                rules={[{ required: true, message: 'Please specify memory requirement' }]}
              >
                <InputNumber
                  min={512}
                  max={32768}
                  step={512}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="minCpuCores"
                label="Minimum CPU Cores"
                rules={[{ required: true, message: 'Please specify CPU requirement' }]}
              >
                <InputNumber
                  min={1}
                  max={16}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="preferredEnvironmentType"
                label="Preferred Environment Type"
              >
                <Select placeholder="Select environment type" allowClear>
                  <Option value={EnvironmentType.QEMU_X86}>QEMU x86</Option>
                  <Option value={EnvironmentType.QEMU_ARM}>QEMU ARM</Option>
                  <Option value={EnvironmentType.DOCKER}>Docker</Option>
                  <Option value={EnvironmentType.PHYSICAL}>Physical Hardware</Option>
                  <Option value={EnvironmentType.CONTAINER}>Container</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="isolationLevel"
                label="Isolation Level"
                rules={[{ required: true, message: 'Please select isolation level' }]}
              >
                <Select placeholder="Select isolation level">
                  <Option value="none">None</Option>
                  <Option value="process">Process</Option>
                  <Option value="container">Container</Option>
                  <Option value="vm">Virtual Machine</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="requiredFeatures"
            label="Required Features"
          >
            <Select
              mode="tags"
              placeholder="Add required features (e.g., kvm, nested-virt, gpu)"
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Card>

        <Card title="Allocation Preferences" size="small" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="maxWaitTime"
                label={
                  <Space>
                    Maximum Wait Time (seconds)
                    <Tooltip title="Maximum time to wait for environment allocation">
                      <InfoCircleOutlined />
                    </Tooltip>
                  </Space>
                }
              >
                <InputNumber
                  min={0}
                  max={3600}
                  placeholder="No limit"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="environmentType"
                label="Preferred Environment Type"
              >
                <Select placeholder="Any compatible type" allowClear>
                  <Option value={EnvironmentType.QEMU_X86}>QEMU x86</Option>
                  <Option value={EnvironmentType.QEMU_ARM}>QEMU ARM</Option>
                  <Option value={EnvironmentType.DOCKER}>Docker</Option>
                  <Option value={EnvironmentType.PHYSICAL}>Physical Hardware</Option>
                  <Option value={EnvironmentType.CONTAINER}>Container</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="allowSharedEnvironment"
                label="Allow Shared Environment"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="requireDedicatedResources"
                label="Require Dedicated Resources"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Divider />

        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              disabled={!compatibility?.compatible}
            >
              Apply Preferences
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                form.resetFields();
                setSelectedProfile(null);
                validateCompatibility();
              }}
            >
              Reset
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
};

export default EnvironmentPreferenceForm;