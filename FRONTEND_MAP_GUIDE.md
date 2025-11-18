# Frontend Map Integration Guide

## Overview

You now have a fully functional frontend map page that works independently without the backend. This guide explains how to use it and how your colleague can integrate it with the backend later.

## 🚀 Current Status

✅ **Frontend Map Page** - Fully implemented

- Google Maps integration with search functionality
- Location details display with photos and ratings
- Click-to-search on map
- Real-time suggestions as you type
- Mock data for testing without backend

⏳ **Backend Integration** - Ready for your colleague

- API endpoints documented
- Expected data structures defined
- Type definitions ready for backend

---

## 📋 What's Implemented

### Frontend Components

#### 1. **Map Page** (`src/app/(main)/map_page/page.tsx`)

Main component that provides:

- Google Map display centered on Ho Chi Minh City
- Search box for finding locations
- Real-time search suggestions
- Detailed place cards showing:
  - Place name and address
  - Rating and number of reviews
  - Phone number
  - Website link
  - Opening hours status
  - Photos
  - Place categories/types
- Click-to-place-marker on map
- Reverse geocoding (click map → get address)

#### 2. **API Client** (`src/lib/api.ts`)

Added new methods for map functionality:

- `searchPlaces(query: string)` - Search for locations
- `getPlaceDetails(placeId: string)` - Get detailed place info
- `reverseGeocode(coords: Position)` - Convert coordinates to address
- `getPhotoUrl(photoReference: string)` - Get photo URLs

#### 3. **Mock API** (`src/lib/mockApi.ts`)

Provides mock data for development:

- 3 sample places (Saigon Zoo, War Remnants Museum, Ben Thanh Market)
- Mock search, place details, and reverse geocoding

---

## 🔧 How to Use

### Development Mode (Without Backend)

1. **Enable mock mode** by setting environment variable:

```bash
NEXT_PUBLIC_MOCK_API=true
```

Or in `.env.local`:

```
NEXT_PUBLIC_MOCK_API=true
```

2. **The app will automatically use mock data** when this is enabled

3. **Test the features:**
   - Type "zoo" or "museum" in search box
   - Click on suggestions
   - Click on the map to see reverse geocoding
   - View place details with ratings and photos

### Production Mode (With Backend)

Once your colleague implements the backend:

1. **Remove or set** `NEXT_PUBLIC_MOCK_API=false`

2. **Real API calls will be made** instead

3. **No frontend code changes needed** - it's already set up!

---

## 🔌 Backend Integration Guide for Your Colleague

Your colleague needs to implement these endpoints:

### Endpoint 1: Search Places

```
POST /map/search
Body: { query: string }
Response: {
  predictions: [
    {
      place_id: string,
      description: string,
      types: string[],
      // ... other fields
    }
  ]
}
```

### Endpoint 2: Get Place Details

```
GET /map/place/{place_id}
Response: {
  place_id: string,
  name: string,
  formatted_address: string,
  location: { lat: number, lng: number },
  geometry?: { location: { ... } },
  rating?: number,
  user_ratings_total?: number,
  photos?: [{ photo_reference: string, ... }],
  formatted_phone_number?: string,
  website?: string,
  types: string[],
  opening_hours?: { open_now: boolean, ... }
}
```

### Endpoint 3: Reverse Geocode

```
POST /map/reverse-geocode
Body: { lat: number, lng: number }
Response: {
  results: [
    {
      formatted_address: string,
      place_id: string,
      types: string[],
      // ... other fields
    }
  ]
}
```

### Endpoint 4: Get Photo URL

```
POST /map/photo
Body: { photo_reference: string, max_width: number }
Response: {
  photo_url: string
}
```

---

## 📁 File Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api.ts              ← Main API client with map methods
│   │   └── mockApi.ts          ← Mock data for testing
│   └── app/
│       └── (main)/
│           └── map_page/
│               ├── page.tsx    ← Main map component
│               └── map.module.css
```

---

## 🎨 Features

### Search Functionality

- **Real-time suggestions** as user types (with 300ms debounce)
- **Autocomplete** - Shows matching locations
- **Click to select** - Clicking a suggestion loads its details

### Map Interaction

- **Clickable map** - Click anywhere to get the address
- **Marker placement** - Shows current selected location
- **Auto-zoom** - Zooms to place details when selected
- **Smooth camera movement** - Animated map transitions

### Place Details

- **Photo display** - Shows place image
- **Rating and reviews** - Displays star rating and review count
- **Contact info** - Phone number when available
- **Website link** - Clickable link to official website
- **Hours status** - Shows if place is currently open
- **Categories** - Shows place types/categories
- **Address display** - Full formatted address

### UX Features

- **Loading states** - Shows spinner during API calls
- **Error handling** - Graceful error messages
- **Empty states** - Clear feedback when no results
- **Responsive design** - Works on mobile and desktop

---

## 🔄 Mock Data

The mock API includes 3 Vietnamese attractions:

1. **Saigon Zoo** (Thảo Cầm Viên Sài Gòn)

   - Location: District 1, HCMC
   - Rating: 4.3/5 (5234 reviews)

2. **War Remnants Museum** (Bảo Tàng Chứng Tích Chiến Tranh)

   - Location: District 3, HCMC
   - Rating: 4.6/5 (8945 reviews)

3. **Ben Thanh Market** (Chợ Bến Thành)
   - Location: District 1, HCMC
   - Rating: 4.1/5 (12567 reviews)

To add more mock data, edit `src/lib/mockApi.ts`

---

## 🧪 Testing Checklist

- [ ] Map loads without errors
- [ ] Search box accepts input
- [ ] Suggestions appear after typing 3+ characters
- [ ] Clicking suggestion loads place details
- [ ] Place details card displays correctly
- [ ] Can close place details card
- [ ] Click on map adds marker
- [ ] Reverse geocoding works (click map)
- [ ] Photos load and display
- [ ] Rating and reviews show
- [ ] Phone numbers display properly
- [ ] Website links work
- [ ] Opening hours status shows
- [ ] Types/categories display
- [ ] Marker moves when selecting new place

---

## 🔐 Environment Variables

Add to `.env.local`:

```
# Google Maps API
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_api_key_here

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mock Mode (for development without backend)
NEXT_PUBLIC_MOCK_API=true
```

---

## 🚀 Deployment Notes

### Frontend Only (Current)

- No backend required
- Uses mock data
- Good for UI/UX development and testing

### With Backend (After integration)

- Backend needs to implement the 4 endpoints
- Frontend will automatically switch to real API calls
- No frontend code changes needed

---

## 📝 Type Definitions

All types are properly defined in `src/lib/api.ts`:

```typescript
interface Position {
  lat: number;
  lng: number;
}

interface PlaceDetails {
  place_id: string;
  name: string;
  formatted_address: string;
  location: Position;
  rating?: number;
  user_ratings_total?: number;
  photos?: Array<{ photo_reference: string; width: number; height: number }>;
  // ... more fields
}

interface AutocompletePrediction {
  place_id: string;
  description: string;
  types: string[];
  // ... more fields
}

// ... more interfaces
```

Your colleague can use these to implement the backend with correct types.

---

## 🐛 Troubleshooting

### Map not showing

- Check `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is set
- Verify API key has Maps JavaScript API enabled
- Check browser console for errors

### Suggestions not appearing

- Make sure you typed at least 3 characters
- Check network tab if in real API mode
- Verify `NEXT_PUBLIC_MOCK_API=true` if using mock

### Photos not loading

- Check photo_reference is valid
- Backend should return valid image URL
- Mock API returns placeholder images

### No results in search

- Check search query matches mock data
- Mock data has "zoo", "museum", "market" keywords
- In real mode, backend should handle search

---

## 📞 Integration Checklist for Your Colleague

When implementing the backend:

- [ ] Create `/map/search` endpoint
- [ ] Create `/map/place/{place_id}` endpoint
- [ ] Create `/map/reverse-geocode` endpoint (POST)
- [ ] Create `/map/photo` endpoint
- [ ] Return data in same format as frontend expects
- [ ] Include CORS headers for frontend
- [ ] Test each endpoint with Postman
- [ ] Handle errors gracefully
- [ ] Add error logs
- [ ] Document API in Swagger/OpenAPI

---

## 💡 Next Steps

1. **Test current implementation** with mock mode
2. **Review the types** in `api.ts` with your colleague
3. **Share backend requirements** from the Integration Guide
4. **Wait for colleague** to implement endpoints
5. **Switch to real mode** once backend is ready
6. **Test end-to-end** integration

---

## 📚 Related Files

- `src/lib/api.ts` - API client definition
- `src/lib/mockApi.ts` - Mock data for testing
- `src/app/(main)/map_page/page.tsx` - Main component
- `src/app/(main)/map_page/map.module.css` - Styles

---

## ✨ Features Ready for Backend

The frontend is ready for these additional features once backend is implemented:

- **Air quality data** - Pollution levels on map
- **Route planning** - Multi-transport mode routes
- **EV charging** - Find electric vehicle chargers
- **Bike sharing** - Locate bike rental stations
- **Distance matrix** - Calculate distances between locations
- **Traffic information** - Real-time traffic data

These are already defined in types but not yet used in UI.

---

## 🎯 Summary

✅ **What You Have:**

- Fully working map page frontend
- All API methods defined
- Mock data for testing
- Type-safe implementation
- Ready for backend integration

✅ **What Your Colleague Needs to Do:**

- Implement 4 REST API endpoints
- Return data matching defined types
- Ensure CORS is configured
- Test with frontend

✅ **How to Switch Modes:**

- Development: `NEXT_PUBLIC_MOCK_API=true`
- Production: `NEXT_PUBLIC_MOCK_API=false` (with real backend)

**The frontend is complete and independent. Backend can be added anytime without frontend changes!**
