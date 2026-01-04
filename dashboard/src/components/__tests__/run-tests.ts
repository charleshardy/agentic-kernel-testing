/**
 * Test Runner for ResourceUtilizationCharts Component Tests
 * 
 * This script runs both unit tests and property-based tests for the
 * ResourceUtilizationCharts component with proper configuration.
 */

import { describe, it, expect } from 'vitest'

// Import test setup
import './setup'

// Import test suites
import './ResourceUtilizationCharts.test'
import './ResourceUtilizationCharts.property.test'

console.log('✅ All ResourceUtilizationCharts tests loaded successfully')
console.log('📊 Running comprehensive test suite with:')
console.log('   - Unit tests for specific functionality')
console.log('   - Property-based tests for edge cases')
console.log('   - Error handling and accessibility tests')
console.log('   - Performance and data processing tests')