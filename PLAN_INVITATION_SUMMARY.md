# 📝 Plan Invitation Feature - Implementation Summary

## ✅ Hoàn thành

Đã implement đầy đủ tính năng mời thành viên vào plan qua chat trong Friend Page.

## 🎯 Chức năng chính

1. **Owner gửi lời mời**: Qua chat với người bạn đã kết nối
2. **Người nhận có 2 lựa chọn**:
   - ✅ **Accept**: Được thêm vào plan với role `member` (chỉ xem)
   - ❌ **Reject**: Lưu trạng thái vào storage, không hiển thị lại khi reload
3. **Trạng thái persistent**: Sử dụng `RoomContext` để lưu trữ

## 📦 Files đã thay đổi

### 1. Models

- `models/message.py`
  ```python
  class MessageType(str, Enum):
      plan_invitation = "plan_invitation"  # ✅ ADDED
  ```

### 2. Schemas

- `schemas/message_schema.py`

  ```python
  class InvitationStatus(str, Enum):
      pending = "pending"
      accepted = "accepted"
      rejected = "rejected"

  class PlanInvitationCreate(BaseModel):
      room_id: int
      plan_id: int
      invitee_id: int
      message: Optional[str]

  class InvitationActionRequest(BaseModel):
      action: InvitationStatus
  ```

### 3. Repository Layer

- `repository/message_repository.py`
  - ✅ `create_plan_invitation_message()` - Tạo message với metadata
  - ✅ `get_invitation_status()` - Lấy status từ RoomContext
  - ✅ `update_invitation_status()` - Update pending → accepted/rejected
  - ✅ `get_pending_invitations()` - Lấy danh sách lời mời chưa xử lý

### 4. Service Layer

- `services/message_service.py`
  - ✅ `send_plan_invitation()` - Gửi lời mời với validation
  - ✅ `respond_to_invitation()` - Accept/reject với logic add member
  - ✅ `get_invitation_details()` - Lấy thông tin chi tiết

### 5. Router/API

- `routers/message_router.py`
  ```
  POST   /messages/invitations/send
  POST   /messages/invitations/{message_id}/respond
  GET    /messages/invitations/{message_id}
  ```

## 🔒 Security & Validations

| Action            | Validation                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| **Send**          | ✅ Sender = plan owner<br>✅ Plan exists<br>✅ Invitee not already member<br>✅ Invitee has room access |
| **Accept/Reject** | ✅ User = invitee<br>✅ Status = pending<br>✅ Message is plan_invitation type                          |

## 💾 Data Flow

### Gửi lời mời

```
1. Validate owner permission
2. Create message (type: plan_invitation)
3. Save to RoomContext:
   {
     "status": "pending",
     "plan_id": 123,
     "invitee_id": 456,
     "sender_id": 789
   }
4. Send via WebSocket
```

### Accept lời mời

```
1. Validate invitee permission
2. Check status = pending
3. Add to plan_members (role: member)
4. Update RoomContext status → "accepted"
5. Return success
```

### Reject lời mời

```
1. Validate invitee permission
2. Check status = pending
3. Update RoomContext status → "rejected"
4. Return success
(Khi reload, frontend check status và không hiển thị)
```

## 🎨 Frontend Integration

### Example API Calls

**1. Send invitation**

```typescript
const response = await fetch("/messages/invitations/send", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    room_id: 1,
    plan_id: 123,
    invitee_id: 456,
    message: "Join my trip to Da Nang!",
  }),
});
```

**2. Respond to invitation**

```typescript
const response = await fetch(`/messages/invitations/${messageId}/respond`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    action: "accepted", // or 'rejected'
  }),
});
```

**3. Get invitation details**

```typescript
const details = await fetch(`/messages/invitations/${messageId}`, {
  headers: { Authorization: `Bearer ${token}` },
}).then((r) => r.json());

// Returns:
// {
//   message_id: 999,
//   sender_id: 789,
//   plan_id: 123,
//   plan_name: "Trip to Da Nang",
//   status: "pending",
//   message: "Join my trip!",
//   created_at: "2025-12-04T10:30:00"
// }
```

### Message Rendering Logic

```typescript
function renderInvitation(message: Message) {
  // 1. Parse content
  const { plan_id, message: inviteText } = JSON.parse(message.content);

  // 2. Get status
  const details = await getInvitationDetails(message.id);

  // 3. Render based on status
  if (details.status === "rejected" && isInvitee) {
    return null; // Don't show
  }

  if (details.status === "accepted") {
    return <AcceptedBadge planName={details.plan_name} />;
  }

  if (details.status === "pending" && isInvitee) {
    return (
      <InvitationCard
        planName={details.plan_name}
        message={inviteText}
        onAccept={() => respondToInvitation(message.id, "accepted")}
        onReject={() => respondToInvitation(message.id, "rejected")}
      />
    );
  }
}
```

## 📊 Database Schema

### Messages Table

```sql
-- Existing columns + new type support
message_type ENUM('text', 'file', 'plan_invitation')
content TEXT -- JSON: {"plan_id": 123, "message": "..."}
```

### RoomContext Table (Already exists)

```sql
-- Stores invitation state
key VARCHAR(128)   -- Format: "invitation_{message_id}"
value JSON         -- {"status": "...", "plan_id": ..., "invitee_id": ...}
```

### PlanMembers Table (Already exists)

```sql
-- Auto-populated on accept
user_id INT
plan_id INT
role ENUM('owner', 'member')
```

## 🧪 Testing

All schemas validated:

```bash
✓ MessageType.plan_invitation
✓ InvitationStatus enum (pending/accepted/rejected)
✓ PlanInvitationCreate schema
✓ InvitationActionRequest schema
✓ All imports successful
```

## 📖 Documentation

Chi tiết đầy đủ xem tại: `backend/PLAN_INVITATION_FEATURE.md`

Bao gồm:

- API endpoint documentation
- Frontend integration guide
- UI suggestions
- Testing examples
- Security considerations

## 🚀 Next Steps (Frontend)

1. ✅ **Backend hoàn thành** - Tất cả API ready
2. ⏳ **Frontend cần implement**:
   - Message component cho plan_invitation type
   - Accept/Reject button handlers
   - WebSocket listener cho real-time notifications
   - Status checking logic
   - UI/UX cho invitation cards

## 🎉 Summary

Feature đã được implement đầy đủ ở backend với:

- ✅ 3 API endpoints
- ✅ Full validation & security
- ✅ Persistent state management
- ✅ WebSocket integration ready
- ✅ Complete documentation

**Status**: 🟢 Ready for frontend integration

---

**Date**: 2025-12-04  
**Backend**: Python 3.10.19, FastAPI  
**Database**: PostgreSQL with RoomContext storage
