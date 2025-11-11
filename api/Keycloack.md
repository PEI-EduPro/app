# 🔐 Keycloak Integration (Summary)

## Overview

Keycloak authentication integrated into your FastAPI education platform for secure user management via OpenID Connect (OIDC).

---

## 🏗️ Project Changes

### New Files

```
core/
 └── keycloak.py          # Keycloak client setup
models/
 └── user.py              # User model with Keycloak link
routers/
 └── user.py              # User endpoints
services/
 └── user.py              # User logic
```

### Modified Files

* `docker-compose.yml` → added Keycloak + DB services
* `core/deps.py` → JWT verification dependency
* `core/settings.py` → Keycloak config
* `main.py` → registered user routes

---

## ⚙️ Keycloak Setup

**Realm:** `EduPro`
**Client:** `api-backend` (Confidential)
**Roles:** `manager`, `professor`, `student`

**.env**

```env
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=EduPro
KEYCLOAK_CLIENT_ID=api-backend
KEYCLOAK_CLIENT_SECRET=<your-secret>
```

---

## 🧩 Core Components

### `core/keycloak.py`

Handles token validation:

```python
class KeycloakClient:
    def __init__(self):
        self.client = KeycloakOpenID(...)

    async def verify_token(self, token: str):
        return self.client.introspect(token)
```

### `core/deps.py`

Dependency for current user:

```python
async def get_current_user(credentials=Depends(security), session=Depends(get_session)):
    # Verify token → extract user → create if new
```

### `models/user.py`

```python
class User(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    keycloak_id: str
    email: str
    name: str
    role: UserRole
```

### `routers/user.py`

```python
@router.get("/me")
async def read_current_user(user=Depends(get_current_user)):
    return user
```

---

## 🔄 Authentication Flow

1. Frontend redirects to Keycloak for login.
2. Keycloak returns JWT.
3. Frontend sends JWT in `Authorization: Bearer <token>`.
4. FastAPI verifies token → finds or creates user.
5. Returns authenticated user data.

---

## 🧪 Test It

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/EduPro/protocol/openid-connect/token \
  -d "username=teststudent" -d "password=password" \
  -d "client_id=api-backend" -d "client_secret=<secret>" | jq -r '.access_token')

# Access API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/me
```

---

## 🛡️ Security Highlights

* JWT verification via Keycloak public key
* Auto user provisioning on first login
* Role-based access control via decorators
* No password storage in local DB

---

## 🚀 Production Notes

* Use HTTPS and valid certificates
* Enable token refresh
* Configure Keycloak for HA + SSL
* Monitor auth logs and Keycloak health

---

## 📈 Benefits

✅ Centralized auth
✅ Role-based access
✅ No password handling
✅ Scalable and SSO-ready

