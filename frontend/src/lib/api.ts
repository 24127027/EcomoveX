const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- INTERFACES & TYPES ---

interface LoginCredentials {
  email: string;
  password: string;
}

export interface UserCredentialUpdate {
  old_password: string;
  new_email?: string;
  new_password?: string;
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

interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
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

// --- NEW TEXT SEARCH TYPES START ---
export interface LocalizedText {
  text: string;
  languageCode?: string;
}

export interface PhotoInfo {
  photo_url: string;
  size: [number, number]; // Tuple matching Python's Tuple[int, int]
}

export interface PlaceSearchResult {
  id: string; //  sends "id"
  displayName: LocalizedText; //  sends "displayName"
  formattedAddress?: string; //  sends "formattedAddress"
  location?: Position;
  types: string[];
  photos?: PhotoInfo | null;
}

export interface TextSearchRequest {
  query: string;
  location?: Position;
  radius?: number; // Integer 100-50000
  place_types?: string; // e.g., "restaurant"
  field_mask?: string[]; // Optional: ["places.id", "places.displayName"]
}

export interface TextSearchResponse {
  places: PlaceSearchResult[]; //  sends "places"
}
// --- NEW TEXT SEARCH TYPES END ---

export type PlaceDataCategory = "basic" | "contact" | "atmosphere";

export interface AutocompleteRequest {
  query: string;
  user_location?: Position;
  radius?: number; // in meters
  place_types?: string; // Comma-separated string
  language?: string;
  session_token?: string | null;
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

export interface SavedDestination {
  id: number;
  destination_id: string;
  name?: string;
  image_url?: string;
}

export interface UploadResponse {
  url: string;
  blob_name: string;
  filename: string;
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
  type: string;
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

export interface RoomResponse {
  id: number;
  name: string;
  created_at: string;
  member_ids: number[]; // Quan trọng: cần trường này để lọc
}
//REWARD & MISSION TYPES
export interface Mission {
  id: number;
  name: string;
  description: string;
  reward_type: string;
  action_trigger: string;
  value: number;
}

export interface UserRewardResponse {
  user_id: number;
  mission: Mission[];
  total_points: number;
}

//PLAN DESTINATION TYPES
export interface PlanDestination {
  id: number;
  destination_id: string;
  destination_type: string;
  visit_date: string;
  note?: string;
  url?: string;
  order_in_day?: number;
}

export interface PlanResponse {
  id: number;
  place_name: string;
  start_date: string;
  end_date: string;
  budget_limit: number;
  destinations: PlanDestination[];
}

export interface PlanActivity {
  id: number | string;
  original_id?: number;
  title: string;
  address: string;
  image_url: string;
  time_slot: "Morning" | "Afternoon" | "Evening";
  date?: string;
  type?: string;
  order_in_day?: number;
  time?: string;
}

export interface TravelPlan {
  id: number;
  destination: string;
  date: string;
  end_date?: string;
  activities: PlanActivity[];
}

export interface PlanDestinationCreate {
  id: number;
  destination_id: string;
  destination_type: string;
  order_in_day: number;
  visit_date: string;
  estimated_cost?: number;
  url?: string;
  note?: string;
}
export interface CreatePlanRequest {
  place_name: string;
  start_date: string;
  end_date?: string;
  budget_limit: number;
  destinations?: PlanDestinationCreate[];
}

export interface DestinationCard {
  tempId: number;
  destinationId: string;
  name: string;
  visitDate: string;
  type: string;
}

//--- REVIEW TYPES ---
export interface ReviewResponse {
  destination_id: string;
  rating: number;
  content: string;
  user_id: number;
  created_at: string;
  files_urls: string[];
}

export interface ReviewStatisticsResponse {
  average_rating: number;
  total_reviews: number;
  rating_distribution: Record<string, number>;
}

// --- API CLIENT CLASS ---

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

    if (!(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

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

    const fetchOptions: RequestInit = {
      ...options,
      headers: options.body instanceof FormData ? headers : headers,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, fetchOptions);

    if (!response.ok) {
      try {
        const errorData = await response.json();

        if (response.status === 422 && Array.isArray(errorData.detail)) {
          const validationErrors = errorData.detail as ValidationError[];
          const firstError = validationErrors[0];
          const fieldName = String(firstError.loc[firstError.loc.length - 1]);
          throw new ApiValidationError(fieldName, firstError.msg);
        }

        console.error(`API Error [${response.status}] ${endpoint}:`, errorData);
        throw new ApiHttpError(
          response.status,
          errorData.detail || `HTTP ${response.status}: An error occurred`
        );
      } catch (e) {
        if (e instanceof ApiValidationError) throw e;
        if (e instanceof ApiHttpError) throw e;
        console.error(`API Error [${response.status}] ${endpoint}:`, e);
        throw new Error(`HTTP ${response.status}: An error occurred`);
      }
    }

    return response.json();
  }

  // --- AUTH ENDPOINTS ---
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
    return this.request("/auth/me", { method: "GET" });
  }

  async resetPassword(email: string): Promise<void> {
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  // --- DESTINATION ENDPOINTS ---
  async getSavedDestinations(): Promise<SavedDestination[]> {
    return this.request<SavedDestination[]>("/destinations/saved/me/all", {
      method: "GET",
    });
  }

  async saveDestination(destinationId: string): Promise<any> {
    return this.request(`/destinations/saved/${destinationId}`, {
      method: "POST",
    });
  }

  async unsaveDestination(destinationId: string): Promise<void> {
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
    return this.request("/users/me", { method: "DELETE" });
  }

  async uploadFile(
    file: File,
    category: "profile_avatar" | "profile_cover" | "travel_photo"
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<UploadResponse>(`/storage/files?category=${category}`, {
      method: "POST",
      body: formData,
    });
  }
  // --- PLAN ENDPOINTS ---
  async createPlan(request: CreatePlanRequest): Promise<PlanResponse> {
    return this.request<PlanResponse>("/plans/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }
  async deletePlan(planId: number): Promise<void> {
    return this.request(`/plans/${planId}`, {
      method: "DELETE",
    });
  }

  async addDestinationToPlan(
    planId: number,
    data: PlanDestination
  ): Promise<any> {
    return this.request(`/plans/${planId}/destinations`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
  async updatePlanDestination(
    destinationId: string | number,
    planId: number,
    data: { note?: string; visit_date?: string }
  ): Promise<any> {
    return this.request(
      `/plans/destinations/${destinationId}?plan_id=${planId}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  }
  async deletePlanDestination(
    planDestinationId: number,
    planId: number
  ): Promise<void> {
    return this.request(
      `/plans/destinations/${planDestinationId}?plan_id=${planId}`,
      {
        method: "DELETE",
      }
    );
  }

  async updatePlan(
    planId: number,
    data: { place_name?: string; start_date?: string; end_date?: string }
  ): Promise<PlanResponse> {
    return this.request<PlanResponse>(`/plans/${planId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getPlans(): Promise<TravelPlan[]> {
    const plans = await this.request<PlanResponse[]>("/plans/", {
      method: "GET",
    });
    return plans.map((p) => {
      const activities = p.destinations.map((d, index) => {
        const dateObj = new Date(d.visit_date);
        const hour = dateObj.getHours();

        let slot = "Morning";
        if (hour >= 12 && hour < 18) slot = "Afternoon";
        if (hour >= 18) slot = "Evening";

        const timeString = dateObj.toLocaleTimeString("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
        });

        return {
          id: `${d.destination_id}-${index}`,
          original_id: d.id,
          title: d.note || "Destination",
          address: "",
          image_url: d.url || "",
          time_slot: slot as "Morning" | "Afternoon" | "Evening",
          date: d.visit_date,
          time: timeString,
          type: d.destination_type,
          order_in_day: d.order_in_day || 0,
        };
      });

      activities.sort((a, b) => {
        const dateA = new Date(a.date).getTime();
        const dateB = new Date(b.date).getTime();
        if (dateA !== dateB) return dateA - dateB;

        return (a.order_in_day || 0) - (b.order_in_day || 0);
      });

      return {
        id: p.id,
        destination: p.place_name,
        date: p.start_date,
        end_date: p.end_date,
        activities: activities,
      };
    });
  }

  // --- FRIEND ENDPOINTS ---
  async getFriends(): Promise<FriendResponse[]> {
    return this.request<FriendResponse[]>("/friends/", { method: "GET" });
  }

  async getPendingRequests(): Promise<FriendResponse[]> {
    return this.request<FriendResponse[]>("/friends/pending", {
      method: "GET",
    });
  }

  async getSentRequests(): Promise<FriendResponse[]> {
    return this.request<FriendResponse[]>("/friends/sent", { method: "GET" });
  }

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

  // --- MAP ENDPOINTS ---

  // Integrated Text Search Function
  async textSearchPlace(
    request: TextSearchRequest
  ): Promise<TextSearchResponse> {
    const response = await this.request<TextSearchResponse>(
      "/map/text-search",
      {
        method: "POST",
        body: JSON.stringify(request),
      }
    );
    return response;
  }

  async autocomplete(
    request: AutocompleteRequest
  ): Promise<AutocompleteResponse> {
    const response = await this.request<AutocompleteResponse>(
      "/map/autocomplete",
      {
        method: "POST",
        body: JSON.stringify(request),
      }
    );
    return response;
  }
  // --- CHAT ENDPOINTS ---
  async getDirectRoomId(partnerId: number): Promise<number> {
    const res = await this.request<{ id: number }>("/rooms/direct", {
      method: "POST",
      body: JSON.stringify({ partner_id: partnerId }),
    });
    return res.id;
  }
  async getAllRooms(): Promise<RoomResponse[]> {
    return this.request<RoomResponse[]>("/rooms/rooms", {
      method: "GET",
    });
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

  async createGroupRoom(
    name: string,
    memberIds: number[]
  ): Promise<RoomResponse> {
    return this.request<RoomResponse>("/rooms/rooms", {
      method: "POST",
      body: JSON.stringify({
        room_name: name,
        member_ids: memberIds,
      }),
    });
  }

  async getPlaceDetails(
    placeId: string,
    sessionToken?: string | null,
    categories?: PlaceDataCategory[]
  ): Promise<PlaceDetails> {
    const params = new URLSearchParams();

    if (sessionToken) {
      params.append("session_token", sessionToken);
    }

    if (categories && categories.length > 0) {
      categories.forEach((cat) => params.append("categories", cat));
    }

    const queryString = params.toString();
    const path = `/map/place/${placeId}${queryString ? `?${queryString}` : ""}`;

    return this.request<PlaceDetails>(path, { method: "GET" });
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

  // --- WEATHER & AIR ENDPOINTS ---

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
    return this.request<AirQualityResponse>(
      `/air/air-quality?lat=${lat}&lng=${lng}`,
      { method: "GET" }
    );
  }

  //REWARD & MISSION ENDPOINTS
  async getAllMissions(): Promise<Mission[]> {
    return this.request<Mission[]>("/rewards/missions", { method: "GET" });
  }

  async getUserRewards(): Promise<UserRewardResponse> {
    return this.request<UserRewardResponse>("/rewards/me/missions", {
      method: "GET",
    });
  }

  // --- REVIEW ENDPOINTS ---

  // Lấy danh sách review theo địa điểm
  async getReviewsByDestination(
    destinationId: string
  ): Promise<ReviewResponse[]> {
    return this.request<ReviewResponse[]>(
      `/reviews/destination/${destinationId}`,
      {
        method: "GET",
      }
    );
  }

  async createReview(
    destinationId: string,
    data: { rating: number; content: string },
    files: File[] = []
  ): Promise<ReviewResponse> {
    const formData = new FormData();
    formData.append("rating", String(data.rating));
    formData.append("content", data.content);

    files.forEach((file) => {
      formData.append("files", file);
    });
    return this.request<ReviewResponse>(`/reviews/${destinationId}`, {
      method: "POST",
      body: formData,
    });
  }

  async getReviewStatistics(
    destinationId: string
  ): Promise<ReviewStatisticsResponse> {
    return this.request<ReviewStatisticsResponse>(
      `/reviews/destination/${destinationId}/statistics`,
      {
        method: "GET",
      }
    );
  }

  // Xóa review
  async deleteReview(destinationId: string): Promise<void> {
    return this.request<void>(`/reviews/${destinationId}`, {
      method: "DELETE",
    });
  }
}

export const api = new ApiClient(API_BASE_URL);
