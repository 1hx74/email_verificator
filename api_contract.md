### 1. Отправка кода подтверждения

**`POST /api/mail/1`**

**Request:**

```json
{
    "email": "string"
}
```

**Response `200 OK`:**

```json
{
    "code": 200,
    "state": "OK"
}
```

**Errors:**

`429 Too Many Requests`

```json
{
    "code": 429,
    "state": "Too Many Requests"
}
```
`403 Invalid email`
```json
{
    "code": 403,
    "state": "Invalid email"
}
```

---

### 2. Проверка кода подтверждения

**`POST /api/mail/2`**

**Request:**

```json
{
    "email": "string",
    "verification_code": "XXXXXX"
}
```

**Response `200 OK`:**

Успешная проверка:

```json
{
    "code": 200,
    "state": "OK",
    "verification": true
}
```

Неверный код:

```json
{
    "code": 200,
    "state": "OK",
    "verification": false
}
```

**Errors:**

`429 Too Many Requests`

```json
{
    "code": 429,
    "state": "Too Many Requests"
}
```

`404 Not Found`

```json
{
    "code": 404,
    "state": "User not found"
}
```
`403 Invalid email`
```json
{
    "code": 403,
    "state": "Invalid email"
}
```
