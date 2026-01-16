# Environment Variables Field Reorganization

## Summary
Moved Environment Variables field from Build Server Settings to Build Configuration section, removing duplicate field.

## Changes Made

### Frontend (`dashboard/src/components/infrastructure/BuildJobDashboard.tsx`)

**Removed duplicate field from Build Server Settings:**
- Deleted the Environment Variables field that was at the end of Build Server Settings section
- This field was redundant since Environment Variables is already present in Build Configuration

**Current form structure:**
1. **Basic Settings**
   - Load Template dropdown
   - Save as Template button
   - Build Mode selector (Custom/Kernel)

2. **Build Configuration** (dynamic based on mode)
   - Custom mode: Pre-Build Commands, Build Commands, Post-Build Commands, Environment Variables
   - Kernel mode: Architecture, Kernel Config, Extra Make Args, Artifact Patterns, Environment Variables

3. **Repository Settings (Optional)**
   - Repository URL, Branch, Commit
   - Git Clone Depth, Clone Submodules

4. **Build Server Settings**
   - Build Server (required)
   - Workspace Root, Output Directory
   - Keep Workspace

## Verification

✅ No TypeScript/React diagnostics errors
✅ Environment Variables field appears in Build Configuration for both modes
✅ No duplicate Environment Variables field in Build Server Settings
✅ Form submission logic correctly captures custom_env from Build Configuration

## Result

Environment Variables is now logically grouped with build commands in the Build Configuration section, making it clear that these variables affect the build process itself rather than server configuration.
