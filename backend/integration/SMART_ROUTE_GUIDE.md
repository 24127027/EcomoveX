# 🧠 SMART ROUTE COMPARISON - HƯỚNG DẪN SỬ DỤNG

## 📋 TỔNG QUAN

Hệ thống so sánh thông minh giúp người dùng chọn phương án di chuyển TỐI ƯU, cân bằng giữa:
- ⚡ **Thời gian** (nhanh nhất)
- 🌱 **Môi trường** (carbon thấp nhất)
- 🧠 **Thông minh** (kết hợp đi bộ + public transport)

---

## 🎯 TÍNH NĂNG CHÍNH

### 1. **Tính Carbon Emission Chi Tiết**

```python
from integration.google_map_api import GoogleMapsAPI

maps = GoogleMapsAPI()

# Tính carbon cho 10km với từng phương thức
carbon = maps._calculate_carbon_emission(10, "driving")
# Output:
# {
#   "co2_kg": 1.2,              # 1.2 kg CO₂
#   "co2_grams": 1200,
#   "emission_factor_g_per_km": 120,
#   "distance_km": 10,
#   "mode": "driving"
# }
```

**Emission Factors (g CO₂/km):**
| Phương thức | Emission | Icon |
|-------------|----------|------|
| Xe hơi (driving) | 120 g/km | 🚗 |
| Xe máy (motorbike) | 80 g/km | 🏍️ |
| Xe bus (transit/bus) | 30 g/km | 🚌 |
| Tàu điện (train/subway) | 20 g/km | 🚄 |
| Xe đạp (bicycling) | 0 g/km | 🚴 |
| Đi bộ (walking) | 0 g/km | 🚶 |

---

### 2. **So Sánh TẤT CẢ Phương Án Di Chuyển**

```python
result = await maps.compare_routes_all_options(
    origin="Chợ Bến Thành, TP.HCM",
    destination="Bitexco Tower, TP.HCM",
    max_time_ratio=1.5  # Chấp nhận chậm hơn 50% so với route nhanh nhất
)
```

**Output:**
```python
{
    "summary": {
        "origin": "Chợ Bến Thành, TP.HCM",
        "destination": "Bitexco Tower, TP.HCM",
        "total_options": 4
    },
    
    # 1. Route NHANH NHẤT
    "fastest_route": {
        "type": "fastest",
        "mode": "driving",
        "mode_display": "🚗 Xe hơi",
        "distance_km": 1.06,
        "duration_minutes": 5.2,
        "duration_text": "5 phút",
        "carbon_emission": {
            "co2_kg": 0.128,
            "co2_grams": 128,
            "emission_factor_g_per_km": 120
        },
        "highlight": "⚡ NHANH NHẤT",
        "is_fastest": true
    },
    
    # 2. Route CARBON THẤP NHẤT
    "lowest_carbon_route": {
        "type": "walking",
        "mode": "walking",
        "mode_display": "🚶 Đi bộ",
        "distance_km": 0.96,
        "duration_minutes": 13.3,
        "duration_text": "13 phút",
        "carbon_emission": {
            "co2_kg": 0.0,
            "emission_factor_g_per_km": 0
        },
        "highlight": "🌱 CARBON THẤP NHẤT",
        "carbon_saved_vs_driving": 0.128,  # Tiết kiệm 128g CO₂
        "health_benefit": "+57 calories",
        "eco_score": 100
    },
    
    # 3. Route THÔNG MINH (nếu có)
    "smart_route": {
        "type": "transit",
        "mode": "transit",
        "mode_display": "🚌 Xe bus/Tàu",
        "distance_km": 5.8,
        "duration_minutes": 48,
        "duration_text": "48 phút",
        "carbon_emission": {
            "co2_kg": 0.174,
            "emission_factor_g_per_km": 30
        },
        "highlight": "🧠 THÔNG MINH (Cân bằng thời gian & môi trường)",
        "smart_route_info": {
            "time_difference_minutes": 13.0,    # Chậm hơn 13 phút
            "time_ratio": 1.37,                 # Chậm hơn 37%
            "carbon_saving_kg": 0.548,          # Tiết kiệm 548g CO₂
            "carbon_saving_percent": 75.9,      # Tiết kiệm 76% CO₂
            "is_recommended": true              # ✅ Khuyến nghị
        },
        "transit_details": {
            "transit_steps": [
                {
                    "line": "1",
                    "vehicle": "BUS",
                    "departure_stop": "Bến xe Bến Thành",
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
            ],
            "total_transit_steps": 1,
            "total_walking_steps": 2
        }
    },
    
    # 4. Tất cả options (đã sắp xếp theo thời gian)
    "all_options": [
        # ... tất cả routes
    ]
}
```

---

## 🧮 LOGIC SMART ROUTE

### Điều kiện để là "Smart Route":

1. ✅ **Mode = Transit** (xe bus/tàu, có kết hợp đi bộ)
2. ✅ **Thời gian chấp nhận được:**
   ```python
   time_ratio = smart_route_time / fastest_route_time
   time_ratio <= max_time_ratio  # Mặc định 1.5 (chậm hơn tối đa 50%)
   ```
3. ✅ **Tiết kiệm carbon đáng kể:**
   ```python
   carbon_saving_percent > 50%  # Tiết kiệm > 50% CO₂ so với xe hơi
   ```

### Công thức tính:

```python
# Carbon saving
carbon_saving_kg = driving_carbon - transit_carbon
carbon_saving_percent = (carbon_saving_kg / driving_carbon) * 100

# Time difference
time_difference = transit_time - fastest_time
time_ratio = transit_time / fastest_time

# Recommendation
is_recommended = (
    time_ratio <= max_time_ratio AND
    carbon_saving_percent > 50
)
```

---

## 💡 USE CASES TRONG ECOMOVEX

### 1. **Màn hình So Sánh Route**

```python
async def get_route_comparison(origin: str, destination: str):
    maps = GoogleMapsAPI()
    result = await maps.compare_routes_all_options(origin, destination)
    
    # Hiển thị 3 tabs:
    # Tab 1: ⚡ Nhanh nhất
    # Tab 2: 🌱 Xanh nhất
    # Tab 3: 🧠 Thông minh (nếu có)
    
    return {
        "fastest": result["fastest_route"],
        "greenest": result["lowest_carbon_route"],
        "smart": result["smart_route"]
    }
```

### 2. **Recommendation Engine**

```python
def get_recommendation(result):
    fastest = result["fastest_route"]
    lowest_carbon = result["lowest_carbon_route"]
    smart = result.get("smart_route")
    
    # Ưu tiên Smart Route
    if smart and smart["smart_route_info"]["is_recommended"]:
        return {
            "type": "smart",
            "route": smart,
            "message": f"Đi {smart['mode_display']} tiết kiệm {smart['smart_route_info']['carbon_saving_percent']}% CO₂, chỉ chậm hơn {smart['smart_route_info']['time_difference_minutes']} phút!"
        }
    
    # Nếu không có Smart Route, ưu tiên Green Route nếu thời gian OK
    elif lowest_carbon["duration_minutes"] <= fastest["duration_minutes"] * 1.3:
        return {
            "type": "green",
            "route": lowest_carbon,
            "message": f"Đi {lowest_carbon['mode_display']} - Tốt cho môi trường & sức khỏe!"
        }
    
    # Mặc định: Fastest
    else:
        return {
            "type": "fastest",
            "route": fastest,
            "message": f"Route nhanh nhất, nhưng hãy cân nhắc {lowest_carbon['mode_display']} để giảm {lowest_carbon['carbon_saved_vs_driving']}kg CO₂"
        }
```

### 3. **Eco Score & Gamification**

```python
def calculate_user_eco_impact(user_routes):
    total_carbon_saved = 0
    
    for route in user_routes:
        if route["chosen_mode"] != "driving":
            # So với nếu user đi xe hơi
            driving_carbon = route["distance_km"] * 0.12  # 120g/km
            actual_carbon = route["carbon_emission"]["co2_kg"]
            saved = driving_carbon - actual_carbon
            total_carbon_saved += saved
    
    return {
        "total_carbon_saved_kg": round(total_carbon_saved, 2),
        "equivalent_trees": round(total_carbon_saved / 20, 1),  # 1 cây = 20kg CO₂/năm
        "eco_points": int(total_carbon_saved * 100),
        "level": calculate_level(total_carbon_saved)
    }
```

### 4. **Display Transit Details**

```python
def format_transit_route(smart_route):
    transit = smart_route["transit_details"]
    
    instructions = []
    
    # Walking to bus stop
    for walk in transit["walking_steps"]:
        instructions.append(f"🚶 Đi bộ {walk['distance']} ({walk['duration']})")
    
    # Bus/Train
    for step in transit["transit_steps"]:
        instructions.append(
            f"{get_vehicle_icon(step['vehicle'])} "
            f"Xe {step['line']}: "
            f"{step['departure_stop']} → {step['arrival_stop']} "
            f"({step['num_stops']} trạm, {step['duration']})"
        )
    
    return "\n".join(instructions)
```

---

## 🎨 UI/UX RECOMMENDATIONS

### **Route Comparison Card:**

```
┌─────────────────────────────────────────────┐
│ 🗺️ CHỢ BẾN THÀNH → BITEXCO                │
├─────────────────────────────────────────────┤
│                                             │
│ ⚡ NHANH NHẤT                                │
│ 🚗 Xe hơi • 5 phút • 1km • 0.13kg CO₂       │
│                                             │
│ 🌱 XANH NHẤT ⭐                              │
│ 🚶 Đi bộ • 13 phút • 0.96km • 0kg CO₂       │
│ 💚 Tiết kiệm 0.13kg CO₂                     │
│ 💪 +57 calories                             │
│                                             │
│ 🧠 KHUYẾN NGHỊ                               │
│ 🚌 Xe bus • 13 phút • 0.96km • 0.03kg CO₂   │
│ ✅ Tốt cho môi trường, thời gian tương đương│
│                                             │
│ [Chọn Route] [Xem Chi Tiết]                │
└─────────────────────────────────────────────┘
```

### **Progress & Achievement:**

```
┌─────────────────────────────────────────────┐
│ 🌍 TÁC ĐỘNG CỦA BẠN                         │
├─────────────────────────────────────────────┤
│                                             │
│ Tháng này bạn đã:                           │
│ 🌱 Tiết kiệm 15.6 kg CO₂                    │
│ 🌳 Tương đương trồng 0.8 cây xanh           │
│ 🏃 Đốt cháy 2,400 calories                  │
│ 💰 Tiết kiệm 280,000 VNĐ                    │
│                                             │
│ ━━━━━━━━━━━━━━━ Level 5 ━━━━━━━━━━━━━━━━   │
│ 78% → Level 6 (còn 4.4kg CO₂)               │
│                                             │
│ 🏆 Huy hiệu: Eco Warrior 🌟                 │
└─────────────────────────────────────────────┘
```

---

## 📊 PARAMETERS & CUSTOMIZATION

### `max_time_ratio`

Tỷ lệ thời gian tối đa chấp nhận cho smart route:

```python
# Strict (user vội)
result = await maps.compare_routes_all_options(
    origin, destination, 
    max_time_ratio=1.2  # Chỉ chấp nhận chậm hơn 20%
)

# Balanced (mặc định)
result = await maps.compare_routes_all_options(
    origin, destination, 
    max_time_ratio=1.5  # Chấp nhận chậm hơn 50%
)

# Eco-focused (user ưu tiên môi trường)
result = await maps.compare_routes_all_options(
    origin, destination, 
    max_time_ratio=2.0  # Chấp nhận chậm hơn 100% (gấp đôi thời gian)
)
```

---

## 🚀 NEXT STEPS

### **Tính năng nâng cao có thể thêm:**

1. **Real-time Traffic Integration:**
   ```python
   # Tính carbon dựa trên traffic thực tế
   # Traffic jam → xe hơi phát thải nhiều hơn
   ```

2. **Air Quality Integration:**
   ```python
   # Tránh route đi qua khu vực AQI cao
   # Ưu tiên route qua công viên (AQI thấp)
   ```

3. **Cost Comparison:**
   ```python
   # So sánh chi phí: xăng vs vé bus vs grab
   ```

4. **Social Features:**
   ```python
   # "5 bạn bè cũng chọn route này"
   # "Route được 87% users đánh giá là tốt"
   ```

5. **Predictive Smart Route:**
   ```python
   # Dựa vào lịch sử user → suggest route phù hợp
   # User thường chọn green route → ưu tiên green
   ```

---

## 📝 EXAMPLE USAGE

```python
from integration.google_map_api import GoogleMapsAPI

async def main():
    maps = GoogleMapsAPI()
    
    # So sánh routes
    result = await maps.compare_routes_all_options(
        origin="Nhà tôi",
        destination="Công ty",
        max_time_ratio=1.5
    )
    
    # Lấy recommendation
    recommendation = get_recommendation(result)
    
    # Hiển thị cho user
    print(f"🎯 Khuyến nghị: {recommendation['message']}")
    
    # Log carbon saved
    if user_chooses_recommended_route:
        carbon_saved = calculate_carbon_saved(result)
        update_user_eco_score(user_id, carbon_saved)
    
    await maps.close()

asyncio.run(main())
```

---

## 🎯 KẾT LUẬN

Hệ thống Smart Route Comparison giúp EcomoveX:
- ✅ Khuyến khích người dùng chọn phương án thân thiện môi trường
- ✅ Cung cấp thông tin minh bạch về carbon emission
- ✅ Cân bằng giữa tiện lợi và bảo vệ môi trường
- ✅ Tạo động lực qua gamification và eco score

**Mission:** Không bắt buộc user đi bộ/xe bus, nhưng KHUYẾN KHÍCH bằng cách cho thấy:
- Tiết kiệm bao nhiêu CO₂
- Chỉ chậm hơn mấy phút
- Có lợi cho sức khỏe
- Tích điểm, nhận thưởng
