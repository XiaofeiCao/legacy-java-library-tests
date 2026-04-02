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

**DELETE the entire `src/test/java/com/microsoft/azure/management/resources/core/` directory. Do NOT migrate these classes — they are fully replaced by `azure-resourcemanager-test`.** It contains:

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

## Fixing Microsoft Graph Endpoint Mismatches in Session Recordings

After swapping session recordings, the modern SDK's `AuthorizationManager` uses **Microsoft Graph v1.0** while legacy recordings contain **Azure AD Graph v1.6** endpoints. The TestProxy will fail to match requests if the recorded URLs don't match.

**When you see errors like:**
```
Unable to find a record for the request POST https://REDACTED/v1.0/applications
Uri doesn't match:
    request <https://REDACTED/v1.0/applications>
    record  <http://REDACTED/00000000-0000-0000-0000-000000000000/applications?api-version=1.6>
```

**Update the session recording files** to replace Azure AD Graph endpoints with Microsoft Graph v1.0 equivalents. Only apply this to Microsoft Graph endpoints — do NOT modify ARM management-plane URLs.

### URL Transformation Rules

| Legacy Azure AD Graph | Modern Microsoft Graph |
| --------------------- | ---------------------- |
| `http://{host}/{tenantId}/applications?api-version=1.6` | `https://{host}/v1.0/applications` |
| `http://{host}/{tenantId}/applications/{id}?api-version=1.6` | `https://{host}/v1.0/applications/{id}` |
| `http://{host}/{tenantId}/applications/{id}/{subresource}?api-version=1.6` | `https://{host}/v1.0/applications/{id}/{subresource}` |
| `http://{host}/{tenantId}/servicePrincipals?api-version=1.6` | `https://{host}/v1.0/servicePrincipals` |
| `http://{host}/{tenantId}/servicePrincipals/{id}?api-version=1.6` | `https://{host}/v1.0/servicePrincipals/{id}` |
| `http://{host}/{tenantId}/servicePrincipals/{id}/{subresource}?api-version=1.6` | `https://{host}/v1.0/servicePrincipals/{id}/{subresource}` |
| `http://{host}/{tenantId}/servicePrincipals?$filter=...&api-version=1.6` | `https://{host}/v1.0/servicePrincipals?$filter=...` |
| `http://{host}/{tenantId}/users?api-version=1.6` | `https://{host}/v1.0/users` |
| `http://{host}/{tenantId}/users/{id}?api-version=1.6` | `https://{host}/v1.0/users/{id}` |
| `http://{host}/{tenantId}/users?$filter=...&api-version=1.6` | `https://{host}/v1.0/users?$filter=...` |
| `http://{host}/{tenantId}/domains?api-version=1.6` | `https://{host}/v1.0/domains` |

**Pattern**: For any Azure AD Graph URL matching `http://{host}/{tenantId}/{resource}?api-version=1.6`:
1. Change protocol from `http://` to `https://`
2. Replace `/{tenantId}/` with `/v1.0/`
3. Remove `api-version=1.6` query parameter (and `&api-version=1.6` if other params exist)
4. Also update any URLs in `ResponseHeaders` (e.g., `location` header) and `ResponseBody` that contain the old pattern

**How to identify Microsoft Graph endpoints**: Look for URLs containing `/{tenantId}/` followed by one of: `applications`, `servicePrincipals`, `users`, `domains`, `groups`, `directoryObjects`. The `{tenantId}` is typically `00000000-0000-0000-0000-000000000000` in sanitized recordings. Do NOT transform ARM management URLs (those contain `/subscriptions/`).
