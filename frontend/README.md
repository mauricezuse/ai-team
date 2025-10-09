# Frontend - Angular Application

## Overview
Angular-based frontend application for the AI Team orchestration platform. Provides a modern, responsive UI for managing workflows, viewing agent conversations, and monitoring AI agent collaboration.

## Architecture

### Core Components
- **Angular Framework**: Latest Angular with standalone components
- **PrimeNG UI**: Professional UI component library
- **PrimeFlex**: CSS utility framework
- **TypeScript**: Strict typing and modern JavaScript features
- **SCSS**: Advanced styling with variables and mixins

### Development Server
- **Port**: 4002 (tests expect this; start with `npm run start -- --port 4002`)
- **Proxy**: Routes API calls to backend on port 8000
- **Hot Reload**: Development mode with file watching
- **Source Maps**: Debug-friendly development builds

## Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── features/           # Feature modules
│   │   │   ├── workflows/      # Workflow management
│   │   │   ├── agents/         # Agent monitoring
│   │   │   └── dashboard/      # Dashboard overview
│   │   ├── shared/             # Shared components
│   │   │   ├── components/     # Reusable UI components
│   │   │   ├── services/       # Angular services
│   │   │   └── models/         # TypeScript interfaces
│   │   ├── core/               # Core functionality
│   │   └── app.component.*      # Root component
│   ├── assets/                 # Static assets
│   └── styles/                 # Global styles
├── angular.json               # Angular CLI configuration
├── package.json               # Dependencies and scripts
├── proxy.conf.json            # API proxy configuration
└── tsconfig.json              # TypeScript configuration
```

## Key Features

### Workflow Management
- **Workflow List**: View all workflows with status and details
- **Workflow Creation**: Create new workflows from Jira stories
- **Workflow Execution**: Execute AI agent workflows
- **Workflow Details**: View conversations, code files, and progress

### Agent Monitoring
- **Agent Conversations**: Real-time view of agent interactions
- **Agent Filtering**: Filter conversations by agent role
- **Conversation Details**: Expandable conversation views
- **Code Files**: View generated code files with syntax highlighting

### Dashboard
- **Overview**: System status and metrics
- **Recent Activity**: Latest workflow executions
- **Agent Status**: Current agent states and performance
- **System Health**: Backend connectivity and status

## Components

### Workflow Components
- `WorkflowsListComponent` - Main workflow listing
- `WorkflowDetailComponent` - Individual workflow view
- `WorkflowCreateComponent` - Workflow creation form
  - Shows success toast: `Workflow {JIRA_ID} created successfully`
  - Submit button uses `[disabled]` and `[loading]` during request
  - Toast life ~4000ms for test reliability
- `WorkflowExecuteComponent` - Workflow execution interface

### Agent Components
- `AgentConversationComponent` - Agent conversation display
- `AgentFilterComponent` - Agent filtering controls
- `CodeFileComponent` - Code file viewer
- `ConversationFlowComponent` - Conversation flow visualization

### Shared Components
- `LoadingSpinnerComponent` - Loading state indicator
- `ErrorAlertComponent` - Error message display
- `StatusBadgeComponent` - Status indicator badges
- `FileViewerComponent` - File content viewer

## Services

### WorkflowService
- `getWorkflows()` - Fetch all workflows
- `getWorkflow(id)` - Get specific workflow
- `createWorkflow(data)` - Create new workflow
- `executeWorkflow(id)` - Execute workflow
- `deleteWorkflow(id)` - Delete workflow

### AgentService
- `getConversations(workflowId)` - Get agent conversations
- `filterConversations(agent)` - Filter by agent role
- `getCodeFiles(conversationId)` - Get generated code files

### ApiService
- HTTP client configuration
- Request/response interceptors
- Error handling and retry logic
- Authentication headers

## Styling

### PrimeNG Theme
- **Saga Blue**: Professional blue theme
- **Responsive**: Mobile-first design approach
- **Accessibility**: WCAG 2.1 AA compliance
- **Customization**: SCSS variables for branding

### PrimeFlex Utilities
- **Layout**: Flexbox and grid utilities
- **Spacing**: Margin and padding classes
- **Typography**: Font size and weight utilities
- **Colors**: Theme color utilities

## Development

### Prerequisites
```bash
# Node.js 18+ required
node --version
npm --version
```

### Installation
```bash
# Install dependencies
npm install

# Start development server (tests expect 4002)
npm run start -- --port 4002
```

### Build
```bash
# Development build
npm run build

# Production build
npm run build --configuration=production
```

### Testing
```bash
# Unit tests
npm run test

# E2E tests
npm run e2e
```

## API Integration

### Proxy Configuration
```json
{
  "/api/*": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true
  }
}
```

### HTTP Client
- **Base URL**: `/api` (proxied to backend)
- **Timeout**: 30 seconds for long-running operations
- **Retry Logic**: 3 attempts for failed requests
- **Error Handling**: Global error interceptor

## State Management

### Component State
- **Local State**: Component-level state management
- **Service State**: Shared state via Angular services
- **Reactive Forms**: Form state management
- **Observables**: RxJS for async data handling

### Data Flow
1. **User Action** → Component
2. **Component** → Service
3. **Service** → HTTP Client
4. **HTTP Client** → Backend API
5. **Response** → Service → Component → View

## Performance

### Optimization
- **Lazy Loading**: Feature modules loaded on demand
- **OnPush Strategy**: Change detection optimization
- **TrackBy Functions**: List rendering optimization
- **Virtual Scrolling**: Large list performance

### Bundle Analysis
- **Initial Bundle**: ~571KB (development)
- **Lazy Chunks**: Loaded on demand
- **Tree Shaking**: Unused code elimination
- **Code Splitting**: Feature-based splitting

## Accessibility

### WCAG Compliance
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: ARIA labels and roles
- **Color Contrast**: Sufficient contrast ratios
- **Focus Management**: Logical focus order

### Testing
- **Automated Testing**: Playwright accessibility tests
- **Manual Testing**: Keyboard and screen reader testing
- **Lighthouse**: Accessibility audits
- **axe-core**: Automated accessibility testing

## Deployment

### Build Configuration
- **Environment**: Production/development configs
- **Asset Optimization**: Minification and compression
- **Source Maps**: Debug-friendly production builds
- **Bundle Analysis**: Webpack bundle analyzer

### Docker Support
- **Multi-stage Build**: Optimized production image
- **Nginx**: Static file serving
- **Environment Variables**: Runtime configuration
- **Health Checks**: Container health monitoring

## Advanced Workflows (New)

- Route: `/workflows/:id/advanced` – timeline view (skeleton)
- Route: `/workflows/:id/advanced/llm-calls?conversationId=<id>` – LLM calls table (skeleton)

Uses PrimeNG components and lazy-loaded module `features/workflows-advanced`.

## Feature Flags

Provide flags via:
- HTML meta tag: `<meta name="ai-team-flags" content="REDACT_SENSITIVE=1">`
- Or JS global: `window.__AI_FLAGS__ = { REDACT_SENSITIVE: '1' }`