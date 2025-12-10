# Agentic AI Testing System - Web Dashboard

A modern React-based web dashboard for monitoring and managing the Agentic AI Testing System. This dashboard provides real-time visualization of test execution, coverage analysis, performance monitoring, and system management capabilities.

## Features

### 🎯 Real-time Test Monitoring
- Live test execution status with WebSocket updates
- Interactive test submission and management
- Detailed test result browsing and filtering
- Test execution progress tracking

### 📊 Coverage Analysis
- Comprehensive code coverage visualization
- Coverage trends and gap identification
- Subsystem-level coverage breakdown
- Interactive coverage reports

### ⚡ Performance Monitoring
- Real-time performance metrics
- Regression detection and alerting
- Benchmark result comparison
- Performance trend analysis

### 🎨 Modern UI/UX
- Responsive design for desktop and mobile
- Dark/light theme support
- Interactive charts and visualizations
- Intuitive navigation and filtering

## Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **UI Library**: Ant Design 5.x
- **Charts**: Recharts for data visualization
- **State Management**: Zustand for global state
- **Data Fetching**: React Query for server state
- **Real-time Updates**: Socket.IO client
- **Build Tool**: Vite for fast development
- **Styling**: CSS-in-JS with Ant Design theming

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- Running Agentic AI Testing System API server

### Installation

1. Install dependencies:
```bash
cd dashboard
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## Configuration

The dashboard automatically connects to the API server at `http://localhost:8000`. To configure a different API endpoint, update the proxy settings in `vite.config.ts`.

### Environment Variables

Create a `.env` file in the dashboard directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=Agentic AI Testing System
```

## Project Structure

```
dashboard/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── Layout/         # Layout components
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # Main dashboard
│   │   ├── TestExecution.tsx
│   │   ├── TestResults.tsx
│   │   ├── Coverage.tsx
│   │   ├── Performance.tsx
│   │   └── Settings.tsx
│   ├── services/           # API and WebSocket services
│   │   ├── api.ts         # REST API client
│   │   └── websocket.ts   # WebSocket client
│   ├── store/             # Global state management
│   │   └── index.ts       # Zustand store
│   ├── App.tsx            # Main app component
│   ├── main.tsx           # App entry point
│   └── index.css          # Global styles
├── public/                # Static assets
├── package.json
├── vite.config.ts         # Vite configuration
└── tsconfig.json          # TypeScript configuration
```

## Key Features

### Dashboard Overview
- System health and metrics
- Active test execution monitoring
- Resource utilization tracking
- Real-time status updates

### Test Execution Management
- Submit new test cases
- Monitor active executions
- View execution progress
- Manage test priorities

### Test Results Analysis
- Browse and filter test results
- View detailed test information
- Download test artifacts
- Analyze failure patterns

### Coverage Visualization
- Line, branch, and function coverage
- Coverage trends over time
- Subsystem coverage breakdown
- Coverage gap identification

### Performance Monitoring
- Benchmark result tracking
- Performance regression detection
- Trend analysis and alerting
- Commit-level performance impact

### System Settings
- Configure system parameters
- Manage notification settings
- Set API and security options
- Customize dashboard behavior

## API Integration

The dashboard integrates with the Agentic AI Testing System API through:

- **REST API**: For data fetching and mutations
- **WebSocket**: For real-time updates
- **Authentication**: Bearer token-based auth
- **Error Handling**: Automatic retry and error recovery

### API Endpoints Used

- `GET /api/v1/health` - System health status
- `GET /api/v1/status/metrics` - System metrics
- `GET /api/v1/tests` - Test case management
- `GET /api/v1/results` - Test results
- `GET /api/v1/status/active` - Active executions
- `POST /api/v1/tests/submit` - Test submission

## Real-time Features

The dashboard uses WebSocket connections for real-time updates:

- Test execution status changes
- System metrics updates
- Coverage data updates
- Performance alerts
- Automatic reconnection handling

## Responsive Design

The dashboard is fully responsive and works on:

- Desktop computers (1920x1080+)
- Tablets (768px - 1024px)
- Mobile devices (320px - 767px)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run type-check` - Run TypeScript checks

### Code Style

The project uses:
- ESLint for code linting
- TypeScript for type safety
- Prettier for code formatting (via ESLint)

### Adding New Features

1. Create components in `src/components/`
2. Add pages in `src/pages/`
3. Update routing in `src/App.tsx`
4. Add API calls in `src/services/api.ts`
5. Update state management in `src/store/`

## Deployment

### Docker Deployment

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Static Hosting

The built dashboard can be deployed to any static hosting service:

- Netlify
- Vercel
- AWS S3 + CloudFront
- GitHub Pages

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check if the API server is running
   - Verify the API URL in configuration
   - Check network connectivity

2. **WebSocket Connection Failed**
   - Ensure WebSocket endpoint is accessible
   - Check firewall settings
   - Verify authentication tokens

3. **Charts Not Rendering**
   - Check browser console for errors
   - Verify data format matches chart expectations
   - Ensure Recharts is properly installed

### Performance Optimization

- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Optimize chart rendering with data sampling
- Use proper loading states and error boundaries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.