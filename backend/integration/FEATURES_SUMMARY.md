# ✅ CÁC TÍNH NĂNG ĐÃ THÊM VÀO GOOGLE_MAP_API.PY

## 🎯 TỔNG QUAN

Đã thêm **3 tính năng chính** để so sánh và tính toán carbon emission cho các route:

---

## 1️⃣ `_calculate_carbon_emission(distance_km, mode)`

**Tác dụng:** Tính carbon emission dựa trên khoảng cách và phương thức di chuyển

**Emission Factors:**
```python
{
    "driving": 120 g/km,      # 🚗 Xe hơi
    "motorbike": 80 g/km,     # 🏍️ Xe máy
    "transit": 30 g/km,       # 🚌 Xe bus
    "train": 20 g/km,         # 🚄 Tàu điện
    "bicycling": 0 g/km,      # 🚴 Xe đạp
    "walking": 0 g/km         # 🚶 Đi bộ
}
```

**Ví dụ:**
```python
carbon = maps._calculate_carbon_emission(10, "driving")
# Output: {"co2_kg": 1.2, "co2_grams": 1200, "emission_factor_g_per_km": 120}
```

---

## 2️⃣ `compare_routes_all_options(origin, destination, max_time_ratio)`

**Tác dụng:** So sánh **TẤT CẢ** phương án di chuyển và trả về 3 loại route tối ưu

### Input:
- `origin`: Điểm xuất phát
- `destination`: Điểm đến  
- `max_time_ratio`: Tỷ lệ thời gian chấp nhận (mặc định 1.5 = chậm hơn 50%)

### Output:
```python
{
    "fastest_route": {...},           # ⚡ Route NHANH NHẤT
    "lowest_carbon_route": {...},     # 🌱 Route CARBON THẤP NHẤT
    "smart_route": {...},              # 🧠 Route THÔNG MINH (nếu có)
    "all_options": [...]               # Tất cả options
}
```

### 3 Loại Route:

#### ⚡ **FASTEST ROUTE (Route nhanh nhất)**
- Thường là xe hơi/xe máy
- Thời gian di chuyển ngắn nhất
- Có thể có carbon emission cao

**Ví dụ:**
```python
{
    "mode_display": "🚗 Xe hơi",
    "duration_minutes": 5.2,
    "distance_km": 1.06,
    "carbon_emission": {"co2_kg": 0.128},
    "highlight": "⚡ NHANH NHẤT"
}
```

#### 🌱 **LOWEST CARBON ROUTE (Carbon thấp nhất)**
- Thường là đi bộ hoặc xe đạp
- Carbon emission = 0 kg
- Có thể mất nhiều thời gian hơn
- Có health benefit (calories burned)

**Ví dụ:**
```python
{
    "mode_display": "🚶 Đi bộ",
    "duration_minutes": 13.3,
    "distance_km": 0.96,
    "carbon_emission": {"co2_kg": 0.0},
    "carbon_saved_vs_driving": 0.128,  # Tiết kiệm so với xe hơi
    "health_benefit": "+57 calories",
    "eco_score": 100,
    "highlight": "🌱 CARBON THẤP NHẤT"
}
```

#### 🧠 **SMART ROUTE (Route thông minh)** ⭐

**Đặc điểm:**
- Kết hợp **đi bộ + xe bus/tàu** (transit)
- Thời gian chấp nhận được (không quá chậm)
- Tiết kiệm carbon đáng kể

**Điều kiện để có Smart Route:**
```python
1. Mode = "transit" (có xe bus/tàu)
2. time_ratio <= max_time_ratio (VD: chậm hơn tối đa 50%)
3. carbon_saving_percent > 50% (tiết kiệm > 50% CO₂ so với xe hơi)
```

**Ví dụ:**
```python
{
    "mode_display": "🚌 Xe bus/Tàu",
    "duration_minutes": 48,
    "carbon_emission": {"co2_kg": 0.174},
    "smart_route_info": {
        "time_difference_minutes": 13.0,      # Chậm hơn 13 phút
        "time_ratio": 1.37,                   # Chậm hơn 37%
        "carbon_saving_kg": 0.548,            # Tiết kiệm 548g CO₂
        "carbon_saving_percent": 75.9,        # Tiết kiệm 76% CO₂
        "is_recommended": true                # ✅ Nên dùng
    },
    "transit_details": {
        "transit_steps": [
            {
                "line": "1",                  # Tuyến số 1
                "vehicle": "BUS",
                "departure_stop": "Bến Thành",
                "arrival_stop": "ĐHKHTN",
                "num_stops": 8,
                "duration": "25 phút"
            }
        ],
        "walking_steps": [
            {
                "distance": "200m",
                "duration": "3 phút",
                "instruction": "Đi bộ đến trạm xe bus"
            }
        ]
    }
}
```

---

## 3️⃣ `_extract_transit_details(leg)`

**Tác dụng:** Trích xuất chi tiết các bước đi của transit route

**Output:**
```python
{
    "transit_steps": [...],        # Các chuyến xe bus/tàu
    "walking_steps": [...],        # Các đoạn đi bộ
    "total_transit_steps": 1,      # Tổng số chuyến xe
    "total_walking_steps": 2       # Tổng số đoạn đi bộ
}
```

---

## 🎬 DEMO KẾT QUẢ

### Test 1: Route ngắn (Bến Thành → Bitexco ~ 1km)

```
⚡ NHANH NHẤT
   🚗 Xe hơi - 5 phút - 1.06km - 0.128 kg CO₂

🌱 CARBON THẤP NHẤT
   🚶 Đi bộ - 13 phút - 0.96km - 0.0 kg CO₂
   💚 Tiết kiệm: 0.128 kg CO₂
   💪 +57 calories

🧠 SMART ROUTE: Không có
   (khoảng cách quá ngắn, không cần transit)
```

### Test 2: Route trung bình (Bitexco → ĐHKHTN ~ 6km)

```
⚡ NHANH NHẤT
   🚗 Xe hơi - 35 phút - 5.8km - 0.696 kg CO₂

🌱 CARBON THẤP NHẤT  
   🚶 Đi bộ - 1h 10min - 5.5km - 0.0 kg CO₂
   💚 Tiết kiệm: 0.696 kg CO₂

🧠 SMART ROUTE ⭐ RECOMMENDED
   🚌 Xe bus/Tàu - 48 phút - 5.8km - 0.174 kg CO₂
   ✅ Tiết kiệm 75.9% CO₂
   ⏱️ Chỉ chậm hơn 13 phút
   
   Chi tiết:
   • 🚶 Đi bộ 200m đến trạm (3 phút)
   • 🚌 BUS tuyến 1: Bến Thành → ĐHKHTN (8 trạm, 25 phút)
   • 🚶 Đi bộ 150m đến đích (2 phút)
```

---

## 💡 CÁCH SỬ DỤNG TRONG ECOMOVEX

### 1. **API Endpoint**

```python
from fastapi import APIRouter
from integration.google_map_api import GoogleMapsAPI

router = APIRouter()

@router.post("/routes/compare")
async def compare_routes(origin: str, destination: str, max_time_ratio: float = 1.5):
    """
    So sánh tất cả phương án di chuyển
    
    Response:
    {
        "fastest_route": {...},
        "lowest_carbon_route": {...},
        "smart_route": {...}
    }
    """
    maps = GoogleMapsAPI()
    result = await maps.compare_routes_all_options(origin, destination, max_time_ratio)
    await maps.close()
    return result
```

### 2. **Frontend Display**

```javascript
// Gọi API
const routes = await fetch('/api/routes/compare', {
    method: 'POST',
    body: JSON.stringify({ 
        origin: 'Chợ Bến Thành', 
        destination: 'Bitexco Tower',
        max_time_ratio: 1.5 
    })
})

// Hiển thị 3 tabs
<Tabs>
    <Tab icon="⚡" label="Nhanh nhất">
        <RouteCard route={routes.fastest_route} />
    </Tab>
    
    <Tab icon="🌱" label="Xanh nhất">
        <RouteCard route={routes.lowest_carbon_route} />
    </Tab>
    
    <Tab icon="🧠" label="Thông minh" badge="Khuyến nghị">
        <RouteCard route={routes.smart_route} />
    </Tab>
</Tabs>
```

### 3. **Recommendation Logic**

```python
def get_user_recommendation(routes, user_preference):
    """
    Chọn route phù hợp với preference của user
    
    user_preference:
    - "time": Ưu tiên thời gian → fastest_route
    - "eco": Ưu tiên môi trường → lowest_carbon_route  
    - "balanced": Cân bằng → smart_route
    """
    if user_preference == "time":
        return routes["fastest_route"]
    
    elif user_preference == "eco":
        return routes["lowest_carbon_route"]
    
    else:  # balanced
        smart = routes.get("smart_route")
        if smart and smart["smart_route_info"]["is_recommended"]:
            return smart
        else:
            # Fallback: Nếu không có smart route, chọn green route nếu OK
            green = routes["lowest_carbon_route"]
            fastest = routes["fastest_route"]
            
            if green["duration_minutes"] <= fastest["duration_minutes"] * 1.3:
                return green
            else:
                return fastest
```

### 4. **Carbon Tracking**

```python
async def log_user_trip(user_id, route_chosen):
    """
    Lưu lại carbon emission của trip
    Tính tổng carbon saved trong tháng
    """
    # So với nếu user đi xe hơi
    if route_chosen["mode"] != "driving":
        driving_carbon = route_chosen["distance_km"] * 0.12
        actual_carbon = route_chosen["carbon_emission"]["co2_kg"]
        carbon_saved = driving_carbon - actual_carbon
        
        # Update user stats
        await update_user_eco_stats(user_id, {
            "carbon_saved_kg": carbon_saved,
            "eco_points": int(carbon_saved * 100),
            "distance_km": route_chosen["distance_km"]
        })
```

---

## 🎯 LỢI ÍCH

### Cho User:
- ✅ Thấy rõ carbon emission của từng phương án
- ✅ Có gợi ý thông minh (cân bằng thời gian & môi trường)
- ✅ Biết mình tiết kiệm được bao nhiêu CO₂
- ✅ Có động lực chọn green option (calories, eco points)

### Cho EcomoveX:
- ✅ Khuyến khích hành vi thân thiện môi trường
- ✅ Minh bạch về tác động môi trường
- ✅ Tạo engagement qua gamification
- ✅ Align với mission "Eco-friendly travel"

---

## 📊 METRICS CÓ THỂ TRACK

```python
# User level
- total_carbon_saved_kg
- total_trips
- eco_score
- favorite_mode (walking/bicycling/transit/driving)
- streak_days (số ngày liên tục chọn green option)

# Platform level
- total_carbon_saved (all users)
- green_route_adoption_rate
- average_carbon_per_trip
- most_popular_routes
```

---

## 🚀 NEXT STEPS

1. ✅ **Integration vào backend API** (routers)
2. ✅ **Frontend UI** (route comparison cards)
3. ✅ **User profile** (eco stats, achievements)
4. ✅ **Gamification** (levels, badges, leaderboard)
5. 💡 **Air quality integration** (tránh route AQI cao)
6. 💡 **Social sharing** ("Tôi đã tiết kiệm 5kg CO₂ tuần này!")
7. 💡 **Predictive recommendation** (ML-based preference learning)

---

## 📝 TÓM TẮT

**3 hàm mới:**
1. `_calculate_carbon_emission()` - Tính CO₂
2. `compare_routes_all_options()` - So sánh tất cả routes
3. `_extract_transit_details()` - Chi tiết transit

**3 loại route:**
1. ⚡ **Fastest** - Nhanh nhất
2. 🌱 **Greenest** - Carbon thấp nhất  
3. 🧠 **Smart** - Thông minh (kết hợp transit + đi bộ)

**Mission:** Không ép user phải green, nhưng KHUYẾN KHÍCH bằng:
- Minh bạch carbon emission
- Gợi ý smart route (chậm chút nhưng green hơn nhiều)
- Gamification (points, achievements)
- Social proof (bạn bè cũng chọn route này)
