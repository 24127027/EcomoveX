from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    UploadFile,
    WebSocket,
    status,
    Body,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.message import MessageType
from schemas.message_schema import (
    CommonMessageResponse,
    InvitationActionRequest,
    MessageResponse,
    PlanInvitationCreate,
)
from services.message_service import MessageService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get(
    "/search/keyword",
    response_model=List[MessageResponse],
    status_code=status.HTTP_200_OK,
)
async def search_messages_by_keyword(
    room_id: int = Query(..., gt=0),
    keyword: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await MessageService.get_message_by_keyword(
        db, current_user["user_id"], room_id, keyword
    )


@router.get(
    "/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def get_message_by_id(
    message_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await MessageService.get_message_by_id(
        db, current_user["user_id"], message_id
    )


@router.get(
    "/room/{room_id}",
    response_model=List[MessageResponse],
    status_code=status.HTTP_200_OK,
)
async def get_messages_in_room(
    room_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await MessageService.get_messages_by_room(
        db, current_user["user_id"], room_id
    )


@router.post(
    "/{room_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def send_message(
    room_id: int = Path(..., gt=0),
    content: Optional[str] = Form(None),
    message_file: Optional[UploadFile] = File(None),
    plan_id: Optional[int] = Form(None),
    message_type: MessageType = Form(MessageType.text),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await MessageService.create_message(
        db=db,
        sender_id=current_user["user_id"],
        room_id=room_id,
        message_text=content if content else None,
        message_file=message_file if message_file else None,
        plan_id=plan_id,
        message_type=message_type,
    )


@router.delete(
    "/{message_id}",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_message(
    message_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await MessageService.delete_message(db, current_user["user_id"], message_id)


@router.put(
    "/{message_id}/decline",
    status_code=status.HTTP_200_OK,
)
async def decline_plan_invitation(
    message_id: int = Path(..., gt=0, description="ID of the invitation message"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Decline a plan invitation.
    Shortcut endpoint for rejecting invitations.
    """
    return await MessageService.respond_to_invitation(
        db,
        user_id=current_user["user_id"],
        message_id=message_id,
        action="rejected",
    )


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user_id = await MessageService.handle_websocket_connection(
        websocket, db, room_id, token
    )
    if user_id:
        await MessageService.handle_websocket_message_loop(
            websocket, db, user_id, room_id
        )


# ======================== Plan Invitation Endpoints ========================


@router.post(
    "/invitations/send",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_plan_invitation(
    invitation_data: PlanInvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Gửi lời mời tham gia plan qua chat.
    
    - **room_id**: ID của room chat (phải là room với người được mời)
    - **plan_id**: ID của plan muốn mời
    - **invitee_id**: ID của người được mời
    - **message**: Tin nhắn kèm theo (optional)
    
    Chỉ owner của plan mới có thể gửi lời mời.
    """
    return await MessageService.send_plan_invitation(
        db,
        sender_id=current_user["user_id"],
        room_id=invitation_data.room_id,
        plan_id=invitation_data.plan_id,
        invitee_id=invitation_data.invitee_id,
        message=invitation_data.message,
    )


@router.post(
    "/invitations/{message_id}/respond",
    status_code=status.HTTP_200_OK,
)
async def respond_to_plan_invitation(
    message_id: int = Path(..., gt=0, description="ID của invitation message"),
    action_request: InvitationActionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept hoặc reject lời mời tham gia plan.
    
    - **message_id**: ID của message chứa lời mời
    - **action**: "accepted" hoặc "rejected"
    
    Chỉ người được mời mới có thể respond.
    Khi accept: Tự động thêm vào plan_members với role member.
    Khi reject: Lưu trạng thái để không hiển thị lại khi reload.
    """
    return await MessageService.respond_to_invitation(
        db,
        user_id=current_user["user_id"],
        message_id=message_id,
        action=action_request.action.value,
    )


@router.get(
    "/invitations/{message_id}",
    status_code=status.HTTP_200_OK,
)
async def get_invitation_details(
    message_id: int = Path(..., gt=0, description="ID của invitation message"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy chi tiết lời mời plan.
    
    Trả về thông tin plan, người gửi, trạng thái (pending/accepted/rejected).
    """
    return await MessageService.get_invitation_details(
        db, current_user["user_id"], message_id
    )

