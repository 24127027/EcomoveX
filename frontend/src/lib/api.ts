import { types } from "util";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface LoginCredentials {
  email: string;
  password: string;
}

export interface UserCredentialUpdate {
  password?: string;
}

interface SignupData {
  username: string;
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  email: string;
}

interface ApiError {
  detail: string;
}

interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

interface ValidationErrorResponse {
  detail?: string | ValidationError[];
}
// User Types
export interface UserProfileUpdate {
  username?: string;
  avt_blob_name?: string | null;
  cover_blob_name?: string | null;
}
export interface UserProfile {
  id: number;
  username: string;
  email: string;
  avt_url?: string | null;
  cover_url?: string | null;
  role?: string;
}

//Friend Types
export interface FriendResponse {
  user_id: number;
  friend_id: number;
  status: string;
  created_at: string;
}
// Map/Location Types
export interface Position {
  lat: number;
  lng: number;
}

export interface SearchPlacesRequest {
  query: string;
  user_location?: Position; 
  radius?: number; // in meters
  place_types?: string; // Comma-separated string
  language?: string;
}
export interface AutocompletePrediction {
  place_id: string;
  description: string;
  structured_formatting?: Record<string, any>;
  types: string[];
  matched_substrings?: Array<Record<string, any>>;
  distance?: number;
}
export interface AutocompleteResponse {
  predictions: AutocompletePrediction[];
}

export interface PlaceDetails {
  place_id: string;
  name: string;
  formatted_address: string;
  address_components?: Array<{
    name: string;
    types: string[];
  }>;
  formatted_phone_number?: string;
  geometry: {
    location: Position;
    bounds?: {
      northeast: Position;
      southwest: Position;
    };
  };
  types: string[];
  rating?: number;
  user_ratings_total?: number;
  price_level?: number;
  opening_hours?: {
    open_now: boolean;
    periods?: Array<Record<string, any>>;
    weekday_text?: string[];
  };
  website?: string;
  photos?: Array<{
    photo_url: string;
    width: number;
    height: number;
  }>;
  reviews?: Array<Record<string, any>>;
  utc_offset?: number;
  sustainable_certified: boolean;
}
export interface ReverseGeocodeResponse {
  results: Array<{
    formatted_address: string;
    address_components?: Array<{
      name: string;
      types: string[];
    }>;
    place_id: string;
    geometry: {
      location: Position;
    };
    types: string[];
  }>;
}

export interface PhotoUrlResponse {
  photo_url: string;
}

export interface SavedDestination {
  id: number; // ID in DB saved_destinations
  destination_id: string; // ID Google Place
  name?: string;
  image_url?: string;
}

export interface UserCredentialUpdate {
  old_password: string; // Bắt buộc
  new_email?: string; // Optional
  new_password?: string; // Optional
}

export interface UploadResponse {
  url: string;
  blob_name: string;
  filename: string;
}

export interface PlanActivity {
  id: number;
  title: string;
  address: string;
  image_url: string;
  time_slot: "Morning" | "Afternoon" | "Evening";
}

export interface TravelPlan {
  id: number;
  destination: string;
  date: string; // e.g., "Day 1"
  activities: PlanActivity[];
}

export class ApiValidationError extends Error {
  constructor(public field: string, public message: string) {
    super(message);
    this.name = "ApiValidationError";
  }
}

export class ApiHttpError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiHttpError";
  }
}

// --- WEATHER & AIR TYPES ---

export interface WeatherCondition {
  description: string;
  icon_base_uri: string;
  type: string; // VD: "CLEAR", "CLOUDY", "RAINY"
}

export interface Temperature {
  temperature: number;
  feelslike_temperature: number;
  max_temperature?: number;
  min_temperature?: number;
}

export interface CurrentWeatherResponse {
  temperature: Temperature;
  weather_condition: WeatherCondition;
  humidity: number;
  cloud_cover: number;
  is_daytime: boolean;
}

export interface AirQualityIndex {
  display_name: string;
  aqi: number;
  category: string;
}

export interface AirQualityResponse {
  location: [number, number];
  aqi_data: AirQualityIndex;
  // recommendations: ... (Có thể thêm nếu cần)
}

//Chat Types
export interface ChatMessage {
  id: number;
  sender_id: number;
  room_id: number;
  content: string;
  timestamp: string;
  message_type: string;
}

const parseMockDate = (dateStr: string) => {
  const [day, month, year] = dateStr.split("/").map(Number);
  return new Date(year, month - 1, day);
};

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;

    const headers = new Headers();

    // Only set Content-Type if not FormData
    if (!(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    // merge any provided headers (Headers | string[][] | Record<string, string>)
    if (options.headers) {
      if (options.headers instanceof Headers) {
        options.headers.forEach((value, key) => headers.set(key, value));
      } else if (Array.isArray(options.headers)) {
        (options.headers as [string, string][]).forEach(([key, value]) =>
          headers.set(key, value)
        );
      } else {
        Object.entries(options.headers as Record<string, string>).forEach(
          ([key, value]) => headers.set(key, value)
        );
      }
    }

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    // If FormData, let browser set Content-Type (with boundary)
    const fetchOptions: RequestInit = {
      ...options,
      headers: options.body instanceof FormData ? headers : headers,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, fetchOptions);

    if (!response.ok) {
      try {
        const errorData = await response.json();

        // Handle FastAPI validation errors (422)
        if (response.status === 422 && Array.isArray(errorData.detail)) {
          const validationErrors = errorData.detail as ValidationError[];
          const firstError = validationErrors[0];
          const fieldName = String(firstError.loc[firstError.loc.length - 1]);
          throw new ApiValidationError(fieldName, firstError.msg);
        }

        // Handle other error responses
        console.error(`API Error [${response.status}] ${endpoint}:`, errorData);
        throw new ApiHttpError(
          response.status,
          errorData.detail || `HTTP ${response.status}: An error occurred`
        );
      } catch (e) {
        if (e instanceof ApiValidationError) {
          throw e;
        }
        if (e instanceof ApiHttpError) {
          throw e;
        }
        console.error(`API Error [${response.status}] ${endpoint}:`, e);
        throw new Error(`HTTP ${response.status}: An error occurred`);
      }
    }

    return response.json();
  }

  // Auth endpoints
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  }

  async signup(data: SignupData): Promise<AuthResponse> {
    return this.request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async logout(): Promise<void> {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_id");
    }
  }

  async getCurrentUser(): Promise<any> {
    return this.request("/auth/me", {
      method: "GET",
    });
  }

  // Add more endpoints as needed
  async resetPassword(email: string): Promise<void> {
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  //Saved Destinantions Endpoint
  async getSavedDestinations(): Promise<SavedDestination[]> {
    return this.request<SavedDestination[]>("/destinations/saved/me/all", {
      method: "GET",
    });
  }

  async unsaveDestination(destinationId: number): Promise<void> {
    return this.request(`/destinations/saved/${destinationId}`, {
      method: "DELETE",
    });
  }

  // --- USER ENDPOINTS ---

  async getUserProfile(): Promise<UserProfile> {
    return this.request<UserProfile>("/users/me", { method: "GET" });
  }

  async updateUserProfile(data: UserProfileUpdate): Promise<UserProfile> {
    return this.request<UserProfile>("/users/me/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async updateCredentials(data: UserCredentialUpdate): Promise<any> {
    return this.request("/users/me/credentials", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteUser(): Promise<void> {
    return this.request("/users/me", {
      method: "DELETE",
    });
  }

  async uploadFile(
    file: File,
    category: "profile_avatar" | "profile_cover" | "travel_photo"
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    // Gọi endpoint POST /storage/files với query params category (lowercase)
    return this.request<UploadResponse>(`/storage/files?category=${category}`, {
      method: "POST",
      body: formData,
    });
  }

  async getPlans(): Promise<TravelPlan[]> {
    // Giả lập delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    return [
      {
        id: 201,
        destination: "Ho Chi Minh City (Upcoming)",
        date: "30/11/2025", // Ngày tương lai (Sẽ là Current Plan)
        activities: [
          {
            id: 1,
            title: "Thảo Cầm Viên",
            address: "2 Nguyen Binh Khiem, D1",
            image_url:
              "https://images.unsplash.com/photo-1596263576925-48c581d6a90a?q=80&w=200",
            time_slot: "Morning",
          },
        ],
      },
      {
        id: 101,
        destination: "District 1 (Past)",
        date: "04/01/2026",
        activities: [],
      },
      {
        id: 102,
        destination: "District 5 (Past)",
        date: "01/01/2023",
        activities: [],
      },
    ];
  }

  // Friend Endpoints

  async getFriends(): Promise<FriendResponse[]> {
    return this.request<FriendResponse[]>("/friends/", {
      method: "GET",
    });
  }

  async getPendingRequests(): Promise<FriendResponse[]> {
    return this.request<FriendResponse[]>("/friends/pending", {
      method: "GET",
    });
  }

  async getSentRequests(): Promise<FriendResponse[]> {
    return this.request<FriendResponse[]>("/friends/sent", {
      method: "GET",
    });
  }
  // -----------------------

  async sendFriendRequest(friendId: number): Promise<FriendResponse> {
    return this.request<FriendResponse>(`/friends/${friendId}/request`, {
      method: "POST",
    });
  }

  async acceptFriendRequest(friendId: number): Promise<FriendResponse> {
    return this.request<FriendResponse>(`/friends/${friendId}/accept`, {
      method: "POST",
    });
  }

  async rejectFriendRequest(friendId: number): Promise<any> {
    return this.request<void>(`/friends/${friendId}/reject`, {
      method: "DELETE",
    });
  }

  async unfriend(friendId: number): Promise<any> {
    return this.request(`/friends/${friendId}`, { method: "DELETE" });
  }

  // Map Endpoints
  async searchPlaces(request: SearchPlacesRequest): 
    Promise<AutocompleteResponse> {
      const response = await this.request<AutocompleteResponse>("/map/search", {
        method: "POST",
        body: JSON.stringify(request),
      });
      return response;
    }

  async getPlaceDetails(placeId: string): Promise<PlaceDetails> {
    return this.request<PlaceDetails>(`/map/place/${placeId}`, {
      method: "GET",
    });
  }

  async geocodeAddress(address: string): Promise<ReverseGeocodeResponse> {
    return this.request<ReverseGeocodeResponse>("/map/geocode", {
      method: "POST",
      body: JSON.stringify({ address }),
    });
  }

  async reverseGeocode(position: Position): Promise<ReverseGeocodeResponse> {
    return this.request<ReverseGeocodeResponse>("/map/reverse-geocode", {
      method: "POST",
      body: JSON.stringify(position),
    });
  }

  async birdDistance(
    origin: Position,
    destination: Position
  ): Promise<number> {
    const params = new URLSearchParams({
      origin_lat: origin.lat.toString(),
      origin_lng: origin.lng.toString(),
      destination_lat: destination.lat.toString(),
      destination_lng: destination.lng.toString(),
    });
    return this.request<number>(`/map/bird-distance?${params.toString()}`, {
      method: "GET",
    });
  }

  async getDirectRoomId(partnerId: number): Promise<number> {
    const res = await this.request<{ id: number }>("/rooms/direct", {
      method: "POST",
      body: JSON.stringify({ partner_id: partnerId }),
    });
    return res.id;
  }

  async getChatHistory(roomId: number): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/messages/room/${roomId}`, {
      method: "GET",
    });
  }

  getWebSocketUrl(roomId: number): string {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("access_token") : "";

    let host = process.env.NEXT_PUBLIC_API_URL || "localhost:8000";
    host = host.replace("http://", "").replace("https://", "");
    if (host.endsWith("/")) {
      host = host.slice(0, -1);
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${host}/messages/ws/${roomId}?token=${token}`;
  }

  async getCurrentWeather(
    lat: number,
    lng: number
  ): Promise<CurrentWeatherResponse> {
    return this.request<CurrentWeatherResponse>(
      `/weather/current?lat=${lat}&lng=${lng}&unit_system=METRIC`,
      { method: "GET" }
    );
  }

  async getAirQuality(lat: number, lng: number): Promise<AirQualityResponse> {
    // Gọi endpoint /air/air-quality
    return this.request<AirQualityResponse>(
      `/air/air-quality?lat=${lat}&lng=${lng}`,
      { method: "GET" }
    );
  }
}

export const api = new ApiClient(API_BASE_URL);
