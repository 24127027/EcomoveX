# Google API Cost Optimization Guide

## � Current Status

✅ **Completed Optimizations:** $17.30/day saved ($519/month)  
🎯 **Remaining Potential:** $123.00/day ($3,690/month)  
💰 **Total Possible Savings:** $140.30/day ($4,209/month)

### Quick Links
- [Autocomplete Session Token Guide](backend/docs/AUTOCOMPLETE_SESSION_TOKEN_GUIDE.md) - **Save $119/day** 🔥
- [Completed Optimizations](#-completed-savedmonth) ✅
- [Next Steps](#-next-priorities-potential-month) 🔜

---

## �🚨 Major Cost Issues Found

### 1. **Photo URL Generation (HIGHEST COST IMPACT)**
**Location:** [map_api.py](backend/integration/map_api.py#L634-L673), [recommendation_service.py](backend/services/recommendation_service.py#L376-L380)

**Problem:**
- `get_place_details()` converts ALL 5 photos to URLs for EVERY place details request
- `text_search_place()` by default converts photo URLs even when not needed
- Photo API calls cost **$0.007 per image** (7 SKUs per 1000 requests)
- With 5 photos × multiple API calls = **35x unnecessary cost**

**Current Code:**
```python
# map_api.py lines 308-318
photos=(
    [
        PhotoInfo(
            photo_url=await self.generate_place_photo_url(
                photo.get("photo_reference")
            ),
            size=(photo.get("width"), photo.get("height")),
        )
        for photo in result.get("photos", [])[:5]  # ❌ Always converts 5 photos
        if photo.get("photo_reference")
    ]
    if result.get("photos")
    else None
),
```

**Solutions:**
- ✅ **Already partially fixed in `text_search_place`**: Has `convert_photo_urls=False` parameter
- ❌ **Still broken in `get_place_details`**: Always converts photos
- ❌ **Recommendation service**: Converts photos for ALL search results before filtering

**Recommended Fixes:**

```python
# Fix 1: Add parameter to get_place_details
async def get_place_details(
    self,
    place_id: str,
    fields: list[str],
    session_token: Optional[str] = None,
    language: str = "vi",
    convert_photo_urls: bool = True,  # ← Add this parameter
    max_photos: int = 1,  # ← Only convert first photo by default
) -> PlaceDetailsResponse:
    # ...
    photos=(
        [
            PhotoInfo(
                photo_url=await self.generate_place_photo_url(
                    photo.get("photo_reference")
                ) if convert_photo_urls else None,
                photo_reference=photo.get("photo_reference"),  # ← Keep reference
                size=(photo.get("width"), photo.get("height")),
            )
            for photo in result.get("photos", [])[:max_photos]  # ← Limit photos
            if photo.get("photo_reference")
        ]
        if result.get("photos")
        else None
    ),
```

```python
# Fix 2: Only convert photos for TOP results in recommendations
# recommendation_service.py lines 370-380
# ✅ GOOD: Already only converts for top K, but move it to frontend lazy loading
```

**Estimated Savings:** **60-80% of photo API costs**

---

### 2. **Unnecessary Place Details API Calls**
**Location:** [map_service.py](backend/services/map_service.py#L138-L200), [plan_edit_agent.py](backend/services/agents/plan_edit_agent.py#L88)

**Problem:**
- Weather service calls `get_location_details()` just to get coordinates
- Air quality service calls `get_location_details()` just to get coordinates  
- Plan edit agent does full text search for every destination added
- Place Details API costs **$0.017 per request** (Basic Data)

**Current Code:**
```python
# weather_service.py line 24
detail = await MapService.get_location_details(request_data)
# Only uses: detail.geometry.location.latitude/longitude
```

**Solution:**
Use the cheaper Geocoding API ($0.005 per request) or cached coordinates:

```python
# Add new method to MapService
@staticmethod
async def get_coordinates(place_id: str) -> Location:
    """Get ONLY coordinates - uses minimal fields (3x cheaper)"""
    map_client = await create_map_client()
    try:
        response = await map_client.get_place_details(
            place_id=place_id,
            fields=["geometry/location"],  # ← Only request coordinates
            convert_photo_urls=False,
            max_photos=0,
        )
        return response.geometry.location
    finally:
        await map_client.close()
```

**Estimated Savings:** **70% on these specific calls** (Weather, Air Quality services)

---

### 3. **Text Search Redundancy**
**Location:** [recommendation_service.py](backend/services/recommendation_service.py#L254-L271)

**Problem:**
- Searches 3-5 categories per user request
- Each search returns ~20 results
- Total: 60-100 API calls per recommendation request
- Text Search costs **$0.032 per request**
- Processes ALL results before filtering

**Current Code:**
```python
# Lines 254-271
for category in cluster_categories[:3]:  # ← 3 separate API calls
    result = await MapService.text_search_place(db, search_request, user_id, convert_photo_urls=False)
    search_results.append(result)
```

**Solution:**
1. **Cache search results** by location + radius + category (1 hour TTL)
2. **Batch categories** into single query where possible
3. **Use Nearby Search** instead of Text Search ($0.017 vs $0.032)

```python
# Option 1: Cache with Redis/in-memory
from functools import lru_cache
from datetime import datetime, timedelta

_search_cache = {}  # In production, use Redis

async def cached_search(location, radius, category):
    cache_key = f"{location.latitude}_{location.longitude}_{radius}_{category}"
    if cache_key in _search_cache:
        result, timestamp = _search_cache[cache_key]
        if datetime.now() - timestamp < timedelta(hours=1):
            return result
    
    result = await MapService.text_search_place(...)
    _search_cache[cache_key] = (result, datetime.now())
    return result
```

```python
# Option 2: Use Nearby Search instead
# map_api.py already has nearby_search_place method
# Nearby Search = $0.017 (47% cheaper than Text Search)
```

**Estimated Savings:** **50-70% on recommendation searches** with caching

---

### 4. **Routes API Excessive Alternatives**
**Location:** [route_api.py](backend/integration/route_api.py#L390-L430)

**Problem:**
- Requests alternative routes for EVERY route calculation
- Routes API costs **$0.005 per route** × 3 alternatives = **3x cost**
- Most users only use the first (fastest) route

**Current Code:**
```python
# route_api.py line 399
"computeAlternativeRoutes": data.alternatives,  # ← Default True
```

**Solution:**
Only compute alternatives when explicitly requested by user:

```python
# Change default to False
class DirectionsRequest(BaseModel):
    origin: Location
    destination: Location
    alternatives: bool = False  # ← Change default
    # ...
```

**Estimated Savings:** **66% on route calculations**

---

### 5. **Autocomplete Session Token Misuse**
**Location:** [map_api.py](backend/integration/map_api.py#L157-L215)

**Problem:**
- Session tokens reduce costs if used correctly
- Must use SAME token from autocomplete → place details
- Currently generates NEW tokens or doesn't reuse properly
- Without proper session tokens: **$0.017 per keystroke**
- With proper session tokens: **$0.017 per selection only**

**Current Code:**
```python
# autocomplete_place - line 172
params = {
    "sessiontoken": data.session_token,  # ← May be None or new token each time
}
```

**Solution:**
Implement proper session token lifecycle:

```typescript
// Frontend: Generate ONE token per autocomplete session
const sessionToken = uuidv4();  // Generate once

// Use SAME token for all autocomplete requests
onTextChange(query) => {
    api.autocomplete(query, sessionToken);
}

// Use SAME token when getting place details after selection
onPlaceSelected(placeId) => {
    api.getPlaceDetails(placeId, sessionToken);  // ← Same token
}

// Generate NEW token only after completing a selection
```

**Estimated Savings:** **80-90% on autocomplete costs** if users type 5+ characters

---

### 6. **Missing Field Masking**
**Location:** [map_api.py](backend/integration/map_api.py#L68-L78)

**Problem:**
- Place Details has tiered pricing based on fields requested:
  - Basic Data: $0.017 per request
  - Contact Data: +$0.003
  - Atmosphere Data: +$0.005
- If you request ALL fields, you pay **147% more**
- Currently requests too many fields in text search

**Current Code:**
```python
# text_search_place - line 68
selected_mask = request.field_mask if request.field_mask else default_mask
# Uses default_mask which includes photos, types, etc.
```

**Solution:**
Be strict about which fields you actually need:

```python
# Create field presets
FIELD_PRESETS = {
    "minimal": "places.id,places.displayName,places.location",  # Just basics
    "search": "places.id,places.displayName,places.location,places.types",  # For search results
    "details": "places.id,places.displayName,places.formattedAddress,places.photos,places.rating",  # For details page
    "full": "places.id,places.displayName,places.formattedAddress,places.photos,places.types,places.location,places.rating,places.openingHours",
}

# Use minimal preset for most calls
async def text_search_place(self, request: TextSearchRequest, convert_photo_urls: bool = False, preset: str = "search") -> TextSearchResponse:
    selected_mask = FIELD_PRESETS.get(preset, FIELD_PRESETS["search"])
```

**Estimated Savings:** **30-50% on place details/search costs**

---

## 💰 Cost Breakdown & Priorities

### Before Optimizations (Baseline):
```
Operation                    | Cost per call | Est. calls/day | Daily cost
----------------------------|---------------|----------------|------------
Text Search                 | $0.032        | 500            | $16.00
Place Details (full)        | $0.017        | 300            | $5.10
Photo URLs (×5)             | $0.007        | 1500 (×5)      | $10.50
Routes (×3 alternatives)    | $0.005        | 400 (×3)       | $6.00
Autocomplete (no session)   | $0.017        | 8000           | $136.00
----------------------------|---------------|----------------|------------
TOTAL (estimated)           |               |                | $173.60/day
                            |               |                | $5,208/month
```

### ✅ After Completed Optimizations:
```
Operation                      | Cost per call | Est. calls/day | Daily cost | Status
-------------------------------|---------------|----------------|------------|---------
Nearby Search (was Text)       | $0.017        | 500            | $8.50      | ✅ DONE
Place Details (1 photo, masks) | $0.017        | 300            | $5.10      | ✅ DONE
Photo URLs (×1, top K only)    | $0.007        | 100 (-93%)     | $0.70      | ✅ DONE
Routes (×3 alternatives)       | $0.005        | 400 (×3)       | $6.00      | TODO
Autocomplete (no session yet)  | $0.017        | 8000           | $136.00    | TODO
-------------------------------|---------------|----------------|------------|---------
CURRENT TOTAL                  |               |                | $156.30/day|
                               |               |                | $4,689/month|
**SAVED SO FAR**               |               |                | **$17.30/day** | **$519/month**
```

### 🎯 After ALL Optimizations (Target):
```
Operation                    | Cost per call | Est. calls/day | Daily cost | Savings
----------------------------|---------------|----------------|------------|--------
Nearby Search               | $0.017        | 500            | $8.50      | $7.50
Place Details (minimal)     | $0.017        | 300            | $5.10      | $0.00
Photo URLs (×1, lazy)       | $0.007        | 100 (-93%)     | $0.70      | $9.80
Routes (no alternatives)    | $0.005        | 400            | $2.00      | $4.00
Autocomplete (sessions)     | $0.017        | 1000 (-87%)    | $17.00     | $119.00
----------------------------|---------------|----------------|------------|--------
TARGET TOTAL                |               |                | $33.30/day | $140.30/day
                            |               |                | $999/month | **$4,209/month saved**
```

## 🎯 Implementation Status

### ✅ Completed (Saved: $17.30/day = $519/month)

1. ✅ **Switch to Nearby Search API** (30 min) - **Saving $7.50/day** ✅
2. ✅ **Limit to 1 photo instead of 5** (5 min) - **Saving $9.80/day** ✅
3. ✅ **Add field masks to text search** (10 min) - **Already included above** ✅
4. ✅ **Reduce categories from 5 to 3** (5 min) - **Already included above** ✅

### 🔜 Next Priorities (Potential: $123.00/day = $3,690/month)

1. **Implement autocomplete session tokens** (1 hour) - **Save $119.00/day**
   - See: [AUTOCOMPLETE_SESSION_TOKEN_GUIDE.md](backend/docs/AUTOCOMPLETE_SESSION_TOKEN_GUIDE.md)
   - Frontend changes required
   - Backend already supports it ✅

2. **Disable route alternatives by default** (5 min) - **Save $4.00/day**
   - Change `alternatives: bool = False` in DirectionsRequest schema
   
3. **Add Redis caching for searches** (2 hours) - **Save $8.50/day**
   - Cache nearby search results for 1 hour
   - Key: `location_radius_category`

**Total Potential Savings:** **$140.30/day = $4,209/month = $50,508/year**

---

## 📋 Quick Fixes Checklist

- [x] Set `convert_photo_urls=False` by default in all services ✅ **DONE**
- [x] Only convert first photo, not 5 photos ✅ **DONE**
- [x] Add `max_photos` parameter to `get_place_details()` ✅ **DONE**
- [x] Use Nearby Search instead of Text Search for recommendations ✅ **DONE**
- [x] Add field mask to text search requests ✅ **DONE**
- [x] Reduced categories from 5 to 3 ✅ **DONE**
- [ ] Implement session token lifecycle on frontend (See: [AUTOCOMPLETE_SESSION_TOKEN_GUIDE.md](backend/docs/AUTOCOMPLETE_SESSION_TOKEN_GUIDE.md))
- [ ] Use `get_coordinates()` instead of `get_place_details()` for weather/air quality
- [ ] Set `alternatives=False` as default in DirectionsRequest
- [ ] Add Redis/in-memory cache for search results (1 hour TTL)
- [ ] Create field mask presets (minimal, search, details)
- [ ] Implement lazy loading for photos on frontend

---

## 🔍 Monitoring Recommendations

1. **Add API cost tracking:**
```python
import time
from functools import wraps

def track_api_cost(api_name: str, cost_per_call: float):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start
            
            # Log to monitoring system
            print(f"API_COST: {api_name} | ${cost_per_call:.4f} | {duration:.2f}s")
            # TODO: Send to logging/monitoring service
            
            return result
        return wrapper
    return decorator

# Usage:
@track_api_cost("text_search", 0.032)
async def text_search_place(...):
    ...
```

2. **Set up billing alerts** in Google Cloud Console:
   - Alert at 50% of monthly budget
   - Alert at 80% of monthly budget
   - Alert at 100% of monthly budget

3. **Weekly cost review:**
   - Check which endpoints use most API calls
   - Identify unusual spikes
   - Verify caching is working

---

## 📚 Resources

- [Google Maps Platform Pricing](https://developers.google.com/maps/billing/understanding-cost-of-use)
- [Places API Field Masks](https://developers.google.com/maps/documentation/places/web-service/place-data-fields)
- [Session Tokens Guide](https://developers.google.com/maps/documentation/places/web-service/session-tokens)
- [Optimization Best Practices](https://developers.google.com/maps/optimization-guide)
