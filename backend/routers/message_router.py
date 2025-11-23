from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from schemas.message_schema import MessageCreate, MessageResponse
from services.message_service import MessageService
from utils.token.authentication_util import get_current_user
from utils.socket_manager import manager
from utils.token.authentication_util import decode_access_token

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.get("/search/keyword", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def search_messages_by_keyword(
    keyword: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await MessageService.get_message_by_keyword(db, current_user["user_id"], keyword)

@router.get("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def get_message_by_id(
    message_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await MessageService.get_message_by_id(db, current_user["user_id"], message_id)

@router.get("/room/{room_id}", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def get_messages_in_room(
    room_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await MessageService.get_messages_by_room(db, current_user["user_id"], room_id)

@router.post("/{room_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    room_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await MessageService.create_message(db, current_user["user_id"], room_id, message_data)

@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await MessageService.delete_message(db, current_user["user_id"], message_id)


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),  # Token gửi qua query param: ws://url?token=...
    db: AsyncSession = Depends(get_db)
):
    # 1. Xác thực thủ công (vì Socket không dùng Depends như HTTP thường)
    try:
        user_data = decode_access_token(token)
        user_id = user_data["user_id"]
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Kết nối
    await manager.connect(websocket, room_id)
    
    try:
        while True:
            # 3. Nhận tin từ Frontend
            data = await websocket.receive_json()
            content = data.get("content")
            
            if content:
                # 4. Lưu vào Database (Dùng Service có sẵn của bạn)
                # Tạo object đúng chuẩn schema MessageCreate của bạn
                msg_input = MessageCreate(content=content, message_type="text")
                saved_msg = await MessageService.create_message(db, user_id, room_id, msg_input)
                
                # 5. Gửi lại cho Frontend để hiển thị ngay lập tức
                if saved_msg:
                    response = {
                        "id": saved_msg.id,
                        "content": saved_msg.content,
                        "sender_id": saved_msg.sender_id,
                        "room_id": room_id,
                        "timestamp": saved_msg.timestamp.isoformat(), # convert datetime to string
                        "message_type": "text"
                    }
                    await manager.broadcast(response, room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)