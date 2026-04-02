---
name: legacy-azure-sdk-for-java-upgrade
description: 'Upgrade legacy Azure Java SDKs (com.microsoft.azure) to modern Azure SDKs (com.azure) with structured planning and execution. USE FOR: "upgrade legacy azure sdk", "migrate azure java sdk". DO NOT USE FOR: "generate upgrade skill", "run benchmark", "analyze benchmark". INVOKES: shell commands, web_fetch, file read/write.'
---

Upgrade all `com.microsoft.azure.*` to `com.azure.*` equivalents in one autonomous session.

## References

- [Rules and Workflow](./references/RULES.md) — success criteria, anti-excuse rules, workflow
- [Migration Guidelines](./references/INSTRUCTION.md) — package mappings, code samples, validation
- [Test Recordings](./references/TEST_RECORDINGS.md) — swapping pre-converted test recordings for TestProxy
- [Plan Template](./references/PLAN_TEMPLATE.md) · [Progress Template](./references/PROGRESS_TEMPLATE.md) · [Summary Template](./references/SUMMARY_TEMPLATE.md)

## Workflow

1. **Precheck** — Verify Maven/Gradle project, detect JDK/build tools, create `plan.md` from [Plan Template](./references/PLAN_TEMPLATE.md). If git available, create branch `java-upgrade/{RUN_ID}`.
2. **Plan** — Inventory deps, consult [Migration Guidelines](./references/INSTRUCTION.md), populate `plan.md`
3. **Execute** — Create `progress.md` from [Progress Template](./references/PROGRESS_TEMPLATE.md), migrate build config then source, build/test/fix, commit per step
4. **Test Recordings** — If module has pre-converted recordings, swap directories per [Test Recordings guide](./references/TEST_RECORDINGS.md): rename `session-records/` → `session-records-legacy/`, `session-records-testproxy/` → `session-records/`
5. **Validate** — Create `summary.md` from [Summary Template](./references/SUMMARY_TEMPLATE.md), apply [validation checklist](./references/INSTRUCTION.md#validation)

## Constraints

- 100% test pass · no premature termination · incremental changes · review each step
- Prefer wrappers (`mvnw`/`gradlew`) · see [Rules](./references/RULES.md)

## Examples

```
"upgrade legacy azure sdk" → precheck → plan → execute → validate
```

## Troubleshooting

- **Build fails**: Debug, fix, rebuild — [Rules](./references/RULES.md)
- **Test failures**: Iterative fix loop — [Rules](./references/RULES.md)
