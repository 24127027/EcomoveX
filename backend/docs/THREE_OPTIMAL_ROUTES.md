# Chức năng tìm 3 tuyến đường tối ưu

## 📋 Tổng quan

Chức năng `find_three_optimal_routes()` trong Google Maps API integration giúp tìm và so sánh 3 tuyến đường dựa trên các tiêu chí khác nhau:

1. **Tuyến nhanh nhất** (Shortest time) - Tiết kiệm thời gian tối đa
2. **Tuyến ít carbon nhất** (Lowest emission) - Thân thiện với môi trường nhất  
3. **Tuyến thông minh** (Smart combination) - Cân bằng giữa thời gian và carbon

---

## ✨ Tính năng chính

### 1️⃣ Tuyến Nhanh Nhất
- **Mục tiêu**: Thời gian di chuyển ngắn nhất
- **Phương thức**: Bất kỳ (driving, walking, transit, bicycling)
- **Ưu tiên**: Tốc độ > Mọi yếu tố khác

### 2️⃣ Tuyến Ít Carbon Nhất
- **Mục tiêu**: Phát thải CO2 thấp nhất
- **Phương thức**: Ưu tiên walking > bicycling > transit > driving
- **Ưu tiên**: Môi trường > Thời gian

### 3️⃣ Tuyến Thông Minh
**Logic ưu tiên (theo thứ tự):**

1. **Transit (Xe công cộng)** - Nếu:
   - Tiết kiệm >30% carbon so với lái xe
   - HOẶC thời gian <= 1.3x tuyến nhanh nhất
   - Kết hợp đi bộ + xe công cộng

2. **Walking (Đi bộ)** - Nếu:
   - Khoảng cách ≤ 3km
   - Thời gian <= 1.3x tuyến nhanh nhất
   - 0% carbon

3. **Bicycling (Đạp xe)** - Nếu:
   - Thời gian <= 1.3x tuyến nhanh nhất
   - 0% carbon

---

## 🔧 API Method

### Signature
```python
async def find_three_optimal_routes(
    self,
    origin: str,
    destination: str,
    max_time_ratio: float = 1.3,
    language: str = "vi"
) -> Dict[str, Any]
```

### Parameters
- **origin** (str): Điểm xuất phát (tên địa điểm hoặc tọa độ)
- **destination** (str): Điểm đến (tên địa điểm hoặc tọa độ)
- **max_time_ratio** (float): Tỷ lệ thời gian tối đa cho tuyến thông minh so với nhanh nhất (mặc định: 1.3 = 130%)
- **language** (str): Ngôn ngữ trả về (mặc định: "vi")

### Return Format
```python
{
    "status": "OK",
    "origin": "Chợ Bến Thành, Hồ Chí Minh",
    "destination": "Bitexco Financial Tower, Hồ Chí Minh",
    "total_routes_analyzed": 5,
    "routes": {
        "fastest": {
            "type": "fastest_driving",
            "mode": "driving",
            "display_name": "Lái xe (nhanh nhất)",
            "distance_km": 1.06,
            "duration_min": 5.2,
            "duration_text": "5 phút",
            "carbon_kg": 0.204,
            "carbon_grams": 204,
            "emission_factor": 192,
            "reason": "Tuyến đường nhanh nhất",
            "route_details": {...}
        },
        "lowest_carbon": {
            "type": "walking",
            "mode": "walking",
            "display_name": "Đi bộ",
            "distance_km": 0.96,
            "duration_min": 13.3,
            "duration_text": "13 phút",
            "carbon_kg": 0.0,
            "carbon_grams": 0,
            "emission_factor": 0,
            "reason": "Tuyến đường ít carbon nhất",
            "route_details": {...}
        },
        "smart_combination": {
            "type": "transit",
            "mode": "transit",
            "display_name": "Phương tiện công cộng",
            "distance_km": 0.96,
            "duration_min": 13.3,
            "duration_text": "13 phút",
            "carbon_kg": 0.065,
            "carbon_grams": 65,
            "emission_factor": 68,
            "reason": "Tuyến thông minh (kết hợp đi bộ + xe công cộng, tiết kiệm 68.1% carbon)",
            "time_comparison": {
                "vs_fastest_min": 8.1,
                "vs_fastest_percent": 156.4
            },
            "carbon_comparison": {
                "vs_driving_kg": 0.139,
                "vs_driving_percent": 68.1
            },
            "transit_info": {
                "transit_steps": [...],
                "walking_steps": [...],
                "total_transit_steps": 1,
                "total_walking_steps": 2
            },
            "route_details": {...}
        }
    },
    "recommendation": "smart_combination",
    "recommendation_reason": "Cân bằng tốt giữa thời gian và carbon"
}
```

---

## 📊 Test Results

### Test Case 1: Quãng ngắn (~1km)
**Route:** Chợ Bến Thành → Bitexco Tower

| Tuyến | Phương thức | Thời gian | Khoảng cách | Carbon |
|-------|-------------|-----------|-------------|---------|
| Nhanh nhất | 🚗 Lái xe | 5 phút | 1.06 km | 0.204 kg |
| Ít carbon | 🚶 Đi bộ | 13 phút | 0.96 km | 0.000 kg |
| Thông minh | 🚌 Xe công cộng | 13 phút | 0.96 km | 0.065 kg |

**Khuyến nghị:** Tuyến thông minh (Cân bằng tốt)
**Tiết kiệm:** 0.204 kg CO2 = 74.5 kg/năm (nếu đi hàng ngày)

---

### Test Case 2: Quãng trung bình (~11km)
**Route:** Sân bay Tân Sơn Nhất → Landmark 81

| Tuyến | Phương thức | Thời gian | Khoảng cách | Carbon |
|-------|-------------|-----------|-------------|---------|
| Nhanh nhất | 🚗 Lái xe | 29 phút | 11.23 km | 2.157 kg |
| Ít carbon | 🚌 Xe công cộng | 51 phút | 9.59 km | 0.652 kg |
| Thông minh | 🚌 Xe công cộng | 51 phút | 9.59 km | 0.652 kg |

**Chi tiết xe công cộng:**
- Chặng 1: Xe buýt 72_2B (5 trạm, 7 phút)
- Chặng 2: Xe buýt 104 (20 trạm, 22 phút)
- Tổng đi bộ: 1 đoạn

**Khuyến nghị:** Tuyến thông minh
**Tiết kiệm:** 1.505 kg CO2 (69.8%) = 549.3 kg/năm

---

### Test Case 3: Quãng dài (~29km)
**Route:** Trung tâm Hà Nội → Sân bay Nội Bài

| Tuyến | Phương thức | Thời gian | Khoảng cách | Carbon |
|-------|-------------|-----------|-------------|---------|
| Nhanh nhất | 🚗 Lái xe | 44 phút | 28.83 km | 5.536 kg |
| Ít carbon | 🚌 Xe công cộng | 1h 52m | 25.60 km | 1.741 kg |
| Thông minh | 🚌 Xe công cộng | 1h 52m | 25.60 km | 1.741 kg |

**Chi tiết xe công cộng:**
- Chặng 1: Xe buýt 86 (6 trạm, 59 phút)
- Tổng đi bộ: 1 đoạn

**Khuyến nghị:** Tuyến nhanh nhất (chênh lệch thời gian quá lớn)
**Tiết kiệm nếu chọn transit:** 3.795 kg CO2 (68.6%) = 1,385 kg/năm

---

## 🌍 Emission Factors (Vietnam)

Sử dụng dữ liệu từ Climatiq API + Electricity Maps:

| Phương thức | Emission Factor (g CO2/km) |
|-------------|----------------------------|
| 🚗 car_petrol | 192 |
| 🚗 car_diesel | 171 |
| 🚗 car_hybrid | 120 |
| 🚗 car_electric | 104 |
| 🏍️ motorbike | 84 |
| 🚌 bus_standard | 68 |
| 🚌 bus_cng | 58 |
| 🚌 bus_electric | 104 |
| 🚇 metro | 35 |
| 🚂 train_diesel | 41 |
| 🚂 train_electric | 27 |
| 🚕 taxi | 155 |
| 🚴 bicycle | 0 |
| 🚶 walking | 0 |

---

## 🎯 Recommendation Logic

```python
# Priority 1: Lowest carbon saves >50% AND reasonable time
if carbon_savings_percent > 50 and time_diff <= 50%:
    recommend = "lowest_carbon"

# Priority 2: Smart route has good balance
elif smart_route exists and saves >30% carbon:
    recommend = "smart_combination"

# Priority 3: Default to fastest
else:
    recommend = "fastest"
```

---

## 💡 Use Cases

### 1. Daily Commute
```python
result = await maps.find_three_optimal_routes(
    origin="Nhà riêng",
    destination="Văn phòng",
    max_time_ratio=1.5  # Chấp nhận chậm hơn 50%
)
# → Hiển thị 3 lựa chọn cho người dùng
```

### 2. Eco-friendly Tourism
```python
result = await maps.find_three_optimal_routes(
    origin="Khách sạn",
    destination="Điểm tham quan",
    max_time_ratio=2.0  # Du lịch không vội
)
# → Ưu tiên tuyến ít carbon
```

### 3. Business Travel
```python
result = await maps.find_three_optimal_routes(
    origin="Văn phòng",
    destination="Họp khách hàng",
    max_time_ratio=1.2  # Không thể chậm nhiều
)
# → Ưu tiên tuyến nhanh nhất
```

---

## 🧪 Testing

### Run comprehensive tests
```bash
# Test 3 tuyến với 3 khoảng cách khác nhau
python tests/test_three_optimal_routes.py

# Test chi tiết với format đẹp
python tests/test_three_routes_detailed.py
```

### Test files created
- `tests/test_three_optimal_routes.py` - Comprehensive test (3 test cases)
- `tests/test_three_routes_detailed.py` - Detailed analysis với UI đẹp

---

## 📈 Benefits

### 1. Tiết kiệm môi trường
- Walking: 100% giảm carbon
- Transit: 60-70% giảm carbon vs driving
- Yearly impact: Hàng trăm kg CO2 tiết kiệm

### 2. So sánh rõ ràng
- 3 lựa chọn với trade-offs rõ ràng
- Time vs Carbon comparison
- Transit details (số chặng, thời gian)

### 3. Smart recommendations
- Auto-select based on context
- Balanced decision making
- User-friendly explanations

### 4. Real-world data
- Vietnam-specific emission factors
- Actual Google Maps routes
- Climatiq API verified data

---

## 🚀 Future Enhancements

1. **Multi-stop routes**
   - Waypoint optimization
   - Best order calculation

2. **Time preferences**
   - Peak hour avoidance
   - Scheduled departures

3. **Cost comparison**
   - Fuel cost
   - Public transport fare
   - Parking fees

4. **Health benefits**
   - Calories burned (walking/bicycling)
   - Air quality along route

5. **Social features**
   - Share routes
   - Community recommendations
   - Popular eco-friendly routes

---

## ✅ Summary

Chức năng tìm 3 tuyến đường tối ưu giúp người dùng:
- ⚡ **Nhanh**: Tìm tuyến nhanh nhất để tiết kiệm thời gian
- 🌱 **Xanh**: Tìm tuyến ít carbon để bảo vệ môi trường  
- 🧠 **Thông minh**: Tìm tuyến cân bằng giữa thời gian và carbon

Tích hợp với:
- ✅ Google Maps API (4 travel modes)
- ✅ Climatiq API (Vietnam emission factors)
- ✅ CarbonService (emission calculation)
- ✅ Transit details (bus/train info)

**Production ready!** 🎉
