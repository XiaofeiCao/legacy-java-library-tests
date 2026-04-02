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

## When to Apply

Apply this step when migrating test code from `com.microsoft.azure.management.resources.core.TestBase` to `com.azure.core.test.TestProxyTestBase`. The test classes must also be updated to extend `TestProxyTestBase` instead of `TestBase`.
