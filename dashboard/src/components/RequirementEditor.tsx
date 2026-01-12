import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Tag,
  Alert,
  Tooltip,
  Row,
  Col,
  Divider,
  Badge,
} from 'antd'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  BulbOutlined,
  EditOutlined,
} from '@ant-design/icons'

const { Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select

interface ValidationResult {
  isValid: boolean
  pattern: string | null
  errors: string[]
  warnings: string[]
  suggestions: string[]
  parsedComponents: {
    trigger?: string
    state?: string
    condition?: string
    system?: string
    response?: string
  }
}

interface RequirementEditorProps {
  value?: string
  onChange?: (value: string) => void
  onValidationChange?: (result: ValidationResult) => void
  glossary?: Record<string, string>
  showTemplates?: boolean
  showValidation?: boolean
}

// EARS Pattern Templates
const EARS_PATTERNS = [
  {
    key: 'event_driven',
    name: 'Event-Driven (WHEN/THEN)',
    template: 'WHEN [trigger event], THE [System] SHALL [response]',
    description: 'Use when the requirement is triggered by an event',
    example: 'WHEN the user clicks submit, THE System SHALL validate the form',
    regex: /^WHEN\s+(.+?),?\s+THE\s+(.+?)\s+SHALL\s+(.+)$/i,
  },
  {
    key: 'state_driven',
    name: 'State-Driven (WHILE)',
    template: 'WHILE [state], THE [System] SHALL [response]',
    description: 'Use when the requirement depends on a system state',
    example: 'WHILE the system is in maintenance mode, THE System SHALL reject new connections',
    regex: /^WHILE\s+(.+?),?\s+THE\s+(.+?)\s+SHALL\s+(.+)$/i,
  },
  {
    key: 'unwanted',
    name: 'Unwanted Behavior (IF/THEN)',
    template: 'IF [unwanted condition], THEN THE [System] SHALL [response]',
    description: 'Use for handling error conditions or unwanted states',
    example: 'IF memory allocation fails, THEN THE System SHALL log the error and retry',
    regex: /^IF\s+(.+?),?\s+THEN\s+THE\s+(.+?)\s+SHALL\s+(.+)$/i,
  },
  {
    key: 'ubiquitous',
    name: 'Ubiquitous (SHALL)',
    template: 'THE [System] SHALL [response]',
    description: 'Use for requirements that always apply',
    example: 'THE System SHALL encrypt all data at rest',
    regex: /^THE\s+(.+?)\s+SHALL\s+(.+)$/i,
  },
  {
    key: 'optional',
    name: 'Optional Feature',
    template: 'WHERE [feature] is supported, THE [System] SHALL [response]',
    description: 'Use for optional or configurable features',
    example: 'WHERE hardware acceleration is supported, THE System SHALL use GPU for rendering',
    regex: /^WHERE\s+(.+?)\s+is\s+supported,?\s+THE\s+(.+?)\s+SHALL\s+(.+)$/i,
  },
  {
    key: 'complex',
    name: 'Complex (WHEN/WHILE/IF)',
    template: 'WHEN [trigger], WHILE [state], IF [condition], THE [System] SHALL [response]',
    description: 'Use for complex requirements with multiple conditions',
    example: 'WHEN data is received, WHILE in active mode, IF checksum is valid, THE System SHALL process the data',
    regex: /^WHEN\s+(.+?),?\s+WHILE\s+(.+?),?\s+IF\s+(.+?),?\s+THE\s+(.+?)\s+SHALL\s+(.+)$/i,
  },
]

// Ambiguous words to detect
const AMBIGUOUS_WORDS = [
  'appropriate', 'adequate', 'reasonable', 'sufficient', 'timely',
  'fast', 'slow', 'quick', 'efficient', 'effective',
  'user-friendly', 'intuitive', 'easy', 'simple', 'complex',
  'many', 'few', 'some', 'several', 'various',
  'etc', 'and so on', 'and more', 'similar',
  'may', 'might', 'could', 'possibly', 'optionally',
]

const RequirementEditor: React.FC<RequirementEditorProps> = ({
  value = '',
  onChange,
  onValidationChange,
  glossary = {},
  showTemplates = true,
  showValidation = true,
}) => {
  const [text, setText] = useState(value)
  const [validation, setValidation] = useState<ValidationResult>({
    isValid: false,
    pattern: null,
    errors: [],
    warnings: [],
    suggestions: [],
    parsedComponents: {},
  })
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null)

  // Validate requirement text
  const validateRequirement = useCallback((reqText: string): ValidationResult => {
    const result: ValidationResult = {
      isValid: false,
      pattern: null,
      errors: [],
      warnings: [],
      suggestions: [],
      parsedComponents: {},
    }

    if (!reqText.trim()) {
      result.errors.push('Requirement text is empty')
      return result
    }

    // Check for EARS pattern match
    let patternMatched = false
    for (const pattern of EARS_PATTERNS) {
      const match = reqText.match(pattern.regex)
      if (match) {
        patternMatched = true
        result.pattern = pattern.key
        
        // Extract components based on pattern
        if (pattern.key === 'event_driven') {
          result.parsedComponents = {
            trigger: match[1],
            system: match[2],
            response: match[3],
          }
        } else if (pattern.key === 'state_driven') {
          result.parsedComponents = {
            state: match[1],
            system: match[2],
            response: match[3],
          }
        } else if (pattern.key === 'unwanted') {
          result.parsedComponents = {
            condition: match[1],
            system: match[2],
            response: match[3],
          }
        } else if (pattern.key === 'ubiquitous') {
          result.parsedComponents = {
            system: match[1],
            response: match[2],
          }
        } else if (pattern.key === 'optional') {
          result.parsedComponents = {
            condition: match[1],
            system: match[2],
            response: match[3],
          }
        } else if (pattern.key === 'complex') {
          result.parsedComponents = {
            trigger: match[1],
            state: match[2],
            condition: match[3],
            system: match[4],
            response: match[5],
          }
        }
        break
      }
    }

    if (!patternMatched) {
      result.errors.push('Requirement does not match any EARS pattern')
      result.suggestions.push('Try using one of the EARS templates above')
    }

    // Check for ambiguous words
    const lowerText = reqText.toLowerCase()
    const foundAmbiguous = AMBIGUOUS_WORDS.filter(word => 
      lowerText.includes(word.toLowerCase())
    )
    if (foundAmbiguous.length > 0) {
      result.warnings.push(`Ambiguous terms detected: ${foundAmbiguous.join(', ')}`)
      result.suggestions.push('Consider replacing ambiguous terms with specific, measurable criteria')
    }

    // Check for undefined glossary terms (words in brackets or capitalized)
    const capitalizedWords = reqText.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g) || []
    const undefinedTerms = capitalizedWords.filter(term => 
      !glossary[term] && term !== 'THE' && term !== 'SHALL' && term !== 'WHEN' && 
      term !== 'WHILE' && term !== 'IF' && term !== 'THEN' && term !== 'WHERE'
    )
    if (undefinedTerms.length > 0 && Object.keys(glossary).length > 0) {
      result.warnings.push(`Terms not in glossary: ${undefinedTerms.join(', ')}`)
    }

    // Check for SHALL keyword
    if (!reqText.includes('SHALL')) {
      result.errors.push('Missing SHALL keyword - requirements must use SHALL for mandatory behavior')
    }

    // Check for system identification
    if (!reqText.includes('THE ') || !reqText.match(/THE\s+\w+/)) {
      result.warnings.push('System not clearly identified - use "THE [System]" format')
    }

    result.isValid = result.errors.length === 0
    return result
  }, [glossary])

  // Update validation when text changes
  useEffect(() => {
    const result = validateRequirement(text)
    setValidation(result)
    onValidationChange?.(result)
  }, [text, validateRequirement, onValidationChange])

  // Handle text change
  const handleTextChange = (newText: string) => {
    setText(newText)
    onChange?.(newText)
  }

  // Apply template
  const applyTemplate = (patternKey: string) => {
    const pattern = EARS_PATTERNS.find(p => p.key === patternKey)
    if (pattern) {
      setSelectedPattern(patternKey)
      handleTextChange(pattern.template)
    }
  }

  // Get pattern color
  const getPatternColor = (pattern: string) => {
    const colors: Record<string, string> = {
      event_driven: 'blue',
      state_driven: 'green',
      unwanted: 'red',
      ubiquitous: 'purple',
      optional: 'orange',
      complex: 'cyan',
    }
    return colors[pattern] || 'default'
  }

  return (
    <div className="requirement-editor">
      {/* Pattern Templates */}
      {showTemplates && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Text strong style={{ marginBottom: 8, display: 'block' }}>
            <BulbOutlined /> EARS Pattern Templates
          </Text>
          <Space wrap>
            {EARS_PATTERNS.map(pattern => (
              <Tooltip 
                key={pattern.key} 
                title={
                  <div>
                    <div><strong>{pattern.description}</strong></div>
                    <div style={{ marginTop: 4 }}>Example: {pattern.example}</div>
                  </div>
                }
              >
                <Tag
                  color={selectedPattern === pattern.key ? getPatternColor(pattern.key) : 'default'}
                  style={{ cursor: 'pointer', marginBottom: 4 }}
                  onClick={() => applyTemplate(pattern.key)}
                >
                  {pattern.name}
                </Tag>
              </Tooltip>
            ))}
          </Space>
        </Card>
      )}

      {/* Editor */}
      <TextArea
        value={text}
        onChange={e => handleTextChange(e.target.value)}
        placeholder="Enter requirement using EARS pattern..."
        rows={4}
        style={{ 
          fontFamily: 'monospace',
          borderColor: validation.isValid ? '#52c41a' : validation.errors.length > 0 ? '#ff4d4f' : undefined,
        }}
      />

      {/* Validation Results */}
      {showValidation && text && (
        <div style={{ marginTop: 16 }}>
          {/* Pattern Detection */}
          {validation.pattern && (
            <Alert
              message={
                <Space>
                  <CheckCircleOutlined />
                  <span>Pattern Detected:</span>
                  <Tag color={getPatternColor(validation.pattern)}>
                    {EARS_PATTERNS.find(p => p.key === validation.pattern)?.name}
                  </Tag>
                </Space>
              }
              type="success"
              style={{ marginBottom: 8 }}
            />
          )}

          {/* Parsed Components */}
          {Object.keys(validation.parsedComponents).length > 0 && (
            <Card size="small" style={{ marginBottom: 8 }}>
              <Text strong>Parsed Components:</Text>
              <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
                {validation.parsedComponents.trigger && (
                  <Col span={12}>
                    <Badge color="blue" text={<Text type="secondary">Trigger:</Text>} />
                    <div style={{ marginLeft: 16 }}>{validation.parsedComponents.trigger}</div>
                  </Col>
                )}
                {validation.parsedComponents.state && (
                  <Col span={12}>
                    <Badge color="green" text={<Text type="secondary">State:</Text>} />
                    <div style={{ marginLeft: 16 }}>{validation.parsedComponents.state}</div>
                  </Col>
                )}
                {validation.parsedComponents.condition && (
                  <Col span={12}>
                    <Badge color="orange" text={<Text type="secondary">Condition:</Text>} />
                    <div style={{ marginLeft: 16 }}>{validation.parsedComponents.condition}</div>
                  </Col>
                )}
                {validation.parsedComponents.system && (
                  <Col span={12}>
                    <Badge color="purple" text={<Text type="secondary">System:</Text>} />
                    <div style={{ marginLeft: 16 }}>{validation.parsedComponents.system}</div>
                  </Col>
                )}
                {validation.parsedComponents.response && (
                  <Col span={24}>
                    <Badge color="cyan" text={<Text type="secondary">Response:</Text>} />
                    <div style={{ marginLeft: 16 }}>{validation.parsedComponents.response}</div>
                  </Col>
                )}
              </Row>
            </Card>
          )}

          {/* Errors */}
          {validation.errors.map((error, idx) => (
            <Alert
              key={`error-${idx}`}
              message={error}
              type="error"
              showIcon
              style={{ marginBottom: 8 }}
            />
          ))}

          {/* Warnings */}
          {validation.warnings.map((warning, idx) => (
            <Alert
              key={`warning-${idx}`}
              message={warning}
              type="warning"
              showIcon
              style={{ marginBottom: 8 }}
            />
          ))}

          {/* Suggestions */}
          {validation.suggestions.length > 0 && (
            <Alert
              message="Suggestions"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {validation.suggestions.map((suggestion, idx) => (
                    <li key={idx}>{suggestion}</li>
                  ))}
                </ul>
              }
              type="info"
              showIcon
              icon={<BulbOutlined />}
            />
          )}
        </div>
      )}

      {/* Glossary Terms Highlight */}
      {Object.keys(glossary).length > 0 && (
        <Card size="small" style={{ marginTop: 16 }}>
          <Text strong>Glossary Terms:</Text>
          <div style={{ marginTop: 8 }}>
            {Object.entries(glossary).map(([term, definition]) => (
              <Tooltip key={term} title={definition}>
                <Tag style={{ marginBottom: 4, cursor: 'help' }}>{term}</Tag>
              </Tooltip>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default RequirementEditor
