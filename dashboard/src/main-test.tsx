console.log('🚀 Starting ultra-minimal test...')

// Ultra-minimal test without any complex dependencies
const root = document.getElementById('root')
if (root) {
  root.innerHTML = `
    <div style="padding: 20px; font-family: Arial, sans-serif;">
      <h1>Ultra-Minimal Test</h1>
      <p>If you can see this, the basic setup is working.</p>
      <p>Current time: ${new Date().toLocaleString()}</p>
      <button onclick="alert('Button works!')">Test Button</button>
    </div>
  `
  console.log('✅ Ultra-minimal test rendered successfully')
} else {
  console.error('❌ Root element not found')
}