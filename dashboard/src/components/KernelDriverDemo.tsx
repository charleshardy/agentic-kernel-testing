import React, { useState } from 'react'
import { Card, Button, Space, Typography, Divider, Tag, Alert, Collapse } from 'antd'
import { 
  CodeOutlined, 
  PlayCircleOutlined, 
  DownloadOutlined,
  FileTextOutlined,
  SettingOutlined,
  SafetyOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

const KernelDriverDemo: React.FC = () => {
  const [selectedExample, setSelectedExample] = useState<string>('kmalloc')

  const examples = {
    kmalloc: {
      name: 'kmalloc',
      file: 'mm/slab.c',
      subsystem: 'Memory Management',
      description: 'Memory allocation function testing',
      testTypes: ['Unit Tests', 'Stress Tests', 'Error Injection'],
      generatedFiles: [
        'test_kmalloc.c',
        'Makefile',
        'run_test.sh',
        'install.sh',
        'README.md'
      ],
      sampleCode: `#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/slab.h>

static int test_kmalloc_basic(void) {
    void *ptr;
    int failures = 0;
    
    // Test various allocation sizes
    for (int i = 1; i <= 100; i++) {
        size_t size = i * 1024; // 1KB to 100KB
        ptr = kmalloc(size, GFP_KERNEL);
        if (!ptr) {
            failures++;
            continue;
        }
        
        // Write and verify pattern
        memset(ptr, 0xAA, size);
        if (((char*)ptr)[0] != (char)0xAA) {
            failures++;
        }
        
        kfree(ptr);
    }
    
    return failures;
}`
    },
    schedule: {
      name: 'schedule',
      file: 'kernel/sched/core.c',
      subsystem: 'Process Scheduler',
      description: 'Scheduler function testing',
      testTypes: ['Unit Tests', 'Performance Tests', 'Concurrency Tests'],
      generatedFiles: [
        'test_schedule.c',
        'Makefile',
        'run_test.sh',
        'install.sh',
        'README.md'
      ],
      sampleCode: `#include <linux/module.h>
#include <linux/kthread.h>
#include <linux/sched.h>

static struct task_struct *test_threads[10];

static int scheduler_test_thread(void *data) {
    int thread_id = (long)data;
    
    for (int i = 0; i < 1000; i++) {
        if (thread_id % 2 == 0) {
            // CPU-intensive work
            udelay(100);
        } else {
            // I/O-bound work
            msleep(1);
        }
        
        if (i % 100 == 0) {
            schedule(); // Test voluntary context switch
        }
    }
    
    return 0;
}`
    },
    netif_rx: {
      name: 'netif_rx',
      file: 'net/core/dev.c',
      subsystem: 'Network Stack',
      description: 'Network packet reception testing',
      testTypes: ['Unit Tests', 'Integration Tests', 'Performance Tests'],
      generatedFiles: [
        'test_netif_rx.c',
        'Makefile',
        'run_test.sh',
        'install.sh',
        'README.md'
      ],
      sampleCode: `#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>

static int test_netif_rx_basic(void) {
    struct sk_buff *skb;
    int result;
    
    // Allocate test packet
    skb = alloc_skb(ETH_HLEN + 64, GFP_KERNEL);
    if (!skb) return -ENOMEM;
    
    skb_reserve(skb, ETH_HLEN);
    skb_put(skb, 64);
    
    // Test packet reception
    result = netif_rx(skb);
    
    return (result == NET_RX_SUCCESS) ? 0 : 1;
}`
    }
  }

  const currentExample = examples[selectedExample as keyof typeof examples]

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Kernel Test Driver Generation Demo</Title>
      <Paragraph>
        Explore how AI generates complete kernel test drivers for testing kernel functions directly in kernel space.
      </Paragraph>

      <Alert
        message="Interactive Demo"
        description="This demo shows the kernel driver generation process. In production, these drivers are compiled and executed in isolated kernel environments."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 24 }}>
        {/* Example Selection */}
        <Card title="Select Kernel Function" size="small">
          <Space direction="vertical" style={{ width: '100%' }}>
            {Object.entries(examples).map(([key, example]) => (
              <Button
                key={key}
                type={selectedExample === key ? 'primary' : 'default'}
                block
                onClick={() => setSelectedExample(key)}
                style={{ textAlign: 'left', height: 'auto', padding: '8px 12px' }}
              >
                <div>
                  <div style={{ fontWeight: 'bold' }}>{example.name}</div>
                  <div style={{ fontSize: '11px', opacity: 0.7 }}>
                    {example.subsystem}
                  </div>
                </div>
              </Button>
            ))}
          </Space>
        </Card>

        {/* Generated Driver Details */}
        <Card 
          title={
            <Space>
              <CodeOutlined />
              <span>Generated Kernel Driver: {currentExample.name}</span>
            </Space>
          }
          extra={
            <Space>
              <Button icon={<PlayCircleOutlined />} type="primary">
                Generate Driver
              </Button>
              <Button icon={<DownloadOutlined />}>
                Download Files
              </Button>
            </Space>
          }
        >
          <div style={{ marginBottom: 16 }}>
            <Space wrap>
              <Tag color="blue">{currentExample.file}</Tag>
              <Tag color="green">{currentExample.subsystem}</Tag>
              {currentExample.testTypes.map(type => (
                <Tag key={type} color="purple">{type}</Tag>
              ))}
            </Space>
          </div>

          <Paragraph>{currentExample.description}</Paragraph>

          <Collapse defaultActiveKey={['files']} style={{ marginBottom: 16 }}>
            <Panel 
              header={
                <Space>
                  <FileTextOutlined />
                  <span>Generated Files ({currentExample.generatedFiles.length})</span>
                </Space>
              } 
              key="files"
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 8 }}>
                {currentExample.generatedFiles.map(file => (
                  <div key={file} style={{ 
                    padding: '8px 12px', 
                    backgroundColor: '#f5f5f5', 
                    borderRadius: 4,
                    fontSize: '12px',
                    fontFamily: 'monospace'
                  }}>
                    {file}
                  </div>
                ))}
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <CodeOutlined />
                  <span>Sample Generated Code</span>
                </Space>
              } 
              key="code"
            >
              <pre style={{ 
                backgroundColor: '#f6f8fa', 
                padding: 16, 
                borderRadius: 4,
                fontSize: '12px',
                overflow: 'auto',
                maxHeight: '300px'
              }}>
                {currentExample.sampleCode}
              </pre>
            </Panel>

            <Panel 
              header={
                <Space>
                  <SettingOutlined />
                  <span>Build & Execution</span>
                </Space>
              } 
              key="build"
            >
              <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                <div style={{ marginBottom: 8 }}>
                  <strong>Build Commands:</strong>
                </div>
                <div style={{ backgroundColor: '#f6f8fa', padding: 8, borderRadius: 4, marginBottom: 12 }}>
                  make clean<br/>
                  make<br/>
                  sudo insmod test_{currentExample.name.toLowerCase()}.ko
                </div>
                
                <div style={{ marginBottom: 8 }}>
                  <strong>View Results:</strong>
                </div>
                <div style={{ backgroundColor: '#f6f8fa', padding: 8, borderRadius: 4, marginBottom: 12 }}>
                  cat /proc/test_{currentExample.name.toLowerCase()}_results<br/>
                  dmesg | tail -20
                </div>

                <div style={{ marginBottom: 8 }}>
                  <strong>Cleanup:</strong>
                </div>
                <div style={{ backgroundColor: '#f6f8fa', padding: 8, borderRadius: 4 }}>
                  sudo rmmod test_{currentExample.name.toLowerCase()}
                </div>
              </div>
            </Panel>

            <Panel 
              header={
                <Space>
                  <SafetyOutlined />
                  <span>Safety & Requirements</span>
                </Space>
              } 
              key="safety"
            >
              <div style={{ fontSize: '12px' }}>
                <div style={{ marginBottom: 12 }}>
                  <strong>Requirements:</strong>
                  <ul style={{ marginTop: 4, paddingLeft: 16 }}>
                    <li>Linux kernel headers for your kernel version</li>
                    <li>GCC compiler and build tools</li>
                    <li>Root privileges for module loading</li>
                    <li>Isolated test environment recommended</li>
                  </ul>
                </div>

                <div>
                  <strong>Safety Features:</strong>
                  <ul style={{ marginTop: 4, paddingLeft: 16 }}>
                    <li>Automatic cleanup on module unload</li>
                    <li>Error handling and bounds checking</li>
                    <li>Resource leak prevention</li>
                    <li>Timeout protection for long-running tests</li>
                    <li>Kernel log integration for debugging</li>
                  </ul>
                </div>
              </div>
            </Panel>
          </Collapse>

          <Alert
            message="Production Ready"
            description="Generated kernel drivers include comprehensive error handling, cleanup routines, and safety checks for production kernel testing environments."
            type="success"
            showIcon
          />
        </Card>
      </div>
    </div>
  )
}

export default KernelDriverDemo