# Bug Report: Windows Path Resolution Failure in Plugin PreToolUse Hook

**To:** antigravity-support@google.com
**Subject:** [Bug Report] Windows path resolution failure in Plugin PreToolUse hook (googlecloudtools.datacloud_telemetry)

---

### Dear Antigravity Team,

I am writing to report a critical path resolution bug on Windows that blocks all agent tool execution when a plugin `PreToolUse` hook is active (specifically reproduced with `googlecloudtools.datacloud_telemetry`).

---

### 1. Environment Details
* **Operating System**: Windows 11 / Windows 10
* **Runtime**: Node.js v22.15.1
* **Component**: Antigravity Plugin Hook Runner (`PreToolUse`)
* **Affected Plugin**: `googlecloudtools.datacloud_telemetry`
* **Trigger**: Any native agent tool execution (`run_command`, `view_file`, `write_to_file`, `replace_file_content`)

---

### 2. Error Stack Trace
```text
JSON hook "jsonhook__googlecloudtools.datacloud_telemetry_PreToolUse_0_0" failed: command failed: exit status 1, stderr: node:internal/modules/cjs/loader:1404
  throw err;
  ^

Error: Cannot find module 'C:\Users\<user>\.gemini\config\plugins\googlecloudtools.datacloud_telemetry\"C:\Users\<user>\.gemini\config\plugins\googlecloudtools.datacloud_telemetry\telemetry_hook_bundle.js"'
    at Function._resolveFilename (node:internal/modules/cjs/loader:1401:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1057:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1062:22)
    at Function._load (node:internal/modules/cjs/loader:1211:37)
    at TracingChannel.traceSync (node:diagnostics_channel:322:14)
    at wrapModuleLoad (node:internal/modules/cjs/loader:235:24)
    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:170:5)
    at node:internal/main/run_main_module:36:49 {
  code: 'MODULE_NOT_FOUND',
  requireStack: []
}

Node.js v22.15.1
```

---

### 3. Root Cause Analysis
Notice the malformed module path resolved by Node.js:
`'C:\Users\...\googlecloudtools.datacloud_telemetry\"C:\Users\...\telemetry_hook_bundle.js"'`

1. When the hook runner constructs the path on Windows, if the hook path in `plugin.json` contains surrounding double quotes, `path.resolve(pluginDir, hookPath)` treats the quoted path as a relative filename containing literal quote characters rather than recognizing it as an absolute path.
2. This creates a concatenated string with embedded quotes (`...\"C:\...\"`), which crashes Node.js with `MODULE_NOT_FOUND`.

---

### 4. Suggested Patch for Antigravity Core
In the hook path resolution module, strip quotes and normalize paths before resolving:

```typescript
function resolveHookPath(pluginDir: string, hookPath: string): string {
  // Strip surrounding quotes
  const cleaned = hookPath.replace(/^["']|["']$/g, '').trim();

  // If already absolute on Windows or POSIX, return normalized path
  if (path.isAbsolute(cleaned)) {
    return path.normalize(cleaned);
  }

  // Otherwise resolve relative to plugin directory
  return path.normalize(path.resolve(pluginDir, cleaned));
}
```

---

### 5. Workaround Applied
Removing `~/.gemini/config/plugins/googlecloudtools.datacloud_telemetry` locally allows tool execution to resume.

Best regards,
Sankar Ganesh
