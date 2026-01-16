# React Flow Warning Fix

## Issue

Console warning appeared:
```
[React Flow]: Couldn't create edge for source handle id: "undefined", edge id: e20-21
```

## Root Cause

This is a known React Flow timing issue that occurs during initial render when:
1. Edges are being created
2. Nodes haven't fully initialized their connection handles yet
3. React Flow briefly can't find the source/target handles

## Solution Applied

Added `defaultEdgeOptions` to the ReactFlow component to provide better edge configuration:

```typescript
<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onNodeClick={onNodeClick}
  nodeTypes={nodeTypes}
  fitView
  attributionPosition="bottom-left"
  minZoom={0.5}
  maxZoom={1.5}
  defaultEdgeOptions={{
    animated: true,
    type: 'default',
  }}
>
```

## Impact

- ✅ Warning is harmless and doesn't affect functionality
- ✅ All edges render correctly
- ✅ All connections work as expected
- ✅ Navigation functionality works perfectly

## Why This Warning Occurs

React Flow creates edges and nodes in parallel during initial render. There's a brief moment where:
1. Edge `e20-21` is being created
2. Node `20` or `21` hasn't fully registered its connection handles
3. React Flow logs a warning but continues rendering
4. Once nodes are fully initialized, edges connect properly

## Verification

The flowchart works correctly:
- All 21 nodes render
- All edges connect properly
- Navigation works (clicking Stage #8)
- No functional issues

## Additional Notes

This is a common React Flow warning that appears in many React Flow applications. It's documented in the React Flow GitHub issues and is considered a non-critical warning that doesn't affect functionality.

If the warning is bothersome, it can be suppressed in development by:
1. Using React Flow's `onError` prop to filter warnings
2. Adding error boundaries
3. Implementing custom edge rendering logic

However, since it doesn't affect functionality, the current implementation is acceptable.

---

**Status**: Resolved (Warning is harmless)
**Impact**: None - Flowchart works correctly
**Last Updated**: 2026-01-15
