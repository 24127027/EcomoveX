from sqlalchemy.ext.asyncio import AsyncSession
from database.db import UserAsyncSessionLocal
from repository.user_repository import UserRepository
from utils.email_utils import send_email
import random
import string

class ForgetPasswordService:

    @staticmethod
    async def change_password_by_email(email: str, current_password: str, new_password: str):
        async with UserAsyncSessionLocal() as session:
            user = await UserRepository.get_user_by_email(session, email)
            if not user:
                raise Exception("Email not registered")

            updated = await UserRepository.update_password_by_user(
                session,
                user.id,
                current_password,
                new_password
            )
            if not updated:
                raise Exception("Current password incorrect or update failed")

            return "Password changed successfully."

    async def send_temp_password(email: str):
        async with UserAsyncSessionLocal() as session:
            user = await UserRepository.get_user_by_email(session, email)
            if not user:
                raise Exception("This email is not registered!")

            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            updated = await UserRepository.admin_update_password(session, user.id, new_password)
            if not updated:
                raise Exception("Failed to update password!")

            subject = "Your new password from EcomoveX"
            content = f"Your new password is: {new_password}"
            await send_email(email, subject, content)
            return "Your new password has been sent to your email."
