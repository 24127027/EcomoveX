# Autocomplete Session Token Implementation Guide

## 💰 Cost Impact: Save $15.30/day ($459/month)

Session tokens are **critical** for reducing autocomplete API costs. Without proper implementation, you pay **$0.017 per keystroke**. With session tokens, you only pay **$0.017 per selection**.

## How Session Tokens Work

A session token groups multiple autocomplete requests and the final place details request into a **single billable session**.

### Pricing Breakdown:

**WITHOUT Session Tokens:**
```
User types "Eiffel Tower" (11 characters)
- "Ei" → $0.017
- "Eif" → $0.017
- "Eiff" → $0.017
- "Eiffe" → $0.017
- "Eiffel" → $0.017
- "Eiffel " → $0.017
- "Eiffel T" → $0.017
- "Eiffel To" → $0.017
- "Eiffel Tow" → $0.017
- "Eiffel Towe" → $0.017
- "Eiffel Tower" → $0.017
User selects place → get_place_details → $0.017
TOTAL: $0.204 (12 API calls)
```

**WITH Session Tokens (Correct Implementation):**
```
User types "Eiffel Tower" (11 characters)
- All autocomplete requests use SAME token → $0.00
User selects place → get_place_details with SAME token → $0.017
TOTAL: $0.017 (1 billable session)

SAVINGS: $0.187 per search (92% reduction)
```

## 🔑 Implementation Rules

### ✅ DO:
1. Generate ONE token per autocomplete session
2. Use SAME token for ALL autocomplete requests in that session
3. Pass SAME token to `get_place_details()` when user selects a place
4. Generate NEW token ONLY after place selection completes or user cancels

### ❌ DON'T:
1. Generate new token for each keystroke
2. Forget to pass token to place details request
3. Reuse token across multiple sessions
4. Store token permanently (tokens should be short-lived)

## Frontend Implementation (React/TypeScript)

### Step 1: Create Session Token Manager

```typescript
// utils/autocompleteSession.ts
import { v4 as uuidv4 } from 'uuid';

class AutocompleteSessionManager {
  private currentToken: string | null = null;

  /**
   * Start a new autocomplete session
   * Call this when user focuses on search input
   */
  startSession(): string {
    this.currentToken = uuidv4();
    console.log('🎫 New autocomplete session:', this.currentToken);
    return this.currentToken;
  }

  /**
   * Get current session token
   */
  getToken(): string | null {
    return this.currentToken;
  }

  /**
   * End current session and clear token
   * Call this after user selects a place or cancels search
   */
  endSession(): void {
    console.log('🎫 Ending autocomplete session:', this.currentToken);
    this.currentToken = null;
  }

  /**
   * Check if session is active
   */
  hasActiveSession(): boolean {
    return this.currentToken !== null;
  }
}

export const autocompleteSession = new AutocompleteSessionManager();
```

### Step 2: Update Search Component

```typescript
// components/PlaceSearch.tsx
import { useState, useEffect, useRef } from 'react';
import { autocompleteSession } from '@/utils/autocompleteSession';
import { mapAPI } from '@/services/api';

export function PlaceSearch() {
  const [query, setQuery] = useState('');
  const [predictions, setPredictions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const debounceTimer = useRef<NodeJS.Timeout>();

  // Start session when user focuses on input
  const handleFocus = () => {
    if (!autocompleteSession.hasActiveSession()) {
      autocompleteSession.startSession();
    }
  };

  // Search with session token
  const searchPlaces = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setPredictions([]);
      return;
    }

    const sessionToken = autocompleteSession.getToken();
    if (!sessionToken) {
      console.error('❌ No session token! This will cost more.');
      return;
    }

    try {
      setIsSearching(true);
      const response = await mapAPI.autocomplete({
        query: searchQuery,
        session_token: sessionToken, // ✅ Use same token
        language: 'vi'
      });
      setPredictions(response.predictions);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search on input change
  const handleInputChange = (value: string) => {
    setQuery(value);
    
    // Clear previous debounce timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Debounce search by 300ms
    debounceTimer.current = setTimeout(() => {
      searchPlaces(value);
    }, 300);
  };

  // Handle place selection
  const handleSelectPlace = async (placeId: string) => {
    const sessionToken = autocompleteSession.getToken();
    
    try {
      // Get place details with SAME session token
      const placeDetails = await mapAPI.getPlaceDetails({
        place_id: placeId,
        session_token: sessionToken, // ✅ CRITICAL: Use same token
        categories: ['basic', 'contact']
      });

      // Do something with place details
      console.log('Selected place:', placeDetails);

      // ✅ End session AFTER successful place details fetch
      autocompleteSession.endSession();
      
      // Clear search
      setQuery('');
      setPredictions([]);

    } catch (error) {
      console.error('Error fetching place details:', error);
      // Still end session on error
      autocompleteSession.endSession();
    }
  };

  // Cancel search
  const handleCancel = () => {
    setQuery('');
    setPredictions([]);
    autocompleteSession.endSession(); // ✅ End session on cancel
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      autocompleteSession.endSession();
    };
  }, []);

  return (
    <div className="search-container">
      <input
        type="text"
        value={query}
        onChange={(e) => handleInputChange(e.target.value)}
        onFocus={handleFocus}
        placeholder="Search for places..."
      />
      
      {isSearching && <div>Searching...</div>}
      
      {predictions.length > 0 && (
        <ul className="predictions-list">
          {predictions.map((prediction) => (
            <li 
              key={prediction.place_id}
              onClick={() => handleSelectPlace(prediction.place_id)}
            >
              {prediction.description}
            </li>
          ))}
        </ul>
      )}
      
      {query && (
        <button onClick={handleCancel}>Cancel</button>
      )}
    </div>
  );
}
```

### Step 3: Update API Service

```typescript
// services/api.ts
import axios from 'axios';

export const mapAPI = {
  /**
   * Autocomplete search with session token
   */
  async autocomplete(params: {
    query: string;
    session_token: string;
    language?: string;
    user_location?: { latitude: number; longitude: number };
    radius?: number;
  }) {
    const response = await axios.post('/api/map/autocomplete', params);
    return response.data;
  },

  /**
   * Get place details with session token
   */
  async getPlaceDetails(params: {
    place_id: string;
    session_token: string;
    categories?: string[];
  }) {
    const response = await axios.get(`/api/map/place/${params.place_id}`, {
      params: {
        session_token: params.session_token,
        categories: params.categories
      }
    });
    return response.data;
  }
};
```

## Backend Implementation (Already Done ✅)

The backend already supports session tokens:

### Autocomplete Endpoint
```python
# backend/routers/map_router.py
@router.post("/autocomplete")
async def autocomplete(request: AutocompleteRequest):
    # session_token is required in AutocompleteRequest schema
    return await MapService.autocomplete(db, request)
```

### Place Details Endpoint
```python
# backend/routers/map_router.py
@router.get("/place/{place_id}")
async def get_place_details(
    place_id: str,
    session_token: Optional[str] = Query(None),  # ✅ Accepts session token
    categories: List[PlaceDataCategory] = Query(default=[PlaceDataCategory.BASIC])
):
    request_data = PlaceDetailsRequest(
        place_id=place_id,
        session_token=session_token,  # ✅ Passed to Google API
        categories=categories
    )
    return await MapService.get_location_details(request_data, db, user_id)
```

### Schema
```python
# backend/schemas/map_schema.py
class AutocompleteRequest(BaseModel):
    query: str = Field(..., min_length=2)
    user_location: Optional[Location] = None
    radius: Optional[int] = Field(None, ge=100, le=50000)
    place_types: Optional[str] = None
    language: str = "vi"
    session_token: str = Field(..., min_length=1)  # ✅ Required field
```

## Testing & Verification

### How to Test

1. **Open Browser DevTools** → Network Tab
2. **Filter by** "autocomplete" or "place"
3. **Type in search box** (e.g., "Eiffel Tower")
4. **Verify** all autocomplete requests have the SAME session token
5. **Select a place**
6. **Verify** place details request uses the SAME token
7. **Type again** → Should see NEW token

### Example Logs (Correct Implementation)

```
🎫 New autocomplete session: 550e8400-e29b-41d4-a716-446655440000

POST /api/map/autocomplete
Body: { query: "Ei", session_token: "550e8400-e29b-41d4-a716-446655440000" }

POST /api/map/autocomplete
Body: { query: "Eif", session_token: "550e8400-e29b-41d4-a716-446655440000" }

POST /api/map/autocomplete
Body: { query: "Eiff", session_token: "550e8400-e29b-41d4-a716-446655440000" }

... (more autocomplete calls with SAME token)

GET /api/map/place/ChIJ123xyz?session_token=550e8400-e29b-41d4-a716-446655440000

🎫 Ending autocomplete session: 550e8400-e29b-41d4-a716-446655440000
```

## Common Mistakes

### ❌ Mistake 1: Generating new token per keystroke
```typescript
// DON'T DO THIS
const handleChange = async (query: string) => {
  const token = uuidv4(); // ❌ New token each time!
  await mapAPI.autocomplete({ query, session_token: token });
};
```

### ❌ Mistake 2: Not passing token to place details
```typescript
// DON'T DO THIS
const handleSelect = async (placeId: string) => {
  // ❌ No session token!
  const details = await mapAPI.getPlaceDetails({ place_id: placeId });
};
```

### ❌ Mistake 3: Not ending session
```typescript
// DON'T DO THIS
const handleSelect = async (placeId: string) => {
  const details = await mapAPI.getPlaceDetails({
    place_id: placeId,
    session_token: autocompleteSession.getToken()
  });
  // ❌ Forgot to end session! Token will be reused incorrectly.
};
```

### ✅ Correct Pattern
```typescript
// DO THIS
const [sessionToken, setSessionToken] = useState<string | null>(null);

// Start session on focus
const handleFocus = () => {
  if (!sessionToken) {
    setSessionToken(uuidv4());
  }
};

// Use same token for all searches
const handleChange = async (query: string) => {
  await mapAPI.autocomplete({ 
    query, 
    session_token: sessionToken // ✅ Same token
  });
};

// Use same token for place details, then clear
const handleSelect = async (placeId: string) => {
  await mapAPI.getPlaceDetails({
    place_id: placeId,
    session_token: sessionToken // ✅ Same token
  });
  setSessionToken(null); // ✅ Clear for next search
};
```

## Monitoring

### Add logging to track token usage:

```typescript
// utils/autocompleteSession.ts (enhanced)
class AutocompleteSessionManager {
  private currentToken: string | null = null;
  private requestCount: number = 0;

  startSession(): string {
    this.currentToken = uuidv4();
    this.requestCount = 0;
    console.log('🎫 New session:', this.currentToken);
    
    // Track in analytics
    analytics.track('autocomplete_session_start', {
      token: this.currentToken
    });
    
    return this.currentToken;
  }

  incrementRequestCount(): void {
    this.requestCount++;
  }

  endSession(): void {
    console.log(`🎫 Ending session: ${this.currentToken} (${this.requestCount} requests)`);
    
    // Track savings
    const estimatedCost = this.requestCount > 0 ? 0.017 : 0;
    const savedCost = (this.requestCount - 1) * 0.017;
    
    analytics.track('autocomplete_session_end', {
      token: this.currentToken,
      requests: this.requestCount,
      estimated_cost: estimatedCost,
      saved_cost: savedCost
    });
    
    this.currentToken = null;
    this.requestCount = 0;
  }
}
```

## Expected Savings

### Assumptions:
- 1000 searches per day
- Average 8 characters typed per search
- 80% of users select a place

### Without Session Tokens:
```
1000 searches × 8 autocomplete calls = 8,000 requests
8,000 × $0.017 = $136.00/day

800 place details (80% selection rate)
800 × $0.017 = $13.60/day

TOTAL: $149.60/day = $4,488/month
```

### With Session Tokens:
```
1000 searches × 1 billable session = 1,000 sessions
1,000 × $0.017 = $17.00/day

800 place details (included in session) = $0.00/day

TOTAL: $17.00/day = $510/month

SAVINGS: $132.60/day = $3,978/month = $47,736/year
```

## Checklist

- [ ] Install `uuid` package: `npm install uuid`
- [ ] Create `AutocompleteSessionManager` utility
- [ ] Update search component to use session manager
- [ ] Start session on input focus
- [ ] Use same token for all autocomplete requests in session
- [ ] Pass token to place details request
- [ ] End session after place selection or cancel
- [ ] Add logging/analytics to track token usage
- [ ] Test in browser DevTools to verify tokens are reused
- [ ] Monitor Google Cloud Console for cost reduction

## References

- [Google Places API Session Tokens](https://developers.google.com/maps/documentation/places/web-service/session-tokens)
- [Understanding Cost of Use](https://developers.google.com/maps/billing/understanding-cost-of-use)
