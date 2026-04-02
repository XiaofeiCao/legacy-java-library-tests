# Legacy Test Infrastructure Replacement

This repository inlines 12 test infrastructure classes from `azure-mgmt-resources:test-jar` (unpublished on Maven Central) into each module under `src/test/java/com/microsoft/azure/management/resources/core/`.

When upgrading to the modern SDK, these inlined classes should be **removed** and replaced by the `azure-resourcemanager-test` dependency.

## Dependency

```xml
<dependency>
    <groupId>com.azure.resourcemanager</groupId>
    <artifactId>azure-resourcemanager-test</artifactId>
    <version>2.0.0-beta.2</version>
    <scope>test</scope>
</dependency>
```

Maven Central: https://repo1.maven.org/maven2/com/azure/resourcemanager/azure-resourcemanager-test/

This brings in `azure-core-test` (with `TestProxyTestBase`) and Azure Identity transitively.

## Classes to Remove

Delete the entire `src/test/java/com/microsoft/azure/management/resources/core/` directory. It contains:

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

## Test Recordings Swap

> **Prerequisite:** The `legacy-test-migration` skill must have already been run for the module, which converts legacy session records to TestProxy format and places them in `session-records-testproxy/` with `ClassName.methodName.json` naming.

TestProxy **hardcodes** the path `src/test/resources/session-records/` — it is not configurable. During the upgrade, rename directories:

```bash
cd <module>/src/test/resources
mv session-records session-records-legacy
mv session-records-testproxy session-records
```

1. `session-records/` → `session-records-legacy/` (archive original legacy-format records)
2. `session-records-testproxy/` → `session-records/` (activate pre-converted TestProxy records)

## When to Apply

Apply these steps when migrating test code from `com.microsoft.azure.management.resources.core.TestBase` to `com.azure.core.test.TestProxyTestBase`:
- Remove the inlined classes and add the `azure-resourcemanager-test` dependency
- Swap the test recordings if the module has both `session-records/` and `session-records-testproxy/` directories
