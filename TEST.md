# Test Documentation

## Overview

This document provides comprehensive documentation for the Education Platform testing suite, including test structure, current coverage, and guidelines for expanding tests.

---

## Table of Contents

1. [Test Structure](#test-structure)
2. [Current Tests](#current-tests)
3. [Unit vs Integration Tests](#unit-vs-integration-tests)
4. [Running Tests](#running-tests)
5. [Expanding Tests](#expanding-tests)
6. [Best Practices](#best-practices)

---

## Test Structure

```
project/app/
├── api/
│   └── tests/
│       ├── conftest.py                     # Shared fixtures for all tests
│       ├── unit/                           # Unit tests (in-memory DB, mocked services)
│       │   ├── conftest.py                 # Unit-specific fixtures
│       │   ├── test_user.py                # User endpoint tests
│       │   ├── test_subject.py             # Subject CRUD + Keycloak mock tests
│       │   ├── test_topic.py               # Topic CRUD tests
│       │   ├── test_question.py            # Question CRUD tests
│       │   └── test_exam.py                # Exam generation tests
│       └── integration/                    # Integration tests (real DB + Keycloak)
│           ├── conftest.py                 # Integration-specific fixtures
│           ├── test_auth_integration.py    # Auth flow tests
│           └── test_full_system.py         # End-to-end system tests
├── test/                                   # Legacy/manual test scripts
│   ├── test_api.sh                         # Shell-based API tests
│   ├── test_prof_end.sh                    # Professor endpoint tests
│   ├── user_creation.sh                    # User creation test script
│   └── generate_exam.sh                    # Exam generation test script
└── run_tests.sh                            # Main test runner script
```

---

## Current Tests

### Unit Tests (`api/tests/unit/`)

Unit tests use an **in-memory SQLite database** with **mocked external services** (Keycloak). They are fast and isolated.

| Test File | Endpoints Tested | Count | Description |
|-----------|-----------------|-------|-------------|
| `test_user.py` | `GET /api/users/me`, `POST /api/users/create` | 4 | User retrieval, creation, authorization, duplicate handling |
| `test_subject.py` | `POST/GET/PUT/DELETE /api/subjects/*` | 8 | Subject CRUD, authorization, regent validation |
| `test_topic.py` | `POST/GET /api/topics/*` | 5 | Topic creation, retrieval, subject validation |
| `test_question.py` | `POST/GET /api/questions/*` | 4 | Question creation, options retrieval, FK validation |
| `test_exam.py` | `POST /api/exams/generate` | 1 | Exam PDF generation (mocked) |

**Total Unit Tests: 22**

### Integration Tests (`api/tests/integration/`)

Integration tests connect to **real PostgreSQL and Keycloak** instances running in Docker containers.

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_auth_integration.py` | 4 | Health check, auth header validation, subject creation flow with Keycloak group verification |
| `test_full_system.py` | 1 | Complete end-to-end test: authenticate → create subject → verify Keycloak groups → delete → verify cleanup |

**Total Integration Tests: 5**

### Manual Test Scripts (`test/`)

Legacy shell scripts for manual testing:

| Script | Purpose |
|--------|---------|
| `test_api.sh` | Basic API endpoint testing |
| `test_prof_end.sh` | Professor-specific endpoint tests |
| `user_creation.sh` | User creation via Keycloak |
| `generate_exam.sh` | Exam PDF generation test |

---

## Unit vs Integration Tests

### Key Differences

| Aspect | Unit Tests | Integration Tests |
|--------|------------|-------------------|
| **Database** | In-memory SQLite (`sqlite+aiosqlite:///:memory:`) | Real PostgreSQL (port 5433) |
| **Keycloak** | Mocked (`MagicMock`, `AsyncMock`) | Real Keycloak instance (port 8081) |
| **External Services** | All mocked | Real services |
| **Speed** | Fast (< 1 second per test) | Slow (5-30 seconds per test) |
| **Isolation** | Fully isolated | Depends on Docker services |
| **Use Case** | Logic validation, edge cases | End-to-end flow validation |
| **Setup** | No external dependencies | Requires `docker-compose.test.yml` |

### When to Use Each

**Unit Tests:**
- Testing business logic in isolation
- Validating edge cases and error handling
- Quick feedback during development
- Testing authorization/permission logic
- Mocking external API responses

**Integration Tests:**
- Validating real database interactions
- Testing Keycloak group creation/deletion
- Verifying end-to-end user flows
- Testing transaction rollback
- Validating foreign key constraints

### Test Isolation

The test suite uses **Docker project namespacing** to avoid conflicts:

```bash
# Test environment (isolated)
docker compose -p edupro-test -f deployment/docker-compose.test.yml

# Ports used by tests:
# - PostgreSQL: 5433 (host) -> 5432 (container)
# - Keycloak:   8081 (host) -> 8080 (container)
```

---

## Running Tests

### Prerequisites

1. **Docker and Docker Compose** installed
2. **UV package manager** for Python dependencies
3. **Python 3.12+**

### Running All Tests

```bash
# From project root
./run_tests.sh
```

This script:
1. Starts isolated Docker services (DB on 5433, Keycloak on 8081)
2. Waits for services to be ready
3. Runs unit tests
4. Runs integration tests
5. Cleans up

### Running Tests Manually

```bash
# Start test infrastructure
docker compose -p edupro-test -f deployment/docker-compose.test.yml up -d

# Wait for services (check logs)
docker compose -p edupro-test -f deployment/docker-compose.test.yml logs -f

# Run unit tests only
cd api
PYTHONPATH=. uv run pytest tests/unit

# Run integration tests only
cd api
PYTHONPATH=. POSTGRES_PORT=5433 KEYCLOAK_SERVER_URL="http://localhost:8081" \
  uv run pytest tests/integration

# Run specific test file
uv run pytest tests/unit/test_subject.py -v

# Run specific test function
uv run pytest tests/unit/test_subject.py::test_create_subject -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run with output (print statements)
uv run pytest -s

# Run tests matching a pattern
uv run pytest -k "subject"
```

### Stopping Test Services

```bash
# Stop and remove all test containers and volumes
docker compose -p edupro-test -f deployment/docker-compose.test.yml down -v
```

---

## Expanding Tests

### Adding a New Unit Test

**Example: Testing a new `PATCH /api/subjects/{id}` endpoint**

```python
# tests/unit/test_subject.py

@pytest.mark.asyncio
async def test_partial_update_subject(client, mock_auth, session):
    """Test PATCH endpoint for partial subject updates."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    # 1. Create initial subject
    from src.models.subject import Subject
    subject = Subject(name="Original Name", description="Original desc")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # 2. Patch only the description
    response = await client.patch(
        f"/api/subjects/{subject.id}",
        json={"description": "Updated description"}
    )

    # 3. Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["name"] == "Original Name"  # Unchanged

    # 4. Assert database state
    updated = await session.get(Subject, subject.id)
    assert updated.description == "Updated description"
```

### Adding a New Integration Test

**Example: Testing student enrollment flow**

```python
# tests/integration/test_student_enrollment.py

import pytest
import uuid
from src.core.settings import settings

@pytest.mark.asyncio
async def test_enroll_student_in_subject(integration_client, manager_token, edupro_admin):
    """
    Integration test for enrolling a student in a subject.
    Validates Keycloak group membership after enrollment.
    """
    headers = {"Authorization": f"Bearer {manager_token}"}

    # 1. Create a test student
    student_username = f"test_student_{uuid.uuid4().hex[:8]}"
    student_data = {
        "username": student_username,
        "email": f"{student_username}@test.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "Student",
        "realm_role": "student"
    }

    create_response = await integration_client.post(
        "/api/users/create",
        json=student_data,
        headers=headers
    )
    assert create_response.status_code == 200
    student_id = create_response.json()["user_id"]

    # 2. Create a subject
    subject_name = f"Enrollment Test Subject {uuid.uuid4().hex[:6]}"
    subject_response = await integration_client.post(
        "/api/subjects/",
        json={"name": subject_name, "regent_keycloak_id": student_id},
        headers=headers
    )
    assert subject_response.status_code == 200
    subject_id = subject_response.json()["id"]

    # 3. Enroll student in subject (new endpoint)
    enroll_payload = {"student_ids": [student_id]}
    enroll_response = await integration_client.post(
        f"/api/subjects/{subject_id}/enroll",
        json=enroll_payload,
        headers=headers
    )
    assert enroll_response.status_code == 200

    # 4. Verify Keycloak group membership
    expected_student_group = f"s{subject_id}/students"
    groups = edupro_admin.get_groups()
    student_group = next((g for g in groups if g['name'] == expected_student_group), None)

    assert student_group is not None, f"Group {expected_student_group} not found"

    members = edupro_admin.get_group_members(student_group['id'])
    member_ids = [m['id'] for m in members]
    assert student_id in member_ids, "Student not found in subject students group"
```

### Testing a New Model

**Step 1: Create unit test file**

```python
# tests/unit/test_workbook.py

import pytest
from src.core.deps import get_current_user_info
from src.main import app

@pytest.fixture
async def setup_subject(session):
    """Create a subject for workbook tests."""
    from src.models.subject import Subject
    sub = Subject(name="Workbook Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub

@pytest.mark.asyncio
async def test_create_workbook(client, mock_auth, setup_subject):
    """Test workbook creation."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    subject = setup_subject

    payload = {
        "subject_id": subject.id,
        "title": "Test Workbook",
        "description": "A test workbook"
    }

    response = await client.post("/api/workbooks/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Workbook"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_workbooks_by_subject(client, session, setup_subject):
    """Test retrieving workbooks by subject."""
    from src.models.workbook import Workbook

    # Create multiple workbooks
    for i in range(3):
        wb = Workbook(
            subject_id=setup_subject.id,
            title=f"Workbook {i}",
            description=f"Description {i}"
        )
        session.add(wb)
    await session.commit()

    response = await client.get(f"/api/workbooks/subject/{setup_subject.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    titles = [w["title"] for w in data]
    assert "Workbook 0" in titles
    assert "Workbook 1" in titles
    assert "Workbook 2" in titles
```

### Mocking Keycloak in Unit Tests

When testing endpoints that interact with Keycloak:

```python
@pytest.mark.asyncio
async def test_endpoint_with_keycloak(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.core.keycloak import keycloak_client
    from unittest.mock import AsyncMock

    # Mock specific Keycloak methods
    with pytest.MonkeyPatch.context() as mp:
        # Mock create_user_in_keycloak
        mp.setattr(
            keycloak_client,
            "create_user_in_keycloak",
            AsyncMock(return_value={"user_id": "new-id", "message": "created"})
        )

        # Mock get_user_by_email
        mp.setattr(
            keycloak_client,
            "get_user_by_email",
            AsyncMock(return_value={"id": "existing-id", "email": "test@test.com"})
        )

        response = await client.post("/api/users/create", json={...})
        assert response.status_code == 200
```

### Testing Error Cases

```python
@pytest.mark.asyncio
async def test_create_subject_with_invalid_regent(client, mock_auth):
    """Test error handling when regent user doesn't exist."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    from unittest.mock import patch
    from fastapi import HTTPException

    # Mock verify_regent_exists to raise exception
    with patch(
        "src.services.subject.verify_regent_exists",
        side_effect=HTTPException(
            status_code=400,
            detail="Regent user with ID 'invalid-id' not found."
        )
    ):
        response = await client.post(
            "/api/subjects/",
            json={"name": "Bad Subject", "regent_keycloak_id": "invalid-id"}
        )

        assert response.status_code == 400
        assert "Regent user" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_nonexistent_subject(client, mock_auth):
    """Test 404 when deleting a subject that doesn't exist."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    response = await client.delete("/api/subjects/99999")
    assert response.status_code == 404
```

---

## Best Practices

### Test Naming Conventions

```python
# Use descriptive names following this pattern:
test_<action>_<entity>_<condition>()

# Examples:
test_create_subject_success()
test_create_subject_unauthorized()
test_create_subject_invalid_regent()
test_get_subject_not_found()
test_delete_subject_cascades_to_topics()
```

### Fixture Organization

```python
# conftest.py - Shared fixtures

@pytest.fixture
def manager_user():
    """Create a mock manager user."""
    return User(
        user_id="manager-id-123",
        username="manager",
        email="manager@example.com",
        realm_roles=["manager"],
        groups=[]
    )

@pytest_asyncio.fixture
async def session(engine):
    """Create an async database session."""
    # Setup
    yield session
    # Teardown
```

### Test Data Setup

```python
# Always clean up after tests
@pytest.mark.asyncio
async def test_something(client, session):
    # Create test data
    item = TestModel(name="Test")
    session.add(item)
    await session.commit()

    try:
        # Run test
        response = await client.get(f"/api/items/{item.id}")
        assert response.status_code == 200
    finally:
        # Cleanup (if not using transaction rollback)
        await session.delete(item)
        await session.commit()
```

### Using Parametrization

```python
import pytest

@pytest.mark.parametrize("role,expected_status", [
    ("manager", 200),
    ("professor", 200),
    ("student", 403),
])
@pytest.mark.asyncio
async def test_create_subject_by_role(client, role, expected_status):
    """Test subject creation with different user roles."""

    user = User(
        user_id=f"{role}-id",
        username=role,
        email=f"{role}@test.com",
        realm_roles=[role],
        groups=[]
    )

    async def mock_user():
        return user

    app.dependency_overrides[get_current_user_info] = mock_user

    response = await client.post("/api/subjects/", json={"name": "Test"})
    assert response.status_code == expected_status
```

### Testing Async Code

```python
# Always use @pytest.mark.asyncio decorator
@pytest.mark.asyncio
async def test_async_endpoint(client):
    response = await client.get("/api/async-endpoint")
    assert response.status_code == 200

# Use pytest_asyncio.fixture for async fixtures
@pytest_asyncio.fixture
async def async_data():
    data = await fetch_data()
    yield data
```

### Coverage Goals

Aim for:
- **80%+ line coverage** on `src/` directory
- **100% coverage** on critical paths (auth, permissions)
- **At least 1 unit test** per endpoint
- **At least 1 integration test** per major flow

Check coverage:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

---

## Troubleshooting

### Common Issues

**1. Tests fail with "database is locked"**

```bash
# Ensure no other test is running
docker compose -p edupro-test down -v

# Clear any leftover volumes
docker volume ls | grep edupro-test
docker volume rm edupro-test_db_data
```

**2. Keycloak connection timeout**

```bash
# Check Keycloak is running
docker compose -p edupro-test ps

# View Keycloak logs
docker compose -p edupro-test logs keycloak

# Increase wait time in run_tests.sh if needed
```

**3. Import errors in tests**

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=.

# Or run with uv
uv run pytest tests/unit/test_subject.py
```

**4. Async test hangs**

```python
# Ensure you're using the decorator
@pytest.mark.asyncio
async def test_something():
    ...

# Check pytest-asyncio is installed
uv pip list | grep pytest-asyncio
```

---

## Future Improvements

- [ ] Add frontend tests (React Testing Library)
- [ ] Add E2E tests (Playwright or Cypress)
- [ ] Add performance/load tests
- [ ] Add API contract tests
- [ ] Add snapshot tests for PDF generation
- [ ] Integrate with CI/CD pipeline
- [ ] Add test coverage reporting (Codecov, Coveralls)

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/testing/)
- [httpx AsyncClient](https://www.python-httpx.org/async/)
