from fastapi import APIRouter, HTTPException
from services.forgetpassword_service import ForgetPasswordService
from pydantic import BaseModel, EmailStr

router = APIRouter(
    prefix="/forgetpassword",
    tags=["ForgetPassword"]
)

class ForgetPasswordRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str


@router.post("/")
async def forget_password(request: ForgetPasswordRequest):
    try:
        message = await ForgetPasswordService.send_temp_password(request.email)
        return {"message": message}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
@router.post("/changepassword/")
async def change_password(request: ChangePasswordRequest):
    try:
        message = await ForgetPasswordService.change_password_by_email(
            email=request.email,
            current_password=request.current_password,
            new_password=request.new_password
        )
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


