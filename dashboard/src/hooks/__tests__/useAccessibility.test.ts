/**
 * Unit tests for accessibility hooks
 * 
 * **Feature: environment-allocation-ui, Task 14.1: Unit tests for component interactions**
 * **Validates: Requirements 1.2, 2.4**
 */

import { renderHook, act } from '@testing-library/react'
import { 
  useKeyboardNavigation,
  useScreenReader,
  useFocusManagement,
  useAriaAttributes,
  useColorContrast,
  useReducedMotion
} from '../useAccessibility'

// Mock DOM methods
const mockFocus = jest.fn()
const mockAddEventListener = jest.fn()
const mockRemoveEventListener = jest.fn()
const mockAppendChild = jest.fn()
const mockRemoveChild = jest.fn()

Object.defineProperty(document, 'activeElement', {
  value: { focus: mockFocus },
  writable: true
})

Object.defineProperty(document, 'createElement', {
  value: jest.fn(() => ({
    setAttribute: jest.fn(),
    style: {},
    textContent: '',
    focus: mockFocus,
    addEventListener: mockAddEventListener,
    removeEventListener: mockRemoveEventListener,
    parentNode: { removeChild: mockRemoveChild }
  })),
  writable: true
})

Object.defineProperty(document.body, 'appendChild', {
  value: mockAppendChild,
  writable: true
})

describe('useKeyboardNavigation Hook', () => {
  const mockItems = ['item1', 'item2', 'item3']
  const mockOnSelect = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('should initialize with default focused index', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { initialIndex: 1 })
    )

    expect(result.current.focusedIndex).toBe(1)
  })

  test('should handle arrow down navigation', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect)
    )

    const containerProps = result.current.getContainerProps()
    const mockContainer = { addEventListener: mockAddEventListener }
    containerProps.ref.current = mockContainer

    // Simulate ArrowDown key press
    const keyDownEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' })
    
    act(() => {
      // Get the event handler that was registered
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(keyDownEvent)
      }
    })

    expect(result.current.focusedIndex).toBe(0)
  })

  test('should handle arrow up navigation', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { initialIndex: 1 })
    )

    const containerProps = result.current.getContainerProps()
    const mockContainer = { addEventListener: mockAddEventListener }
    containerProps.ref.current = mockContainer

    // Simulate ArrowUp key press
    const keyUpEvent = new KeyboardEvent('keydown', { key: 'ArrowUp' })
    
    act(() => {
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(keyUpEvent)
      }
    })

    expect(result.current.focusedIndex).toBe(0)
  })

  test('should handle Enter key selection', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { initialIndex: 1 })
    )

    const containerProps = result.current.getContainerProps()
    const mockContainer = { addEventListener: mockAddEventListener }
    containerProps.ref.current = mockContainer

    // Simulate Enter key press
    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' })
    
    act(() => {
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(enterEvent)
      }
    })

    expect(mockOnSelect).toHaveBeenCalledWith(1, 'item2')
  })

  test('should handle Home and End keys', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { initialIndex: 1 })
    )

    const containerProps = result.current.getContainerProps()
    const mockContainer = { addEventListener: mockAddEventListener }
    containerProps.ref.current = mockContainer

    // Test Home key
    const homeEvent = new KeyboardEvent('keydown', { key: 'Home' })
    act(() => {
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(homeEvent)
      }
    })

    expect(result.current.focusedIndex).toBe(0)

    // Test End key
    const endEvent = new KeyboardEvent('keydown', { key: 'End' })
    act(() => {
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(endEvent)
      }
    })

    expect(result.current.focusedIndex).toBe(2)
  })

  test('should provide correct item props', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { initialIndex: 1 })
    )

    const itemProps = result.current.getItemProps(1)

    expect(itemProps).toEqual({
      tabIndex: 0,
      'aria-selected': true,
      role: 'option',
      onFocus: expect.any(Function),
      onMouseEnter: expect.any(Function)
    })

    const nonFocusedItemProps = result.current.getItemProps(0)
    expect(nonFocusedItemProps.tabIndex).toBe(-1)
    expect(nonFocusedItemProps['aria-selected']).toBe(false)
  })

  test('should handle loop navigation', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { loop: true, initialIndex: 2 })
    )

    const containerProps = result.current.getContainerProps()
    const mockContainer = { addEventListener: mockAddEventListener }
    containerProps.ref.current = mockContainer

    // Navigate down from last item should loop to first
    const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' })
    act(() => {
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(downEvent)
      }
    })

    expect(result.current.focusedIndex).toBe(0)
  })

  test('should not navigate when disabled', () => {
    const { result } = renderHook(() => 
      useKeyboardNavigation(mockItems, mockOnSelect, { disabled: true })
    )

    const containerProps = result.current.getContainerProps()
    const mockContainer = { addEventListener: mockAddEventListener }
    containerProps.ref.current = mockContainer

    const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' })
    act(() => {
      const eventHandler = mockAddEventListener.mock.calls.find(
        call => call[0] === 'keydown'
      )?.[1]
      
      if (eventHandler) {
        eventHandler(downEvent)
      }
    })

    expect(result.current.focusedIndex).toBe(-1)
  })
})

describe('useScreenReader Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('should create announcement element and announce message', () => {
    const { result } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('Test announcement', 'assertive')
    })

    expect(document.createElement).toHaveBeenCalledWith('div')
    expect(mockAppendChild).toHaveBeenCalled()
  })

  test('should clean up announcement element on unmount', () => {
    const { unmount } = renderHook(() => useScreenReader())

    unmount()

    expect(mockRemoveChild).toHaveBeenCalled()
  })
})

describe('useFocusManagement Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('should save and restore focus', () => {
    const { result } = renderHook(() => useFocusManagement())

    act(() => {
      result.current.saveFocus()
    })

    act(() => {
      result.current.restoreFocus()
    })

    expect(mockFocus).toHaveBeenCalled()
  })

  test('should trap focus within container', () => {
    const { result } = renderHook(() => useFocusManagement())

    const mockContainer = {
      querySelectorAll: jest.fn(() => [
        { focus: mockFocus },
        { focus: mockFocus }
      ]),
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener
    }

    act(() => {
      const cleanup = result.current.trapFocus(mockContainer as any)
      cleanup()
    })

    expect(mockContainer.addEventListener).toHaveBeenCalledWith('keydown', expect.any(Function))
    expect(mockContainer.removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function))
    expect(mockFocus).toHaveBeenCalled()
  })
})

describe('useAriaAttributes Hook', () => {
  test('should generate unique IDs', () => {
    const { result } = renderHook(() => useAriaAttributes())

    const id1 = result.current.generateId('test')
    const id2 = result.current.generateId('test')

    expect(id1).toMatch(/^test-/)
    expect(id2).toMatch(/^test-/)
    expect(id1).not.toBe(id2)
  })

  test('should generate combobox props', () => {
    const { result } = renderHook(() => useAriaAttributes())

    const props = result.current.getComboboxProps(true, 'listbox-1', 'option-1')

    expect(props).toEqual({
      role: 'combobox',
      'aria-expanded': true,
      'aria-haspopup': 'listbox',
      'aria-controls': 'listbox-1',
      'aria-activedescendant': 'option-1'
    })
  })

  test('should generate listbox props', () => {
    const { result } = renderHook(() => useAriaAttributes())

    const props = result.current.getListboxProps('listbox-1', 'label-1')

    expect(props).toEqual({
      id: 'listbox-1',
      role: 'listbox',
      'aria-labelledby': 'label-1'
    })
  })

  test('should generate option props', () => {
    const { result } = renderHook(() => useAriaAttributes())

    const props = result.current.getOptionProps('option-1', true, false)

    expect(props).toEqual({
      id: 'option-1',
      role: 'option',
      'aria-selected': true,
      'aria-disabled': false
    })
  })

  test('should generate progress props', () => {
    const { result } = renderHook(() => useAriaAttributes())

    const props = result.current.getProgressProps(50, 100, 'Loading progress')

    expect(props).toEqual({
      role: 'progressbar',
      'aria-valuenow': 50,
      'aria-valuemin': 0,
      'aria-valuemax': 100,
      'aria-label': 'Loading progress'
    })
  })

  test('should generate alert props', () => {
    const { result } = renderHook(() => useAriaAttributes())

    const props = result.current.getAlertProps('assertive')

    expect(props).toEqual({
      role: 'alert',
      'aria-live': 'assertive',
      'aria-atomic': true
    })
  })
})

describe('useColorContrast Hook', () => {
  test('should calculate contrast ratio correctly', () => {
    const { result } = renderHook(() => useColorContrast())

    const contrast = result.current.checkContrast('#000000', '#ffffff')

    expect(contrast).toEqual({
      ratio: 21,
      AA: true,
      AAA: true,
      AALarge: true,
      AAALarge: true
    })
  })

  test('should handle invalid hex colors', () => {
    const { result } = renderHook(() => useColorContrast())

    const contrast = result.current.checkContrast('invalid', '#ffffff')

    expect(contrast).toBeNull()
  })

  test('should calculate low contrast correctly', () => {
    const { result } = renderHook(() => useColorContrast())

    const contrast = result.current.checkContrast('#888888', '#999999')

    expect(contrast?.AA).toBe(false)
    expect(contrast?.AAA).toBe(false)
  })
})

describe('useReducedMotion Hook', () => {
  const mockMatchMedia = jest.fn()

  beforeEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      value: mockMatchMedia,
      writable: true
    })
  })

  test('should detect reduced motion preference', () => {
    const mockMediaQuery = {
      matches: true,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    }

    mockMatchMedia.mockReturnValue(mockMediaQuery)

    const { result } = renderHook(() => useReducedMotion())

    expect(result.current).toBe(true)
    expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)')
  })

  test('should update when preference changes', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    }

    mockMatchMedia.mockReturnValue(mockMediaQuery)

    const { result } = renderHook(() => useReducedMotion())

    expect(result.current).toBe(false)

    // Simulate preference change
    act(() => {
      const changeHandler = mockMediaQuery.addEventListener.mock.calls.find(
        call => call[0] === 'change'
      )?.[1]
      
      if (changeHandler) {
        changeHandler({ matches: true })
      }
    })

    expect(result.current).toBe(true)
  })

  test('should clean up event listener on unmount', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    }

    mockMatchMedia.mockReturnValue(mockMediaQuery)

    const { unmount } = renderHook(() => useReducedMotion())

    unmount()

    expect(mockMediaQuery.removeEventListener).toHaveBeenCalledWith(
      'change',
      expect.any(Function)
    )
  })
})