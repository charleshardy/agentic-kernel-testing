import React, { useState, useEffect, useCallback } from 'react';
import { Input, Modal, List, Tag, Spin, Empty } from 'antd';
import { SearchOutlined, FileTextOutlined, UserOutlined, TeamOutlined, 
         BellOutlined, BookOutlined, BarChartOutlined, SecurityScanOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';

interface SearchResult {
  id: string;
  type: 'test-case' | 'test-plan' | 'security' | 'user' | 'team' | 'notification' | 
        'knowledge' | 'analytics' | 'integration' | 'audit';
  title: string;
  description: string;
  path: string;
  metadata?: Record<string, any>;
}

interface UnifiedSearchProps {
  visible: boolean;
  onClose: () => void;
}

const UnifiedSearch: React.FC<UnifiedSearchProps> = ({ visible, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Debounced search function
  const performSearch = useCallback(
    debounce(async (query: string) => {
      if (!query.trim()) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        // In production, this would call the unified search API
        const mockResults = await mockUnifiedSearch(query);
        setResults(mockResults);
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    performSearch(searchQuery);
  }, [searchQuery, performSearch]);

  const handleResultClick = (result: SearchResult) => {
    navigate(result.path);
    onClose();
    setSearchQuery('');
  };

  const getIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'test-case': <FileTextOutlined />,
      'test-plan': <FileTextOutlined />,
      'security': <SecurityScanOutlined />,
      'user': <UserOutlined />,
      'team': <TeamOutlined />,
      'notification': <BellOutlined />,
      'knowledge': <BookOutlined />,
      'analytics': <BarChartOutlined />,
      'integration': <FileTextOutlined />,
      'audit': <SecurityScanOutlined />
    };
    return iconMap[type] || <FileTextOutlined />;
  };

  const getTypeColor = (type: string): string => {
    const colorMap: Record<string, string> = {
      'test-case': 'blue',
      'test-plan': 'cyan',
      'security': 'red',
      'user': 'green',
      'team': 'purple',
      'notification': 'orange',
      'knowledge': 'geekblue',
      'analytics': 'magenta',
      'integration': 'gold',
      'audit': 'volcano'
    };
    return colorMap[type] || 'default';
  };

  return (
    <Modal
      title={
        <Input
          placeholder="Search across all features..."
          prefix={<SearchOutlined />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          autoFocus
          size="large"
          style={{ border: 'none', boxShadow: 'none' }}
        />
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
      bodyStyle={{ maxHeight: '60vh', overflow: 'auto' }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
        </div>
      ) : results.length > 0 ? (
        <List
          dataSource={results}
          renderItem={(result) => (
            <List.Item
              onClick={() => handleResultClick(result)}
              style={{ cursor: 'pointer', padding: '12px' }}
              className="search-result-item"
            >
              <List.Item.Meta
                avatar={getIcon(result.type)}
                title={
                  <div>
                    {result.title}
                    <Tag color={getTypeColor(result.type)} style={{ marginLeft: 8 }}>
                      {result.type.replace('-', ' ')}
                    </Tag>
                  </div>
                }
                description={result.description}
              />
            </List.Item>
          )}
        />
      ) : searchQuery ? (
        <Empty description="No results found" />
      ) : (
        <Empty description="Start typing to search" />
      )}
    </Modal>
  );
};

// Mock search function - replace with actual API call
async function mockUnifiedSearch(query: string): Promise<SearchResult[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 200));

  const allResults: SearchResult[] = [
    {
      id: '1',
      type: 'test-case',
      title: 'Login Authentication Test',
      description: 'Validates user login with various credentials',
      path: '/test-cases/1'
    },
    {
      id: '2',
      type: 'security',
      title: 'CVE-2024-1234 Buffer Overflow',
      description: 'Critical vulnerability in memory management',
      path: '/security?finding=2'
    },
    {
      id: '3',
      type: 'user',
      title: 'John Doe',
      description: 'Senior Test Engineer - QA Team',
      path: '/users/3'
    },
    {
      id: '4',
      type: 'knowledge',
      title: 'Getting Started with Fuzzing',
      description: 'Complete guide to fuzzing configuration',
      path: '/knowledge-base/4'
    },
    {
      id: '5',
      type: 'analytics',
      title: 'Q4 Test Coverage Report',
      description: 'Comprehensive coverage analysis for Q4 2024',
      path: '/analytics?report=5'
    }
  ];

  // Filter results based on query
  const lowerQuery = query.toLowerCase();
  return allResults.filter(result =>
    result.title.toLowerCase().includes(lowerQuery) ||
    result.description.toLowerCase().includes(lowerQuery)
  );
}

export default UnifiedSearch;
