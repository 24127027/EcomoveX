# 🌍 Emission Factors: Web vs API

## Tóm tắt nhanh

### ❓ Câu hỏi: "Đang lấy emission factor từ web hay API?"

**Câu trả lời:** 

Hiện tại hệ thống hỗ trợ **CÁ 2 phương pháp**:

| Phương pháp | Source | Trạng thái | Độ chính xác |
|------------|--------|-----------|-------------|
| **1. Hard-coded (Fallback)** | Climatiq Web → Copy vào code | ✅ Đang dùng | 📊 Static |
| **2. Climatiq API (Mới)** | Real-time từ Climatiq API | 🆕 Mới thêm | 📈 Dynamic |

---

## 📊 Chi tiết 2 phương pháp

### 1️⃣ Hard-coded (Phương pháp hiện tại)

#### Cách hoạt động:
```
Developer → Vào Climatiq Web → Copy emission factors → Paste vào code
```

#### Code:
```python
# File: services/carbon_service.py
EMISSION_FACTORS_VN = {
    "car_petrol": 192,    # ← Copy từ web Climatiq
    "motorbike": 84,      # ← Copy từ web Climatiq
    "bus_standard": 68,   # ← Copy từ web Climatiq
    # ... 20+ modes
}
```

#### Ưu điểm:
- ✅ Không cần API key
- ✅ Không tốn API quota
- ✅ Luôn hoạt động (offline)
- ✅ Fast (không có network latency)

#### Nhược điểm:
- ❌ Phải update code thủ công khi data thay đổi
- ❌ Có thể outdated
- ❌ Tốn công maintain

---

### 2️⃣ Climatiq API (Phương pháp mới - RECOMMENDED)

#### Cách hoạt động:
```
Application startup → Call Climatiq API → Get latest factors → Auto-update code
```

#### Code:
```python
# File: services/carbon_service.py
@app.on_event("startup")
async def startup():
    # Tự động fetch data mới nhất từ Climatiq API
    await CarbonService.refresh_emission_factors()
```

#### Ưu điểm:
- ✅ **Always up-to-date** (tự động sync với Climatiq database)
- ✅ **Scientifically verified** (IPCC, IEA sources)
- ✅ **Zero maintenance** (không cần update code)
- ✅ **Free tier available** (5,000 requests/month)
- ✅ **24h cache** → chỉ 1 API call/day
- ✅ **Fallback protection** (dùng hard-coded nếu API fail)

#### Nhược điểm:
- ⚠️ Cần API key (FREE, sign up tại climatiq.io)
- ⚠️ Cần internet connection (1 lần/24h)

---

## 🚀 Migration Path (Khuyến nghị)

### Phase 1: Current (Hard-coded) ← BẠN Ở ĐÂY
```
✅ Works offline
❌ Manual updates needed
```

### Phase 2: Hybrid (Recommended)
```
✅ API key → Fetch from Climatiq
❌ No API key → Use hard-coded fallback
```

### Phase 3: Full API (Production)
```
✅ Always use fresh Climatiq data
✅ Hard-coded only as emergency fallback
```

---

## 💡 Hướng dẫn Setup (5 phút)

### Bước 1: Get FREE API key

1. Đi đến: https://www.climatiq.io/
2. Sign up (email + password)
3. Vào Dashboard → Copy API key
4. Free tier: **5,000 requests/month** (đủ dùng!)

### Bước 2: Add to .env file

```env
# File: backend/.env
CLIMATIQ_API_KEY=your_api_key_here
```

### Bước 3: Enable auto-refresh

Thêm vào `main.py`:

```python
from services.carbon_service import CarbonService

@app.on_event("startup")
async def startup_event():
    """Load latest emission factors on startup"""
    print("🌍 Refreshing emission factors from Climatiq API...")
    await CarbonService.refresh_emission_factors()
    print("✅ Ready!")
```

### Bước 4: Test

```bash
cd backend
python tests/test_climatiq_integration.py
```

Expected output:
```
✅ API Key found
🔄 REFRESHING EMISSION FACTORS FROM CLIMATIQ API:
  📊 car_petrol: 192.0 → 192.5 gCO2/km (+0.3%)
  📊 motorbike: 84.0 → 84.2 gCO2/km (+0.2%)
  ...
✅ Emission factors refreshed from Climatiq API (12 modes)
```

---

## 🎯 Recommended Approach

Dùng **HYBRID** (cả 2 phương pháp):

```python
# 1. Hard-coded fallback (luôn có)
EMISSION_FACTORS_VN = {
    "car_petrol": 192,  # Fallback nếu API fail
    ...
}

# 2. Auto-refresh từ Climatiq API (nếu có key)
async def startup():
    if settings.CLIMATIQ_API_KEY:
        await CarbonService.refresh_emission_factors()
        # → Update EMISSION_FACTORS_VN với data mới
    else:
        print("Using fallback emission factors")
```

### Why Hybrid?

| Scenario | Behavior |
|----------|----------|
| ✅ Có API key + Internet | Use **Climatiq API** (latest data) |
| ⚠️ Có API key + No Internet | Use **hard-coded fallback** |
| ⚠️ No API key | Use **hard-coded fallback** |
| ❌ API error/timeout | Use **hard-coded fallback** |

→ **100% uptime guarantee!**

---

## 📈 Impact Analysis

### Scenario: 10,000 users/day calculating emissions

#### Method 1: Hard-coded only
```
API calls: 0
Accuracy: Static (may be outdated)
Maintenance: Manual code updates
Cost: $0
```

#### Method 2: Climatiq API with 24h cache
```
API calls: 1/day = 30/month (FREE tier: 5,000/month)
Accuracy: Always latest from IPCC/IEA
Maintenance: Zero (automatic)
Cost: $0 (within free tier)
```

**Winner:** Method 2 (Climatiq API) 🏆

---

## 🔍 Data Sources Comparison

### Hard-coded (Current)
```
Climatiq Web (manually copied)
  ↓
  ├─ IPCC 2019 Guidelines
  ├─ IEA Statistics
  └─ Vietnam MONRE
  
Last updated: When developer manually updates code
```

### Climatiq API (New)
```
Climatiq API (auto-sync)
  ↓
  ├─ IPCC 2019/2023 Guidelines (updated regularly)
  ├─ IEA Statistics (monthly updates)
  ├─ National GHG Inventories (yearly)
  ├─ Academic Research (peer-reviewed)
  └─ Government Sources (official data)
  
Last updated: Every 24h automatically
```

---

## 📝 Files Created

| File | Purpose |
|------|---------|
| `integration/climatiq_api.py` | Climatiq API client |
| `tests/test_climatiq_integration.py` | Test script |
| `integration/CLIMATIQ_INTEGRATION_GUIDE.md` | Detailed guide |
| `integration/EMISSION_FACTORS_README.md` | This file |

---

## 🎓 Quick Start Guide

### If you have 2 minutes:
```bash
# 1. Get API key from climatiq.io
# 2. Add to .env:
echo "CLIMATIQ_API_KEY=your_key" >> .env

# 3. Test:
python tests/test_climatiq_integration.py
```

### If you have 5 minutes:
Read: `CLIMATIQ_INTEGRATION_GUIDE.md`

### If you have 10 minutes:
1. Get API key
2. Setup auto-refresh in `main.py`
3. Test with real calculations
4. Compare old vs new factors

---

## ✅ Recommendation

**TL;DR:** 

1. ✅ **Get FREE Climatiq API key** (5 minutes)
2. ✅ **Add to .env file**
3. ✅ **Enable auto-refresh on startup**
4. ✅ **Keep hard-coded values as fallback**

→ Best of both worlds: **Always accurate + 100% uptime**

---

## 📞 Questions?

- 📚 Climatiq Docs: https://www.climatiq.io/docs
- 🔍 Data Explorer: https://www.climatiq.io/data/explorer
- 📧 Support: support@climatiq.io
- 💬 Our team: Check `CLIMATIQ_INTEGRATION_GUIDE.md`

---

**Last Updated:** November 7, 2025  
**Status:** ✅ Ready to use  
**Free Tier:** 5,000 requests/month
