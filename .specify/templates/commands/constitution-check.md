# Constitution Compliance Check

Execute a comprehensive compliance check against the project constitution to identify deviations and recommend improvements.

## Execution Steps

1. **Load Constitution** - Read `.specify/memory/constitution.md`
2. **Scan Codebase** - Check all Python and TypeScript files for compliance
3. **Verify Principles** - Test each of the 8 core principles:
   - AI-First Architecture (LangChain v1.0)
   - Modular Middleware Framework
   - Vector Storage Excellence
   - Type Safety and Validation
   - Async-First Implementation
   - Semantic Code Organization
   - Production Readiness
   - Observability and Monitoring
4. **Generate Report** - Output compliance status and remediation items

## Output Format

- Constitution version and effective date
- Compliance score (0-100%)
- Principle-by-principle breakdown
- Code violations with line numbers
- Recommended remediation steps
- Next review date

## Examples

```bash
# Check entire codebase
/speckit.constitution-check

# Check specific file
/speckit.constitution-check backend/src/services/agent_service.py

# Generate detailed report
/speckit.constitution-check --detailed
```
