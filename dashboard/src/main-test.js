console.log('🚀 Starting JavaScript test...')

// Ultra-minimal JavaScript test
const root = document.getElementById('root')
if (root) {
  root.innerHTML = `
    <div style="padding: 20px; font-family: Arial, sans-serif; background: #f0f2f5; min-height: 100vh;">
      <h1 style="color: #1890ff;">JavaScript Test Working!</h1>
      <p>If you can see this, the basic Vite setup is working.</p>
      <p>Current time: ${new Date().toLocaleString()}</p>
      <button onclick="alert('Button works!')" style="padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer;">Test Button</button>
      <div style="margin-top: 20px; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h3>Debug Info:</h3>
        <p>Location: ${window.location.href}</p>
        <p>User Agent: ${navigator.userAgent}</p>
        <p>Timestamp: ${Date.now()}</p>
      </div>
    </div>
  `
  console.log('✅ JavaScript test rendered successfully')
} else {
  console.error('❌ Root element not found')
  document.body.innerHTML = '<h1 style="color: red;">ERROR: Root element not found!</h1>'
}