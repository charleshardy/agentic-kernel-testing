# ResourceUtilizationCharts Component Tests

This directory contains comprehensive test coverage for the `ResourceUtilizationCharts` component, implementing both unit tests and property-based tests as specified in the Environment Allocation UI design document.

## Test Coverage

### **Feature: environment-allocation-ui, Property 3: Resource Metrics Display Completeness**
**Validates: Requirements 2.1, 2.2, 2.3, 7.1, 7.3**

## Test Files

### 1. `ResourceUtilizationCharts.test.tsx`
**Unit Tests** - Specific functionality and user interaction tests

#### Test Categories:
- **Basic Rendering**: Component structure, titles, environment count display
- **Chart Rendering and Types**: Line, area, and bar chart switching
- **Metric Selection and Filtering**: Multi-select metrics, environment filtering
- **Threshold Management**: Alert configuration, threshold sliders, reset functionality
- **Environment Cards**: Resource display, status indicators, test assignments
- **Export Functionality**: Data export, default export behavior
- **Fullscreen Mode**: UI state management
- **Loading and Empty States**: Loading indicators, empty state messages
- **Error Handling**: Error boundaries, recovery mechanisms
- **Real-time Updates**: Auto-refresh intervals, live indicators
- **Accessibility**: ARIA labels, keyboard navigation, tooltips
- **Performance**: Large dataset handling, memoization
- **Data Processing**: Aggregate calculations, data filtering, grouping

### 2. `ResourceUtilizationCharts.property.test.tsx`
**Property-Based Tests** - Edge cases and invariant validation (100+ iterations each)

#### Properties Tested:
1. **Component Always Renders Successfully** - No crashes with any valid input
2. **Environment Count Display Accuracy** - Correct active environment counting
3. **Resource Metrics Display Completeness** - All required metrics shown
4. **Aggregate Statistics Consistency** - Correct calculation across all inputs
5. **Threshold Alert Consistency** - Proper alert triggering
6. **Chart Type Consistency** - Appropriate chart rendering
7. **Resource Value Bounds** - Handles 0-100% values correctly
8. **Empty State Handling** - Graceful empty array handling
9. **Test Assignment Display** - Correct test count display
10. **Status Tag Consistency** - All statuses properly displayed
11. **Refresh Interval Behavior** - Various intervals handled correctly
12. **Architecture Display Consistency** - All architectures supported

### 3. `setup.ts`
**Test Configuration** - Mocks and environment setup

#### Mocked APIs:
- `window.matchMedia` - For Ant Design responsive components
- `ResizeObserver` - For responsive chart containers
- `IntersectionObserver` - For virtualization features
- `performance.now` - For consistent timing
- `URL.createObjectURL/revokeObjectURL` - For export functionality
- Console methods - To suppress test noise

### 4. `run-tests.ts`
**Test Runner** - Orchestrates test execution with proper setup

## Running Tests

### Prerequisites
```bash
npm install --save-dev fast-check @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest
```

### Execute Tests
```bash
# Run all tests
npm test

# Run specific test file
npm test ResourceUtilizationCharts.test.tsx

# Run property-based tests only
npm test ResourceUtilizationCharts.property.test.tsx

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## Test Strategy

### Unit Tests
- **Specific Examples**: Test concrete scenarios and user interactions
- **Edge Cases**: Boundary conditions, error states, empty data
- **User Interactions**: Clicks, selections, form inputs, keyboard navigation
- **Integration Points**: Component communication, prop handling, state management

### Property-Based Tests
- **Universal Properties**: Rules that must hold for ALL valid inputs
- **Invariants**: Conditions that never change regardless of input
- **Edge Case Discovery**: Automatically find problematic input combinations
- **Regression Prevention**: Catch issues across wide input ranges

## Coverage Goals

- **Line Coverage**: >95%
- **Branch Coverage**: >90%
- **Function Coverage**: 100%
- **Statement Coverage**: >95%

## Key Testing Principles

1. **Comprehensive Coverage**: Both unit and property-based tests complement each other
2. **Real Behavior Testing**: Tests verify actual user-facing functionality
3. **Error Resilience**: Extensive error handling and recovery testing
4. **Performance Validation**: Tests ensure component handles large datasets
5. **Accessibility Compliance**: ARIA labels, keyboard navigation, screen readers
6. **Cross-browser Compatibility**: Mocked APIs ensure consistent behavior

## Maintenance

### Adding New Tests
1. **Unit Tests**: Add to `ResourceUtilizationCharts.test.tsx` for specific functionality
2. **Property Tests**: Add to `ResourceUtilizationCharts.property.test.tsx` for invariants
3. **Update Documentation**: Reflect new test coverage in this README

### Test Data Generators
Property-based tests use Fast-Check generators for:
- **Environment Objects**: Random but valid environment configurations
- **Resource Values**: 0-100% utilization values
- **Time Ranges**: Valid date ranges
- **Thresholds**: Warning < Critical threshold pairs
- **Status Values**: All valid environment statuses

### Debugging Failed Tests
1. **Check Console Output**: Error messages and stack traces
2. **Inspect Generated Data**: Property test failures show counterexamples
3. **Run Single Test**: Isolate failing test case
4. **Add Debug Logging**: Temporary console.log statements
5. **Check Mocks**: Ensure mocked dependencies behave correctly

## Integration with CI/CD

These tests are designed to run in continuous integration environments:
- **Fast Execution**: Optimized for quick feedback
- **Deterministic Results**: Consistent across different environments
- **Clear Failure Messages**: Easy to diagnose issues
- **Coverage Reports**: Integrated with coverage tools

## Quality Assurance

The test suite ensures:
- **Functional Correctness**: Component works as specified
- **Error Resilience**: Graceful handling of edge cases
- **Performance**: Acceptable performance with large datasets
- **Accessibility**: Compliance with accessibility standards
- **User Experience**: Smooth interactions and clear feedback