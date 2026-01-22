# Users API

Endpoints for managing users within a tenant.

---

## List Users {#list}

```http
GET /api/v1/admin/users
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

---

## Create User {#create}

```http
POST /api/v1/admin/users
Authorization: Bearer YOUR_TOKEN
```

**Request:**
```json
{
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "role": "user",
  "password": "SecurePassword123!"
}
```

**Response (201):**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T11:00:00Z"
}
```

---

## Get User {#get}

```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer YOUR_TOKEN
```

---

## Update User {#update}

```http
PATCH /api/v1/admin/users/{user_id}
Authorization: Bearer YOUR_TOKEN
```

**Request:**
```json
{
  "name": "Jane Smith",
  "role": "admin"
}
```

---

## Delete User {#delete}

```http
DELETE /api/v1/admin/users/{user_id}
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

---

## User Roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only access |
| `user` | Use gateway, view own usage |
| `admin` | Full tenant management |
