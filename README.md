# Legacy Java Library Tests

Tests copied from legacy Azure SDK for Java repositories for preservation and reference.

## Source Repository

[Azure/azure-libraries-for-java](https://github.com/Azure/azure-libraries-for-java)

## Structure

Each legacy artifact has its own directory with a standalone Maven project:

```
azure-mgmt-keyvault/       # Key Vault Management tests
azure-mgmt-compute/        # (future) Compute Management tests
azure-mgmt-network/        # (future) Network Management tests
...
```

## Building

Each module is self-contained. To compile a specific module:

```bash
cd azure-mgmt-keyvault
mvn compile test-compile
```

## Adding a New Module

1. Create a directory named after the artifact (e.g., `azure-mgmt-storage`)
2. Add a standalone `pom.xml` referencing published Maven artifacts
3. Copy test files into `src/test/java/...`
4. Copy session records into `src/test/resources/session-records/`
5. Verify with `mvn compile test-compile`

## License

MIT — see [LICENSE](LICENSE)
