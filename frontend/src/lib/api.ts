const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- UTILITY FUNCTIONS ---

export const birdDistance = (pos1: { lat: number; lng: number }, pos2: { lat: number; lng: number }): number => {
  const toRad = (value: number) => (value * Math.PI) / 180;
  const R = 6371; // Earth's radius in km
  const dLat = toRad(pos2.lat - pos1.lat);
  const dLon = toRad(pos2.lng - pos1.lng);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(pos1.lat)) *
      Math.cos(toRad(pos2.lat)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

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
  role?: "Admin" | "User" | string;
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
  role: string;
}

// Preference Types

export interface PreferenceUpdate {
  weather_pref?: {
    climate?: "warm" | "cool" | "cold" | "any";
  } | null;
  attraction_types?: string[] | null;
  budget_range?: {
    level?: "low" | "mid" | "luxury";
  } | null;
  kids_friendly?: boolean | null;
  visited_destinations?: string[] | null;
  embedding?: number[] | null;
  weight?: number | null;
  cluster_id?: number | null;
}

//GREEN TYPE
export interface GreenVerificationResponse {
  green_score: number;
  status: "Green Certified" | "AI Green Verified" | "Not Green Verified";
}
//==========================================================================================
// Clustering Types
export interface ClusteringStats {
  embeddings_updated: number;
  users_clustered: number;
  associations_created: number;
  clusters_updated: number;
}

export interface ClusteringResultResponse {
  success: boolean;
  message: string;
  stats: ClusteringStats;
}
//==========================================================================================
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

export type TransportModeType =
  | "car"
  | "motorbike"
  | "walking"
  | "metro"
  | "bus"
  | "train";

export interface RouteLocation {
  lat: number;
  lng: number;
}

export type RouteTypeOption = "fastest" | "low_carbon" | "smart_combination";

export interface RouteStepDetails {
  distance: number;
  duration: number;
  start_location: Position;
  end_location: Position;
  travel_mode: TransportModeType;
  polyline?: string;
}

export interface RouteLegDetails {
  distance: number;
  duration: number;
  steps: RouteStepDetails[];
}

export interface RouteDetails {
  overview_polyline: string;
  legs: RouteLegDetails[];
}

export interface RouteOption {
  type: RouteTypeOption | string;
  mode: TransportModeType[];
  distance: number;
  duration: number;
  carbon: number;
  route_details: RouteDetails;
}

export interface FindRoutesResponse {
  origin: RouteLocation;
  destination: RouteLocation;
  routes: Record<RouteTypeOption | string, RouteOption>;
  recommendation: string;
}

// --- NEW TEXT SEARCH TYPES START ---
export interface LocalizedText {
  text: string;
  languageCode?: string;
}

export interface AutocompleteMatchedSubstring {
  length: number;
  offset: number;
}

export interface AutocompleteStructuredFormatting {
  main_text: string;
  secondary_text?: string;
  main_text_matched_substrings?: AutocompleteMatchedSubstring[];
  secondary_text_matched_substrings?: AutocompleteMatchedSubstring[];
}

export interface PhotoInfo {
  photo_url: string;
  size: [number, number]; // Tuple matching Python's Tuple[int, int]
}

export interface GreenPlaceRecommendation {
  place_id: string;
  destination_id?: string | null;
  name: string;
  formatted_address: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  rating?: number;
  combined_score?: number;
  photo_url?: string;
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
  convert_photo_urls?: boolean; // Convert photo references to full URLs (default: true)
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
  place_types?: string;
  language?: string;
  session_token?: string | null;
}

export interface AutocompletePrediction {
  place_id: string;
  description: string;
  structured_formatting?: AutocompleteStructuredFormatting;
  types: string[];
  matched_substrings?: AutocompleteMatchedSubstring[];
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
    periods?: OpeningHoursPeriod[];
    weekday_text?: string[];
  };
  website?: string;
  photos?: Array<{
    photo_url: string;
    width: number;
    height: number;
  }>;
  reviews?: PlaceReview[];
  utc_offset?: number;
  sustainable_certificate:
    | "Green Certified"
    | "AI Green Verified"
    | "Not Green Verified";
}

export interface OpeningHoursPeriodEndpoint {
  day: number;
  time: string;
}

export interface OpeningHoursPeriod {
  open: OpeningHoursPeriodEndpoint;
  close?: OpeningHoursPeriodEndpoint;
}

export interface PlaceReview {
  author_name: string;
  rating: number;
  relative_time_description?: string;
  text?: string;
  time?: number;
  profile_photo_url?: string;
  files_urls?: string[]; 
  created_at?: string;
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

// Destination certificate/verification types
export type GreenVerifiedStatus =
  | "Green Certified"
  | "Not Green Verified"
  | "AI Green Verified";

export interface DestinationWithCertificate {
  place_id: string;
  green_verified: GreenVerifiedStatus;
}

export interface CertificateUpdateRequest {
  destination_id: string;
  new_status: GreenVerifiedStatus;
}

export interface ExternalApiCheckResult {
  destination_id: string;
  passed: boolean;
  score?: number;
  details?: string;
}

export interface AiCheckResult {
  destination_id: string;
  verified: boolean;
  confidence?: number;
  green_score?: number;
}

export interface UploadResponse {
  url: string;
  blob_name: string;
  filename: string;
}

export interface ApiMessageResponse {
  detail?: string;
  message?: string;
  email?: string;
  [key: string]: unknown;
}

// Route Types for Plans
export interface RouteForPlanResponse {
  origin: string;
  destination: string;
  distance_km: number;
  estimated_travel_time_min: number;
  carbon_emission_kg: number;
  route_polyline: string;
  transport_mode: string;
  route_type: string;
}

export interface RouteResponse {
  id: number;
  plan_id: number;
  origin_plan_destination_id: number;
  destination_plan_destination_id: number;
  distance_km: number;
  carbon_emission_kg: number;
  mode: string;
}

export interface PlanBasicInfo {
  id: number;
  place_name: string;
  budget_limit: number | null;
}

type PlanListResponse =
  | { plans: Array<number | PlanBasicInfo> }
  | Array<number | PlanBasicInfo>;

export interface PlanDestinationResponse {
  id: number;
  destination_id: string;
  type: string;
  destination_type?: string;
  order_in_day: number;
  visit_date: string;
  estimated_cost?: number | null;
  url?: string | null;
  note?: string | null;
  time_slot: string;
}

// Backend Plan Response Type (matches PlanResponse from backend)
export interface Plan {
  id: number;
  user_id: number;
  place_name: string;
  start_date: string; // date string
  end_date: string; // date string
  budget_limit: number | null;
  destinations: PlanDestinationResponse[];
  route?: RouteForPlanResponse[] | null;
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
  plan_id?: number;
}

export interface RoomResponse {
  id: number;
  name: string;
  created_at: string;
  member_ids: number[];
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
  time_slot: string;
  note?: string;
  url?: string;
  order_in_day?: number;
}

export interface PlanResponse {
  id: number;
  user_id: number;
  place_name: string;
  start_date: string;
  end_date: string;
  budget_limit: number;
  destinations: PlanDestination[];
}

// Member management interfaces
export interface PlanMember {
  id: number;
  email: string;
  display_name?: string;
}

export interface PlanMemberDetail {
  user_id: number;
  plan_id: number;
  role: "owner" | "member";
  joined_at: string;
  username?: string;
  email?: string;
}

export interface PlanMemberResponse {
  plan_id: number;
  members: PlanMemberDetail[];
}

export interface AddMemberRequest {
  ids: number[];
}

export interface PlanActivity {
  id: number | string;
  original_id?: number | string;
  destination_id?: string;
  title: string;
  address: string;
  image_url: string;
  time_slot: "Morning" | "Afternoon" | "Evening";
  date?: string;
  type?: string;
  order_in_day?: number;
  time?: string;
  day?: number;
  lat?: number;
  lng?: number;
}

export interface TravelPlan {
  id: number;
  user_id?: number;
  destination: string;
  date: string;
  end_date?: string;
  activities: PlanActivity[];
  budget?: number;
  budget_limit?: number;
}

export interface PlanDestinationCreate {
  id: number;
  destination_id: string;
  destination_type: string;
  order_in_day: number;
  visit_date: string;
  time_slot: "morning" | "afternoon" | "evening";
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

export interface UpdatePlanRequest {
  place_name?: string;
  start_date?: string;
  end_date?: string;
  budget_limit?: number;
  destinations?: PlanDestinationCreate[];
}

export interface PlanGenerationDestination {
  destination_id: string;
  destination_type: string;
  visit_date: string;
  order_in_day: number;
  time_slot: string;
  note?: string;
  estimated_cost?: number;
  url?: string;
}

export interface GeneratedPlanPayload {
  place_name: string;
  start_date: string;
  end_date: string;
  budget_limit?: number;
  destinations: PlanGenerationDestination[];
}

export interface PlanGenerationResponse {
  success: boolean;
  message?: string;
  detail?: string;
  plan?: GeneratedPlanPayload;
  warnings?: string[];
  modifications?: string[];
}

export interface BotMessageResponse {
  response: string;
  room_id: number;
  metadata?: {
    intent?: "plan_edit" | "plan_query" | "chit_chat" | string;
    raw?: any;
    [key: string]: any;
  };
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

// --- ADMIN TYPES ---
export interface UserFilterParams {
  role?: string;
  status?: string;
  search?: string;
  created_from?: string;
  created_to?: string;
  skip?: number;
  limit?: number;
}

export interface AdminUserResponse extends UserProfile {
  eco_point: number;
  rank: string;
  created_at?: string;
  last_login?: string;
}

export interface DashboardStats {
  total_users: number;
  active_destinations: number;
  pending_reviews: number;
  eco_impact_score: number;
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
      cache: "no-store", // ✅ Disable cache để luôn lấy data mới nhất
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, fetchOptions);
    console.log("BASE URL:", this.baseURL);
    console.log("ENDPOINT:", endpoint);
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

  async getCurrentUser(): Promise<UserProfile> {
    return this.request<UserProfile>("/auth/me", { method: "GET" });
  }

  async resetPassword(email: string, username: string): Promise<{ message: string }> {
    const params = new URLSearchParams({
      email: email,
      user_name: username,
    });
    return this.request<{ message: string }>(`/auth/forgot-password?${params.toString()}`, {
      method: "POST",
    });
  }

  // --- DESTINATION ENDPOINTS ---
  async getSavedDestinations(): Promise<SavedDestination[]> {
    return this.request<SavedDestination[]>("/destinations/saved/me/all", {
      method: "GET",
    });
  }

  async saveDestination(destinationId: string): Promise<SavedDestination> {
    return this.request<SavedDestination>(
      `/destinations/saved/${destinationId}`,
      {
        method: "POST",
      }
    );
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

  async getUserByEmail(email: string): Promise<UserProfile> {
    return this.request<UserProfile>(
      `/users/email/${encodeURIComponent(email)}`,
      {
        method: "GET",
      }
    );
  }

  async getUserByUsername(username: string): Promise<UserProfile> {
    return this.request<UserProfile>(
      `/users/username/${encodeURIComponent(username)}`,
      {
        method: "GET",
      }
    );
  }

  async getUserById(userId: number): Promise<UserProfile> {
    return this.request<UserProfile>(`/users/id/${userId}`, {
      method: "GET",
    });
  }

  async updateUserProfile(data: UserProfileUpdate): Promise<UserProfile> {
    return this.request<UserProfile>("/users/me/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async updateCredentials(
    data: UserCredentialUpdate
  ): Promise<ApiMessageResponse> {
    return this.request<ApiMessageResponse>("/users/me/credentials", {
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
  private extractPlanIdsFromPayload(
    payload: PlanListResponse | null | undefined
  ): number[] {
    if (!payload) return [];
    const planArray = Array.isArray(payload) ? payload : payload.plans;
    if (!Array.isArray(planArray)) return [];

    const ids = planArray
      .map((plan) => {
        if (typeof plan === "number") {
          return plan;
        }

        if (plan && typeof plan === "object" && "id" in plan) {
          const typedPlan = plan as PlanBasicInfo;
          return typeof typedPlan.id === "number" ? typedPlan.id : null;
        }

        return null;
      })
      .filter((id): id is number => typeof id === "number");

    return Array.from(new Set(ids));
  }

  private async fetchPlanIdsFromApi(): Promise<number[]> {
    try {
      const response = await this.request<PlanListResponse>("/plans/", {
        method: "GET",
      });
      return this.extractPlanIdsFromPayload(response);
    } catch (error) {
      console.error("Failed to fetch plan IDs", error);
      return [];
    }
  }

  private async fetchPlansByIds(planIds: number[]): Promise<Plan[]> {
    if (!planIds.length) {
      return [];
    }

    const planPromises = planIds.map(async (planId) => {
      try {
        return await this.getPlanDetails(planId);
      } catch (error) {
        console.error(`Failed to fetch plan ${planId}`, error);
        return null;
      }
    });

    const results = await Promise.all(planPromises);
    return results.filter((plan): plan is Plan => Boolean(plan));
  }

  private transformPlanToTravelPlan(plan: Plan): TravelPlan {
    const planStartDate = new Date(`${plan.start_date}T00:00:00`);

    const normalizeTimeSlot = (
      slot: string
    ): "Morning" | "Afternoon" | "Evening" => {
      const lower = (slot || "morning").toLowerCase();
      if (lower === "afternoon") return "Afternoon";
      if (lower === "evening") return "Evening";
      return "Morning";
    };

    const activities = (plan.destinations || []).map((d, index) => {
      const dateObj = new Date(d.visit_date);
      const slot = normalizeTimeSlot(d.time_slot || "morning");

      const timeString = dateObj.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
      });

      const actDateOnly = new Date(dateObj);
      actDateOnly.setHours(0, 0, 0, 0);

      const baseDate = new Date(planStartDate);
      baseDate.setHours(0, 0, 0, 0);

      const diffDays = Math.round(
        (actDateOnly.getTime() - baseDate.getTime()) / (1000 * 60 * 60 * 24)
      );
      const dayIndex = diffDays + 1;

      return {
        id: `${d.destination_id}-${index}`,
        original_id: d.id,
        destination_id: d.destination_id,
        title: d.note || "Destination",
        address: "",
        image_url: d.url || "",
        time_slot: slot,
        date: d.visit_date,
        time: timeString,
        type: d.type || d.destination_type || "",
        order_in_day: d.order_in_day ?? 0,
        day: dayIndex >= 1 ? dayIndex : 1,
      };
    });

    activities.sort((a, b) => {
      const dateA = new Date(a.date!).getTime();
      const dateB = new Date(b.date!).getTime();
      if (dateA !== dateB) return dateA - dateB;

      return (a.order_in_day || 0) - (b.order_in_day || 0);
    });

    return {
      id: plan.id,
      user_id: plan.user_id,
      destination: plan.place_name,
      date: plan.start_date,
      end_date: plan.end_date,
      budget_limit: plan.budget_limit ?? undefined,
      activities,
    };
  }

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
  ): Promise<PlanDestination> {
    return this.request<PlanDestination>(`/plans/${planId}/destinations`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
  async updatePlanDestination(
    destinationId: string | number,
    planId: number,
    data: { note?: string; visit_date?: string }
  ): Promise<PlanDestination> {
    return this.request<PlanDestination>(
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
    data: UpdatePlanRequest
  ): Promise<PlanResponse> {
    return this.request<PlanResponse>(`/plans/${planId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async joinPlan(planId: number): Promise<void> {
    await this.request(`/plans/${planId}/join`, {
      method: "POST",
    });
  }

  async sendPlanInvitation(
    userId: number,
    roomId: number,
    planId: number
  ): Promise<ChatMessage> {
    const formData = new FormData();
    formData.append("user_id", userId.toString());
    formData.append("plan_id", planId.toString());
    formData.append("message_type", "plan_invitation");
    formData.append("content", "Invitation to join plan");

    return this.request<ChatMessage>(`/messages/${roomId}`, {
      method: "POST",
      body: formData,
    });
  }

  async acceptInvitation(messageId: number): Promise<void> {
    await this.request(`/messages/invitations/${messageId}/respond`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action: "accepted" }),
    });
  }

  async declineInvitation(messageId: number): Promise<void> {
    await this.request(`/messages/${messageId}/decline`, {
      method: "PUT",
    });
  }

  async getInvitationStatus(
    messageId: number
  ): Promise<{ status: string; plan_id: number }> {
    return this.request(`/messages/invitations/${messageId}`, {
      method: "GET",
    });
  }

  // --- PLAN MEMBER ENDPOINTS ---
  async getPlanMembers(planId: number): Promise<PlanMemberResponse> {
    return this.request<PlanMemberResponse>(`/plans/${planId}/members`, {
      method: "GET",
    });
  }

  async addPlanMembers(
    planId: number,
    memberIds: number[]
  ): Promise<PlanMemberResponse> {
    return this.request<PlanMemberResponse>(`/plans/${planId}/members`, {
      method: "POST",
      body: JSON.stringify({ ids: memberIds }),
    });
  }

  // ✅ Add members with roles (for auto-adding owner)
  async addPlanMembersWithRoles(
    planId: number,
    members: Array<{ user_id: number; role: string }>
  ): Promise<PlanMemberResponse> {
    return this.request<PlanMemberResponse>(`/plans/${planId}/members`, {
      method: "POST",
      body: JSON.stringify({ ids: members }),
    });
  }

  async removePlanMembers(planId: number, memberIds: number[]): Promise<void> {
    return this.request(`/plans/${planId}/members`, {
      method: "DELETE",
      body: JSON.stringify({ ids: memberIds }),
    });
  }

  // Get raw plans from backend (for track pages)
  async getRawPlans(): Promise<Plan[]> {
    const planIds = await this.fetchPlanIdsFromApi();
    return this.fetchPlansByIds(planIds);
  }

  async leavePlan(planId: number): Promise<void> {
    const profile = await this.getUserProfile();
    return this.removePlanMembers(planId, [profile.id]);
  }

  async getPlans(): Promise<TravelPlan[]> {
    const detailedPlans = await this.getRawPlans();
    return detailedPlans.map((plan) => this.transformPlanToTravelPlan(plan));
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

  async sendFriendRequestByUsername(username: string): Promise<FriendResponse> {
    return this.request<FriendResponse>(`/friends/request/by-username`, {
      method: "POST",
      body: JSON.stringify({ username }),
    });
  }

  async acceptFriendRequest(friendId: number): Promise<FriendResponse> {
    return this.request<FriendResponse>(`/friends/${friendId}/accept`, {
      method: "POST",
    });
  }

  async rejectFriendRequest(friendId: number): Promise<ApiMessageResponse> {
    return this.request<ApiMessageResponse>(`/friends/${friendId}/reject`, {
      method: "DELETE",
    });
  }

  async unfriend(friendId: number): Promise<ApiMessageResponse> {
    return this.request<ApiMessageResponse>(`/friends/${friendId}`, {
      method: "DELETE",
    });
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
    return this.request<RoomResponse[]>("/rooms/", {
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
    return this.request<RoomResponse>("/rooms/", {
      method: "POST",
      body: JSON.stringify({
        name: name,
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

  // --- RECOMMENDATION ENDPOINTS ---

  async getNearbyGreenPlaces(
    lat: number,
    lng: number,
    radiusKm: number = 5,
    k: number = 10
  ): Promise<TextSearchResponse> {
    return this.request<TextSearchResponse>(
      `/recommendations/user/me/nearby-by-cluster?latitude=${lat}&longitude=${lng}&radius_km=${radiusKm}&k=${k}`,
      { method: "GET" }
    );
  }

  async getPersonalizedRecommendations(
    k: number = 5
  ): Promise<{ recommendation: string[] }> {
    return this.request<{ recommendation: string[] }>(
      `/recommendations/user/me/cluster-affinity?k=${k}`,
      { method: "GET" }
    );
  }

  async getPlanChatRoom(planId: number): Promise<{ room_id: number }> {
    return this.request<{ room_id: number }>(`/plans/${planId}/chat-room`, {
      method: "GET",
    });
  }

  // --- CARBON EMISSIONS ---
  async estimateCarbon(
    transportMode: "car" | "motorbike" | "bus" | "walking" | "metro" | "train",
    distanceKm: number,
    passengers: number = 1
  ): Promise<number> {
    return this.request<number>(
      `/carbon/estimate?transport_mode=${transportMode}&distance_km=${distanceKm}&passengers=${passengers}`,
      {
        method: "POST",
      }
    );
  }

  // --- ROUTES ---
  async findOptimalRoutes(params: {
    origin: RouteLocation;
    destination: RouteLocation;
    maxTimeRatio?: number;
    language?: string;
  }): Promise<FindRoutesResponse> {
    const { origin, destination, maxTimeRatio = 1.3, language = "vi" } = params;

    return this.request<FindRoutesResponse>("/routes/find-optimal", {
      method: "POST",
      body: JSON.stringify({
        origin: { lat: origin.lat, lng: origin.lng },
        destination: { lat: destination.lat, lng: destination.lng },
        max_time_ratio: maxTimeRatio,
        language,
      }),
    });
  }

  // Get all plans (basic info only for track page)
  async getAllPlansBasic(): Promise<{ plans: PlanBasicInfo[] }> {
    const detailedPlans = await this.getRawPlans();
    return {
      plans: detailedPlans.map((plan) => ({
        id: plan.id,
        place_name: plan.place_name,
        budget_limit: plan.budget_limit ?? null,
      })),
    };
  }

  // Get routes for a specific plan
  async getPlanRoutes(planId: number): Promise<RouteResponse[]> {
    return this.request<RouteResponse[]>(`/plans/${planId}/routes`, {
      method: "GET",
    });
  }

  // Get plan details with destinations
  async getPlanDetails(planId: number): Promise<Plan> {
    return this.request<Plan>(`/plans/${planId}`, {
      method: "GET",
    });
  }

  // --- CHATBOT & AI ---
  async generatePlan(
    planData: GeneratedPlanPayload
  ): Promise<PlanGenerationResponse> {
    return this.request<PlanGenerationResponse>("/chatbot/plan/generate", {
      method: "POST",
      body: JSON.stringify(planData),
    });
  }

  async sendBotMessage(
    userId: number,
    roomId: number,
    message: string
  ): Promise<BotMessageResponse> {
    return this.request<BotMessageResponse>("/chatbot/message", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, room_id: roomId, message }),
    });
  }

  async sendMessage(
    roomId: number,
    content?: string,
    file?: File,
    planId?: number,
    messageType: "text" | "file" | "plan_invitation" = "text"
  ): Promise<ChatMessage> {
    const formData = new FormData();
    if (content) formData.append("content", content);
    if (file) formData.append("message_file", file);
    if (planId) formData.append("plan_id", String(planId));
    formData.append("message_type", messageType);

    return this.request<ChatMessage>(`/messages/${roomId}`, {
      method: "POST",
      body: formData,
    });
  }

  // --- ADMIN ENDPOINTS ---

  // List all users with filters (Admin only)
  async listAllUsers(filters?: UserFilterParams): Promise<AdminUserResponse[]> {
    const params = new URLSearchParams();
    if (filters?.role) params.append("role", filters.role);
    if (filters?.status) params.append("status", filters.status);
    if (filters?.search) params.append("search", filters.search);
    if (filters?.created_from)
      params.append("created_from", filters.created_from);
    if (filters?.created_to) params.append("created_to", filters.created_to);
    if (filters?.skip !== undefined)
      params.append("skip", String(filters.skip));
    if (filters?.limit !== undefined)
      params.append("limit", String(filters.limit));

    const queryString = params.toString();
    return this.request<AdminUserResponse[]>(
      `/users/users${queryString ? `?${queryString}` : ""}`,
      { method: "GET" }
    );
  }

  // Delete user by ID (Admin only)
  async adminDeleteUser(userId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/users/${userId}`, {
      method: "DELETE",
    });
  }

  // Add eco points to a user (Admin only)
  async addEcoPointsToUser(
    userId: number,
    points: number
  ): Promise<UserProfile> {
    return this.request<UserProfile>(
      `/users/${userId}/eco_point/add?point=${points}`,
      { method: "POST" }
    );
  }
//==========================================================================================
  // Clustering: Trigger user clustering
  async triggerClustering(): Promise<ClusteringResultResponse> {
    return this.request<ClusteringResultResponse>('/clustering/run', {
      method: 'POST',
    });
  }
//==========================================================================================
  // Get all reviews (for moderation)
  async getAllReviews(): Promise<ReviewResponse[]> {
    return this.request<ReviewResponse[]>("/reviews/me", { method: "GET" });
  }

  // Get all missions (Admin)
  async adminGetAllMissions(): Promise<Mission[]> {
    return this.request<Mission[]>("/rewards/missions", { method: "GET" });
  }

  // Create mission (Admin only)
  async createMission(data: {
    name: string;
    description: string;
    reward_type: string;
    action_trigger: string;
    value: number;
  }): Promise<Mission> {
    return this.request<Mission>("/rewards/missions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Update mission (Admin only)
  async updateMission(
    missionId: number,
    data: {
      name?: string;
      description?: string;
      reward_type?: string;
      action_trigger?: string;
      value?: number;
    }
  ): Promise<Mission> {
    return this.request<Mission>(`/rewards/missions/${missionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // Delete mission (Admin only)
  async deleteMission(missionId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/rewards/missions/${missionId}`, {
      method: "DELETE",
    });
  }

  // Admin update user password (Admin only)
  async adminUpdatePassword(
    userId: number,
    newPassword: string
  ): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/users/${userId}/password`, {
      method: "PUT",
      body: JSON.stringify({ new_password: newPassword }),
    });
  }

  // Admin update user role (Admin only)
  async adminUpdateRole(userId: number, newRole: string): Promise<UserProfile> {
    return this.request<UserProfile>(`/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify({ new_role: newRole }),
    });
  }

  // --- ADMIN DESTINATION/CERTIFICATE ENDPOINTS ---

  // Get all destinations (Admin only)
  async adminGetAllDestinations(params?: {
    skip?: number;
    limit?: number;
    verified_status?: GreenVerifiedStatus;
  }): Promise<DestinationWithCertificate[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined)
      queryParams.append("skip", String(params.skip));
    if (params?.limit !== undefined)
      queryParams.append("limit", String(params.limit));
    if (params?.verified_status)
      queryParams.append("verified_status", params.verified_status);

    const queryString = queryParams.toString();
    return this.request<DestinationWithCertificate[]>(
      `/destinations/admin/all${queryString ? `?${queryString}` : ""}`,
      { method: "GET" }
    );
  }

  // Update destination certificate status (Admin only)
  async adminUpdateCertificate(
    destinationId: string,
    newStatus: GreenVerifiedStatus
  ): Promise<DestinationWithCertificate> {
    return this.request<DestinationWithCertificate>(
      `/destinations/admin/${destinationId}/certificate?new_status=${encodeURIComponent(
        newStatus
      )}`,
      { method: "PUT" }
    );
  }

  // Mock: Check destination with external API (not implemented on backend yet)
  async adminCheckExternalApi(
    destinationId: string
  ): Promise<ExternalApiCheckResult> {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Mock response - randomly pass or fail
    const passed = Math.random() > 0.3;
    const score = passed ? Math.random() * 0.3 + 0.7 : Math.random() * 0.5;

    return {
      destination_id: destinationId,
      passed,
      score,
      details: passed
        ? "External verification passed: Location meets green standards"
        : "External verification failed: Insufficient green coverage detected",
    };
  }

  // Check destination with AI verification using green-verification endpoint
  async adminCheckAiVerification(destinationId: string): Promise<AiCheckResult> {
    try {
      const response = await this.request<GreenVerificationResponse>(
        `/green-verification/verify-place?place_id=${encodeURIComponent(destinationId)}`,
        { method: "GET" }
      );
      
      // Map GreenVerificationResponse to AiCheckResult format
      const verified = response.status === "AI Green Verified" || response.status === "Green Certified";
      
      return {
        destination_id: destinationId,
        verified,
        confidence: response.green_score, // Use green_score as confidence
        green_score: response.green_score,
      };
    } catch (error: any) {
      // Handle service unavailable error gracefully
      if (error.message && error.message.includes('503')) {
        throw new Error('AI verification service is currently unavailable due to technical issues. Please try again later or contact support.');
      }
      throw error;
    }
  }

  async updateRoute(
    planId: number,
    routeId: number,
    mode: string,
    carbonEmission: number
  ): Promise<RouteResponse> {
    const queryParams = new URLSearchParams({
      mode: mode,
      carbon_emission_kg: carbonEmission.toString(),
    });
    return this.request<RouteResponse>(
      `/plans/${planId}/routes/${routeId}?${queryParams.toString()}`,
      {
        method: "POST",
      }
    );
  }

  // --- PREFERENCE ENDPOINTS ---
  async checkUserHasPreferences(): Promise<boolean> {
    return this.request<boolean>("/clustering/preference-exists", {
      method: "GET",
    });
  }

  async updateUserPreferences(preferences: PreferenceUpdate | {}): Promise<any> {
    return this.request<any>("/clustering/preference", {
      method: "PUT",
      body: JSON.stringify(preferences),
    });
  }
}

export const api = new ApiClient(API_BASE_URL);
