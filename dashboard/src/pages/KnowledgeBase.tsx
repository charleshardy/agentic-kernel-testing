import React from 'react'
import { Card, Row, Col, Input, Table, Tag, Space, Button, Tabs, List, Avatar } from 'antd'
import { 
  BookOutlined, 
  SearchOutlined, 
  FileTextOutlined,
  QuestionCircleOutlined,
  BulbOutlined,
  StarOutlined,
  EyeOutlined,
  EditOutlined,
  PlusOutlined,
  UserOutlined
} from '@ant-design/icons'

const { Search } = Input
const { TabPane } = Tabs

const KnowledgeBase: React.FC = () => {
  // Mock knowledge base data
  const stats = {
    totalArticles: 156,
    popularArticles: 23,
    recentUpdates: 8,
    searchQueries: 342
  }

  const articles = [
    {
      key: '1',
      title: 'Getting Started with Kernel Testing',
      category: 'Tutorial',
      author: 'Alice Johnson',
      lastUpdated: '2024-01-10',
      views: 245,
      rating: 4.8,
      tags: ['kernel', 'testing', 'beginner'],
      description: 'Complete guide to setting up and running kernel tests for new developers'
    },
    {
      key: '2',
      title: 'Debugging Memory Leaks in Kernel Modules',
      category: 'Troubleshooting',
      author: 'Bob Smith',
      lastUpdated: '2024-01-08',
      views: 189,
      rating: 4.9,
      tags: ['debugging', 'memory', 'kernel'],
      description: 'Step-by-step guide to identify and fix memory leaks in kernel code'
    },
    {
      key: '3',
      title: 'Security Testing Best Practices',
      category: 'Security',
      author: 'Carol Davis',
      lastUpdated: '2024-01-05',
      views: 167,
      rating: 4.7,
      tags: ['security', 'best-practices', 'testing'],
      description: 'Comprehensive security testing methodology for kernel and BSP development'
    },
    {
      key: '4',
      title: 'Performance Optimization Techniques',
      category: 'Performance',
      author: 'David Wilson',
      lastUpdated: '2024-01-03',
      views: 134,
      rating: 4.6,
      tags: ['performance', 'optimization', 'profiling'],
      description: 'Advanced techniques for optimizing kernel performance and reducing latency'
    }
  ]

  const faqs = [
    {
      key: '1',
      question: 'How do I configure test environments for different hardware?',
      answer: 'Use the Test Environment page to configure QEMU virtual machines or connect physical hardware boards. Each environment can be customized with specific kernel configurations and test parameters.',
      category: 'Environment Setup',
      helpful: 23,
      views: 156
    },
    {
      key: '2',
      question: 'What should I do when tests fail with memory errors?',
      answer: 'Memory errors typically indicate kernel address sanitizer (KASAN) findings. Check the test logs for specific error messages, review the code changes that triggered the test, and use debugging tools like GDB or crash dumps.',
      category: 'Troubleshooting',
      helpful: 18,
      views: 134
    },
    {
      key: '3',
      question: 'How can I add custom test cases to the system?',
      answer: 'Navigate to Test Cases page and click "Create Test Case". You can write custom test scripts, define test parameters, and specify target environments. The AI generator can also help create test cases based on code analysis.',
      category: 'Test Creation',
      helpful: 31,
      views: 198
    }
  ]

  const recentActivity = [
    {
      key: '1',
      type: 'article_created',
      title: 'New article: "ARM64 Testing Guidelines"',
      user: 'Alice Johnson',
      timestamp: '2024-01-13 10:30:00'
    },
    {
      key: '2',
      type: 'article_updated',
      title: 'Updated: "Security Testing Best Practices"',
      user: 'Carol Davis',
      timestamp: '2024-01-13 09:15:00'
    },
    {
      key: '3',
      type: 'faq_added',
      title: 'New FAQ: "How to interpret coverage reports?"',
      user: 'Bob Smith',
      timestamp: '2024-01-13 08:45:00'
    }
  ]

  const articleColumns = [
    {
      title: 'Article',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: any) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{title}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
          <div style={{ marginTop: '8px' }}>
            {record.tags.map((tag: string) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
          </div>
        </div>
      )
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => {
        const colors = {
          'Tutorial': 'blue',
          'Troubleshooting': 'orange',
          'Security': 'red',
          'Performance': 'green'
        }
        return <Tag color={colors[category as keyof typeof colors]}>{category}</Tag>
      }
    },
    {
      title: 'Author',
      dataIndex: 'author',
      key: 'author',
      render: (author: string) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          <span style={{ fontSize: '12px' }}>{author}</span>
        </Space>
      )
    },
    {
      title: 'Updated',
      dataIndex: 'lastUpdated',
      key: 'lastUpdated',
      render: (date: string) => <span style={{ fontSize: '12px' }}>{date}</span>
    },
    {
      title: 'Views',
      dataIndex: 'views',
      key: 'views',
      render: (views: number) => (
        <Space>
          <EyeOutlined />
          <span>{views}</span>
        </Space>
      )
    },
    {
      title: 'Rating',
      dataIndex: 'rating',
      key: 'rating',
      render: (rating: number) => (
        <Space>
          <StarOutlined style={{ color: '#faad14' }} />
          <span>{rating}</span>
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: () => (
        <Space>
          <Button size="small" icon={<EyeOutlined />}>View</Button>
          <Button size="small" icon={<EditOutlined />}>Edit</Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <BookOutlined />
          Knowledge Base
        </h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Searchable documentation, tutorials, and troubleshooting guides
        </p>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff', marginBottom: '8px' }} />
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>{stats.totalArticles}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Articles</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <StarOutlined style={{ fontSize: '24px', color: '#faad14', marginBottom: '8px' }} />
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>{stats.popularArticles}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Popular Articles</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <BulbOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>{stats.recentUpdates}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Recent Updates</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <SearchOutlined style={{ fontSize: '24px', color: '#722ed1', marginBottom: '8px' }} />
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>{stats.searchQueries}</div>
              <div style={{ fontSize: '14px', color: '#666' }}>Search Queries</div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card style={{ marginBottom: '24px' }}>
        <Search
          placeholder="Search articles, tutorials, and documentation..."
          size="large"
          prefix={<SearchOutlined />}
          style={{ marginBottom: '16px' }}
        />
        <div style={{ fontSize: '12px', color: '#666' }}>
          Popular searches: kernel testing, memory debugging, security scanning, performance optimization
        </div>
      </Card>

      <Card>
        <Tabs defaultActiveKey="articles">
          <TabPane 
            tab={
              <span>
                <FileTextOutlined />
                Articles
              </span>
            } 
            key="articles"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
              <h3>Documentation Articles</h3>
              <Button type="primary" icon={<PlusOutlined />}>
                Create Article
              </Button>
            </div>
            <Table
              columns={articleColumns}
              dataSource={articles}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <QuestionCircleOutlined />
                FAQ
              </span>
            } 
            key="faq"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
              <h3>Frequently Asked Questions</h3>
              <Button type="primary" icon={<PlusOutlined />}>
                Add FAQ
              </Button>
            </div>
            <List
              itemLayout="vertical"
              dataSource={faqs}
              renderItem={(item) => (
                <List.Item
                  key={item.key}
                  actions={[
                    <Space key="stats">
                      <EyeOutlined /> {item.views}
                      <span style={{ marginLeft: '16px' }}>👍 {item.helpful}</span>
                    </Space>
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <QuestionCircleOutlined />
                        <span>{item.question}</span>
                        <Tag>{item.category}</Tag>
                      </div>
                    }
                    description={item.answer}
                  />
                </List.Item>
              )}
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <BulbOutlined />
                Recent Activity
              </span>
            } 
            key="activity"
          >
            <div style={{ marginBottom: '16px' }}>
              <h3>Recent Knowledge Base Activity</h3>
            </div>
            <List
              itemLayout="horizontal"
              dataSource={recentActivity}
              renderItem={(item) => (
                <List.Item key={item.key}>
                  <List.Item.Meta
                    avatar={<Avatar icon={<UserOutlined />} />}
                    title={item.title}
                    description={
                      <Space>
                        <span>{item.user}</span>
                        <span style={{ color: '#666' }}>•</span>
                        <span style={{ fontSize: '12px', color: '#666' }}>{item.timestamp}</span>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default KnowledgeBase