// Simple script to check for common issues
console.log('=== Checking for common issues ===')

// Check if React Query is available
console.log('React Query available:', typeof window.ReactQuery !== 'undefined')

// Check if Ant Design is available
console.log('Ant Design available:', typeof window.antd !== 'undefined')

// Check current URL
console.log('Current URL:', window.location.href)

// Check for any global errors
window.addEventListener('error', (event) => {
  console.error('Global error caught:', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
})

console.log('=== Error checking setup complete ===')