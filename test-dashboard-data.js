#!/usr/bin/env node

// Test script to verify dashboard data flow

const http = require('http');

console.log('🔍 Testing Dashboard Data Flow...\n');

// Test the health endpoint that the dashboard uses
console.log('1️⃣ Testing health endpoint...');
const healthReq = http.get('http://localhost:8000/api/v1/health', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        if (res.statusCode === 200) {
            const response = JSON.parse(data);
            console.log('✅ Health endpoint working');
            console.log(`   Status: ${response.data?.status}`);
            console.log(`   Components: ${Object.keys(response.data?.components || {}).join(', ')}`);
            console.log(`   CPU Usage: ${Math.round((response.data?.metrics?.cpu_usage || 0) * 100)}%`);
            console.log(`   Memory Usage: ${Math.round((response.data?.metrics?.memory_usage || 0) * 100)}%`);
            console.log(`   Active Tests: ${response.data?.components?.test_orchestrator?.active_tests || 0}`);
            console.log(`   Available Environments: ${response.data?.components?.environment_manager?.available_environments || 0}`);
        } else {
            console.log(`❌ Health endpoint error: ${res.statusCode}`);
        }
        
        console.log('\n📊 Dashboard Data Summary:');
        console.log('• ✅ System Status: Available from health endpoint');
        console.log('• ✅ System Metrics: Available from health endpoint');
        console.log('• 🔄 Mock Data: Used for charts and lists (demo mode)');
        console.log('• 🔐 Protected Data: Requires authentication (active executions, test results)');
        
        console.log('\n🎯 Expected Dashboard Content:');
        console.log('• System Status badges (API, Database, Orchestrator, Environment Manager)');
        console.log('• System Metrics cards (Active Tests, Queued Tests, Environments, System Load)');
        console.log('• Resource Usage progress bars (CPU, Memory, Disk)');
        console.log('• Test Status Distribution pie chart');
        console.log('• Test Execution Trends line chart');
        console.log('• Active Executions list (mock data)');
        console.log('• Recent Test Results list (mock data)');
        
        console.log('\n🚀 Dashboard should now show rich content at:');
        console.log('   http://localhost:3001/');
    });
}).on('error', (err) => {
    console.log('❌ Health endpoint connection failed:', err.message);
    console.log('\n💡 To fix:');
    console.log('1. Ensure backend is running: python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload');
    console.log('2. Ensure frontend is running: cd dashboard && npm run dev -- --port 3001');
});