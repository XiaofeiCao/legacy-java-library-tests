# Azure SDK Migration Guidelines

## Context

The application is identified using legacy Azure SDKs for Java (`com.microsoft.azure.*`). These libraries reached end of support in 2023. They are not recommended for use in production, should be migrated to the latest Azure SDKs with the latest security patches and new capabilities support.

Follow these steps:

* **Inventory legacy dependencies**: Use tools such as `mvn dependency:tree` or `gradlew dependencies` to find every `com.microsoft.azure.*` SDK and map each one to its modern counterpart under `com.azure.*`.

* **Adopt supported SDKs**: Replace the legacy dependencies with their modern equivalents in your `pom.xml` or `build.gradle`, following the migration guide to align feature parity and new SDK names.

* **Update application code**: Refactor your code to the builder-based APIs, updated authentication flows (Azure Identity), and modern async or reactive patterns required by the latest SDKs. Add concise comments explaining non-obvious changes.

* **Test thoroughly**: Run unit, integration, and end-to-end tests to validate that the modern SDKs behave as expected, focusing on authentication, retry, and serialization differences.

## Migration Guide

### Assumption

- Project is Maven or Gradle.
- Java code is on JDK 8 or above.

### Migrate pom.xml

It is recommended to use azure-sdk-bom (version higher than 1.3.0).

Help with looking up the latest stable version on https://repo1.maven.org/maven2/ and proceed with migration. `azure-resourcemanager-xx` should have groupId `com.azure.resourcemanager` instead of `com.azure`.

Example of pom.xml
```xml
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>com.azure</groupId>
                <artifactId>azure-sdk-bom</artifactId>
                <version>1.3.3</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <dependencies>
        <dependency>
            <groupId>com.azure</groupId>
            <artifactId>azure-identity</artifactId>
        </dependency>
        <dependency>
            <groupId>com.azure.resourcemanager</groupId>
            <artifactId>azure-resourcemanager</artifactId>
        </dependency>
    </dependencies>
```
Example of build.gradle
```groovy
dependencies {
    implementation enforcedPlatform('com.azure:azure-sdk-bom:1.3.3')

    implementation 'com.azure:azure-identity'
    implementation 'com.azure.resourcemanager:azure-resourcemanager'
}
```

### Migrate Java Code

- Make a list of source code/maven/gradle files that contains legacy SDK packages. Migrate each of them.
- Determine legacy SDK artifacts according to previous files, find suitable migration guides in [Package-Specific Migration Guides](#package-specific-migration-guides) and follow the guides whenever possible. Record which migration guide URL you used for each legacy package (e.g., in your plan or commit messages), so you can validate against them later.
- Do not change the Java `package ...;` declaration at the top of each source file; update import statements and type usages as needed.
- Do not upgrade JDK version, if it is already JDK 8 or above.
- If there is test in the project, Java code there also need to be updated.

## Package-Specific Source Code Guidelines (Add them to plan guidelines when generating plan)

### com.microsoft.azure.management.**

#### Code Checklist

- Keep Azure resources, operations, and property values identical. The goal is functional equivalence, not feature expansion.
- Do not change the method sequence when creating or updating an Azure resource unless the new SDK requires it.
- Preserve the existing async pattern. For example, a delayed provisioning pattern that uses `Creatable<Resource>` should not be replaced by a direct `.create()` call. Similarly, when provisioning a resource, do not swap `.withNewDependencyResource` for `.withExistingDependencyResource` unless mandated by the new API surface.
- Keep the text emitted by logging and stdout/stderr unchanged to avoid breaking downstream consumers of those streams.
- Do not replace `resource.region()` with `resource.regionName()`; doing so changes the type from `Region` to `String` and can introduce subtle regressions.

#### Code Samples

##### Authentication with File
Even though file-based authentication is deprecated in the modern SDKs, preserve the existing logic when performing the upgrade.

Legacy code
```java
final File credentialFile = new File(System.getenv("AZURE_AUTH_LOCATION"));
Azure azure = Azure.configure()
    .authenticate(credentialFile)
    .withDefaultSubscription();
```
can be updated to read the JSON file via `ObjectMapper` from the Jackson library and authenticate with the `ClientSecretCredential` class.
```java
final File credentialFile = new File(System.getenv("AZURE_AUTH_LOCATION"));
ObjectMapper mapper = new ObjectMapper();
JsonNode credentialFileNode = mapper.readTree(credentialFile);
String clientId = credentialFileNode.get("clientId").asText();
String clientSecret = credentialFileNode.get("clientSecret").asText();
String tenantId = credentialFileNode.get("tenantId").asText();
String subscriptionId = credentialFileNode.get("subscriptionId").asText();

AzureProfile profile = new AzureProfile(tenantId, subscriptionId, AzureEnvironment.AZURE);
ClientSecretCredential credential = new ClientSecretCredentialBuilder()
    .clientId(clientId)
    .clientSecret(clientSecret)
    .tenantId(tenantId)
    .build();

AzureResourceManager azure = AzureResourceManager.configure()
    .authenticate(credential, profile)
    .withSubscription(subscriptionId);
```

If Jackson is not included in the project, add a compatible version of `jackson-databind`.

Handle `IOException` and other checked exceptions according to the project's standards.

##### ProviderRegistrationInterceptor
If legacy client(XXManager) initializes with `ProviderRegistrationInterceptor`, check whether this client is one of the premium ones:
- Azure
- AuthorizationManager
- CdnManager
- ComputeManager
- ContainerInstanceManager
- ContainerRegistryManager
- ContainerServiceManager
- CosmosDBManager
- DnsZoneManager
- EventHubManager
- KeyVaultManager
- MonitorManager
- MSIManager
- NetworkManager
- RedisManager
- ResourceManager
- SearchServiceManager
- ServiceBusManager
- SqlServerManager
- StorageManager
- TrafficManager

If not, add `ProviderRegistrationPolicy` when initializing the client. Otherwise, don't.

For each legacy client, add along with whether to initialize with `ProviderRegistrationPolicy`, to the generated plan guideline, and migrate accordingly.

1. Legacy client(not premium client):
```java
BatchManager batchManager = BatchManager.configure()
    .withLogLevel(LogLevel.BASIC)
    .withInterceptor(new ProviderRegistrationInterceptor(credentials))
    .authenticate(credentials, subscriptionId);
```
should be migrated to:
```java
BatchManager batchManager = BatchManager.configure()
    .withPolicy(new ProviderRegistrationPolicy())
    .withLogOptions(new HttpLogOptions().setLogLevel(HttpLogDetailLevel.BASIC))
    .authenticate(credential, profile);
```

2. Legacy client(premium clients):
```java
Azure azure = Azure.configure()
    .withInterceptor(new ProviderRegistrationInterceptor(credentials))
    .withLogLevel(LogLevel.BASIC)
    .authenticate(credentials)
    .withSubscription(subscriptionId);
```
should be migrated to:
```java
AzureResourceManager.configure()
    .withLogLevel(HttpLogDetailLevel.BASIC)
    .authenticate(credential, profile);
```

##### BatchAccount
azure-resourcemanager-batch is no longer a premium/handwritten library. In BatchAccount, `withNewStorageAccount` should be replaced by `.withAutoStorage(new AutoStorageBaseProperties().withStorageAccountId(storageAccount.id()))`, while the `storageAccount` needs to be created separately.
Legacy code:
```java
BatchAccount batchAccount = azure.batchAccounts().define(batchAccountName)
    .withRegion(region)
    .withNewResourceGroup(rgName)
    .defineNewApplication(applicationName)
        .defineNewApplicationPackage(applicationPackageName)
        .withAllowUpdates(true)
        .withDisplayName(applicationDisplayName)
        .attach()
    .withNewStorageAccount(storageAccountName)
    .create();
```
Migrated:
```java
StorageAccount storageAccount = storageManager.storageAccounts()
    .define(storageAccountName)
    .withRegion(REGION)
    .withExistingResourceGroup(resourceGroup)
    .create();
BatchAccount account = batchManager.batchAccounts()
    .define(batchAccountName)
    .withRegion(REGION)
    .withExistingResourceGroup(resourceGroup)
    .withAutoStorage(new AutoStorageBaseProperties().withStorageAccountId(storageAccount.id()))
    .create();
// create application with batch account
application = batchManager.applications()
    .define(applicationName)
    .withExistingBatchAccount(resourceGroup, account.name())
    .withDisplayName(applicationDisplayName)
    .withAllowUpdates(true)
    .create();
applicationPackage = batchManager.applicationPackages()
    .define(applicationPackageName)
    .withExistingApplication(resourceGroup, batchAccountName, applicationName)
    .create();
```


## Validation

**Make sure**
- Migrated project pass compilation.
- All tests pass. Don't silently skip tests.
- No legacy SDK dependencies/references exist.
- If azure-sdk-bom is used, ensure no explicit version dependencies for Azure libraries that are in azure-sdk-bom.
  E.g. Instead of `implementation 'com.azure.resourcemanager:azure-resourcemanager:2.60.0'`, we should use `implementation 'com.azure.resourcemanager:azure-resourcemanager'`.
  For Azure libraries in azure-sdk-bom, check https://repo1.maven.org/maven2/com/azure/azure-sdk-bom/{bom_version}/azure-sdk-bom-{bom_version}.pom (bom_version be version used during migration)
- For each migration guide you recorded during migration:
  1. Fetch and read the full content of the guide URL.
  2. Identify the migrated source files that correspond to that guide's package.
  3. Verify the migrated code follows the guide's recommended API replacements, class mappings, authentication patterns, and async/sync conventions.
  4. Fix any deviations — do not just report them.

## Package-Specific Migration Guides

- [Migrate to `com.azure.resourcemanager.**` from `com.microsoft.azure.management.**`](https://aka.ms/java-track2-migration-guide)
- [Migrate to com.azure:azure-messaging-servicebus from com.microsoft.azure:azure-servicebus](https://aka.ms/azsdk/java/migrate/sb)
- [Migrate to azure-messaging-eventhubs from azure-eventhubs and azure-eventhubs-eph](https://aka.ms/azsdk/java/migrate/eh)
- [Migrate to `azure-messaging-eventgrid` from `microsoft-azure-eventgrid`](https://aka.ms/azsdk/java/migrate/eg)
- [Storage Blob Service SDK Migration Guide from 8.x to 12.x](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/storage/azure-storage-blob/migrationGuides/V8_V12.md)
- [Storage Blob Service SDK Migration Guide from 10.x/11.x to 12.x](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/storage/azure-storage-blob/migrationGuides/V10_V12.md)
- [Storage Queue Service SDK Migration Guide from 8.x to 12.x](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/storage/azure-storage-queue/migrationGuides/V8_V12.md)
- [Storage File Share Service SDK Migration Guide from 8.x to 12.x](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/storage/azure-storage-file-share/migrationGuides/V8_V12.md)
- [Migrate to azure-security-keyvault-secrets from azure-keyvault](https://aka.ms/azsdk/java/migrate/kv-secrets)
- [Migrate to azure-security-keyvault-keys from azure-keyvault](https://aka.ms/azsdk/java/migrate/kv-keys)
- [Migrate to azure-security-keyvault-certificates from azure-keyvault](https://aka.ms/azsdk/java/migrate/kv-cert)
- [Migrate to `Azure-Compute-Batch` from `Microsoft-Azure-Batch`](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/batch/azure-compute-batch/MigrationGuide.md)
- [Migrate to `azure-ai-documentintelligence` from `azure-ai-formrecognizer`](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/documentintelligence/azure-ai-documentintelligence/MIGRATION_GUIDE.md)
- [Migrate to `azure-ai-formrecognizer 4.0.0-beta.1 - above` from `azure-ai-formrecognizer 3.1.x - lower`](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/formrecognizer/azure-ai-formrecognizer/migration-guide.md)
- [Migration Guide from Azure OpenAI Java SDK to OpenAI Java SDK](https://raw.githubusercontent.com/Azure/azure-sdk-for-java/main/sdk/openai/azure-ai-openai-stainless/MIGRATION.md)
- [Migrate to azure-monitor-query from azure-loganalytics and azure-applicationinsights-query](https://aka.ms/azsdk/java/migrate/monitorquery)
