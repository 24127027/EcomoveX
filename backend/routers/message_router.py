from typing import List
from fastapi import APIRouter, Depends, Path, Query, status, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from schemas.message_schema import MessageCreate, MessageResponse
from services.message_service import MessageService
from utils.token.authentication_util import get_current_user

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
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user_id = await MessageService.handle_websocket_connection(websocket, db, room_id, token)
    if user_id:
        await MessageService.handle_websocket_message_loop(websocket, db, user_id, room_id)