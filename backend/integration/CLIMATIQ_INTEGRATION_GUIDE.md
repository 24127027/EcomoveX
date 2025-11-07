# Climatiq API Integration Guide

## 📋 Overview

Hệ thống đã được nâng cấp để **tự động lấy emission factors từ Climatiq API** thay vì hard-code.

### Trước đây (Hard-coded):
```python
EMISSION_FACTORS_VN = {
    "car_petrol": 192,  # ❌ Giá trị cố định, phải cập nhật thủ công
    "motorbike": 84,
    ...
}
```

### Bây giờ (Climatiq API):
```python
# ✅ Tự động lấy data mới nhất từ Climatiq API
await CarbonService.refresh_emission_factors()
```

---

## 🚀 Setup

### 1. Get Climatiq API Key (FREE)

1. Đi đến: https://www.climatiq.io/
2. Sign up (miễn phí)
3. Get API key từ dashboard
4. Free tier: 5,000 requests/month (đủ dùng)

### 2. Add API Key to .env

Thêm vào file `.env`:

```env
# Climatiq API (for emission factors)
CLIMATIQ_API_KEY=your_climatiq_api_key_here
```

### 3. Test Connection

Chạy test script:

```bash
cd backend
python tests/test_climatiq_integration.py
```

---

## 💡 Usage

### Option 1: Auto-refresh on startup (RECOMMENDED)

Thêm vào `main.py`:

```python
from services.carbon_service import CarbonService

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🌍 Refreshing emission factors from Climatiq API...")
    await CarbonService.refresh_emission_factors()
    print("✅ Application started")
```

### Option 2: Manual refresh via API endpoint

Thêm router trong `routers/carbon_router.py`:

```python
@router.post("/carbon/refresh-factors")
async def refresh_emission_factors(force: bool = False):
    """
    Refresh emission factors from Climatiq API
    
    Args:
        force: Force refresh even if cached
    """
    factors = await CarbonService.refresh_emission_factors(force=force)
    
    return {
        "message": "Emission factors refreshed",
        "updated_at": datetime.now().isoformat(),
        "factors": factors
    }
```

### Option 3: Manual refresh in code

```python
from services.carbon_service import CarbonService

# Refresh (with 24h cache)
await CarbonService.refresh_emission_factors()

# Force refresh (ignore cache)
await CarbonService.refresh_emission_factors(force=True)
```

---

## 📊 How It Works

### 1. Fallback Values (Default)

Khi **KHÔNG có API key**, hệ thống dùng **hard-coded fallback values**:

```python
EMISSION_FACTORS_VN = {
    "car_petrol": 192,    # Fallback value
    "motorbike": 84,
    "bus_standard": 68,
    ...
}
```

### 2. Climatiq API (Preferred)

Khi **có API key**, hệ thống **tự động fetch** data mới nhất:

```python
# Fetch from Climatiq API
climatiq = get_climatiq_client()
fresh_factors = await climatiq.get_vietnam_transport_factors()

# Update EMISSION_FACTORS_VN
CarbonService.EMISSION_FACTORS_VN["car_petrol"] = fresh_factors["car_petrol"]
```

### 3. Caching (24 hours)

- Data được **cache 24 giờ** để giảm API calls
- Free tier: 5,000 requests/month → ~166 requests/day
- Với cache 24h: chỉ dùng **1 request/day** cho tất cả factors

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. Application Startup                                 │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  2. Call refresh_emission_factors()                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  3. Check API Key                                       │
│     ├─ NO  → Use hard-coded fallback                    │
│     └─ YES → Continue to Climatiq API                   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  4. Check Cache (24h)                                   │
│     ├─ Valid → Return cached data                       │
│     └─ Expired → Fetch from API                         │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  5. Fetch from Climatiq API                             │
│     - Search for each transport mode                    │
│     - Get latest emission factors                       │
│     - Convert units (kg → grams)                        │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  6. Update EMISSION_FACTORS_VN                          │
│     - Compare old vs new values                         │
│     - Log changes                                       │
│     - Cache for 24h                                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  7. Calculate Emissions                                 │
│     - Use updated factors                               │
│     - More accurate results                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 Benefits

### ✅ Always Up-to-date
- Emission factors được **tự động cập nhật** từ Climatiq database
- Climatiq cập nhật data từ **IPCC, IEA, government sources**

### ✅ Scientifically Verified
- Data được **verify bởi scientists**
- Tham khảo từ **peer-reviewed research**

### ✅ No Manual Updates
- **Không cần update code** khi emission standards thay đổi
- Tự động sync với **international standards**

### ✅ Cost-effective
- **Free tier**: 5,000 requests/month
- **24h cache**: ~30 requests/month
- **$0 cost** cho most use cases

### ✅ Fallback Protection
- Nếu API fail → **tự động dùng fallback values**
- **Zero downtime** khi có vấn đề với Climatiq

---

## 🧪 Testing

### Test 1: Basic Connection
```bash
python tests/test_climatiq_integration.py
```

Expected output:
```
🌍 CLIMATIQ API INTEGRATION TEST
📋 CURRENT EMISSION FACTORS (Hard-coded fallback values):
  car_petrol          :  192.0 gCO2/km
  ...

🔌 TESTING CLIMATIQ API CONNECTION:
✅ API Key found: sk_...

🔍 SEARCHING CLIMATIQ DATABASE:
✅ Found 15 results for 'passenger car petrol vietnam'
  Sample result:
    Name: Passenger car - Petrol - Vietnam
    Factor: 192.5 gCO2/km
    Source: IPCC 2019
```

### Test 2: Compare Factors
```python
import asyncio
from services.carbon_service import CarbonService

async def test():
    # Before refresh
    old = CarbonService.EMISSION_FACTORS_VN["car_petrol"]
    print(f"Old: {old} gCO2/km")
    
    # Refresh from Climatiq
    await CarbonService.refresh_emission_factors()
    
    # After refresh
    new = CarbonService.EMISSION_FACTORS_VN["car_petrol"]
    print(f"New: {new} gCO2/km")
    print(f"Change: {new - old} gCO2/km")

asyncio.run(test())
```

---

## 🔧 API Reference

### ClimatiqAPI Class

```python
from integration.climatiq_api import get_climatiq_client

client = get_climatiq_client()
```

#### Methods:

**1. search_emission_factors()**
```python
results = await client.search_emission_factors(
    query="passenger car petrol vietnam",
    region="VN",
    category="Transportation"
)
```

**2. get_vietnam_transport_factors()**
```python
factors = await client.get_vietnam_transport_factors(use_cache=True)
# Returns: {"car_petrol": 192.5, "motorbike": 84.3, ...}
```

**3. estimate_emission()**
```python
estimate = await client.estimate_emission(
    activity_id="passenger_vehicle-vehicle_type_car-fuel_source_petrol",
    parameters={"distance": 10, "distance_unit": "km"},
    region="VN"
)
```

### CarbonService Methods

**1. refresh_emission_factors()**
```python
# Refresh with 24h cache
factors = await CarbonService.refresh_emission_factors()

# Force refresh (ignore cache)
factors = await CarbonService.refresh_emission_factors(force=True)
```

**2. calculate_emission_by_mode()** (unchanged)
```python
result = await CarbonService.calculate_emission_by_mode(
    distance_km=10.0,
    mode="driving"
)
# Now uses Climatiq data instead of hard-coded!
```

---

## 🌟 Example: Full Integration

```python
from fastapi import FastAPI
from services.carbon_service import CarbonService

app = FastAPI()

@app.on_event("startup")
async def startup():
    """Refresh emission factors on startup"""
    print("🌍 Loading latest emission factors...")
    await CarbonService.refresh_emission_factors()
    print("✅ Ready!")

@app.get("/")
async def root():
    # Calculate emission using fresh Climatiq data
    emission = await CarbonService.calculate_emission_by_mode(
        distance_km=10.0,
        mode="driving"
    )
    
    return {
        "message": "Using real Climatiq data!",
        "emission": emission
    }
```

---

## ❓ FAQ

### Q: API key có miễn phí không?
**A:** Có! Free tier: 5,000 requests/month (đủ dùng với 24h cache)

### Q: Nếu không có API key thì sao?
**A:** Hệ thống tự động dùng hard-coded fallback values (như trước)

### Q: Bao lâu data được update?
**A:** Climatiq update data định kỳ từ IPCC/IEA sources. Hệ thống cache 24h.

### Q: API call có chậm không?
**A:** Cache 24h → chỉ call API 1 lần/ngày → không ảnh hưởng performance

### Q: Có thể force refresh không?
**A:** Có! `await CarbonService.refresh_emission_factors(force=True)`

---

## 📞 Support

- Climatiq Docs: https://www.climatiq.io/docs
- API Explorer: https://www.climatiq.io/explorer
- Support: support@climatiq.io

---

**Created:** 2025-11-07  
**Last Updated:** 2025-11-07
