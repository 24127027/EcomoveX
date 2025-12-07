## 🌳 EcomoveX Frontend Overview

The EcomoveX frontend provides the user interface for all eco-friendly navigation, missions, rewards, and other core features. It is built using **Next.js**, a powerful React-based framework for modern web applications.

---

### Project Structure

The Next.js application follows a standard, organized file structure:

- **`src/app/`**: Contains all Next.js-specific files, including pages, layouts, and routing logic.
  - `(auth)/`: Pages related to user **authentication** (e.g., login, signup).
  - `(main)/`: **Main application pages** and features (e.g., map, missions, user profile).
  - `globals.css`: **Global styles** for the application.
  - `layout.tsx`: The **Root Layout** component for the entire application.
  - `page.tsx`: The **default landing page**.
- **`src/components/`**: Houses all **reusable React components** used across the application (e.g., buttons, forms, navigation bars).
- **`src/lib/`**: Contains **utility functions** and **API clients**.
  - `api.ts`: The **API client** for communicating with the backend server.
  - `useGoogleMaps.ts`: Logic for **integrating Google Maps** features.
  - `validation.ts`: Utilities for **form validation**.
- **`public/`**: Directory for **static assets** like images, fonts, and icons.

---

### 🌐 Connecting Frontend to Backend (API Integration)

The frontend communicates with the backend via a RESTful API. Proper configuration is essential for seamless data exchange.

#### 1. Configure the Frontend API URL

Set the backend server address in the frontend's environment file (`.env`):

- **File:** `.env` (in the frontend root directory)
- **Variable:** `NEXT_PUBLIC_API_URL`
- **Local Development Example:**
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

#### 2. API Client Implementation

The `src/lib/api.ts` file uses this environment variable to correctly target the backend:

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export const api = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  }
  async getSavedDestinations(): Promise<SavedDestination[]> {
    return this.request<SavedDestination[]>("/destinations/saved/me/all", {
      method: "GET",
    });
  }
}
```

#### 3. Enable CORS in the Backend

The backend must allow the frontend's origin to make requests. This is done by setting the CORS (Cross-Origin Resource Sharing) configuration in the backend's environment file:

- File: .env (in the backend root directory)
- Variable: CORS_ORIGINS
- Local Development Example: (Assuming frontend runs on port 3000)
  CORS_ORIGINS=http://localhost:3000
