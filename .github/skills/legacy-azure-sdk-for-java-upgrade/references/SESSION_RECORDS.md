# Session Record Migration for TestProxy

When upgrading legacy Azure SDK tests to use the modern `TestProxyTestBase`, session records must be converted and renamed to match TestProxy conventions.

## Naming Convention

| Mode | File Name Pattern | Example |
|---|---|---|
| Legacy (`com.microsoft.azure`) | `methodName.json` | `canCRUDVault.json` |
| TestProxy (`com.azure`) | `ClassName.methodName.json` | `VaultTests.canCRUDVault.json` |

The modern `InterceptorManager` resolves recordings as `ClassName.methodName.json` first, then falls back to `methodName.json`.

## Record Format

| Legacy Format | TestProxy Format |
|---|---|
| `networkCallRecords` (array) | `Entries` (array) |
| `.Method` | `.RequestMethod` |
| `.Uri` | `.RequestUri` |
| `.Headers` | `.RequestHeaders` |
| (not separate) | `.RequestBody` (null) |
| `.Response.StatusCode` (string) | `.StatusCode` (int) |
| `.Response.Body` | `.ResponseBody` |
| `.Response.*` (other keys) | `.ResponseHeaders` |
| `variables` (positional array) | `Variables` (keyed dict `{"0":"v1",...}`) |

## File Placement

TestProxy **hardcodes** the path `src/test/resources/session-records/` — it is not configurable.

When upgrading, rename directories:
1. `session-records/` → `session-records-legacy/` (archive original)
2. `session-records-testproxy/` → `session-records/` (activate TestProxy records)

## Converter Script

Use the converter at `.github/skills/legacy-test-migration/scripts/convert_session_records.py`:

```bash
python3 .github/skills/legacy-test-migration/scripts/convert_session_records.py \
  <module>/src/test/resources/session-records \
  <module>/src/test/resources/session-records-testproxy \
  --test-dir <module>/src/test/java/com/microsoft/azure/management/<service>/
```

The `--test-dir` flag auto-scans Java test files to build a method→class mapping, producing correctly named `ClassName.methodName.json` output files.

## TestProxy Integration

- TestProxy runs on `localhost:5000`, started with `--storage-location <repoRoot>`
- Without `assets.json`, it reads records locally from `src/test/resources/session-records/`
- With `assets.json`, it fetches records from `Azure/azure-sdk-assets` into `.assets/<worktree>/`
- REST API: `POST /playback/start` with `x-recording-file` header specifying the repo-relative record path

## When to Apply

Apply session record migration as part of the test upgrade step when:
- Legacy tests used `TestBase` from `com.microsoft.azure.management.resources.core`
- Tests are being migrated to `TestProxyTestBase` from `com.azure.core.test`
- Session records exist in legacy format under `session-records/`
