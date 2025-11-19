const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://ecomovex.onrender.com";

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

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  phone_number?: string | null;
  avatar_url?: string | null;
  role?: string;
}
// Map/Location Types
export interface Position {
  lat: number;
  lng: number;
}

export interface AutocompletePrediction {
  place_id: string;
  description: string;
  structured_formatting?: Record<string, any>;
  types: string[];
  matched_substrings?: Array<Record<string, any>>;
  distance?: number;
}

export interface PlaceDetails {
  place_id: string;
  name: string;
  formatted_address: string;
  address_components?: Array<{
    name: string;
    types: string[];
  }>;
  location: Position;
  geometry?: {
    location: Position;
    bounds?: {
      northeast: Position;
      southwest: Position;
    };
  };
  rating?: number;
  user_ratings_total?: number;
  photos?: Array<{
    photo_reference: string;
    width: number;
    height: number;
  }>;
  formatted_phone_number?: string;
  opening_hours?: {
    open_now: boolean;
    periods?: Array<Record<string, any>>;
    weekday_text?: string[];
  };
  website?: string;
  types: string[];
  vicinity?: string;
}

export interface SearchPlacesResponse {
  predictions: AutocompletePrediction[];
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

export interface UserProfileUpdate {
  username?: string;
  email?: string;
  phone_number?: string;
  avatar_url?: string;
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

    // use a Headers instance so we can call typed .set() and merge any incoming headers
    const headers = new Headers();

    // set default content type
    headers.set("Content-Type", "application/json");

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

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

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
        throw new Error(
          errorData.detail || `HTTP ${response.status}: An error occurred`
        );
      } catch (e) {
        if (e instanceof ApiValidationError) {
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
  //User endpoint
  async getUserProfile(): Promise<UserProfile> {
    return this.request<UserProfile>("/users/me", {
      method: "GET",
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

  async updateUserProfile(data: UserProfileUpdate): Promise<UserProfile> {
    return this.request<UserProfile>("/users/me/credentials", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getPlans(): Promise<TravelPlan[]> {
    // Giả lập delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    return [
      {
        id: 201,
        destination: "Ho Chi Minh City (Upcoming)",
        date: "20/11/2025", // Ngày tương lai (Sẽ là Current Plan)
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
        date: "04/01/2024", // Ngày quá khứ
        activities: [
          // ... (Dữ liệu cũ)
        ],
      },
      {
        id: 102,
        destination: "District 5 (Past)",
        date: "01/01/2023", // Ngày quá khứ xa hơn
        activities: [],
      },
    ];
  }
}

export const api = new ApiClient(API_BASE_URL);
