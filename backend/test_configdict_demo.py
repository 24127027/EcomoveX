"""
Demo để giải thích tại sao cần ConfigDict(from_attributes=True)
"""
from pydantic import BaseModel, ConfigDict

# Giả lập SQLAlchemy model (ORM object)
class UserModel:
    """Đây là object từ database (SQLAlchemy)"""
    def __init__(self):
        self.id = 1
        self.username = "testuser"
        self.email = "test@example.com"
        self.eco_point = 100
        self.rank = "Bronze"


# ===== TH1: Schema KHÔNG có ConfigDict =====
class UserResponseWithoutConfig(BaseModel):
    id: int
    username: str
    email: str
    eco_point: int
    rank: str
    # KHÔNG có: model_config = ConfigDict(from_attributes=True)


# ===== TH2: Schema CÓ ConfigDict =====
class UserResponseWithConfig(BaseModel):
    id: int
    username: str
    email: str
    eco_point: int
    rank: str
    
    model_config = ConfigDict(from_attributes=True)


if __name__ == "__main__":
    # Lấy user từ database (giả lập)
    user_from_db = UserModel()
    
    print("=" * 60)
    print("DEMO: Tại sao cần ConfigDict(from_attributes=True)")
    print("=" * 60)
    
    # --- Test 1: Schema KHÔNG có ConfigDict ---
    print("\n1️⃣ TRƯỜNG HỢP KHÔNG CÓ ConfigDict:")
    print("-" * 60)
    try:
        # Cố gắng convert ORM object -> Pydantic schema
        response = UserResponseWithoutConfig(**user_from_db.__dict__)
        print("✅ Thành công (nhưng phải dùng __dict__):")
        print(f"   {response}")
    except Exception as e:
        print(f"❌ Lỗi khi convert trực tiếp:")
        print(f"   {type(e).__name__}: {e}")
    
    try:
        # Thử convert trực tiếp (KHÔNG dùng __dict__)
        response = UserResponseWithoutConfig(user_from_db)
        print("✅ Thành công convert trực tiếp")
    except Exception as e:
        print(f"❌ Lỗi khi convert trực tiếp ORM object:")
        print(f"   {type(e).__name__}: {e}")
    
    
    # --- Test 2: Schema CÓ ConfigDict ---
    print("\n2️⃣ TRƯỜNG HỢP CÓ ConfigDict(from_attributes=True):")
    print("-" * 60)
    try:
        # Convert trực tiếp ORM object -> Pydantic schema
        response = UserResponseWithConfig.model_validate(user_from_db)
        print("✅ Thành công convert trực tiếp:")
        print(f"   {response}")
        print(f"   Type: {type(response)}")
    except Exception as e:
        print(f"❌ Lỗi: {type(e).__name__}: {e}")
    
    
    # --- Kết luận ---
    print("\n" + "=" * 60)
    print("📊 KẾT LUẬN:")
    print("=" * 60)
    print("""
    KHÔNG CÓ ConfigDict:
    ❌ Phải dùng: UserResponse(**user.__dict__)
    ❌ FastAPI không thể tự động convert ORM -> Response
    ❌ Code phức tạp hơn, dễ lỗi
    
    CÓ ConfigDict(from_attributes=True):
    ✅ Chỉ cần: return user (FastAPI tự convert)
    ✅ Pydantic tự động đọc attributes từ ORM object
    ✅ Code clean, đơn giản, ít lỗi
    ✅ FastAPI response_model hoạt động hoàn hảo
    
    ⚠️  ConfigDict CHỈ CẦN cho Response schemas
        (schemas được dùng làm response_model trong router)
    ⚠️  KHÔNG CẦN cho Create/Update schemas  
        (schemas nhận data từ request body)
    """)
