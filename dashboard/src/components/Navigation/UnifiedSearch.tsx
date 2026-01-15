import React, { useState, useCallback } from 'react';
import { Input, Modal, List, Tag, Space, Empty, Spin } from 'antd';
import {
  SearchOutlined,
  FileTextOutlined,
  SafetyOutlined,
  UserOutlined,
  ApiOutlined,
  BellOutlined,
  BookOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import NavigationService, { SearchResult } from '../../services/NavigationService';

const { Search } = Input;

interface UnifiedSearchProps {
  visible: boolean;
  onClose: () => void;
}

const typeIcons: Record<string, React.ReactNode> = {
  'test': <FileTextOutlined />,
  'security': <SafetyOutlined />,
  'user': <UserOutlined />,
  'integration': <ApiOutlined />,
  'notification': <BellOutlined />,
  'knowledge': <BookOutlined />,
  'analytics': <LineChartOutlined />
};

const typeColors: Record<string, string> = {
  'test': 'blue',
  'security': 'red',
  'user': 'green',
  'integration': 'purple',
  'notification': 'orange',
  'knowledge': 'cyan',
  'analytics': 'magenta'
};

// Simple debounce implementation
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };
    
    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

const UnifiedSearch: React.FC<UnifiedSearchProps> = ({ visible, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const performSearch = useCallback(
    debounce(async (query: string) => {
      if (!query || query.length < 2) {
        setSearchResults([]);
        return;
      }

      setLoading(true);
      try {
        const results = await NavigationService.unifiedSearch(query, { limit: 20 });
        setSearchResults(results);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    performSearch(value);
  };

  const handleResultClick = (result: SearchResult) => {
    navigate(result.path);
    onClose();
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <Modal
      title="Search Everything"
      visible={visible}
      onCancel={onClose}
      footer={null}
      width={700}
      bodyStyle={{ padding: '24px' }}
    >
      <Search
        placeholder="Search tests, security findings, users, integrations, and more..."
        size="large"
        prefix={<SearchOutlined />}
        value={searchQuery}
        onChange={(e) => handleSearch(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
        allowClear
      />

      <div style={{ marginTop: '24px', maxHeight: '500px', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
          </div>
        ) : searchResults.length > 0 ? (
          <List
            dataSource={searchResults}
            renderItem={(result) => (
              <List.Item
                key={result.id}
                onClick={() => handleResultClick(result)}
                style={{ cursor: 'pointer', padding: '12px 16px' }}
                className="search-result-item"
              >
                <List.Item.Meta
                  avatar={
                    <div style={{ 
                      width: '40px', 
                      height: '40px', 
                      borderRadius: '8px', 
                      background: '#f0f0f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '20px'
                    }}>
                      {typeIcons[result.type]}
                    </div>
                  }
                  title={
                    <Space>
                      <span style={{ fontWeight: 500 }}>{result.title}</span>
                      <Tag color={typeColors[result.type]}>
                        {result.type.toUpperCase()}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <div style={{ marginBottom: '4px' }}>{result.description}</div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        Relevance: {Math.round(result.relevance * 100)}%
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        ) : searchQuery.length >= 2 ? (
          <Empty
            description="No results found"
            style={{ marginTop: '40px' }}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            <SearchOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>Start typing to search across all features</div>
            <div style={{ fontSize: '12px', marginTop: '8px' }}>
              Search for tests, security findings, users, integrations, and more
            </div>
          </div>
        )}
      </div>

      <style>{`
        .search-result-item:hover {
          background-color: #f5f5f5;
          border-radius: 8px;
        }
      `}</style>
    </Modal>
  );
};

export default UnifiedSearch;
