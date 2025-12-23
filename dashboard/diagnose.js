const fs = require('fs');
const path = require('path');

console.log('🔍 Diagnosing React Frontend Issues...\n');

// Check if key files exist
const keyFiles = [
  'src/main.tsx',
  'src/App.tsx', 
  'src/index.css',
  'src/components/Layout/DashboardLayout.tsx',
  'src/pages/Dashboard.tsx',
  'src/store/index.ts',
  'src/services/api.ts',
  'src/services/websocket.ts',
  'index.html',
  'package.json',
  'vite.config.ts'
];

console.log('📁 Checking key files:');
keyFiles.forEach(file => {
  const exists = fs.existsSync(path.join(__dirname, file));
  console.log(`  ${exists ? '✅' : '❌'} ${file}`);
});

// Check package.json dependencies
console.log('\n📦 Checking package.json:');
try {
  const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
  console.log(`  Name: ${pkg.name}`);
  console.log(`  Version: ${pkg.version}`);
  console.log(`  React version: ${pkg.dependencies?.react || 'not found'}`);
  console.log(`  React-DOM version: ${pkg.dependencies?.['react-dom'] || 'not found'}`);
  console.log(`  Vite version: ${pkg.devDependencies?.vite || 'not found'}`);
  console.log(`  TypeScript version: ${pkg.devDependencies?.typescript || 'not found'}`);
} catch (error) {
  console.log(`  ❌ Error reading package.json: ${error.message}`);
}

// Check Vite config
console.log('\n⚙️ Checking Vite config:');
try {
  const viteConfig = fs.readFileSync(path.join(__dirname, 'vite.config.ts'), 'utf8');
  const portMatch = viteConfig.match(/port:\s*(\d+)/);
  const port = portMatch ? portMatch[1] : 'default (3000)';
  console.log(`  Configured port: ${port}`);
  
  if (viteConfig.includes('proxy')) {
    console.log('  ✅ API proxy configured');
  } else {
    console.log('  ❌ No API proxy found');
  }
} catch (error) {
  console.log(`  ❌ Error reading vite.config.ts: ${error.message}`);
}

// Check if node_modules exists
console.log('\n📚 Checking dependencies:');
const nodeModulesExists = fs.existsSync(path.join(__dirname, 'node_modules'));
console.log(`  node_modules: ${nodeModulesExists ? '✅ exists' : '❌ missing - run npm install'}`);

if (nodeModulesExists) {
  const reactExists = fs.existsSync(path.join(__dirname, 'node_modules', 'react'));
  const viteExists = fs.existsSync(path.join(__dirname, 'node_modules', 'vite'));
  console.log(`  react: ${reactExists ? '✅' : '❌'}`);
  console.log(`  vite: ${viteExists ? '✅' : '❌'}`);
}

console.log('\n🔧 Recommended debugging steps:');
console.log('1. Check if Vite dev server is actually running:');
console.log('   curl http://localhost:3001/ || curl http://localhost:3000/');
console.log('2. Check browser console for JavaScript errors');
console.log('3. Try restarting the dev server:');
console.log('   npm run dev:clean');
console.log('4. Check if all dependencies are installed:');
console.log('   npm install');
console.log('5. Try building the project to check for TypeScript errors:');
console.log('   npm run build');