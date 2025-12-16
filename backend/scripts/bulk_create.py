from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, Rank, Role
from models.cluster import Preference


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


async def create_user_with_preference(
    db: AsyncSession,
    user_data: dict
) -> tuple[User | None, Preference | None]:
    """Tạo user và preference tương ứng."""
    
    # Kiểm tra user đã tồn tại chưa
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.email == user_data["email"])
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        print(f"  ⚠️  User '{user_data['email']}' đã tồn tại, bỏ qua.")
        return None, None
    
    # Tạo user mới
    preference_data = user_data.pop("preference", None)
    
    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"],
        rank=user_data.get("rank", Rank.bronze),
        role=Role.user,
    )
    db.add(new_user)
    await db.flush()  # Để lấy user.id
    
    # Tạo preference nếu có
    new_preference = None
    if preference_data:
        new_preference = Preference(
            user_id=new_user.id,
            weather_pref=preference_data.get("weather_pref"),
            attraction_types=preference_data.get("attraction_types"),
            budget_range=preference_data.get("budget_range"),
            kids_friendly=preference_data.get("kids_friendly", False),
            visited_destinations=preference_data.get("visited_destinations"),
        )
        db.add(new_preference)    
        await db.flush()
        
    await db.commit()
    await db.refresh(new_user)
    await db.refresh(new_preference)

    return new_user, new_preference


async def bulk_create_users(
    db: AsyncSession,
) -> tuple[int, int]:
    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU TẠO BULK USERS")
    print("=" * 60)
    
    # Nếu có db session từ bên ngoài (main.py), sử dụng nó
    if db is not None:
        return await _process_bulk_create(db)


async def _process_bulk_create(
    db: AsyncSession
) -> tuple[int, int]:
    try:
        created_users = 0
        created_preferences = 0
        
        for user_data in SAMPLE_USERS:
            # Copy để không modify original data
            data = user_data.copy()
            
            user, preference = await create_user_with_preference(db, data)
            
            if user:
                created_users += 1
                print(f"  ✅ Tạo user: {user.username} ({user.email}) - {user.rank.value}")
                
            if preference:
                created_preferences += 1
        
        print("\n" + "-" * 60)
        print(f"📊 KẾT QUẢ:")
        print(f"   - Tổng users trong danh sách: {len(SAMPLE_USERS)}")
        print(f"   - Users đã tạo: {created_users}")
        print(f"   - Preferences đã tạo: {created_preferences}")
        print("=" * 60 + "\n")
        
        return created_users, created_preferences
        
    except Exception as e:
        await db.rollback()
        print(f"\n❌ LỖI: {e}")
        raise e
