const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://ecomovex.onrender.com/";

interface LoginCredentials {
  email: string;
  password: string;
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
      const error: ApiError = await response.json();
      throw new Error(error.detail || "An error occurred");
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
}

export const api = new ApiClient(API_BASE_URL);
