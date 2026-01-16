# Build Execution Architecture - Current State and Configuration

## Your Questions Answered

### Q1: Where can I find the build project located and images generated?

**Current Implementation:**
- **Artifact Storage Path**: `/var/lib/artifacts` (default, configurable)
- **Build Job Artifacts**: Stored in `BuildJob.artifacts` field (list of artifact IDs)
- **Log Path**: `BuildJob.log_path` field stores the path to build logs

**Current State**: 
The artifact storage is **configured but not yet implemented**. The BuildJobManager has the infrastructure ready, but the actual SSH-based build execution that would create these artifacts is not yet implemented.

### Q2: Is there a build path user can set?

**Yes, but needs implementation.** Here's what's available:

#### Current Configuration Options:

1. **Artifact Storage Path** (System-level)
   ```python
   BuildJobManager(
       server_pool=server_pool,
       artifact_storage_path="/var/lib/artifacts",  # Configurable
       max_queue_size=1000,
   )
   ```

2. **Build Configuration** (Per-job)
   ```python
   BuildConfig:
       kernel_config: Optional[str] = None  # defconfig name or path
       extra_make_args: List[str] = []
       enable_modules: bool = True
       build_dtbs: bool = True
       custom_env: Dict[str, str] = {}
   ```

**What's Missing:**
- No `build_directory` or `workspace_path` field in BuildConfig
- No `output_directory` configuration
- No remote build path specification

### Q3: Does the build job run on the build server directly or in a Docker?

**Current Design: Direct on Build Server (SSH-based)**

The system is designed to run builds **directly on the build server via SSH**, NOT in Docker containers.

## Current Architecture

### Build Server Model

```python
@dataclass
class BuildServer:
    id: str
    hostname: str
    ip_address: str
    ssh_username: str
    ssh_port: int = 22
    ssh_key_path: Optional[str] = None
    supported_architectures: List[str]
    toolchains: List[Toolchain]
    total_cpu_cores: int
    total_memory_mb: int
    total_storage_gb: int
    # ... other fields
```

**Key Points:**
- Uses SSH credentials (username, port, key path)
- No Docker/container configuration
- Direct access to build server resources
- Toolchains installed directly on the server

### Build Execution Flow (Intended Design)

```
1. Job Submitted
   ↓
2. Server Selected (based on architecture, toolchain, capacity)
   ↓
3. SSH Connection to Build Server
   ↓
4. Create Build Workspace on Server
   ├─ Clone repository
   ├─ Checkout branch/commit
   └─ Create build directory
   ↓
5. Execute Build Commands via SSH
   ├─ Configure kernel (make defconfig)
   ├─ Compile (make -j<cores>)
   └─ Build modules/dtbs
   ↓
6. Collect Artifacts
   ├─ Kernel image (vmlinux, bzImage, etc.)
   ├─ Modules (*.ko files)
   ├─ Device trees (*.dtb files)
   └─ Build logs
   ↓
7. Transfer Artifacts to Central Storage
   ├─ SCP/rsync from build server
   └─ Store in /var/lib/artifacts/<job_id>/
   ↓
8. Update Job Status
   ├─ Mark as COMPLETED/FAILED
   ├─ Record artifact paths
   └─ Store build logs
```

## What's Currently Implemented

### ✅ Implemented
- Build job submission and queuing
- Server selection strategy
- Job status tracking
- Log collection infrastructure
- Artifact path storage (field exists)
- Background queue processing
- Job cancellation

### ❌ Not Yet Implemented
- **SSH-based build execution**
- **Repository cloning on build server**
- **Actual build command execution**
- **Artifact collection and transfer**
- **Build workspace management**
- **Cleanup after build completion**

## Recommended Build Path Configuration

To properly support user-configurable build paths, the system should be enhanced:

### Enhanced BuildConfig

```python
@dataclass
class BuildConfig:
    # Existing fields
    kernel_config: Optional[str] = None
    extra_make_args: List[str] = field(default_factory=list)
    enable_modules: bool = True
    build_dtbs: bool = True
    custom_env: Dict[str, str] = field(default_factory=dict)
    
    # NEW: Build path configuration
    workspace_root: str = "/tmp/builds"  # Root directory for all builds
    build_directory: Optional[str] = None  # Specific build dir (auto-generated if None)
    output_directory: Optional[str] = None  # Where to place artifacts
    keep_workspace: bool = False  # Keep workspace after build
    
    # NEW: Repository configuration
    git_depth: int = 1  # Shallow clone depth
    git_submodules: bool = False  # Clone submodules
    
    # NEW: Artifact configuration
    artifact_patterns: List[str] = field(default_factory=lambda: [
        "arch/*/boot/bzImage",
        "arch/*/boot/Image",
        "vmlinux",
        "*.ko",
        "*.dtb"
    ])
```

### Build Workspace Structure (Proposed)

On the build server:
```
/tmp/builds/                          # workspace_root
├── job-<uuid>/                       # Per-job workspace
│   ├── source/                       # Cloned repository
│   │   ├── .git/
│   │   ├── Makefile
│   │   └── ...
│   ├── build/                        # Build output (O=build)
│   │   ├── .config
│   │   ├── vmlinux
│   │   ├── arch/x86/boot/bzImage
│   │   └── ...
│   └── artifacts/                    # Collected artifacts
│       ├── bzImage
│       ├── modules/
│       └── dtbs/
```

On the central server:
```
/var/lib/artifacts/                   # artifact_storage_path
├── <job-id>/                         # Per-job artifacts
│   ├── bzImage
│   ├── vmlinux
│   ├── modules/
│   │   └── *.ko
│   ├── dtbs/
│   │   └── *.dtb
│   └── build.log
```

## Docker vs Direct Execution

### Current Design: Direct Execution ✅

**Advantages:**
- Simpler implementation
- Direct access to server resources
- No container overhead
- Easier debugging
- Toolchains pre-installed on server

**Disadvantages:**
- Less isolation between builds
- Potential conflicts between concurrent builds
- Harder to ensure clean build environment
- Security concerns (builds run as SSH user)

### Alternative: Docker-based Execution

**Would require:**
```python
@dataclass
class BuildServer:
    # ... existing fields ...
    docker_enabled: bool = False
    docker_images: List[str] = field(default_factory=list)
    docker_registry: Optional[str] = None
```

**Build execution would:**
1. SSH to build server
2. Pull/use Docker image with toolchain
3. Run build in container
4. Extract artifacts from container
5. Clean up container

**Advantages:**
- Better isolation
- Reproducible build environment
- Easier to manage toolchain versions
- Better security

**Disadvantages:**
- More complex implementation
- Docker must be installed on build servers
- Additional overhead
- Network required for image pulls

## Implementation Recommendations

### Phase 1: Basic SSH Build Execution (Direct)
1. Implement SSH command execution
2. Clone repository to build server
3. Execute make commands
4. Collect build logs
5. Transfer artifacts back

### Phase 2: Enhanced Configuration
1. Add build path configuration to BuildConfig
2. Support custom workspace locations
3. Implement workspace cleanup
4. Add artifact pattern matching

### Phase 3: Docker Support (Optional)
1. Add Docker detection to build servers
2. Support Docker-based builds
3. Manage Docker images
4. Handle container lifecycle

## Example API Usage (Future)

```bash
# Submit build with custom paths
curl -X POST http://localhost:8000/api/v1/infrastructure/build-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_repository": "https://github.com/torvalds/linux",
    "branch": "master",
    "commit_hash": "HEAD",
    "target_architecture": "x86_64",
    "build_config": {
      "kernel_config": "defconfig",
      "workspace_root": "/mnt/fast-storage/builds",
      "output_directory": "/mnt/artifacts",
      "keep_workspace": false,
      "extra_make_args": ["-j16"],
      "artifact_patterns": [
        "arch/x86/boot/bzImage",
        "vmlinux",
        "System.map"
      ]
    }
  }'
```

## Summary

**Current State:**
- ✅ Build job orchestration complete
- ✅ Queue management working
- ✅ Server selection implemented
- ❌ Actual build execution NOT implemented
- ❌ Artifact collection NOT implemented
- ❌ Build path configuration LIMITED

**Execution Model:**
- Designed for **direct SSH execution** on build servers
- NOT using Docker containers (by default)
- Builds run directly on the server filesystem

**Build Paths:**
- Default artifact storage: `/var/lib/artifacts`
- Build workspace: Not yet configurable (needs implementation)
- Artifacts: Tracked in BuildJob.artifacts field

**Next Steps:**
1. Implement SSH-based build execution
2. Add build workspace management
3. Implement artifact collection and transfer
4. Add configurable build paths to BuildConfig
5. (Optional) Add Docker support for isolated builds
