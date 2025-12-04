# Friend Request by Username Feature

## 📋 Tổng quan

Tính năng gửi lời mời kết bạn bằng **username** thay vì phải biết `friend_id`.

## 🎯 Vấn đề đã giải quyết

- ❌ **Trước đây**: Phải biết `friend_id` (số) để gửi lời mời → Không user-friendly
- ✅ **Bây giờ**: Chỉ cần nhập username → Dễ dàng hơn nhiều

## 🚀 API Endpoint

### POST `/friends/request/by-username`

Gửi lời mời kết bạn bằng username.

**Request Body:**

```json
{
  "username": "target_username"
}
```

**Response (201 Created):**

```json
{
  "user_id": 1,
  "friend_id": 2,
  "status": "pending",
  "created_at": "2025-12-04T10:30:00Z"
}
```

**Error Responses:**

| Status Code | Detail                                 | Nguyên nhân                           |
| ----------- | -------------------------------------- | ------------------------------------- |
| 404         | User with username 'xxx' not found     | Username không tồn tại trong database |
| 400         | Cannot send friend request to yourself | Đang cố kết bạn với chính mình        |
| 400         | Friendship with 'xxx' already exists   | Đã gửi lời mời hoặc đã là bạn         |

## 💡 Cách hoạt động

1. **Search user**: Tìm user theo username (case-insensitive)

   - Sử dụng `UserRepository.search_users()`
   - Filter exact match: `user.username.lower() == username.lower()`

2. **Validate**:

   - Kiểm tra user tồn tại
   - Không cho phép kết bạn với chính mình
   - Kiểm tra đã có friendship chưa

3. **Create friendship**:
   - Gọi `FriendRepository.send_friend_request()`
   - Status: `pending`

## 📝 Code Changes

### 1. Schema (`schemas/friend_schema.py`)

```python
class FriendRequestByUsername(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
```

### 2. Service (`services/friend_service.py`)

```python
async def send_friend_request_by_username(
    db: AsyncSession,
    user_id: int,
    username: str
) -> FriendResponse
```

### 3. Router (`routers/friend_router.py`)

```python
@router.post("/request/by-username")
async def send_friend_request_by_username(...)
```

## 🧪 Testing

### Test với Python:

```python
import requests

# Login để lấy token
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = login_response.json()["access_token"]

# Gửi friend request
response = requests.post(
    "http://localhost:8000/friends/request/by-username",
    headers={"Authorization": f"Bearer {token}"},
    json={"username": "friend_username"}
)
print(response.json())
```

### Test với cURL:

```bash
curl -X POST http://localhost:8000/friends/request/by-username \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "friend_username"}'
```

## ⚠️ Lưu ý quan trọng

1. **Username search là case-insensitive**:

   - `"JohnDoe"` = `"johndoe"` = `"JOHNDOE"`

2. **Phải exact match**:

   - Nhập `"john"` sẽ KHÔNG match với `"johndoe"`
   - Phải nhập đúng username hoàn chỉnh

3. **Search limit**:
   - Chỉ search 10 users đầu tiên
   - Nếu có nhiều users với username tương tự, chỉ lấy exact match

## 🔄 So sánh với endpoint cũ

| Feature       | Old Endpoint                   | New Endpoint                   |
| ------------- | ------------------------------ | ------------------------------ |
| Path          | `/friends/{friend_id}/request` | `/friends/request/by-username` |
| Method        | POST                           | POST                           |
| Input         | Path param (integer)           | Body (username string)         |
| User-friendly | ❌ Khó                         | ✅ Dễ                          |
| Use case      | API internal                   | User-facing UI                 |

## 📱 Frontend Integration

### Example with fetch:

```typescript
async function sendFriendRequest(username: string) {
  const token = localStorage.getItem("access_token");

  const response = await fetch("/friends/request/by-username", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
}

// Usage
try {
  await sendFriendRequest("johndoe");
  alert("Friend request sent!");
} catch (error) {
  alert(error.message); // "User with username 'johndoe' not found"
}
```

## ✅ Completed Features

- ✅ Username-based friend request API
- ✅ Case-insensitive username search
- ✅ Exact match validation
- ✅ Proper error handling với meaningful messages
- ✅ Documentation

## 🎉 Kết luận

Giờ user có thể gửi lời mời kết bạn chỉ bằng cách nhập username, không cần biết ID nữa! 🚀
