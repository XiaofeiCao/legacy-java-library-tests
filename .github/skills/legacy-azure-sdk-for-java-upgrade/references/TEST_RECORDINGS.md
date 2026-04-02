# Session Record Migration for TestProxy

When upgrading legacy Azure SDK tests to use the modern `TestProxyTestBase`, session records must be swapped from the pre-converted `session-records-testproxy/` folder into the active `session-records/` path.

> **Prerequisite:** The `legacy-test-migration` skill must have already been run for the module, which converts legacy session records to TestProxy format and places them in `session-records-testproxy/` with `ClassName.methodName.json` naming.

## File Placement

TestProxy **hardcodes** the path `src/test/resources/session-records/` — it is not configurable.

During the upgrade, rename directories:
```bash
cd <module>/src/test/resources
mv session-records session-records-legacy
mv session-records-testproxy session-records
```

1. `session-records/` → `session-records-legacy/` (archive original legacy-format records)
2. `session-records-testproxy/` → `session-records/` (activate pre-converted TestProxy records)

## When to Apply

Apply this step when:
- The module has both `session-records/` and `session-records-testproxy/` directories
- Tests are being migrated to `TestProxyTestBase` from `com.azure.core.test`

