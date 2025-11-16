"""
Testing guide for LangChain 1.0 migration.

Comprehensive testing strategy for validating migration correctness,
performance, and backward compatibility.
"""

# See test files created in /tests directory
# Key test modules:

# 1. Unit Tests: tests/unit/test_middleware.py
#    - Test each middleware hook independently
#    - Test Pydantic schema validation
#    - Test error handling

# 2. Integration Tests: tests/integration/test_agent_migration.py
#    - Test backward compatibility with old AgentService
#    - Test new create_agent() pattern
#    - Test middleware composition
#    - Test tool execution

# 3. Performance Tests: tests/performance/test_migration_perf.py
#    - Compare latency: 0.x vs 1.0
#    - Measure token usage efficiency
#    - Test streaming throughput
#    - Measure middleware overhead

# 4. E2E Tests: tests/e2e/test_conversation_flows.py
#    - Full conversation flows
#    - Error recovery
#    - Stream interruption handling
#    - Multiple tool calls

## Running Tests

# Run all tests:
# pytest tests/ -v

# Run specific test module:
# pytest tests/unit/test_middleware.py -v

# Run with coverage:
# pytest tests/ --cov=src --cov-report=html

# Run performance tests only:
# pytest tests/performance/ -v -s

## Test Data

# Use fixtures for consistent test data
# Mock external services (embeddings, database)
# Use async test fixtures for async code

## Acceptance Criteria

Before deploying migration:
- [ ] All existing tests passing (100%)
- [ ] New unit tests passing (100%)
- [ ] No performance regression
- [ ] Backward compatibility verified
- [ ] Code coverage > 80%
- [ ] Load test: 100 concurrent conversations
- [ ] Cost tracking accurate within 5%
