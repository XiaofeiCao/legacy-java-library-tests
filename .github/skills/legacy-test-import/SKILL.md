---
name: legacy-test-import
description: Import tests from Azure/azure-libraries-for-java legacy SDK modules into this repository. Use when adding a new azure-mgmt-* module's tests.
---

# Legacy Azure Java SDK Test Migration Skill

## Purpose

This repository hosts tests copied from **Azure/azure-libraries-for-java** (the legacy Azure Management Libraries for Java). Each legacy `azure-mgmt-*` artifact gets its own directory with a standalone Maven project.

## Source Repository

- **Repo:** `Azure/azure-libraries-for-java` (branch: `master`)
- **Structure:** Each module is at `azure-mgmt-{service}/` with tests at `src/test/java/com/microsoft/azure/management/{service}/`

## Migration Process

Follow these 8 steps to add a new legacy module:

### Step 1: Discover test files

List the contents of `Azure/azure-libraries-for-java/azure-mgmt-{service}/src/test/java/com/microsoft/azure/management/{service}/` to find all test `.java` files.

### Step 2: Create directory and pom.xml

Create `azure-mgmt-{service}/pom.xml` by cloning an existing module's pom.xml (e.g., `azure-mgmt-keyvault/pom.xml`) and adjusting:

- `<artifactId>` → `azure-mgmt-{service}-tests`
- `<name>` and `<description>` → update for the service
- **Dependencies** → keep the shared ones, add/remove service-specific deps

**Shared dependency versions (do not change):**

| Dependency | Version | Scope |
|---|---|---|
| `azure-client-runtime` | 1.7.14 | compile |
| `azure-mgmt-resources` | 1.41.4 | compile |
| `junit` | 4.13.2 | test |
| `azure-client-authentication` | 1.7.14 | test |
| `commons-io` | 2.7 | test |
| `slf4j-simple` | 1.7.36 | test |

**Service-specific deps** — check the source module's `pom.xml` for additional deps like:
- `azure-mgmt-{service}:1.41.4` (the module itself)
- Cross-module deps (e.g., keyvault needs `azure-mgmt-graph-rbac`, `azure-keyvault`)

### Step 3: Download test Java files

Download all `.java` files from the source test directory into:
```
azure-mgmt-{service}/src/test/java/com/microsoft/azure/management/{service}/
```

### Step 4: Copy test infrastructure classes

Copy the 12 test infrastructure classes into:
```
azure-mgmt-{service}/src/test/java/com/microsoft/azure/management/resources/core/
```

These classes come from `azure-mgmt-resources/src/test/` in the source repo and are **not available on Maven Central** (the test-jar is unpublished). If another module in this repo already has them, copy from there.

**Complete list of required classes:**
1. `TestBase.java`
2. `InterceptorManager.java`
3. `AzureTestCredentials.java`
4. `NetworkCallRecord.java`
5. `RecordedData.java`
6. `ResourceGroupTaggingInterceptor.java`
7. `TestDelayProvider.java`
8. `TestFileProvider.java`
9. `TestResourceNamer.java`
10. `TestResourceNamerFactory.java`
11. `TestResourceProviderRegistration.java`
12. `TestUtilities.java`

### Step 5: Download session records and create TestProxy copies

Check which `@Test` methods are **not** `@Ignore`. For each active test method, download its session record from the source repo into:
```
azure-mgmt-{service}/src/test/resources/session-records/{methodName}.json
```

**Keep the originals as-is.** Then create a converted copy in TestProxy format with class-prefixed naming:
```bash
python3 .github/skills/legacy-test-import/scripts/convert_session_records.py \
  azure-mgmt-{service}/src/test/resources/session-records \
  azure-mgmt-{service}/src/test/resources/session-records-testproxy \
  --test-dir azure-mgmt-{service}/src/test/java/com/microsoft/azure/management/{service}/
```

This preserves the original legacy format in `session-records/` and adds the migrated TestProxy format in `session-records-testproxy/`.

**Naming convention:**
- Legacy format uses `methodName.json` (e.g., `canCRUDVault.json`)
- TestProxy format uses `ClassName.methodName.json` (e.g., `VaultTests.canCRUDVault.json`)
- The `--test-dir` flag scans Java test files to auto-build the method→class mapping

The converter transforms old format → new TestProxy format:

| Old Format | New TestProxy Format |
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
| file: `methodName.json` | file: `ClassName.methodName.json` |

Only non-`@Ignore` tests have session records.

**TestProxy placement:**
- `session-records/` — original legacy format for the legacy `InterceptorManager`
- `session-records-testproxy/` — converted TestProxy format with `ClassName.methodName.json` naming
- **Important:** TestProxy hardcodes the path `src/test/resources/session-records/` (not configurable). When test code is migrated to `TestProxyTestBase`, rename folders: `session-records/` → `session-records-legacy/`, then `session-records-testproxy/` → `session-records/`
- The test proxy runs locally with `--storage-location <repoRoot>` and does not require `assets.json` for this repo

### Step 6: Verify build

```bash
cd azure-mgmt-{service}
mvn compile test-compile
```

Fix any compilation errors (usually missing dependencies in pom.xml).

### Step 7: Verify tests

Run the tests in playback mode to confirm session records load correctly:

```bash
cd azure-mgmt-{service}
mvn test
```

All non-`@Ignore` tests should pass using the session records for playback.

**SecurityException workaround:** If tests fail with a `java.lang.SecurityException` (e.g., "sealing violation" or "package access" errors), it means the test package collides with a sealed package in one of the dependency JARs. Fix this by renaming the test package:

1. Choose a new package name that avoids the conflict, e.g., `com.microsoft.azure.management.{service}.tests`
2. Create the new directory structure:
   ```
   azure-mgmt-{service}/src/test/java/com/microsoft/azure/management/{service}/tests/
   ```
3. Move all test `.java` files into the new directory
4. Update the `package` declaration in each moved file from:
   ```java
   package com.microsoft.azure.management.{service};
   ```
   to:
   ```java
   package com.microsoft.azure.management.{service}.tests;
   ```
5. Re-run `mvn test` to confirm the issue is resolved

### Step 8: Commit and push

```bash
git add azure-mgmt-{service}/
git commit -m "Add azure-mgmt-{service} tests from Azure/azure-libraries-for-java"
git push
```

## Known Issues

### GitHub rate limiting
When downloading many files via `curl` from `raw.githubusercontent.com`, you may get 429 (Too Many Requests) responses that silently replace file content with an HTML error page. **Always verify** downloaded files aren't error pages (check first line for `429`). Use the GitHub API as a fallback.

### Test-jar unavailable
The `com.microsoft.azure:azure-mgmt-resources:test-jar:1.41.4` artifact is **not published on Maven Central**. This is why the 12 test infrastructure classes must be inlined into each module rather than declared as a Maven dependency.

### Java version
Source repo targets Java 7 (`<source>1.7</source>`). This repo uses Java 8 for broader compatibility.

### SecurityException (sealed package)
Some legacy modules have test classes whose package name collides with a sealed package inside a dependency JAR (e.g., `azure-mgmt-{service}`). At runtime this causes `java.lang.SecurityException`. The fix is to move the test classes into a sub-package such as `com.microsoft.azure.management.{service}.tests` — see Step 7 for details.

## Available Modules

Modules in `Azure/azure-libraries-for-java` (✅ = migrated):

- ✅ `azure-mgmt-keyvault`
- ⬜ `azure-mgmt-appservice`
- ⬜ `azure-mgmt-batch`
- ⬜ `azure-mgmt-batchai`
- ⬜ `azure-mgmt-cdn`
- ⬜ `azure-mgmt-compute`
- ⬜ `azure-mgmt-containerinstance`
- ⬜ `azure-mgmt-containerregistry`
- ⬜ `azure-mgmt-containerservice`
- ⬜ `azure-mgmt-cosmosdb`
- ⬜ `azure-mgmt-datalake-analytics`
- ⬜ `azure-mgmt-datalake-store`
- ⬜ `azure-mgmt-dns`
- ⬜ `azure-mgmt-eventhub`
- ⬜ `azure-mgmt-graph-rbac`
- ⬜ `azure-mgmt-locks`
- ⬜ `azure-mgmt-monitor`
- ⬜ `azure-mgmt-msi`
- ⬜ `azure-mgmt-network`
- ⬜ `azure-mgmt-redis`
- ⬜ `azure-mgmt-resources`
- ⬜ `azure-mgmt-search`
- ⬜ `azure-mgmt-servicebus`
- ⬜ `azure-mgmt-sql`
- ⬜ `azure-mgmt-storage`
- ⬜ `azure-mgmt-trafficmanager`
