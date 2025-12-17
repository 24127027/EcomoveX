from sqlalchemy.ext.asyncio import AsyncSession
from models.user import Rank, Activity
from repository.user_repository import UserRepository
from repository.cluster_repository import ClusterRepository
from schemas.authentication_schema import UserRegister
from schemas.cluster_schema import PreferenceUpdate
from schemas.destination_schema import DestinationCreate
from schemas.map_schema import AutocompleteRequest
from schemas.user_schema import UserActivityCreate, UserFilterParams
from services.destination_service import DestinationService
from services.map_service import MapService
from services.user_service import UserService
from services.cluster_service import ClusterService
import random


# Sample users data (59 users with diverse preferences)
SAMPLE_USERS = [
    # Nhóm 1: Du lịch gia đình, thích thời tiết ấm áp
    {
        "username": "NguyenVanAn",
        "email": "nguyenvanan@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 22, "max_temp": 32},
            "attraction_types": ["beach", "park", "zoo", "museum"],
            "budget_range": {"min": 500, "max": 2000},
            "kids_friendly": True,
            "visited_destinations": ["Da Nang", "Nha Trang", "Phu Quoc"],
        },
    },
    {
        "username": "TranThiBich",
        "email": "tranthibich@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 30},
            "attraction_types": ["beach", "resort", "water_park", "aquarium"],
            "budget_range": {"min": 800, "max": 3000},
            "kids_friendly": True,
            "visited_destinations": ["Vung Tau", "Con Dao", "Quy Nhon"],
        },
    },

    # Nhóm 2: Phượt thủ, thích mạo hiểm
    {
        "username": "LeHoangPhong",
        "email": "lehoangphong@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 15, "max_temp": 25},
            "attraction_types": ["mountain", "hiking", "camping", "waterfall"],
            "budget_range": {"min": 200, "max": 800},
            "kids_friendly": False,
            "visited_destinations": ["Sapa", "Ha Giang", "Fansipan", "Ta Xua"],
        },
    },
    {
        "username": "PhamMinhTuan",
        "email": "phamminhtuan@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 10, "max_temp": 22},
            "attraction_types": ["mountain", "trekking", "cave", "forest"],
            "budget_range": {"min": 150, "max": 600},
            "kids_friendly": False,
            "visited_destinations": ["Moc Chau", "Mai Chau", "Pu Luong", "Cao Bang"],
        },
    },
    {
        "username": "VoThanhHai",
        "email": "vothanhhai@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 12, "max_temp": 24},
            "attraction_types": ["mountain", "off_road", "camping", "adventure"],
            "budget_range": {"min": 300, "max": 1000},
            "kids_friendly": False,
            "visited_destinations": ["Ha Giang", "Dong Van", "Ban Gioc", "Lung Cu"],
        },
    },

    # Nhóm 3: Du lịch văn hóa, lịch sử
    {
        "username": "DoThiHuong",
        "email": "dothihuong@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 28},
            "attraction_types": ["museum", "temple", "historical_site", "palace"],
            "budget_range": {"min": 400, "max": 1500},
            "kids_friendly": True,
            "visited_destinations": ["Hue", "Hoi An", "Hanoi Old Quarter"],
        },
    },
    {
        "username": "NguyenDucThanh",
        "email": "nguyenducthanh@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 30},
            "attraction_types": ["temple", "pagoda", "historical_site", "village"],
            "budget_range": {"min": 300, "max": 1200},
            "kids_friendly": True,
            "visited_destinations": ["Ninh Binh", "Trang An", "Bai Dinh", "Hue"],
        },
    },

    # Nhóm 4: Du lịch nghỉ dưỡng cao cấp
    {
        "username": "HoangThiMai",
        "email": "hoangthimai@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 24, "max_temp": 32},
            "attraction_types": ["resort", "spa", "beach", "golf"],
            "budget_range": {"min": 2000, "max": 10000},
            "kids_friendly": False,
            "visited_destinations": ["Phu Quoc", "Da Nang", "Nha Trang", "Maldives"],
        },
    },
    {
        "username": "TranVanDuc",
        "email": "tranvanduc@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 22, "max_temp": 30},
            "attraction_types": ["resort", "fine_dining", "yacht", "private_beach"],
            "budget_range": {"min": 3000, "max": 15000},
            "kids_friendly": False,
            "visited_destinations": ["Con Dao", "Six Senses", "Amanoi", "Singapore"],
        },
    },

    # Nhóm 5: Du lịch ẩm thực
    {
        "username": "LeThiNgoc",
        "email": "lethingoc@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 30},
            "attraction_types": ["food_tour", "street_food", "market", "cooking_class"],
            "budget_range": {"min": 300, "max": 1000},
            "kids_friendly": True,
            "visited_destinations": ["Saigon", "Hanoi", "Hue", "Hoi An"],
        },
    },
    {
        "username": "PhamHongSon",
        "email": "phamhongson@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 32},
            "attraction_types": ["local_restaurant", "food_market", "brewery", "cafe"],
            "budget_range": {"min": 400, "max": 1500},
            "kids_friendly": True,
            "visited_destinations": ["Da Lat", "Can Tho", "Phu Quoc"],
        },
    },

    # Nhóm 6: Du lịch sinh thái, xanh
    {
        "username": "NguyenThiLan",
        "email": "nguyenthilan@gmail.com",
        "password": "password123",
        "rank": Rank.diamond,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 28},
            "attraction_types": ["eco_resort", "national_park", "bird_watching", "organic_farm"],
            "budget_range": {"min": 500, "max": 2000},
            "kids_friendly": True,
            "visited_destinations": ["Cat Tien", "Cuc Phuong", "U Minh", "Tram Chim"],
        },
    },
    {
        "username": "VuVanKhanh",
        "email": "vuvankhanh@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 16, "max_temp": 26},
            "attraction_types": ["wildlife", "forest", "river", "sustainable_tourism"],
            "budget_range": {"min": 400, "max": 1800},
            "kids_friendly": False,
            "visited_destinations": ["Phong Nha", "Ba Be", "Cat Ba", "Con Dao"],
        },
    },

    # Nhóm 7: Du lịch đô thị, mua sắm
    {
        "username": "TranThiHong",
        "email": "tranthihong@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 22, "max_temp": 32},
            "attraction_types": ["shopping_mall", "night_market", "entertainment", "club"],
            "budget_range": {"min": 600, "max": 3000},
            "kids_friendly": False,
            "visited_destinations": ["Ho Chi Minh City", "Bangkok", "Singapore", "Hong Kong"],
        },
    },
    {
        "username": "LeVanHung",
        "email": "levanhung@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 30},
            "attraction_types": ["landmark", "rooftop_bar", "shopping", "art_gallery"],
            "budget_range": {"min": 800, "max": 4000},
            "kids_friendly": False,
            "visited_destinations": ["Hanoi", "Da Nang", "Tokyo", "Seoul"],
        },
    },

    # Nhóm 8: Du lịch biển đảo
    {
        "username": "PhanThiMy",
        "email": "phanthimy@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 26, "max_temp": 34},
            "attraction_types": ["island", "snorkeling", "diving", "beach"],
            "budget_range": {"min": 700, "max": 2500},
            "kids_friendly": False,
            "visited_destinations": ["Phu Quoc", "Con Dao", "Ly Son", "Cu Lao Cham"],
        },
    },
    {
        "username": "NguyenHoangNam",
        "email": "nguyenhoangnam@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 25, "max_temp": 33},
            "attraction_types": ["beach", "surfing", "kayaking", "coral_reef"],
            "budget_range": {"min": 600, "max": 2200},
            "kids_friendly": True,
            "visited_destinations": ["Nha Trang", "Quy Nhon", "Mui Ne", "Da Nang"],
        },
    },

    # Nhóm 9: Du lịch Tây Nguyên
    {
        "username": "BuiThiHoa",
        "email": "buithihoa@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 15, "max_temp": 25},
            "attraction_types": ["coffee_plantation", "waterfall", "ethnic_village", "highland"],
            "budget_range": {"min": 250, "max": 900},
            "kids_friendly": True,
            "visited_destinations": ["Da Lat", "Buon Ma Thuot", "Pleiku", "Kon Tum"],
        },
    },
    {
        "username": "DangVanTien",
        "email": "dangvantien@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 14, "max_temp": 24},
            "attraction_types": ["flower_garden", "lake", "pine_forest", "valley"],
            "budget_range": {"min": 300, "max": 1100},
            "kids_friendly": True,
            "visited_destinations": ["Da Lat", "Lang Biang", "Valley of Love", "Xuan Huong Lake"],
        },
    },

    # Nhóm 10: Du lịch miền Tây sông nước
    {
        "username": "NguyenThiTuyet",
        "email": "nguyenthituyet@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 24, "max_temp": 34},
            "attraction_types": ["floating_market", "river_cruise", "fruit_garden", "homestay"],
            "budget_range": {"min": 200, "max": 700},
            "kids_friendly": True,
            "visited_destinations": ["Can Tho", "Ben Tre", "An Giang", "Vinh Long"],
        },
    },
    {
        "username": "TranVanLong",
        "email": "tranvanlong@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 25, "max_temp": 35},
            "attraction_types": ["mekong_delta", "mangrove", "local_craft", "rural_life"],
            "budget_range": {"min": 180, "max": 650},
            "kids_friendly": True,
            "visited_destinations": ["Soc Trang", "Tra Vinh", "Ca Mau", "Chau Doc"],
        },
    },

    # Nhóm 11: Sinh viên tiết kiệm
    {
        "username": "HoangMinh",
        "email": "hoangminh.student@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 30},
            "attraction_types": ["backpacking", "hostel", "street_food", "free_attraction"],
            "budget_range": {"min": 50, "max": 300},
            "kids_friendly": False,
            "visited_destinations": ["Hoi An", "Da Nang", "Ninh Binh"],
        },
    },
    {
        "username": "LeThuHa",
        "email": "lethuha.student@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 32},
            "attraction_types": ["budget_travel", "camping", "public_beach", "hiking"],
            "budget_range": {"min": 80, "max": 400},
            "kids_friendly": False,
            "visited_destinations": ["Vung Tau", "Da Lat", "Sapa"],
        },
    },

    # Nhóm 12: Du lịch tâm linh
    {
        "username": "PhamThiTam",
        "email": "phamthitam@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 28},
            "attraction_types": ["pagoda", "temple", "meditation", "pilgrimage"],
            "budget_range": {"min": 300, "max": 1200},
            "kids_friendly": True,
            "visited_destinations": ["Yen Tu", "Bai Dinh", "Huong Pagoda", "My Son"],
        },
    },
    {
        "username": "NguyenVanDat",
        "email": "nguyenvandat@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 16, "max_temp": 26},
            "attraction_types": ["buddhist_temple", "retreat", "spiritual_site", "monastery"],
            "budget_range": {"min": 250, "max": 1000},
            "kids_friendly": True,
            "visited_destinations": ["Linh Ung", "Thien Mu", "Vinh Nghiem", "Truc Lam"],
        },
    },

    # Nhóm 13: Thêm nhiều gia đình trẻ em
    {
        "username": "VuThiLien",
        "email": "vuthilien@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 22, "max_temp": 30},
            "attraction_types": ["theme_park", "water_park", "zoo", "children_museum"],
            "budget_range": {"min": 600, "max": 2500},
            "kids_friendly": True,
            "visited_destinations": ["Vinpearl", "Dam Sen", "Suoi Tien"],
        },
    },
    {
        "username": "NguyenQuocTuan",
        "email": "nguyenquoctuan@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 32},
            "attraction_types": ["amusement_park", "beach", "aquarium", "play_area"],
            "budget_range": {"min": 500, "max": 2000},
            "kids_friendly": True,
            "visited_destinations": ["Ba Na Hills", "Sun World", "Asia Park"],
        },
    },
    {
        "username": "DaoThiHang",
        "email": "daothihang@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 23, "max_temp": 31},
            "attraction_types": ["family_resort", "kids_club", "pool", "playground"],
            "budget_range": {"min": 700, "max": 3000},
            "kids_friendly": True,
            "visited_destinations": ["Nha Trang", "Phan Thiet", "Vung Tau"],
        },
    },

    # Nhóm 14: Thêm nhiều phượt thủ
    {
        "username": "TranMinhTri",
        "email": "tranminhtri@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 10, "max_temp": 20},
            "attraction_types": ["mountain", "trekking", "camping", "backpacking"],
            "budget_range": {"min": 100, "max": 500},
            "kids_friendly": False,
            "visited_destinations": ["Ha Giang Loop", "Phong Nha", "Pu Luong"],
        },
    },
    {
        "username": "LeVanHieu",
        "email": "levanhieu@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 8, "max_temp": 22},
            "attraction_types": ["off_road", "motorbike", "adventure", "wild_camping"],
            "budget_range": {"min": 150, "max": 700},
            "kids_friendly": False,
            "visited_destinations": ["Cao Bang", "Bac Ha", "Mu Cang Chai"],
        },
    },
    {
        "username": "PhamThiNgoc",
        "email": "phamthingoc@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 12, "max_temp": 24},
            "attraction_types": ["hiking", "nature", "waterfall", "cave"],
            "budget_range": {"min": 200, "max": 800},
            "kids_friendly": False,
            "visited_destinations": ["Son Doong", "Hang En", "Tu Lan Cave"],
        },
    },
    {
        "username": "BuiVanNam",
        "email": "buivannam@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 14, "max_temp": 26},
            "attraction_types": ["trekking", "ethnic_village", "homestay", "highland"],
            "budget_range": {"min": 180, "max": 650},
            "kids_friendly": False,
            "visited_destinations": ["Ta Xua", "Y Ty", "Hoang Su Phi"],
        },
    },

    # Nhóm 15: Thêm nhiều người thích biển
    {
        "username": "NguyenThiHuyen",
        "email": "nguyenthihuyen@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 26, "max_temp": 34},
            "attraction_types": ["beach", "swimming", "sunbathing", "seafood"],
            "budget_range": {"min": 400, "max": 1500},
            "kids_friendly": True,
            "visited_destinations": ["Nha Trang", "Mui Ne", "Vung Tau", "Phu Quoc"],
        },
    },
    {
        "username": "TranVanHai",
        "email": "tranvanhai@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 27, "max_temp": 35},
            "attraction_types": ["island", "diving", "snorkeling", "boat_tour"],
            "budget_range": {"min": 700, "max": 2800},
            "kids_friendly": False,
            "visited_destinations": ["Con Dao", "Cu Lao Cham", "Ly Son", "Whale Island"],
        },
    },
    {
        "username": "LeThiAnh",
        "email": "lethianh@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 25, "max_temp": 33},
            "attraction_types": ["beach", "resort", "spa", "seafood_restaurant"],
            "budget_range": {"min": 800, "max": 3500},
            "kids_friendly": True,
            "visited_destinations": ["Da Nang", "Hoi An Beach", "Quy Nhon"],
        },
    },
    {
        "username": "HoangVanTung",
        "email": "hoangvantung@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 24, "max_temp": 32},
            "attraction_types": ["beach", "water_sports", "jet_ski", "parasailing"],
            "budget_range": {"min": 600, "max": 2200},
            "kids_friendly": False,
            "visited_destinations": ["Mui Ne", "Nha Trang", "Phu Quoc"],
        },
    },

    # Nhóm 16: Thêm nhiều du lịch văn hóa
    {
        "username": "PhamThiThao",
        "email": "phamthithao@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 28},
            "attraction_types": ["museum", "art_gallery", "theater", "concert"],
            "budget_range": {"min": 400, "max": 1600},
            "kids_friendly": True,
            "visited_destinations": ["Hanoi", "Hue", "Saigon", "Hoi An"],
        },
    },
    {
        "username": "NguyenDucMinh",
        "email": "nguyenducminh@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 30},
            "attraction_types": ["historical_site", "ancient_town", "architecture", "heritage"],
            "budget_range": {"min": 350, "max": 1400},
            "kids_friendly": True,
            "visited_destinations": ["Hue Imperial City", "My Son", "Hoi An Old Town"],
        },
    },
    {
        "username": "VuThiHien",
        "email": "vuthihien@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 19, "max_temp": 29},
            "attraction_types": ["temple", "pagoda", "cultural_show", "traditional_craft"],
            "budget_range": {"min": 300, "max": 1100},
            "kids_friendly": True,
            "visited_destinations": ["Hoi An", "Hanoi Old Quarter", "Can Tho"],
        },
    },

    # Nhóm 17: Thêm nhiều người thích ẩm thực
    {
        "username": "TranVanQuang",
        "email": "tranvanquang@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 32},
            "attraction_types": ["food_tour", "cooking_class", "street_food", "local_market"],
            "budget_range": {"min": 300, "max": 1200},
            "kids_friendly": True,
            "visited_destinations": ["Hanoi", "Saigon", "Hoi An", "Hue"],
        },
    },
    {
        "username": "LeThiQuyen",
        "email": "lethiquyen@gmail.com",
        "password": "password123",
        "rank": Rank.silver,
        "preference": {
            "weather_pref": {"min_temp": 22, "max_temp": 33},
            "attraction_types": ["restaurant", "cafe", "bakery", "dessert"],
            "budget_range": {"min": 400, "max": 1500},
            "kids_friendly": True,
            "visited_destinations": ["Da Lat", "Saigon", "Hanoi"],
        },
    },
    {
        "username": "NguyenVanThanh",
        "email": "nguyenvanthanh@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 30},
            "attraction_types": ["fine_dining", "wine_tasting", "gourmet", "michelin"],
            "budget_range": {"min": 1000, "max": 5000},
            "kids_friendly": False,
            "visited_destinations": ["Saigon", "Hanoi", "Da Nang"],
        },
    },

    # Nhóm 18: Thêm nhiều người thích nghỉ dưỡng
    {
        "username": "PhamThiLan",
        "email": "phamthilan@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 24, "max_temp": 32},
            "attraction_types": ["resort", "spa", "wellness", "yoga"],
            "budget_range": {"min": 1500, "max": 8000},
            "kids_friendly": False,
            "visited_destinations": ["Phu Quoc", "Nha Trang", "Da Nang", "Hoi An"],
        },
    },
    {
        "username": "HoangVanDung",
        "email": "hoangvandung@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 22, "max_temp": 30},
            "attraction_types": ["luxury_resort", "private_villa", "butler_service", "golf"],
            "budget_range": {"min": 3000, "max": 20000},
            "kids_friendly": False,
            "visited_destinations": ["Six Senses", "Four Seasons", "Amanoi"],
        },
    },
    {
        "username": "NguyenThiNhu",
        "email": "nguyenthinhu@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 23, "max_temp": 31},
            "attraction_types": ["boutique_hotel", "spa", "massage", "hot_spring"],
            "budget_range": {"min": 1200, "max": 6000},
            "kids_friendly": False,
            "visited_destinations": ["Da Lat", "Ninh Binh", "Mai Chau"],
        },
    },

    # Nhóm 19: Thêm nhiều sinh viên budget thấp
    {
        "username": "TranThiHuong",
        "email": "tranthihuong.sv@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 32},
            "attraction_types": ["backpacking", "hostel", "street_food", "public_transport"],
            "budget_range": {"min": 50, "max": 350},
            "kids_friendly": False,
            "visited_destinations": ["Hanoi", "Da Nang", "Hoi An"],
        },
    },
    {
        "username": "LeVanHung2",
        "email": "levanhung2.sv@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 30},
            "attraction_types": ["budget_travel", "camping", "hitchhiking", "free_walking_tour"],
            "budget_range": {"min": 60, "max": 400},
            "kids_friendly": False,
            "visited_destinations": ["Sapa", "Ninh Binh", "Ha Long"],
        },
    },
    {
        "username": "PhamMinhAnh",
        "email": "phamminhanh.sv@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 19, "max_temp": 31},
            "attraction_types": ["dorm", "local_bus", "street_market", "budget_food"],
            "budget_range": {"min": 40, "max": 300},
            "kids_friendly": False,
            "visited_destinations": ["Da Lat", "Nha Trang", "Mui Ne"],
        },
    },
    {
        "username": "NguyenThiThuy",
        "email": "nguyenthithuy.sv@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 21, "max_temp": 33},
            "attraction_types": ["youth_hostel", "motorbike_rental", "local_food", "free_beach"],
            "budget_range": {"min": 70, "max": 450},
            "kids_friendly": False,
            "visited_destinations": ["Quy Nhon", "Phu Yen", "Vung Tau"],
        },
    },
    {
        "username": "VuVanLong",
        "email": "vuvanlong.sv@gmail.com",
        "password": "password123",
        "rank": Rank.bronze,
        "preference": {
            "weather_pref": {"min_temp": 17, "max_temp": 29},
            "attraction_types": ["couchsurfing", "camping", "hitchhike", "volunteer"],
            "budget_range": {"min": 30, "max": 250},
            "kids_friendly": False,
            "visited_destinations": ["Ha Giang", "Cao Bang", "Lang Son"],
        },
    },

    # Nhóm 20: Thêm nhiều người cao tuổi ưa thư giãn
    {
        "username": "NguyenVanBinh",
        "email": "nguyenvanbinh@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 20, "max_temp": 28},
            "attraction_types": ["garden", "park", "lake", "temple"],
            "budget_range": {"min": 500, "max": 2000},
            "kids_friendly": True,
            "visited_destinations": ["Da Lat", "Hue", "Hanoi"],
        },
    },
    {
        "username": "TranThiNgoc",
        "email": "tranthingoc@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 19, "max_temp": 27},
            "attraction_types": ["pagoda", "peaceful_resort", "hot_spring", "massage"],
            "budget_range": {"min": 600, "max": 2500},
            "kids_friendly": True,
            "visited_destinations": ["Ninh Binh", "Tam Dao", "Ba Vi"],
        },
    },
    {
        "username": "LeVanChien",
        "email": "levanchien@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 26},
            "attraction_types": ["historical_site", "slow_travel", "scenic_view", "tea_house"],
            "budget_range": {"min": 450, "max": 1800},
            "kids_friendly": True,
            "visited_destinations": ["Hue", "Hoi An", "Da Lat"],
        },
    },

    # Nhóm 21: Thêm nhiều người thích hoạt động ngoài trời
    {
        "username": "PhamVanDat",
        "email": "phamvandat@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 15, "max_temp": 25},
            "attraction_types": ["cycling", "kayaking", "rock_climbing", "zip_line"],
            "budget_range": {"min": 300, "max": 1200},
            "kids_friendly": False,
            "visited_destinations": ["Ninh Binh", "Phong Nha", "Da Lat"],
        },
    },
    {
        "username": "NguyenThiLinh",
        "email": "nguyenthilinh@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 16, "max_temp": 26},
            "attraction_types": ["trekking", "mountain_biking", "rafting", "canyoning"],
            "budget_range": {"min": 350, "max": 1400},
            "kids_friendly": False,
            "visited_destinations": ["Sapa", "Ha Giang", "Mai Chau"],
        },
    },
    {
        "username": "HoangVanThang",
        "email": "hoangvanthang@gmail.com",
        "password": "password123",
        "rank": Rank.platinum,
        "preference": {
            "weather_pref": {"min_temp": 14, "max_temp": 24},
            "attraction_types": ["paragliding", "bungee_jump", "skydiving", "extreme_sports"],
            "budget_range": {"min": 500, "max": 2000},
            "kids_friendly": False,
            "visited_destinations": ["Mui Ne", "Da Lat", "Nha Trang"],
        },
    },

    # Nhóm 22: Thêm nhiều người thích nhiếp ảnh
    {
        "username": "TranVanQuyet",
        "email": "tranvanquyet@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 10, "max_temp": 25},
            "attraction_types": ["scenic_view", "sunrise", "sunset", "landscape"],
            "budget_range": {"min": 300, "max": 1500},
            "kids_friendly": False,
            "visited_destinations": ["Ha Giang", "Sapa", "Moc Chau", "Mu Cang Chai"],
        },
    },
    {
        "username": "LeThiThao",
        "email": "lethithao@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 18, "max_temp": 28},
            "attraction_types": ["cultural_photo", "street_photography", "portrait", "village"],
            "budget_range": {"min": 350, "max": 1300},
            "kids_friendly": False,
            "visited_destinations": ["Hoi An", "Hanoi", "Hue", "Can Tho"],
        },
    },
    {
        "username": "NguyenVanHieu",
        "email": "nguyenvanhieu@gmail.com",
        "password": "password123",
        "rank": Rank.gold,
        "preference": {
            "weather_pref": {"min_temp": 12, "max_temp": 22},
            "attraction_types": ["mountain_photography", "fog", "terrace_field", "wilderness"],
            "budget_range": {"min": 250, "max": 1000},
            "kids_friendly": False,
            "visited_destinations": ["Y Ty", "Lung Cu", "Ma Pi Leng", "Hoang Su Phi"],
        },
    },
]
  # Truncated for brevity - add remaining 55 users as needed


# Vietnamese locations for autocomplete searches
VIETNAM_LOCATIONS = [
    # Major cities
    "Ho Chi Minh City Vietnam", "Hanoi Vietnam", "Da Nang Vietnam", "Hai Phong Vietnam", "Can Tho Vietnam",

    # Popular tourist destinations
    "Hoi An Vietnam", "Hue Vietnam", "Nha Trang Vietnam", "Phu Quoc Island Vietnam", "Dalat Vietnam",
    "Sapa Vietnam", "Ha Long Bay Vietnam", "Ninh Binh Vietnam", "Vung Tau Vietnam", "Mui Ne Vietnam",

    # Cultural sites
    "Hue Imperial City Vietnam", "My Son Sanctuary Vietnam", "Cu Chi Tunnels Vietnam", "Mekong Delta Vietnam",
    "Phong Nha Ke Bang National Park Vietnam", "Cat Ba Island Vietnam", "Con Dao Vietnam",

    # Beach destinations
    "Nha Trang Beach Vietnam", "Phu Quoc Beach Vietnam", "Mui Ne Beach Vietnam", "Da Nang Beach Vietnam",
    "Quy Nhon Beach Vietnam", "Vung Tau Beach Vietnam", "Phan Thiet Beach Vietnam",

    # Mountain destinations
    "Sapa Mountain Vietnam", "Dalat Highlands Vietnam", "Ha Giang Loop Vietnam", "Fansipan Mountain Vietnam",
    "Moc Chau Vietnam", "Mai Chau Vietnam", "Pu Luong Vietnam", "Ta Xua Vietnam",

    # Specific attractions - Ho Chi Minh
    "Ben Thanh Market Ho Chi Minh", "Notre Dame Cathedral Saigon", "War Remnants Museum Ho Chi Minh",
    "Independence Palace Ho Chi Minh", "Saigon Opera House", "Bitexco Tower Ho Chi Minh",

    # Specific attractions - Hanoi
    "Hoan Kiem Lake Hanoi", "Temple of Literature Hanoi", "Old Quarter Hanoi", "Ho Chi Minh Mausoleum",
    "Tran Quoc Pagoda Hanoi", "West Lake Hanoi", "Long Bien Bridge Hanoi",

    # Specific attractions - Da Nang
    "Marble Mountains Da Nang", "Ba Na Hills Da Nang", "Golden Bridge Da Nang", "Dragon Bridge Da Nang",
    "My Khe Beach Da Nang", "Lady Buddha Da Nang",

    # Specific attractions - Hoi An
    "Japanese Bridge Hoi An", "Old Town Hoi An", "An Bang Beach Hoi An", "Tra Que Village Hoi An",

    # Specific attractions - Nha Trang
    "Vinpearl Nha Trang", "Po Nagar Cham Towers Nha Trang", "Long Son Pagoda Nha Trang",

    # Nature & Parks
    "Phong Nha Cave Vietnam", "Son Doong Cave Vietnam", "Bach Ma National Park Vietnam",
    "Cuc Phuong National Park Vietnam", "Tam Coc Ninh Binh", "Trang An Ninh Binh",

    # Additional cities
    "Quy Nhon Vietnam", "Phan Thiet Vietnam", "Buon Ma Thuot Vietnam", "Pleiku Vietnam",
    "Kon Tum Vietnam", "Ca Mau Vietnam", "Rach Gia Vietnam", "Ha Tien Vietnam",

    # Islands & coastal
    "Con Dao Island Vietnam", "Ly Son Island Vietnam", "Quan Lan Island Vietnam",
    "Co To Island Vietnam", "Nam Du Island Vietnam",

    # More specific POIs
    "Saigon Central Post Office", "Reunification Palace Ho Chi Minh", "Suoi Tien Park Ho Chi Minh",
    "Dam Sen Park Ho Chi Minh", "Binh Tay Market Ho Chi Minh", "Giac Lam Pagoda Ho Chi Minh",
    "Dong Khoi Street Ho Chi Minh", "Nguyen Hue Walking Street Ho Chi Minh",

    "Ba Dinh Square Hanoi", "Dong Xuan Market Hanoi", "Hanoi Opera House", "Vietnam Museum of Ethnology",
    "Thang Long Water Puppet Theatre", "St Joseph Cathedral Hanoi", "Train Street Hanoi",

    "Linh Ung Pagoda Da Nang", "Han River Bridge Da Nang", "Asia Park Da Nang", "Sun World Ba Na Hills",

    "Coconut Forest Hoi An", "Cam Thanh Village Hoi An", "Cham Island Hoi An",

    "Yang Bay Waterfall Nha Trang", "Nha Trang Cathedral", "Dam Market Nha Trang",

    # Historical sites
    "Dien Bien Phu Battlefield Vietnam", "DMZ Vietnam", "Vinh Moc Tunnels Vietnam",

    # Food & Markets
    "Ben Thanh Night Market", "Dong Ba Market Hue", "Han Market Da Nang", "Cai Rang Floating Market Can Tho",

    # Additional beaches & resorts
    "Bai Chay Beach Ha Long", "Tuan Chau Island Ha Long", "Doc Let Beach Nha Trang",
    "Bai Dai Beach Nha Trang", "Ke Ga Beach Phan Thiet", "Bai Xep Beach Quy Nhon",

    # Mountain towns
    "Tam Dao Vietnam", "Ba Vi Vietnam", "Da Lat Flower Garden", "Dalat Night Market",
    "Crazy House Dalat", "Datanla Waterfall Dalat", "Langbiang Mountain Dalat",

    # Additional cultural sites
    "Thien Mu Pagoda Hue", "Tomb of Khai Dinh Hue", "Tomb of Minh Mang Hue",
    "Perfume Pagoda Hanoi", "Bai Dinh Pagoda Ninh Binh", "Huong Tich Cave Hanoi",

    # Adventure & nature
    "Cat Tien National Park Vietnam", "Yok Don National Park Vietnam", "Phu Quoc National Park",
    "Dray Nur Waterfall Vietnam", "Dray Sap Waterfall Vietnam", "Elephant Falls Dalat",

    # Additional islands
    "Hon Mun Island Nha Trang", "Hon Tam Island Nha Trang", "Monkey Island Nha Trang",
    "Ngoc Island Phu Quoc", "Fingernail Island Phu Quoc", "May Rut Island Phu Quoc",

    # Urban attractions
    "Bitexco Financial Tower", "Landmark 81 Ho Chi Minh", "Lotte Center Hanoi",
    "Vincom Center Da Nang", "Indochina Plaza Hanoi",

    # More beaches
    "Non Nuoc Beach Da Nang", "Thanh Binh Beach Da Nang", "Bai Truoc Beach Vung Tau",
    "Bai Sau Beach Vung Tau", "Ham Tien Beach Mui Ne", "Hon Rom Beach Phan Thiet",
]


async def create_user_with_preference(db: AsyncSession, user_data: dict):
    """Helper to create user with preference using services"""
    try:
        # Check if user already exists
        users = await UserRepository.search_users(db, user_data["email"], limit=1)
        if users:
            return None, None

        # Create user via repository (direct creation for bulk import without email verification)
        register_data = UserRegister(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"]
        )
        new_user = await UserRepository.create_user(db, register_data)
        if not new_user:
            print(f"  ❌ Failed to create user {user_data.get('username')}")
            return None, None

        # Update rank if specified
        if user_data.get("rank") and user_data["rank"] != Rank.bronze:
            # Note: In real scenario, rank should be set by eco_points logic
            new_user.rank = user_data["rank"]
            await db.commit()
            await db.refresh(new_user)

        # Create preference
        pref_data = user_data.get("preference", {})
        if pref_data:
            preference_update = PreferenceUpdate(
                weather_pref=pref_data.get("weather_pref"),
                attraction_types=pref_data.get("attraction_types"),
                budget_range=pref_data.get("budget_range"),
                kids_friendly=pref_data.get("kids_friendly", False),
                visited_destinations=pref_data.get("visited_destinations")
            )
            await ClusterRepository.update_preference(
                db,
                user_id=new_user.id,
                preference_data=preference_update
            )
        else:
            # Create empty preference
            await ClusterRepository.create_preference(db, user_id=new_user.id)

        preference = await ClusterRepository.get_preference_by_user_id(db, new_user.id)

        return new_user, preference
    except Exception as e:
        await db.rollback()
        print(f"  ❌ Failed to create user {user_data.get('username')}: {e}")
        return None, None


async def fetch_destinations_via_autocomplete(db: AsyncSession, sample_size: int = 200) -> list[str]:
    """Fetch real destination Place IDs using autocomplete API"""
    print(f"\n🗺️  Fetching {sample_size} destinations from Vietnam using Google Places API...")

    place_ids = []
    seen_ids = set()

    # Shuffle locations for variety
    locations = VIETNAM_LOCATIONS.copy()
    random.shuffle(locations)

    # Generate a session token for the autocomplete requests
    import uuid
    session_token = str(uuid.uuid4())

    for query in locations:
        if len(place_ids) >= sample_size:
            break

        try:
            request = AutocompleteRequest(query=query, session_token=session_token)
            response = await MapService.autocomplete(db, request)

            if response and response.predictions:
                for prediction in response.predictions[:3]:  # Take up to 3 from each search
                    place_id = prediction.place_id
                    if place_id not in seen_ids:
                        place_ids.append(place_id)
                        seen_ids.add(place_id)
                        print(f"  ✅ [{len(place_ids)}] {prediction.description}")

                    if len(place_ids) >= sample_size:
                        break
        except Exception as e:
            print(f"  ⚠️ Failed to fetch '{query}': {e}")
            continue

    print(f"\n📍 Successfully collected {len(place_ids)} unique destinations\n")
    return place_ids


async def create_destinations_with_embeddings(db: AsyncSession, place_ids: list[str]) -> int:
    """Create destination records with embeddings using services"""
    print(f"🏗️  Creating {len(place_ids)} destination records with embeddings...")

    created_count = 0
    for idx, place_id in enumerate(place_ids, 1):
        try:
            # Check if destination already exists
            existing = await DestinationService.get_destination_by_id(db, place_id)
            if existing:
                continue
        except:
            # Destination doesn't exist, create it
            pass

        try:
            # Create destination using service
            dest_data = DestinationCreate(place_id=place_id)
            await DestinationService.create_destination(db, dest_data)

            # Generate and save embedding using service
            destination_metadata = {
                "name": "Tourist destination in Vietnam",
                "tags": ["tourist_attraction", "place_to_visit", "vietnam"],
                "category": "tourist_attraction"
            }

            embedding = await DestinationService.embed_destination_by_id(
                db, place_id, destination_metadata
            )

            if embedding:
                created_count += 1

            if idx % 20 == 0:
                print(f"  ⏳ Progress: {idx}/{len(place_ids)} destinations processed")

        except Exception as e:
            print(f"  ⚠️ Failed to create destination {place_id}: {e}")
            continue

    print(f"✅ Created {created_count} destinations with embeddings\n")
    return created_count


async def create_user_activities(db: AsyncSession, user_ids: list[int], place_ids: list[str]) -> int:
    """Create random user activities for destinations using services"""
    print(f"👥 Creating user activities for {len(user_ids)} users across {len(place_ids)} destinations...")

    activity_count = 0
    for user_id in user_ids:
        # Each user interacts with 5-15 random destinations
        num_interactions = random.randint(5, 15)
        user_destinations = random.sample(place_ids, min(num_interactions, len(place_ids)))

        for place_id in user_destinations:
            try:
                # Use UserService to log activities
                activity_data = UserActivityCreate(
                    activity=random.choice([Activity.search_destination, Activity.save_destination]),
                    destination_id=place_id
                )
                await UserService.log_user_activity(db, user_id, activity_data)
                activity_count += 1
            except Exception:
                # Silently continue if activity creation fails (could be duplicate or other issue)
                continue

    print(f"✅ Created {activity_count} user activities\n")
    return activity_count


async def bulk_create_users(db: AsyncSession) -> tuple[int, int]:
    """Main bulk creation function"""
    print("\n" + "=" * 70)
    print("🚀 BULK DATA CREATION - VIETNAM DESTINATIONS")
    print("=" * 70)
    print(f"📊 Sample data: {len(SAMPLE_USERS)} users, {len(VIETNAM_LOCATIONS)} locations")

    try:
        # Step 1: Create users from SAMPLE_USERS
        print("\n📋 Step 1: Checking/Creating users...")
        created_users = 0
        created_preferences = 0
        user_ids = []  # Will store IDs of created/existing users

        for user_data in SAMPLE_USERS:
            user, pref = await create_user_with_preference(db, user_data)
            if user:
                created_users += 1
                user_ids.append(user.id)
                print(f"  ✅ Created user: {user.username} (ID: {user.id})")
            if pref:
                created_preferences += 1

        # If no new users created, get existing user IDs from database
        if not user_ids:
            print("  ℹ️  No new users created. Fetching existing users...")
            filters = UserFilterParams(skip=0, limit=len(SAMPLE_USERS))
            existing_users = await UserRepository.fetch_users(db, filters)
            user_ids = [u.id for u in existing_users]

        print(f"\n✅ Total users available: {len(user_ids)}")
        print(f"   New users created: {created_users}")
        print(f"   Preferences created: {created_preferences}\n")

        # Step 2: Fetch ~200 destinations via autocomplete
        print("\n📋 Step 2: Fetching destinations...")
        place_ids = await fetch_destinations_via_autocomplete(db, sample_size=200)

        if not place_ids:
            print("❌ No destinations fetched. Aborting.")
            return created_users, created_preferences

        # Step 3: Create destination records with embeddings
        print("\n📋 Step 3: Creating destination records...")
        destinations_created = await create_destinations_with_embeddings(db, place_ids)

        # Step 4: Create user activities
        print("\n📋 Step 4: Creating user activities...")
        activities_created = await create_user_activities(db, user_ids, place_ids)

        # Step 5: Generate embeddings for all users with preferences
        print("\n📋 Step 5: Generating user embeddings...")
        try:
            embeddings_generated = await ClusterService.update_user_embeddings(db)
            print(f"  ✅ Generated {embeddings_generated} user embeddings")
        except Exception as embed_error:
            print(f"  ⚠️ Embedding generation failed: {embed_error}")
            embeddings_generated = 0

        # Step 6: Run clustering to assign users to clusters
        print("\n📋 Step 6: Running clustering algorithm...")
        clusters_created = []
        try:
            clustering_result = await ClusterService.run_user_clustering(db)
            print("  ✅ Clustering completed successfully:")
            print(f"     - Users clustered: {clustering_result.stats.users_clustered}")
            print(f"     - Clusters updated: {clustering_result.stats.clusters_updated}")
            print(f"     - Embeddings generated: {clustering_result.stats.embeddings_generated}")
            print(f"     - Users in noise: {clustering_result.stats.users_in_noise}")
            clusters_created = list(range(1, clustering_result.stats.clusters_updated + 1))
            
        except Exception as cluster_error:
            print(f"  ❌ Clustering failed: {cluster_error}")
            print(f"  ⚠️ This may affect recommendation quality. Please run clustering manually.")

        # Step 7: Compute cluster popularity scores
        print("\n📋 Step 7: Computing cluster popularity scores...")
        clusters_computed = 0
        for cluster_id in clusters_created:
            try:
                await ClusterService.compute_cluster_popularity(db, cluster_id)
                clusters_computed += 1
            except Exception as pop_error:
                print(f"  ⚠️ Failed to compute popularity for cluster {cluster_id}: {pop_error}")
        print(f"  ✅ Computed popularity for {clusters_computed}/{len(clusters_created)} clusters")

        # Final summary
        print("\n" + "=" * 70)
        print("📊 BULK CREATION SUMMARY")
        print("=" * 70)
        print(f"   👥 Users: {len(user_ids)} total ({created_users} new)")
        print(f"   🗂️  Preferences: {created_preferences} created")
        print(f"   🧠 User Embeddings: {embeddings_generated} generated")
        print(f"   📍 Destinations: {destinations_created} created")
        print(f"   🔢 Place IDs collected: {len(place_ids)}")
        print(f"   📝 User Activities: {activities_created} created")
        print(f"   🎯 Clusters with popularity: {clusters_computed}")
        print("=" * 70 + "\n")

        return created_users, created_preferences

    except Exception as e:
        await db.rollback()
        print(f"\n❌ ERROR: {e}")
        raise e
