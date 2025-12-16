from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from models.user import User
from repository.user_repository import UserRepository
from repository.cluster_repository import ClusterRepository
from schemas.authentication_schema import (
    AuthenticationResponse,
    UserLogin,
    UserRegister,
)
from schemas.user_schema import UserCredentialUpdate
from utils.config import settings
from utils.email.email_utils import send_email
from utils.token.authentication_util import (
    generate_temporary_password,
    generate_verification_token,
    verify_email_token,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    @staticmethod
    async def authenticate_user(db: AsyncSession, credentials: UserLogin):
        try:
            users = await UserRepository.search_users(db, credentials.email, limit=1)
            user = users[0] if users else None
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            if credentials.password != user.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error authenticating user: {e}",
            )

    @staticmethod
    def create_access_token(user: User) -> str:
        try:
            expiration = datetime.utcnow() + timedelta(days=7)
            
            payload = {
                "sub": str(user.id),
                "role": (
                    user.role.value if hasattr(user.role, "value") else str(user.role)
                ),
                "exp": expiration
            }
            token = jwt.encode(
                payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
            )
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating access token: {e}",
            )

    @staticmethod
    async def login_user(
        db: AsyncSession, email: str, password: str
    ) -> AuthenticationResponse:
        try:
            users = await UserRepository.search_users(db, email, limit=1)
            user = users[0] if users else None
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            if password != user.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            
            token = AuthenticationService.create_access_token(user)
            return AuthenticationResponse(
                user_id=user.id, role=user.role, access_token=token, token_type="bearer"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error logging in user: {e}",
            )

    @staticmethod
    async def register_user(
        db: AsyncSession, user_data: UserRegister
    ) -> bool:
        try:
            # Kiểm tra xem email đã tồn tại chưa
            existing_users = await UserRepository.search_users(db, user_data.email, limit=1)
            if existing_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            
            # Tạo verification token chứa thông tin đăng ký
            verification_token = generate_verification_token(
                email=user_data.email,
                username=user_data.username,
                password=user_data.password
            )
            
            # Gửi email xác nhận - link trỏ thẳng đến backend API
            verification_link = f"{settings.CORS_ORIGINS.split(',')[1]}/auth/verify-email?token={verification_token}"
            email_subject = "Verify Your Email - EcomoveX"
            email_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification - EcomoveX</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #1e293b;
            background: #f8fafc;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 640px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 40px;
            text-align: center;
        }}
        .logo {{
            font-size: 38px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        .tagline {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
        }}
        .content {{
            padding: 40px;
        }}
        .icon-wrapper {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .icon {{
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        }}
        .title {{
            color: #0f172a;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 16px;
            text-align: center;
        }}
        .message {{
            font-size: 15px;
            color: #64748b;
            margin-bottom: 28px;
            line-height: 1.7;
            text-align: center;
        }}
        .button-container {{
            text-align: center;
            margin: 40px 0;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #ffffff;
            padding: 16px 48px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.25);
        }}
        .info-box {{
            background: #f1f5f9;
            border-left: 4px solid #10b981;
            padding: 16px 20px;
            margin: 24px 0;
            border-radius: 8px;
            font-size: 14px;
            color: #475569;
        }}
        .footer {{
            background: #f8fafc;
            padding: 40px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        .footer-brand {{
            font-weight: 800;
            color: #0f172a;
            font-size: 18px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">EcomoveX</div>
            <div class="tagline">Your Trip. Your Impact. Your Choice.</div>
        </div>
        
        <div class="content">
            <div class="icon-wrapper">
                <div class="icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="white" viewBox="0 0 24 24">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                    </svg>
                </div>
            </div>
            
            <h1 class="title">Welcome to EcomoveX!</h1>
            
            <p class="message">
                Thank you for joining EcomoveX, where sustainable travel meets innovation. To get started, please verify your email address by clicking the button below.
            </p>
            
            <div class="button-container">
                <a href="{verification_link}" class="button">Verify Your Email</a>
            </div>
            
            <div class="info-box">
                <strong>Note:</strong> This verification link will expire in 24 hours for security purposes. If you didn't create an account with EcomoveX, please ignore this email.
            </div>
        </div>
        
        <div class="footer">
            <div class="footer-brand">EcomoveX</div>
            <p style="color: #64748b; font-size: 14px;">Making sustainable travel accessible to everyone</p>
            <p style="color: #94a3b8; font-size: 13px; margin-top: 20px;">© 2025 EcomoveX. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
            
            try:
                await send_email(user_data.email, email_subject, email_content, content_type="html")
            except Exception as email_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to send verification email: {email_error}"
                )
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error registering user: {e}",
            )
            
    @staticmethod
    async def reset_user_password(db: AsyncSession, email: str, user_name: str) -> str:
        try:
            user = await UserRepository.get_user_by_email(db, email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User with the provided email does not exist",
                )
            if user.username != user_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username does not match the provided email",
                )
            temp_password = generate_temporary_password()
            data = UserCredentialUpdate(
                old_password=user.password, new_password=temp_password
            )
            await UserRepository.update_user_credentials(db, user.id, data)
            
            email_subject = "Password Reset Confirmation - EcomoveX"
            email_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset - EcomoveX</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #1e293b;
            background: #f8fafc;
            padding: 40px 20px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        .email-wrapper {{
            max-width: 640px;
            margin: 0 auto;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #f1f5f9;
        }}
        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 40px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, transparent 70%);
            opacity: 0.5;
        }}
        .logo-container {{
            position: relative;
            z-index: 2;
        }}
        .logo {{
            font-size: 38px;
            font-weight: 700;
            color: #ffffff;
            font-style: normal;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            letter-spacing: -0.5px;
        }}
        .tagline {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            font-weight: 500;
            letter-spacing: 0.3px;
        }}
        .content {{
            padding: 40px 40px;
        }}
        .icon-wrapper {{
            text-align: center;
            margin-bottom: 24px;
        }}
        .icon {{
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        }}
        .icon svg {{
            width: 32px;
            height: 32px;
            fill: white;
        }}
        .title {{
            color: #0f172a;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 16px;
            text-align: center;
            line-height: 1.3;
            letter-spacing: -0.3px;
        }}
        .greeting {{
            font-size: 15px;
            color: #475569;
            margin-bottom: 20px;
            font-weight: 500;
        }}
        .greeting strong {{
            color: #0f172a;
            font-weight: 600;
        }}
        .message {{
            font-size: 15px;
            color: #64748b;
            margin-bottom: 28px;
            line-height: 1.7;
        }}
        .password-container {{
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid #10b981;
            border-radius: 12px;
            padding: 28px 24px;
            margin: 28px 0;
            text-align: center;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
        }}
        .password-label {{
            color: #047857;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 12px;
        }}
        .password-value {{
            font-size: 28px;
            font-weight: 700;
            color: #065f46;
            letter-spacing: 4px;
            font-family: 'Courier New', Consolas, Monaco, monospace;
            background: #ffffff;
            padding: 16px 24px;
            border-radius: 10px;
            display: inline-block;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
            user-select: all;
            border: 1px solid #d1fae5;
        }}
        .info-box {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 4px solid #f59e0b;
            padding: 18px 20px;
            margin: 24px 0;
            border-radius: 8px;
            font-size: 14px;
            color: #92400e;
            line-height: 1.6;
            box-shadow: 0 1px 4px rgba(245, 158, 11, 0.1);
        }}
        .info-box strong {{
            color: #78350f;
            font-weight: 600;
            display: block;
            margin-bottom: 6px;
            font-size: 14px;
        }}
        .info-icon {{
            display: inline-block;
            width: 20px;
            height: 20px;
            background: #f59e0b;
            border-radius: 50%;
            margin-right: 10px;
            vertical-align: middle;
            position: relative;
        }}
        .info-icon::before {{
            content: '!';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-weight: 800;
            font-size: 14px;
        }}
        .button-container {{
            text-align: center;
            margin: 40px 0;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #ffffff;
            padding: 14px 40px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.25);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: 0.2px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .security-tips {{
            background: #f8fafc;
            border-radius: 10px;
            padding: 24px;
            margin: 28px 0;
            border: 1px solid #e2e8f0;
        }}
        .security-tips h3 {{
            color: #0f172a;
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 16px;
            letter-spacing: -0.2px;
        }}
        .security-tips h3::before {{
            content: '';
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #10b981;
            border-radius: 50%;
            margin-right: 12px;
            vertical-align: middle;
        }}
        .security-tips ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .security-tips li {{
            padding: 8px 0;
            color: #475569;
            font-size: 14px;
            display: flex;
            align-items: flex-start;
            line-height: 1.5;
        }}
        .security-tips li::before {{
            content: '✓';
            color: #10b981;
            font-weight: 700;
            margin-right: 10px;
            font-size: 14px;
            flex-shrink: 0;
        }}
        .divider {{
            height: 1px;
            background: linear-gradient(to right, transparent, #e2e8f0, transparent);
            margin: 40px 0;
        }}
        .help-text {{
            font-size: 15px;
            color: #64748b;
            text-align: center;
            line-height: 1.7;
        }}
        .help-link {{
            color: #10b981;
            text-decoration: none;
            font-weight: 700;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
        }}
        .help-link:hover {{
            border-bottom-color: #10b981;
        }}
        .footer {{
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 48px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        .footer-brand {{
            font-weight: 800;
            color: #0f172a;
            font-size: 18px;
            margin-bottom: 10px;
            letter-spacing: -0.3px;
        }}
        .footer-tagline {{
            color: #64748b;
            font-size: 15px;
            margin-bottom: 24px;
            font-weight: 500;
        }}
        .footer-links {{
            margin: 24px 0;
        }}
        .footer-links a {{
            color: #10b981;
            text-decoration: none;
            margin: 0 16px;
            font-size: 14px;
            font-weight: 600;
            transition: color 0.2s;
        }}
        .footer-links a:hover {{
            color: #059669;
        }}
        .footer-disclaimer {{
            color: #94a3b8;
            font-size: 13px;
            margin-top: 24px;
            line-height: 1.7;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 20px 10px;
            }}
            .content {{
                padding: 40px 28px;
            }}
            .header {{
                padding: 48px 28px;
            }}
            .title {{
                font-size: 26px;
            }}
            .logo {{
                font-size: 44px;
            }}
            .password-value {{
                font-size: 28px;
                letter-spacing: 3px;
                padding: 16px 20px;
            }}
            .button {{
                padding: 16px 40px;
                font-size: 16px;
            }}
            .security-tips {{
                padding: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="container">
            <div class="header">
                <div class="logo-container">
                    <div class="logo">EcomoveX</div>
                    <div class="tagline">Your Trip. Your Impact. Your Choice.</div>
                </div>
            </div>
            
            <div class="content">
                <div class="icon-wrapper">
                    <div class="icon">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                </div>
                
                <h1 class="title">Account Security Notification</h1>
                
                <p class="greeting">Dear <strong>{user.name if hasattr(user, 'name') else 'Valued User'}</strong>,</p>
                
                <p class="message">
                    This email confirms that your account password has been successfully reset. Please find your temporary access credentials below. We recommend changing this password immediately upon your next login.
                </p>
                
                <div class="password-container">
                    <div class="password-label">Temporary Access Password</div>
                    <div class="password-value">{temp_password}</div>
                </div>
                
                <div class="info-box">
                    <strong><span class="info-icon"></span>Security Advisory</strong>
                    For optimal account security, we strongly recommend updating this temporary password immediately after logging in. Please ensure you do not share this information with anyone.
                </div>
                
                <div class="button-container">
                    <a href="{settings.CORS_ORIGINS.split(',')[0]}/login" class="button">Access Your Account</a>
                </div>
                
                <div class="security-tips">
                    <h3>Security Best Practices</h3>
                    <ul>
                        <li>Update your password within 24 hours of receipt</li>
                        <li>Create a strong, unique password combining letters, numbers, and symbols</li>
                        <li>Enable multi-factor authentication for enhanced security</li>
                        <li>Never share your password through email or messaging platforms</li>
                    </ul>
                </div>
                
                <div class="divider"></div>
                
                <p class="help-text">
                    If you did not initiate this password reset request, please contact our support team immediately at<br>
                    <a href="mailto:{settings.SMTP_USER}" class="help-link">{settings.SMTP_USER}</a>
                </p>
            </div>
            
            <div class="footer">
                <div class="footer-brand">EcomoveX</div>
                <div class="footer-tagline">Making sustainable travel accessible to everyone</div>
                
                <div class="footer-links">
                    <a href="#">Help Center</a>
                    <a href="#">Privacy Policy</a>
                    <a href="#">Terms of Service</a>
                </div>
                
                <div class="footer-disclaimer">
                    This is an automated email from EcomoveX. Please do not reply to this message.<br>
                    © 2025 EcomoveX. All rights reserved.
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
            
            try:
                await send_email(email, email_subject, email_content, content_type="html")
            except Exception as email_error:
                print(f"[WARNING] Password reset successful but email failed: {email_error}")
            
            return temp_password
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resetting user password: {e}",
            )
    
    @staticmethod
    async def verify_user_email(db: AsyncSession, token: str) -> dict:
        try:
            # Giải mã token để lấy thông tin đăng ký
            user_data = verify_email_token(token)
            
            # Kiểm tra xem email đã tồn tại chưa (trường hợp verify 2 lần)
            existing_users = await UserRepository.search_users(db, user_data["email"], limit=1)
            if existing_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already verified and registered",
                )
            
            # Tạo user mới từ thông tin trong token
            from schemas.authentication_schema import UserRegister
            register_data = UserRegister(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"]
            )
            
            new_user = await UserRepository.create_user(db, register_data)
            if not new_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user account",
                )
                            
            await ClusterRepository.create_preference(db, user_id=new_user.id)
            
            # Tạo access token để user có thể login ngay
            access_token = AuthenticationService.create_access_token(new_user)
            
            return {
                "message": "Email verified successfully! Your account has been created.",
                "user_id": new_user.id,
                "role": new_user.role,
                "access_token": access_token,
                "token_type": "bearer"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying email: {e}",
            )