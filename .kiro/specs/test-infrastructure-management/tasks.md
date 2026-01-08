# Implementation Plan

## Test Infrastructure Host Management

- [x] 1. Set up project structure and core data models
  - [x] 1.1 Create infrastructure management module structure
    - Create `infrastructure/` directory with `__init__.py`
    - Create subdirectories: `models/`, `services/`, `connectors/`, `strategies/`
    - Set up module exports and dependencies
    - _Requirements: 1.1, 7.1, 8.1_

  - [x] 1.2 Implement core data models for all resource types
    - Create `BuildServer`, `BuildServerStatus`, `Toolchain`, `BuildServerCapacity` models
    - Create `Host`, `HostStatus`, `HostCapacity`, `ResourceUtilization` models
    - Create `Board`, `BoardStatus`, `BoardHealth`, `PowerControlConfig` models
    - Create shared models: `ResourceGroup`, `AllocationPolicy`, `HealthThresholds`
    - _Requirements: 1.3, 7.3, 8.3_

  - [x] 1.3 Write property test for data model validation
    - **Property 1: Build Server Registration Adds to Pool**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 1.4 Write property test for host data model
    - **Property 8: Host Registration Adds to Pool**
    - **Validates: Requirements 7.2, 7.3**

  - [x] 1.5 Write property test for board data model
    - **Property 12: Board Registration Adds to Pool**
    - **Validates: Requirements 8.2, 8.3**

- [x] 2. Implement SSH and connectivity connectors
  - [x] 2.1 Create SSH connector for remote command execution
    - Implement `SSHConnector` class with connection pooling
    - Add methods for command execution, file transfer, and connection validation
    - Implement retry logic with exponential backoff
    - _Requirements: 1.2, 7.2, 8.2_

  - [x] 2.2 Create Libvirt connector for VM management
    - Implement `LibvirtConnector` class for QEMU host management
    - Add methods for VM listing, creation, destruction, and capability detection
    - Implement connection validation and error handling
    - _Requirements: 7.2, 7.5_

  - [x] 2.3 Create Serial connector for board communication
    - Implement `SerialConnector` class for serial console access
    - Add methods for connection, command execution, and log capture
    - Implement connection validation and timeout handling
    - _Requirements: 8.2_

  - [x] 2.4 Write unit tests for connectors
    - Test SSH connection establishment and command execution
    - Test Libvirt connection and VM operations
    - Test Serial connection and communication
    - _Requirements: 1.2, 7.2, 8.2_


- [x] 3. Implement Build Server Management Service
  - [x] 3.1 Create Build Server Management Service
    - Implement `BuildServerManagementService` class
    - Add registration with SSH validation and toolchain detection
    - Add status monitoring and capacity tracking
    - Implement maintenance mode and decommissioning
    - _Requirements: 1.1-1.5, 2.1-2.5_

  - [x] 3.2 Write property test for build server selection
    - **Property 2: Build Server Selection Meets Architecture Requirements**
    - **Validates: Requirements 3.2, 3.3**

  - [x] 3.3 Write property test for disk space warning
    - **Property 3: Build Server Disk Space Warning**
    - **Validates: Requirements 2.4**

  - [x] 3.4 Create Build Server Selection Strategy
    - Implement `BuildServerSelectionStrategy` class
    - Add scoring algorithm based on architecture support, load, and estimated time
    - Implement resource reservation and release
    - _Requirements: 3.2, 13.1_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Build Job and Artifact Management
  - [x] 5.1 Create Build Job Manager
    - Implement `BuildJobManager` class
    - Add job submission, queuing, and status tracking
    - Implement log streaming and progress monitoring
    - Add job cancellation and retry functionality
    - _Requirements: 3.1-3.5_

  - [x] 5.2 Create Artifact Repository Manager
    - Implement `ArtifactRepositoryManager` class
    - Add artifact storage with checksum verification
    - Implement retrieval by build ID, commit hash, and "latest"
    - Add cleanup and retention policy enforcement
    - _Requirements: 4.1-4.5_

  - [x] 5.3 Write property test for artifact integrity
    - **Property 4: Build Artifact Integrity**
    - **Validates: Requirements 4.2**

  - [x] 5.4 Write property test for artifact retrieval
    - **Property 5: Build Artifact Retrieval Consistency**
    - **Validates: Requirements 4.5**

- [x] 6. Implement QEMU Host Management Service
  - [x] 6.1 Create Host Management Service
    - Implement `HostManagementService` class
    - Add registration with SSH and libvirt validation
    - Add status monitoring and capacity tracking
    - Implement maintenance mode and decommissioning
    - _Requirements: 7.1-7.5, 9.1-9.5_

  - [x] 6.2 Create Host Selection Strategy
    - Implement `HostSelectionStrategy` class
    - Add scoring algorithm based on CPU, memory, architecture, and KVM support
    - Implement resource reservation and release
    - _Requirements: 11.3, 13.2_

  - [x] 6.3 Write property test for host utilization threshold
    - **Property 9: Host Utilization Threshold Enforcement**
    - **Validates: Requirements 9.4**

  - [x] 6.4 Write property test for host status transition
    - **Property 10: Unreachable Host Status Transition**
    - **Validates: Requirements 9.3**

  - [x] 6.5 Write property test for host selection
    - **Property 11: Host Selection Meets Requirements**
    - **Validates: Requirements 11.3, 13.2**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Physical Board Management Service
  - [x] 8.1 Create Board Management Service
    - Implement `BoardManagementService` class
    - Add registration with SSH/serial validation
    - Add status monitoring and health tracking
    - Implement maintenance mode and decommissioning
    - _Requirements: 8.1-8.5, 10.1-10.5_

  - [x] 8.2 Create Power Controller
    - Implement `PowerController` class
    - Add support for USB hub, network PDU, and GPIO relay control
    - Implement power cycle sequence with monitoring
    - _Requirements: 18.1-18.5_

  - [x] 8.3 Create Flash Station Controller
    - Implement `FlashStationController` class
    - Add firmware flashing with progress tracking
    - Implement verification and rollback support
    - _Requirements: 6.2-6.4_

  - [x] 8.4 Create Board Selection Strategy
    - Implement `BoardSelectionStrategy` class
    - Add filtering by architecture, board type, and peripherals
    - Implement board reservation and release
    - _Requirements: 11.3, 13.3_

  - [x] 8.5 Write property test for board recovery
    - **Property 13: Unreachable Board Recovery Attempt**
    - **Validates: Requirements 10.3**

  - [x] 8.6 Write property test for board selection
    - **Property 14: Board Selection Meets Requirements**
    - **Validates: Requirements 11.3, 13.3**

  - [x] 8.7 Write property test for board flashing lock
    - **Property 15: Board Flashing Locks Board**
    - **Validates: Requirements 6.2**

  - [x] 8.8 Write property test for power cycle sequence
    - **Property 16: Power Cycle Recovery Sequence**
    - **Validates: Requirements 18.2**


- [-] 9. Implement Deployment Manager
  - [x] 9.1 Create Deployment Manager
    - Implement `DeploymentManager` class
    - Add deployment to QEMU hosts with artifact transfer and VM configuration
    - Add deployment to physical boards with flashing support
    - Implement boot verification and rollback
    - _Requirements: 5.1-5.5, 6.1-6.5_

  - [ ] 9.2 Write property test for deployment compatibility
    - **Property 6: Deployment Artifact Compatibility**
    - **Validates: Requirements 5.1, 6.1**

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Health Monitoring and Alerting
  - [ ] 11.1 Create Health Monitor Service
    - Implement `HealthMonitorService` class
    - Add periodic health checks for all resource types
    - Implement threshold-based status transitions
    - Add health history tracking
    - _Requirements: 2.1-2.3, 9.1-9.3, 10.1-10.4_

  - [ ] 11.2 Create Alert Service
    - Implement `AlertService` class
    - Add alert generation for resource issues
    - Implement notification via dashboard, email, and webhook
    - Add alert acknowledgment and resolution tracking
    - _Requirements: 16.1-16.5_

  - [ ] 11.3 Write property test for alert timing
    - **Property 23: Alert Generation Within Time Limit**
    - **Validates: Requirements 16.1**

- [ ] 12. Implement Resource Groups and Policies
  - [ ] 12.1 Create Resource Group Manager
    - Implement resource grouping by labels and purpose
    - Add group statistics aggregation
    - Implement group-based filtering for selection strategies
    - _Requirements: 14.1, 14.3, 14.5_

  - [ ] 12.2 Create Allocation Policy Enforcer
    - Implement policy enforcement during allocation
    - Add support for max concurrent, team restrictions, and priority
    - Implement policy conflict resolution
    - _Requirements: 14.2, 14.4_

  - [ ] 12.3 Write property test for load balancing
    - **Property 17: Load Balancing Preference**
    - **Validates: Requirements 13.4**

  - [ ] 12.4 Write property test for maintenance mode
    - **Property 18: Maintenance Mode Blocks Allocations**
    - **Validates: Requirements 12.1**

  - [ ] 12.5 Write property test for decommission safety
    - **Property 19: Decommission Requires No Active Workloads**
    - **Validates: Requirements 12.4**

  - [ ] 12.6 Write property test for reservation consistency
    - **Property 20: Resource Reservation Consistency**
    - **Validates: Requirements 11.5**

  - [ ] 12.7 Write property test for policy enforcement
    - **Property 21: Policy Enforcement During Allocation**
    - **Validates: Requirements 14.2**

  - [ ] 12.8 Write property test for group statistics
    - **Property 22: Group Statistics Aggregation**
    - **Validates: Requirements 14.5**

- [ ] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Implement Pipeline Manager
  - [ ] 14.1 Create Pipeline Manager
    - Implement `PipelineManager` class
    - Add pipeline creation with build → deploy → boot → test stages
    - Implement stage sequencing and status tracking
    - Add failure handling and stage retry
    - _Requirements: 17.1-17.5_

  - [ ] 14.2 Write property test for pipeline sequencing
    - **Property 7: Pipeline Stage Sequencing**
    - **Validates: Requirements 17.2, 17.4**

  - [ ] 14.3 Write property test for failure recovery
    - **Property 24: Provisioning Failure Triggers Alternative**
    - **Validates: Requirements 16.4**


- [ ] 15. Implement API Endpoints
  - [ ] 15.1 Create Build Server API router
    - Implement `/build-servers` CRUD endpoints
    - Add `/build-servers/{id}/status` and `/build-servers/{id}/capacity` endpoints
    - Implement `/build-servers/{id}/maintenance` endpoint
    - _Requirements: 1.1-1.5, 2.1-2.5_

  - [ ] 15.2 Create Build Jobs API router
    - Implement `/build-jobs` submission and listing endpoints
    - Add `/build-jobs/{id}/status` and `/build-jobs/{id}/logs` endpoints
    - Implement `/build-jobs/{id}/cancel` endpoint
    - _Requirements: 3.1-3.5_

  - [ ] 15.3 Create Artifacts API router
    - Implement `/artifacts` listing and retrieval endpoints
    - Add `/artifacts/latest` endpoint for branch-based retrieval
    - Implement artifact download endpoints
    - _Requirements: 4.1-4.5_

  - [ ] 15.4 Create Hosts API router
    - Implement `/hosts` CRUD endpoints
    - Add `/hosts/{id}/status` and `/hosts/{id}/capacity` endpoints
    - Implement `/hosts/{id}/vms` endpoint
    - _Requirements: 7.1-7.5, 9.1-9.5_

  - [ ] 15.5 Create Boards API router
    - Implement `/boards` CRUD endpoints
    - Add `/boards/{id}/status` and `/boards/{id}/health` endpoints
    - Implement `/boards/{id}/power-cycle` and `/boards/{id}/flash` endpoints
    - _Requirements: 8.1-8.5, 10.1-10.5, 18.1-18.5_

  - [ ] 15.6 Create Pipelines API router
    - Implement `/pipelines` creation and listing endpoints
    - Add `/pipelines/{id}/status` and `/pipelines/{id}/logs` endpoints
    - Implement `/pipelines/{id}/cancel` endpoint
    - _Requirements: 17.1-17.5_

  - [ ] 15.7 Write integration tests for API endpoints
    - Test build server registration and management flow
    - Test build job submission and artifact retrieval flow
    - Test host and board registration and selection flow
    - Test pipeline creation and execution flow
    - _Requirements: All_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 17. Implement Frontend Components
  - [ ] 17.1 Create Build Server Management Panel
    - Implement build server list view with status indicators (online/offline/maintenance)
    - Add build server registration form with hostname, IP, SSH credentials, and toolchain configuration
    - Implement build server detail view with active builds, queue depth, and history
    - Add maintenance mode toggle and decommission confirmation dialog
    - Implement real-time status updates via WebSocket
    - _Requirements: 1.1, 2.1, 2.5, 15.1_

  - [ ] 17.2 Create Build Job Dashboard
    - Implement build job submission form with repository URL, branch, architecture, and server selection
    - Add "Auto" option for automatic server selection with tooltip explaining selection criteria
    - Implement build queue view with estimated start times
    - Add active builds view with progress bars and cancel buttons
    - Implement build log viewer with real-time streaming and search
    - Add build history table with filtering by status, architecture, and date range
    - _Requirements: 3.1, 3.5, 15.1_

  - [ ] 17.3 Create Artifact Browser
    - Implement artifact list view grouped by build with download links
    - Add artifact search by build ID, commit hash, or branch
    - Implement "Latest" artifact selector for each branch/architecture combination
    - Add artifact detail view with checksums, sizes, and metadata
    - Implement artifact retention policy configuration UI
    - _Requirements: 4.1-4.5, 15.2_

  - [ ] 17.4 Create Host Management Panel
    - Implement host list view with capacity bars (CPU, memory, storage)
    - Add host registration form with hostname, IP, SSH credentials, and resource specs
    - Implement host detail view with running VMs, network config, and performance graphs
    - Add maintenance mode toggle and decommission confirmation dialog
    - Implement real-time utilization updates via WebSocket
    - _Requirements: 7.1, 9.1, 9.5, 15.2_

  - [ ] 17.5 Create Board Management Panel
    - Implement board list view with health indicators (connectivity, temperature, power)
    - Add board registration form with board type, serial number, connection method, and power control config
    - Implement board detail view with hardware specs, peripherals, firmware version, and test history
    - Add power cycle button with confirmation and status monitoring
    - Add firmware flash button with progress indicator and log viewer
    - Implement maintenance mode toggle and decommission confirmation dialog
    - _Requirements: 8.1, 10.1, 10.5, 15.3, 18.1-18.5_

  - [ ] 17.6 Create Environment Creation Form Updates
    - Add "Build Artifacts" section with build ID, commit hash, or "Latest" selection
    - Add artifact preview showing kernel image, rootfs, and device tree files
    - Add "Target Resource" section with host/board selection dropdown
    - Implement "Auto" option with tooltip explaining selection criteria
    - Add capacity warning indicators when selected resource is near limits
    - Implement alternative resource suggestions when selected resource is unavailable
    - Add deployment progress indicator after form submission
    - _Requirements: 5.1, 6.1, 11.1-11.5_

  - [ ] 17.7 Create Pipeline Dashboard
    - Implement pipeline creation form with source repo, branch, architecture, and environment type
    - Add pipeline list with stage progress indicators (build → deploy → boot → test)
    - Implement pipeline detail view with expandable stage cards
    - Add stage log viewer with real-time streaming
    - Implement pipeline cancel and retry buttons
    - Add pipeline history with filtering and success rate statistics
    - _Requirements: 17.1-17.5, 15.4_

  - [ ] 17.8 Create Resource Group Management UI
    - Implement resource group list view with member counts and utilization
    - Add resource group creation form with name, type, and label filters
    - Implement drag-and-drop resource assignment to groups
    - Add allocation policy configuration form (max concurrent, team restrictions, priority)
    - Implement group statistics dashboard with aggregate capacity and utilization charts
    - _Requirements: 14.1-14.5_

  - [ ] 17.9 Create Infrastructure Dashboard
    - Implement overview dashboard with resource counts and health summary
    - Add resource utilization charts (build servers, hosts, boards)
    - Implement alert panel with recent alerts and acknowledgment buttons
    - Add quick actions panel for common operations (register resource, submit build, create pipeline)
    - Implement resource search across all types with unified results
    - _Requirements: 15.1-15.4, 16.1-16.5_

  - [ ] 17.10 Create Infrastructure Settings Page
    - Implement health check interval configuration
    - Add alert threshold configuration for each resource type
    - Implement notification channel configuration (email, webhook)
    - Add artifact retention policy configuration
    - Implement default selection strategy configuration
    - _Requirements: 2.4, 9.4, 10.4, 16.1-16.5_

  - [ ] 17.11 Write frontend component tests
    - Test build server management panel interactions
    - Test build job submission and log viewing
    - Test host and board management panel interactions
    - Test environment creation form with resource selection
    - Test pipeline creation and monitoring
    - _Requirements: 15.1-15.4_

- [ ] 18. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
