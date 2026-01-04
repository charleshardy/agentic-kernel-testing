import React, { useState, useEffect } from 'react';
import {
  Modal,
  Tabs,
  List,
  Card,
  Button,
  Space,
  Typography,
  Tag,
  Popconfirm,
  message,
  Empty,
  Descriptions,
  Row,
  Col
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import EnvironmentPreferenceForm, { PreferenceProfile, CompatibilityResult } from './EnvironmentPreferenceForm';
import {
  HardwareRequirements,
  AllocationPreferences,
  Environment,
  EnvironmentType
} from '../types/environment';

const { TabPane } = Tabs;
const { Text, Title } = Typography;

export interface EnvironmentPreferenceModalProps {
  visible: boolean;
  onClose: () => void;
  testId?: string;
  availableEnvironments: Environment[];
  onApplyPreferences: (requirements: HardwareRequirements, preferences: AllocationPreferences) => void;
  initialRequirements?: Partial<HardwareRequirements>;
  initialPreferences?: Partial<AllocationPreferences>;
}

const EnvironmentPreferenceModal: React.FC<EnvironmentPreferenceModalProps> = ({
  visible,
  onClose,
  testId,
  availableEnvironments,
  onApplyPreferences,
  initialRequirements,
  initialPreferences
}) => {
  const [activeTab, setActiveTab] = useState('configure');
  const [savedProfiles, setSavedProfiles] = useState<PreferenceProfile[]>([]);
  const [compatibility, setCompatibility] = useState<CompatibilityResult | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<PreferenceProfile | null>(null);

  useEffect(() => {
    if (visible) {
      loadSavedProfiles();
    }
  }, [visible]);

  const loadSavedProfiles = () => {
    try {
      const profiles = localStorage.getItem('environment_preference_profiles');
      if (profiles) {
        setSavedProfiles(JSON.parse(profiles));
      }
    } catch (error) {
      console.error('Failed to load preference profiles:', error);
    }
  };

  const deleteProfile = (profileId: string) => {
    try {
      const updatedProfiles = savedProfiles.filter(p => p.id !== profileId);
      setSavedProfiles(updatedProfiles);
      localStorage.setItem('environment_preference_profiles', JSON.stringify(updatedProfiles));
      message.success('Profile deleted successfully');
    } catch (error) {
      console.error('Failed to delete profile:', error);
      message.error('Failed to delete profile');
    }
  };

  const duplicateProfile = (profile: PreferenceProfile) => {
    try {
      const newProfile: PreferenceProfile = {
        ...profile,
        id: Date.now().toString(),
        name: `${profile.name} (Copy)`,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      const updatedProfiles = [...savedProfiles, newProfile];
      setSavedProfiles(updatedProfiles);
      localStorage.setItem('environment_preference_profiles', JSON.stringify(updatedProfiles));
      message.success('Profile duplicated successfully');
    } catch (error) {
      console.error('Failed to duplicate profile:', error);
      message.error('Failed to duplicate profile');
    }
  };

  const applyProfile = (profile: PreferenceProfile) => {
    onApplyPreferences(profile.requirements, profile.preferences);
    message.success(`Applied profile: ${profile.name}`);
    onClose();
  };

  const handlePreferenceSubmit = (requirements: HardwareRequirements, preferences: AllocationPreferences) => {
    onApplyPreferences(requirements, preferences);
    onClose();
  };

  const renderProfileCard = (profile: PreferenceProfile) => {
    const { requirements, preferences } = profile;
    
    return (
      <Card
        key={profile.id}
        size="small"
        title={
          <Space>
            <Text strong>{profile.name}</Text>
            {compatibility && selectedProfile?.id === profile.id && (
              compatibility.compatible ? (
                <Tag color="green" icon={<CheckCircleOutlined />}>Compatible</Tag>
              ) : (
                <Tag color="red" icon={<ExclamationCircleOutlined />}>Incompatible</Tag>
              )
            )}
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              size="small"
              onClick={() => applyProfile(profile)}
            >
              Apply
            </Button>
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => duplicateProfile(profile)}
            />
            <Popconfirm
              title="Are you sure you want to delete this profile?"
              onConfirm={() => deleteProfile(profile.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {profile.description && (
          <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
            {profile.description}
          </Text>
        )}
        
        <Row gutter={16}>
          <Col span={12}>
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="Architecture">
                {requirements.architecture}
              </Descriptions.Item>
              <Descriptions.Item label="Memory">
                {requirements.minMemoryMB} MB
              </Descriptions.Item>
              <Descriptions.Item label="CPU Cores">
                {requirements.minCpuCores}
              </Descriptions.Item>
              <Descriptions.Item label="Isolation">
                {requirements.isolationLevel}
              </Descriptions.Item>
            </Descriptions>
          </Col>
          <Col span={12}>
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="Environment Type">
                {requirements.preferredEnvironmentType || 'Any'}
              </Descriptions.Item>
              <Descriptions.Item label="Max Wait Time">
                {preferences.maxWaitTime ? `${preferences.maxWaitTime}s` : 'No limit'}
              </Descriptions.Item>
              <Descriptions.Item label="Shared Environment">
                {preferences.allowSharedEnvironment ? 'Yes' : 'No'}
              </Descriptions.Item>
              <Descriptions.Item label="Dedicated Resources">
                {preferences.requireDedicatedResources ? 'Yes' : 'No'}
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>
        
        {requirements.requiredFeatures.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <Text strong>Required Features: </Text>
            {requirements.requiredFeatures.map(feature => (
              <Tag key={feature} size="small">{feature}</Tag>
            ))}
          </div>
        )}
      </Card>
    );
  };

  const renderEnvironmentSummary = () => {
    const environmentCounts = availableEnvironments.reduce((acc, env) => {
      acc[env.type] = (acc[env.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const architectureCounts = availableEnvironments.reduce((acc, env) => {
      acc[env.architecture] = (acc[env.architecture] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <Title level={5}>Available Environments Summary</Title>
        <Row gutter={16}>
          <Col span={12}>
            <Text strong>By Type:</Text>
            <div style={{ marginTop: 4 }}>
              {Object.entries(environmentCounts).map(([type, count]) => (
                <Tag key={type} style={{ marginBottom: 4 }}>
                  {type}: {count}
                </Tag>
              ))}
            </div>
          </Col>
          <Col span={12}>
            <Text strong>By Architecture:</Text>
            <div style={{ marginTop: 4 }}>
              {Object.entries(architectureCounts).map(([arch, count]) => (
                <Tag key={arch} style={{ marginBottom: 4 }}>
                  {arch}: {count}
                </Tag>
              ))}
            </div>
          </Col>
        </Row>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">
            Total: {availableEnvironments.length} environments available
          </Text>
        </div>
      </Card>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <SettingOutlined />
          Environment Preferences
          {testId && <Text type="secondary">for Test {testId}</Text>}
        </Space>
      }
      visible={visible}
      onCancel={onClose}
      width={800}
      footer={null}
      destroyOnClose
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Configure Preferences" key="configure">
          {renderEnvironmentSummary()}
          <EnvironmentPreferenceForm
            testId={testId}
            initialRequirements={initialRequirements}
            initialPreferences={initialPreferences}
            availableEnvironments={availableEnvironments}
            onSubmit={handlePreferenceSubmit}
            onValidationChange={(isValid, compatibilityResult) => {
              setCompatibility(compatibilityResult);
            }}
            showProfileManagement={true}
          />
        </TabPane>
        
        <TabPane tab={`Saved Profiles (${savedProfiles.length})`} key="profiles">
          {savedProfiles.length === 0 ? (
            <Empty
              description="No saved profiles"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button
                type="primary"
                onClick={() => setActiveTab('configure')}
              >
                Create First Profile
              </Button>
            </Empty>
          ) : (
            <div>
              {savedProfiles.map(renderProfileCard)}
            </div>
          )}
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default EnvironmentPreferenceModal;