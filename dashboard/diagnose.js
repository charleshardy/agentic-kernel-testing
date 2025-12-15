#!/usr/bin/env node

// Diagnostic script for Vite/React dashboard issues

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 Diagnosing Vite/React Dashboard Issues...\n');

// Check 1: Verify essential files exist
const essentialFiles = [
    'package.json',
    'vite.config.ts', 
    'index.html',
    'src/main.tsx',
    'src/App.tsx'
];

console.log('📁 Checking essential files:');
essentialFiles.forEach(file => {
    const exists = fs.existsSync(file);
    console.log(`${exists ? '✅' : '❌'} ${file}`);
});

// Check 2: Verify node_modules
console.log('\n📦 Checking dependencies:');
const nodeModulesExists = fs.existsSync('node_modules');
console.log(`${nodeModulesExists ? '✅' : '❌'} node_modules directory`);

if (nodeModulesExists) {
    const viteExists = fs.existsSync('node_modules/vite');
    const reactExists = fs.existsSync('node_modules/react');
    console.log(`${viteExists ? '✅' : '❌'} Vite installed`);
    console.log(`${reactExists ? '✅' : '❌'} React installed`);
}

// Check 3: Try to parse package.json
console.log('\n📋 Checking package.json:');
try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    console.log('✅ package.json is valid JSON');
    console.log(`   Name: ${packageJson.name}`);
    console.log(`   Version: ${packageJson.version}`);
    
    // Check scripts
    if (packageJson.scripts && packageJson.scripts.dev) {
        console.log('✅ dev script found');
    } else {
        console.log('❌ dev script missing');
    }
} catch (error) {
    console.log('❌ package.json parse error:', error.message);
}

// Check 4: TypeScript compilation
console.log('\n🔧 Checking TypeScript compilation:');
try {
    execSync('npx tsc --noEmit', { stdio: 'pipe' });
    console.log('✅ TypeScript compilation successful');
} catch (error) {
    console.log('❌ TypeScript compilation errors:');
    console.log(error.stdout?.toString() || error.message);
}

// Check 5: Port availability
console.log('\n🌐 Checking port availability:');
const net = require('net');

function checkPort(port) {
    return new Promise((resolve) => {
        const server = net.createServer();
        server.listen(port, () => {
            server.once('close', () => resolve(true));
            server.close();
        });
        server.on('error', () => resolve(false));
    });
}

checkPort(3000).then(available => {
    console.log(`${available ? '✅' : '❌'} Port 3000 ${available ? 'available' : 'in use'}`);
    
    if (!available) {
        console.log('   💡 Port 3000 is in use. Try:');
        console.log('      - Kill existing process: pkill -f "vite"');
        console.log('      - Use different port: npm run dev -- --port 3001');
    }
});

// Check 6: Environment variables
console.log('\n🌍 Environment check:');
console.log(`   NODE_ENV: ${process.env.NODE_ENV || 'not set'}`);
console.log(`   XDG_RUNTIME_DIR: ${process.env.XDG_RUNTIME_DIR || 'not set'}`);
console.log(`   QT_QPA_PLATFORM: ${process.env.QT_QPA_PLATFORM || 'not set'}`);

console.log('\n💡 Common solutions:');
console.log('1. Install dependencies: npm install');
console.log('2. Clear cache: rm -rf node_modules package-lock.json && npm install');
console.log('3. Check browser console for JavaScript errors');
console.log('4. Verify Vite is running: npm run dev');
console.log('5. Try different port: npm run dev -- --port 3001');
console.log('6. Check network tab in browser dev tools');

console.log('\n🚀 To start debugging:');
console.log('1. Run: npm run dev');
console.log('2. Open browser to: http://localhost:3000');
console.log('3. Open browser dev tools (F12)');
console.log('4. Check Console and Network tabs for errors');