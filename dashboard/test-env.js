#!/usr/bin/env node

// Test script to verify environment variables for headless Vite development

console.log('🔍 Testing environment configuration for headless Vite development...\n');

const checks = [
    {
        name: 'XDG_RUNTIME_DIR',
        value: process.env.XDG_RUNTIME_DIR,
        expected: 'Should be set to a writable directory',
        test: (val) => val && val.includes('/tmp/runtime-')
    },
    {
        name: 'QT_QPA_PLATFORM', 
        value: process.env.QT_QPA_PLATFORM,
        expected: 'Should be "offscreen" for headless environments',
        test: (val) => val === 'offscreen'
    },
    {
        name: 'QT_LOGGING_RULES',
        value: process.env.QT_LOGGING_RULES,
        expected: 'Should be "*=false" to suppress Qt warnings',
        test: (val) => val === '*=false'
    },
    {
        name: 'NODE_VERSION',
        value: process.version,
        expected: 'Should be 18.0.0 or higher',
        test: (val) => {
            const version = parseInt(val.replace('v', '').split('.')[0]);
            return version >= 18;
        }
    }
];

let allPassed = true;

checks.forEach(check => {
    const passed = check.test(check.value);
    const status = passed ? '✅' : '❌';
    const value = check.value || 'Not set';
    
    console.log(`${status} ${check.name}: ${value}`);
    console.log(`   Expected: ${check.expected}\n`);
    
    if (!passed) allPassed = false;
});

console.log('📊 SUMMARY:');
if (allPassed) {
    console.log('🎉 All environment checks passed! Vite should run without warnings.');
} else {
    console.log('⚠️  Some checks failed. You may see warnings when running Vite.');
    console.log('\n💡 To fix, run one of these commands:');
    console.log('   npm run dev         # Uses built-in environment fixes');
    console.log('   npm run dev:headless # Specifically for headless environments');
    console.log('   ./run-dev.sh        # Uses shell script with all fixes');
}

console.log('\n🚀 To start the development server:');
console.log('   npm run dev');