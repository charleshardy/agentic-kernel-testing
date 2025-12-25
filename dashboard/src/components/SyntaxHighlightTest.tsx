import React from 'react'
import { Card, Alert } from 'antd'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs, prism } from 'react-syntax-highlighter/dist/esm/styles/prism'

const SyntaxHighlightTest: React.FC = () => {
  const testCode = `#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

static int __init test_init(void) {
    printk(KERN_INFO "Test module loaded\\n");
    return 0;
}

static void __exit test_exit(void) {
    printk(KERN_INFO "Test module unloaded\\n");
}

module_init(test_init);
module_exit(test_exit);
MODULE_LICENSE("GPL");`

  const bashCode = `#!/bin/bash
# Build the kernel module
make clean
make

# Load the module
sudo insmod test_module.ko

# Check results
cat /proc/test_results

# Unload the module
sudo rmmod test_module`

  return (
    <div style={{ padding: '20px' }}>
      <Alert
        message="Syntax Highlighting Test"
        description="This component tests if syntax highlighting is working correctly."
        type="info"
        style={{ marginBottom: 16 }}
      />
      
      <Card title="C Code with vscDarkPlus Theme" style={{ marginBottom: 16 }}>
        <SyntaxHighlighter
          language="c"
          style={vscDarkPlus}
          customStyle={{
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
          }}
          showLineNumbers={true}
        >
          {testCode}
        </SyntaxHighlighter>
      </Card>
      
      <Card title="Bash Code with vscDarkPlus Theme" style={{ marginBottom: 16 }}>
        <SyntaxHighlighter
          language="bash"
          style={vscDarkPlus}
          customStyle={{
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
          }}
          showLineNumbers={true}
        >
          {bashCode}
        </SyntaxHighlighter>
      </Card>
      
      <Card title="C Code with VS Light Theme">
        <SyntaxHighlighter
          language="c"
          style={vs}
          showLineNumbers={true}
        >
          {testCode}
        </SyntaxHighlighter>
      </Card>
    </div>
  )
}

export default SyntaxHighlightTest