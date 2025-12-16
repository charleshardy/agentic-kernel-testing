import React from 'react'
import { render, screen } from '@testing-library/react'
import TestCaseModal from '../TestCaseModal'
import { TestCase } from '../../services/api'

// Mock test case data
const mockTestCase: TestCase = {
  id: 'test-1',
  name: 'Sample Test Case',
  description: 'This is a sample test case for testing the modal',
  test_type: 'unit',
  target_subsystem: 'kernel/core',
  code_paths: ['/path/to/code.c'],
  execution_time_estimate: 30,
  test_script: '#!/bin/bash\necho "Test script content"',
  metadata: {
    generation_method: 'ai_diff',
    generated_at: '2024-01-15T10:00:00Z',
    ai_model: 'gpt-4',
    source_data: {
      diff_content: 'diff --git a/file.c b/file.c\n+added line',
      files_changed: ['file.c']
    }
  },
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z'
}

describe('TestCaseModal', () => {
  const mockProps = {
    testCase: mockTestCase,
    visible: true,
    mode: 'view' as const,
    onClose: jest.fn(),
    onSave: jest.fn(),
    onModeChange: jest.fn(),
  }

  it('renders without crashing', () => {
    render(<TestCaseModal {...mockProps} />)
    expect(screen.getByText('Test Case Details')).toBeInTheDocument()
  })

  it('displays test case information in view mode', () => {
    render(<TestCaseModal {...mockProps} />)
    expect(screen.getByText('Sample Test Case')).toBeInTheDocument()
    expect(screen.getByText('This is a sample test case for testing the modal')).toBeInTheDocument()
  })

  it('shows generation source information for AI-generated tests', () => {
    render(<TestCaseModal {...mockProps} />)
    expect(screen.getByText('AI from Diff')).toBeInTheDocument()
  })

  it('does not render when testCase is null', () => {
    render(<TestCaseModal {...mockProps} testCase={null} />)
    expect(screen.queryByText('Test Case Details')).not.toBeInTheDocument()
  })
})