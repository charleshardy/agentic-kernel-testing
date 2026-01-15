import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Input,
  List,
  Tag,
  Button,
  Space,
  Typography,
  Avatar
} from 'antd';
import {
  BookOutlined,
  SearchOutlined,
  FileTextOutlined,
  PlusOutlined
} from '@ant-design/icons';

const { Search } = Input;
const { Title } = Typography;

const KnowledgeBase: React.FC = () => {
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Knowledge Base</Title>
        <Button type="primary" icon={<PlusOutlined />}>
          New Article
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Search
            placeholder="Search articles..."
            size="large"
            prefix={<SearchOutlined />}
            onSearch={(value) => console.log(value)}
          />
        </Col>
      </Row>

      <Card title="Articles">
        <List
          dataSource={[]}
          renderItem={item => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar icon={<FileTextOutlined />} />}
                title="Article Title"
                description="Article description"
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default KnowledgeBase;