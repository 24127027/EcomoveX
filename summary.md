# EcomoveX - Feature Summary Document

**Application Type:** Sustainable Travel & Eco-Mobility Platform  
**Purpose:** Web application promoting eco-friendly travel through route optimization, carbon tracking, and green destination discovery  
**Architecture:** FastAPI Backend + Next.js Frontend

---

## 1. Authentication & User Management Module

### 1.1 User Authentication
**What it does:** Handles user registration, login, and password management  
**Inputs:**
- Registration: username, email, password
- Login: email, password
- Password generation: email

**Outputs:**
- Authentication response with access token and user details
- JWT token for subsequent API calls

**Key Flows:**
- User registers → Account created → Auto-login with token
- User logs in → Credentials validated → Token issued
- Forgot password → Temporary password generated

**APIs:**
- POST `/auth/register` - Create new user account
- POST `/auth/login` - Authenticate user
- POST `/auth/generate-password` - Generate temporary password

**Dependencies:** Database (users table), JWT token service

---

### 1.2 User Profile Management
**What it does:** Manages user profile data, credentials, and account settings  
**Inputs:**
- User ID (from JWT token)
- Profile updates: username, avatar, preferences
- Credential updates: email, password

**Outputs:**
- User profile data (username, email, rank, eco points, created date)
- Updated profile confirmation
- Account deletion confirmation

**Key Flows:**
- View own profile → Retrieve user data
- Update profile → Validate → Save changes
- Update credentials → Verify password → Update
- Delete account → Confirm → Remove all user data

**APIs:**
- GET `/users/me` - Get current user profile
- GET `/users/id/{user_id}` - Get user by ID
- GET `/users/search/` - Search users by query string
- PUT `/users/me/credentials` - Update email/password
- PUT `/users/me/profile` - Update profile information
- DELETE `/users/me` - Delete own account
- DELETE `/users/{user_id}` - Admin delete user (Admin only)

**Dependencies:** Authentication service, Storage service (for avatars)

---

### 1.3 Admin User Management
**What it does:** Administrative features for managing users system-wide  
**Inputs:**
- Filter parameters (role, rank, limit, offset)
- User ID for admin actions
- Role/password update data

**Outputs:**
- Paginated list of users
- User details with admin metadata
- Update/delete confirmations

**Key Flows:**
- Admin lists users → Apply filters → Return paginated results
- Admin updates user role → Validate permissions → Update role
- Admin resets password → Generate new password → Notify user
- Admin deletes user → Confirm → Cascade delete user data

**APIs:**
- POST `/users/list` - List all users with filters (Admin only)
- PUT `/users/{user_id}/role` - Update user role (Admin only)
- POST `/users/{user_id}/reset-password` - Reset user password (Admin only)

**Dependencies:** Role-based authorization, User repository

---

## 2. Social & Friend Management Module

### 2.1 Friend System
**What it does:** Manages friend connections between users  
**Inputs:**
- Friend user ID
- Current user ID (from token)

**Outputs:**
- Friend relationship status (pending, accepted)
- List of friends, pending requests, sent requests
- Success/error messages

**Key Flows:**
- Send friend request → Create pending relationship
- Accept request → Update status to accepted → Both users now friends
- Reject request → Delete relationship record
- Unfriend → Remove relationship

**APIs:**
- POST `/friends/{friend_id}/request` - Send friend request
- POST `/friends/{friend_id}/accept` - Accept friend request
- DELETE `/friends/{friend_id}/reject` - Reject friend request
- DELETE `/friends/{friend_id}` - Unfriend user
- GET `/friends/` - Get list of friends
- GET `/friends/pending` - Get pending friend requests
- GET `/friends/sent` - Get sent friend requests

**Dependencies:** User service, Friend repository

---

## 3. Destination & Places Module

### 3.1 Map Search & Exploration
**What it does:** Search, discover, and view detailed information about destinations  
**Inputs:**
- Search query (text)
- Location coordinates (lat, lng)
- Place ID
- Session token for autocomplete
- Search radius, filters

**Outputs:**
- Place search results with name, address, photos, rating
- Autocomplete suggestions
- Detailed place information (opening hours, reviews, photos, location)
- Geocoding results (address ↔ coordinates)

**Key Flows:**
- User searches text → API queries Google Places → Returns matching results
- User types in search → Autocomplete suggests places
- User clicks place → Fetch details → Display full information
- User enters address → Geocode → Return coordinates
- User provides coordinates → Reverse geocode → Return address

**APIs:**
- POST `/map/text-search` - Search places by text query
- POST `/map/autocomplete` - Get autocomplete suggestions
- GET `/map/place/{place_id}` - Get detailed place information
- POST `/map/geocode` - Convert address to coordinates
- POST `/map/reverse-geocode` - Convert coordinates to address
- POST `/map/search-along-route` - Find places along a route

**Dependencies:** Google Places API, Google Maps Geocoding API, User activity logging

---

### 3.2 Saved Destinations
**What it does:** Allows users to save and manage favorite destinations  
**Inputs:**
- Destination ID (place_id)
- User ID (from token)

**Outputs:**
- Saved destination confirmation
- List of user's saved destinations
- Unsave confirmation

**Key Flows:**
- User saves destination → Create saved record → Log activity → Confirm
- User views saved destinations → Retrieve all saved places
- User unsaves destination → Delete record → Confirm

**APIs:**
- POST `/destinations/saved/{destination_id}` - Save destination
- GET `/destinations/saved/me/all` - Get all saved destinations
- DELETE `/destinations/saved/{destination_id}` - Unsave destination

**Dependencies:** Destination repository, User activity service

---

### 3.3 Place Reviews
**What it does:** Users can review destinations with ratings, text, and photos  
**Inputs:**
- Destination ID
- Review data: rating (1-5), comment, photos (optional)
- User ID (from token)

**Outputs:**
- Review submission confirmation
- List of reviews for a destination
- Review statistics (average rating, count)
- User's own reviews

**Key Flows:**
- User submits review → Upload photos (if any) → Save review → Log activity
- User views place → Load reviews → Display with ratings and photos
- User updates review → Modify data → Upload new photos → Update record
- User deletes review → Remove review and photos → Confirm

**APIs:**
- POST `/reviews/{destination_id}` - Create review with photos
- PUT `/reviews/{destination_id}` - Update existing review
- DELETE `/reviews/{destination_id}` - Delete review
- GET `/reviews/me` - Get current user's reviews
- GET `/reviews/destination/{destination_id}` - Get reviews for destination
- GET `/reviews/destination/{destination_id}/statistics` - Get review statistics

**Dependencies:** Storage service (photo uploads), User activity service, Review repository

---

## 4. Route & Navigation Module

### 4.1 Route Planning
**What it does:** Calculates optimal routes between locations with multiple transport modes  
**Inputs:**
- Origin location (lat, lng)
- Destination location (lat, lng)
- Transport mode (car, motorbike, walking, bus, metro, train)
- Waypoints (optional)
- Preferences (avoid tolls, highways, etc.)

**Outputs:**
- Up to 3 route alternatives
- Route details: distance, duration, polyline, steps
- Turn-by-turn navigation instructions
- Carbon emission estimates per route

**Key Flows:**
- User selects origin and destination → Choose transport mode → System calculates routes
- System ranks routes by eco-friendliness (carbon emissions)
- User selects route → View detailed steps and map
- System provides turn-by-turn navigation

**APIs:**
- POST `/routes/find-optimal` - Find 3 optimal routes with eco-scoring

**Dependencies:** Google Routes API, Carbon estimation service

---

### 4.2 Carbon Emission Estimation
**What it does:** Calculates CO2 emissions for different transport modes  
**Inputs:**
- Transport mode (car, motorbike, bus, metro, train, walking)
- Distance in kilometers
- Number of passengers

**Outputs:**
- Estimated carbon emissions in kg CO2e per passenger
- Eco-score for route comparison

**Key Flows:**
- Calculate emission → Query Climatiq API with mode and distance
- Adjust for passenger count (carpool reduces per-person emissions)
- Return emission value for display/comparison

**APIs:**
- POST `/carbon/estimate` - Estimate carbon emissions for transport

**Dependencies:** Climatiq API, Transport emission factors database

---

## 5. Travel Planning Module

### 5.1 Plan Creation & Management
**What it does:** Create and manage multi-day travel plans with destinations  
**Inputs:**
- Plan details: place name, start date, end date, budget limit
- User ID (from token)
- Plan updates

**Outputs:**
- Created plan with ID
- Plan details with destinations and members
- Updated plan data
- Deletion confirmation

**Key Flows:**
- User creates plan → Set dates and budget → Plan created
- User adds destinations to plan → Specify visit dates and time slots
- User updates plan → Modify dates/budget → Save changes
- User deletes plan → Cascade delete destinations and members

**APIs:**
- GET `/plans/` - Get user's travel plans
- POST `/plans/` - Create new travel plan
- PUT `/plans/{plan_id}` - Update plan details
- DELETE `/plans/{plan_id}` - Delete travel plan

**Dependencies:** Plan repository, User authorization

---

### 5.2 Plan Collaboration
**What it does:** Share plans with friends and collaborate on trip planning  
**Inputs:**
- Plan ID
- Member user IDs to add/remove
- User ID (from token)

**Outputs:**
- List of plan members with roles (owner, member)
- Member addition confirmation
- Member removal confirmation

**Key Flows:**
- Plan owner adds members → Send invitations → Members can view/edit plan
- View plan members → Display all collaborators
- Remove member → Update permissions → Member loses access
- Plan shared via chat rooms for real-time collaboration

**APIs:**
- GET `/plans/{plan_id}/members` - Get plan members
- POST `/plans/{plan_id}/members` - Add members to plan
- DELETE `/plans/{plan_id}/members` - Remove members from plan

**Dependencies:** Friend system, Room messaging (for collaboration), User service

---

### 5.3 AI Travel Planning Assistant
**What it does:** AI-powered chatbot generates travel plans based on preferences  
**Inputs:**
- Plan parameters: destination, dates, budget, preferences
- User messages in natural language
- User ID, Room ID (for chat context)

**Outputs:**
- AI-generated travel itinerary
- Destination recommendations
- Response to user questions about travel

**Key Flows:**
- User provides plan requirements → AI agent generates itinerary
- User asks questions → AI provides contextual responses
- AI suggests destinations based on user preferences
- Generated plan can be saved to user's plans

**APIs:**
- POST `/chatbot/plan/generate` - Generate travel plan with AI
- POST `/chatbot/message` - Send message to travel chatbot

**Dependencies:** OpenRouter LLM API, Planning agent service, User context

---

## 6. Messaging & Chat Module

### 6.1 Chat Rooms
**What it does:** Group chat functionality for travel planning collaboration  
**Inputs:**
- Room details: name, member list
- User ID (from token)
- Room ID

**Outputs:**
- Room creation confirmation
- List of user's chat rooms
- Room details with members
- Direct message room info

**Key Flows:**
- User creates room → Add members → Room created
- User lists rooms → Display all accessible rooms
- User opens room → Load messages and members
- Add/remove members → Update room membership

**APIs:**
- GET `/rooms/rooms` - List all user's chat rooms
- GET `/rooms/direct-rooms` - List direct message rooms
- GET `/rooms/rooms/{room_id}` - Get room details
- GET `/rooms/direct-rooms/{direct_room_id}` - Get direct room details
- POST `/rooms/rooms` - Create new chat room
- POST `/rooms/rooms/{room_id}/members` - Add members to room
- DELETE `/rooms/rooms/{room_id}/members` - Remove members from room

**Dependencies:** User service, Friend service, Plan service

---

### 6.2 Messaging
**What it does:** Send and receive messages in chat rooms with various content types  
**Inputs:**
- Room ID
- Message content (text, file, plan reference)
- Message type (text, image, file, plan)
- User ID (from token)

**Outputs:**
- Message delivery confirmation
- Message list for room
- Message search results
- Real-time message updates via WebSocket

**Key Flows:**
- User sends text message → Message saved → Broadcast to room members
- User uploads file → Store in cloud → Send file message
- User shares plan → Link plan to message → Visible to room members
- User searches messages → Query by keyword → Return matching messages
- Real-time messaging via WebSocket connection

**APIs:**
- POST `/messages/{room_id}` - Send message to room
- GET `/messages/room/{room_id}` - Get messages in room
- GET `/messages/{message_id}` - Get specific message
- GET `/messages/search/keyword` - Search messages by keyword
- DELETE `/messages/{message_id}` - Delete message
- WebSocket `/messages/ws/{room_id}` - Real-time messaging connection

**Dependencies:** Storage service (file uploads), Room service, WebSocket manager

---

## 7. Gamification & Rewards Module

### 7.1 Mission System
**What it does:** Define and track eco-friendly missions users can complete  
**Inputs:**
- Mission data: title, description, reward points, type (Admin creates)
- User ID (from token)

**Outputs:**
- List of available missions
- Mission details
- User's completed missions
- Reward points earned

**Key Flows:**
- Admin creates mission → Define criteria and rewards → Mission published
- User views missions → See available challenges
- System tracks user activities → Auto-complete missions → Award points
- User views completed missions → See progress and rewards

**APIs:**
- GET `/rewards/missions` - Get all available missions
- GET `/rewards/missions/{mission_id}` - Get mission details
- POST `/rewards/missions` - Create mission (Admin only)
- PUT `/rewards/missions/{mission_id}` - Update mission (Admin only)
- DELETE `/rewards/missions/{mission_id}` - Delete mission (Admin only)
- GET `/rewards/me/missions` - Get user's completed missions and points

**Dependencies:** User activity tracking, Admin authorization

---

### 7.2 User Rewards & Ranking
**What it does:** Track user eco-points, rank, and mission completion  
**Inputs:**
- User activities (saving destinations, reviews, eco-friendly transport)
- Mission completions

**Outputs:**
- User's total eco-points
- User rank (Bronze, Silver, Gold, Platinum, Diamond)
- Completed missions count
- Rank progression status

**Key Flows:**
- User completes activity → Earn eco-points → Points accumulated
- Points reach threshold → Rank upgraded → User notified
- User views rewards → See points, rank, and completed missions
- Leaderboard displays top eco-conscious users

**Dependencies:** Mission system, User activity service, Ranking algorithm

---

## 8. Environmental Data Module

### 8.1 Air Quality Monitoring
**What it does:** Provides real-time air quality information for destinations  
**Inputs:**
- Place ID or location coordinates

**Outputs:**
- Air Quality Index (AQI)
- Pollutant levels (PM2.5, PM10, O3, NO2, SO2, CO)
- Health recommendations based on AQI
- Air quality category (Good, Moderate, Unhealthy, etc.)

**Key Flows:**
- User views destination → System fetches air quality → Display AQI and warnings
- System provides health recommendations based on air quality

**APIs:**
- GET `/air/air-quality?place_id={id}` - Get air quality for location

**Dependencies:** Google Air Quality API

---

### 8.2 Weather Information
**What it does:** Provides current weather and forecasts for travel planning  
**Inputs:**
- Place ID or location coordinates
- Forecast hours (1-120 hours)
- Unit system (metric/imperial)

**Outputs:**
- Current weather: temperature, conditions, humidity, wind
- Hourly forecast for next 120 hours
- Weather icons and descriptions

**Key Flows:**
- User views destination → System fetches weather → Display current conditions
- User plans trip → View weather forecast → Adjust travel dates if needed

**APIs:**
- GET `/weather/current` - Get current weather conditions
- GET `/weather/forecast` - Get hourly weather forecast (up to 5 days)

**Dependencies:** Google Weather API

---

### 8.3 Green Verification
**What it does:** Verifies green/vegetation coverage in destination images using AI  
**Inputs:**
- Image URLs (single or batch)
- Green threshold (0.0 - 1.0, default 0.3)
- User ID (from token)

**Outputs:**
- Green coverage proportion (0-1)
- Depth-weighted green score
- Verification status (passes/fails threshold)
- Segmentation and depth analysis results

**Key Flows:**
- User uploads destination image → AI segments vegetation → Calculate green proportion
- System uses depth estimation → Prioritize foreground vegetation
- Calculate final green score → Compare to threshold → Return verification result
- Batch processing for multiple images → Return individual and aggregate results

**APIs:**
- POST `/green-verification/verify-batch` - Verify multiple images
- GET `/green-verification/verify` - Verify single image
- GET `/green-verification/health` - Check service health status

**Dependencies:** YOLO segmentation model, MiDaS depth estimation model, Image processing pipeline

---

## 9. Recommendation System Module

### 9.1 Personalized Recommendations
**What it does:** AI-powered destination recommendations based on user preferences and behavior  
**Inputs:**
- User ID (from token)
- Number of recommendations (k)
- Hybrid mode flag (collaborative + content-based)

**Outputs:**
- Ranked list of recommended destinations
- Recommendation scores
- Place details for each recommendation

**Key Flows:**
- System analyzes user history → Identify preferences → Generate recommendations
- Collaborative filtering: Find similar users → Recommend their favorite places
- Content-based: Match place features to user preferences
- Hybrid: Combine both approaches for better results

**APIs:**
- GET `/recommendations/user/me` - Get personalized recommendations

**Dependencies:** User activity history, Machine learning models, Place data

---

### 9.2 Cluster-Based Recommendations
**What it does:** Group users by travel preferences and recommend based on cluster affinity  
**Inputs:**
- User ID (from token)
- Current location (for nearby recommendations)
- Search radius in kilometers
- Number of results (k)
- List of recommendations to sort

**Outputs:**
- Recommendations sorted by cluster affinity
- Nearby places matching user's cluster preferences
- Cluster-based scoring

**Key Flows:**
- System clusters users by behavior → Assign each user to cluster
- User requests recommendations → Find cluster preferences → Recommend matching places
- User provides location → Search nearby → Filter by cluster tags → Rank by relevance

**APIs:**
- POST `/recommendations/user/me/sort-by-cluster` - Sort recommendations by cluster affinity
- POST `/recommendations/user/{user_id}/sort-by-cluster` - Sort for specific user
- GET `/recommendations/user/me/nearby-by-cluster` - Get nearby recommendations by cluster
- GET `/recommendations/user/{user_id}/nearby-by-cluster` - Get nearby recommendations for user

**Dependencies:** User clustering algorithm, Place categorization, Location-based search

---

### 9.3 User Clustering
**What it does:** Machine learning algorithm that groups users with similar travel patterns  
**Inputs:**
- All user activity data
- User preferences and behaviors
- Destination interactions

**Outputs:**
- User cluster assignments
- Cluster characteristics and preferences
- Cluster statistics

**Key Flows:**
- Admin triggers clustering → System analyzes all users → Apply clustering algorithm
- Users grouped by similarities → Assign cluster IDs → Update user records
- Clusters used for recommendations → Match users with similar preferences

**APIs:**
- POST `/clustering/run` - Trigger user clustering algorithm

**Dependencies:** User activity data, Machine learning service, Scikit-learn clustering algorithms

---

## 10. File Storage Module

### 10.1 File Management
**What it does:** Cloud storage for user files (photos, documents, avatars)  
**Inputs:**
- File upload (multipart/form-data)
- File category (profile, review, message, plan)
- File metadata filters (date range, content type)
- User ID (from token)

**Outputs:**
- File metadata (URL, size, type, upload date)
- File list with filtering and sorting
- Upload/delete confirmations

**Key Flows:**
- User uploads file → Validate → Store in cloud (Azure/GCS) → Save metadata → Return URL
- User lists files → Apply filters → Return sorted results
- User deletes file → Remove from storage → Delete metadata
- Files automatically linked to related entities (reviews, messages)

**APIs:**
- GET `/storage/files` - List user's files with filters
- GET `/storage/files/{blob_name}` - Get file metadata
- POST `/storage/files` - Upload file
- DELETE `/storage/files/{blob_name}` - Delete file

**Dependencies:** Azure Blob Storage or Google Cloud Storage, File metadata repository

---

## 11. Admin Panel Module

### 11.1 Admin Dashboard
**What it does:** Overview dashboard for system administrators  
**Inputs:**
- Admin credentials (role verification)

**Outputs:**
- Total users count
- Active destinations count
- Pending reviews count
- Total eco-impact score (sum of all user eco-points)
- User growth trends
- Activity statistics

**Key Flows:**
- Admin logs in → Verify admin role → Display dashboard
- Dashboard shows key metrics → Updated in real-time
- Admin can navigate to detailed management sections

**Frontend Pages:**
- `/admin` - Main admin dashboard with statistics

**Dependencies:** All data repositories for aggregated statistics

---

### 11.2 User Management (Admin)
**What it does:** Administrative interface to manage all users  
**Inputs:**
- Search/filter criteria
- User ID for actions
- Role updates, password resets

**Outputs:**
- Paginated user list
- User details and activity
- Action confirmations

**Key Flows:**
- Admin searches users → Apply filters → View results
- Admin views user details → See activity history
- Admin updates roles → Validate → Apply changes
- Admin deletes problematic users → Confirm → Remove data

**Frontend Features:**
- User search and filtering
- Role management (User/Admin)
- Password reset for users
- User deletion

**Dependencies:** User management APIs, Role authorization

---

### 11.3 Content Moderation
**What it does:** Tools for moderating user-generated content  
**Inputs:**
- Review IDs
- Mission data
- Moderation actions

**Outputs:**
- List of reviews requiring moderation
- Review approval/rejection
- Mission management

**Frontend Features:**
- Review moderation queue
- Mission creation and management
- Content flagging and removal

**Dependencies:** Review service, Mission service, Admin authorization

---

## 12. Frontend Pages & User Experience

### 12.1 Authentication Pages
**Location:** `/login`, `/signup`, `/forget_Password`

**What it does:** User authentication interface  
**Inputs:** Email, password, username (signup)  
**Outputs:** Login success/error, registration confirmation  
**Key Features:**
- Form validation
- Password visibility toggle
- Remember me option
- Password recovery flow
- Social login (future)

---

### 12.2 Homepage
**Location:** `/homepage`

**What it does:** Main landing page with personalized content  
**Key Features:**
- Search bar for destinations
- Upcoming travel plan preview
- User rewards and eco-points display
- Green place recommendations carousel
- Saved locations quick access
- Location-based nearby suggestions

**Outputs:**
- Personalized dashboard
- Quick access to main features
- Travel inspiration

**Dependencies:** User profile, Plans API, Recommendations API, Saved destinations API

---

### 12.3 Map & Exploration Page
**Location:** `/map_page`

**What it does:** Interactive map interface for discovering destinations  
**Key Features:**
- Google Maps integration
- Real-time search with autocomplete
- Place markers on map
- Distance calculation from user location
- Place details preview
- Filter by place types
- Geolocation tracking
- Save/unsave destinations directly

**Outputs:**
- Interactive map view
- Search results list
- Place previews with distance

**Dependencies:** Google Maps API, Map service, Saved destinations API

---

### 12.4 Place Detail Page
**Location:** `/place_detail_page`

**What it does:** Comprehensive information about a destination  
**Key Features:**
- Place photos gallery
- Ratings and reviews
- Opening hours
- Address and location
- Save/unsave destination
- Add review with photos
- Green certification badge
- Air quality indicator
- Weather information
- Share to plans

**Outputs:**
- Complete place information
- User reviews and ratings
- Environmental data
- Action buttons (save, review, share)

**Dependencies:** Map API, Review API, Air quality API, Weather API, Storage API

---

### 12.5 Travel Planning Pages
**Location:** `/planning_page/*`

**Sub-pages:**
- `/create_plan` - Plan creation wizard
- `/[plan_id]` - View specific plan
- `/[plan_id]/details` - Detailed plan view
- `/showing_plan_page` - List all plans
- `/add_destinations` - Add destinations to plan
- `/review_plan` - Review and finalize plan

**What it does:** Complete travel planning workflow  
**Key Features:**
- Multi-step plan creation (dates, budget, destination)
- Calendar date picker
- Budget tracking
- Add destinations to timeline
- Drag-and-drop itinerary builder
- Share with friends
- AI plan generation
- Route visualization
- Carbon footprint estimation

**Outputs:**
- Created travel plans
- Detailed itineraries
- Shared plans with collaborators

**Dependencies:** Plans API, Map API, Route API, Carbon API, Friend API, Chatbot API

---

### 12.6 User Profile Pages
**Location:** `/user_page/*`

**Sub-pages:**
- `/main_page` - Profile overview with saved places
- `/profile_page` - Detailed profile information
- `/friend_page` - Friend management
- `/setting_page` - Account settings

**What it does:** User account and profile management  
**Key Features:**
- View profile information
- Edit profile (username, avatar)
- View saved destinations
- Friend requests management
- Account settings (email, password)
- Eco-points and rank display
- Activity history
- Delete account option

**Outputs:**
- User profile data
- Saved places list
- Friend list
- Settings updates

**Dependencies:** User API, Friend API, Saved destinations API, Storage API

---

## 13. External API Integrations

### 13.1 Google Maps Platform
**APIs Used:**
- Places API - Search, details, photos
- Geocoding API - Address ↔ coordinates conversion
- Routes API - Route calculations and directions
- Air Quality API - AQI and pollutant data
- Weather API - Current weather and forecasts

**Purpose:** Core mapping, navigation, and environmental data

---

### 13.2 Climatiq API
**Purpose:** Carbon emission calculations  
**Features:**
- Emission factors for various transport modes
- Per-passenger calculations
- Real-time emission data

---

### 13.3 OpenRouter API
**Purpose:** LLM-powered AI features  
**Model:** Meta LLaMA 3.3 70B Instruct  
**Features:**
- Travel planning chatbot
- Natural language processing
- Context-aware responses
- Itinerary generation

---

### 13.4 BREEAM API
**Purpose:** Green building certification data  
**Features:**
- Sustainability certification verification
- Building environmental ratings

---

### 13.5 AI/ML Models (Local)
**Models:**
- YOLO - Vegetation segmentation
- MiDaS - Depth estimation

**Purpose:** Green verification of destination images

---

## 14. Database Models & Entities

### Core Entities:
1. **User** - User accounts with authentication, roles, ranks, eco-points
2. **Friend** - Friend relationships (pending, accepted)
3. **Destination** - Places with metadata from Google Places
4. **Review** - User reviews with ratings and photos
5. **Plan** - Travel plans with dates and budget
6. **PlanDestination** - Destinations within a plan (itinerary)
7. **PlanMember** - Plan collaborators (owner, member)
8. **Room** - Chat rooms for messaging
9. **Message** - Chat messages (text, files, plans)
10. **Mission** - Eco-challenges with rewards
11. **UserMission** - Completed missions by users
12. **Metadata** - File storage metadata
13. **Cluster** - User clustering for recommendations

---

## 15. Key System Flows

### 15.1 Complete Trip Planning Flow
1. User searches for destination on map
2. Views place details, reviews, environmental data
3. Saves interesting places
4. Creates travel plan with dates and budget
5. Adds saved places to plan timeline
6. AI chatbot suggests additional destinations
7. Invites friends to collaborate on plan
8. Friends join via shared chat room
9. Group discusses in chat, shares plans
10. Calculates routes between destinations
11. Reviews carbon footprint
12. Finalizes plan
13. Earns eco-points for eco-friendly choices

### 15.2 Social Interaction Flow
1. User searches for friends
2. Sends friend requests
3. Friends accept requests
4. Create or join chat rooms
5. Share plans and destinations
6. Collaborate on travel planning
7. Send messages (text, files, plans)
8. Real-time updates via WebSocket

### 15.3 Gamification Flow
1. User completes activities (save, review, eco-travel)
2. System tracks activities
3. Auto-completes missions
4. Awards eco-points
5. User rank increases
6. Unlocks achievements
7. Displays on leaderboard

---

## 16. Testing Considerations

### Functional Testing Areas:
- Authentication (register, login, token refresh, password reset)
- Authorization (role-based access control)
- CRUD operations (users, plans, reviews, destinations)
- Search and filtering (destinations, users, messages)
- File uploads and storage
- Real-time messaging (WebSocket)
- API integrations (Google, Climatiq, OpenRouter)
- AI/ML model inference (green verification)
- Recommendation algorithms
- Carbon calculations
- Clustering algorithms

### Non-Functional Testing Areas:
- Performance (API response times, large data sets)
- Scalability (concurrent users, WebSocket connections)
- Security (authentication, authorization, data protection)
- Reliability (error handling, fallbacks)
- Usability (frontend UX, mobile responsiveness)
- Compatibility (browsers, devices)
- Data integrity (cascading deletes, transactions)

### Edge Cases:
- Empty search results
- Invalid place IDs
- Network failures during external API calls
- File upload size limits
- Invalid date ranges in plans
- Duplicate friend requests
- Message ordering in real-time chat
- Token expiration during session
- GPS/location permission denied
- Image processing failures

---

## 17. Security & Privacy Features

### Authentication & Authorization:
- JWT-based authentication
- Password hashing (bcrypt)
- Role-based access control (User, Admin)
- Token expiration and refresh
- Secure password reset flow

### Data Protection:
- User data isolation (users can only access own data)
- Cascading deletes (remove all user data on account deletion)
- File access control (only owner can view/delete files)
- Plan privacy (only members can view/edit)
- Message privacy (only room members can view)

### API Security:
- Rate limiting (via external API keys)
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- HTTPS enforcement (production)

---

## 18. Performance Optimizations

### Database:
- Indexed columns for fast queries (email, user_id, place_id, dates)
- Compound indexes for common query patterns
- Relationship lazy loading
- Database connection pooling

### Caching:
- User session caching
- Place details caching (reduce API calls)
- Static asset caching (frontend)

### API Optimizations:
- Pagination for large result sets
- Batch processing (multiple images, users)
- Async/await for concurrent operations
- Connection pooling for external APIs

### Frontend:
- Lazy loading of images
- Debounced search inputs
- Virtual scrolling for long lists
- Code splitting (Next.js)
- Image optimization (Next.js Image component)

---

## Summary Statistics

**Total API Endpoints:** ~80+  
**Core Modules:** 11  
**Frontend Pages:** 20+  
**External Integrations:** 5  
**Database Tables:** 13+  
**User Roles:** 2 (User, Admin)  
**Message Types:** 4 (text, image, file, plan)  
**Transport Modes:** 6 (car, motorbike, walking, bus, metro, train)  
**File Categories:** 4 (profile, review, message, plan)  
**User Ranks:** 5 (Bronze, Silver, Gold, Platinum, Diamond)

---

**Document Purpose:** This summary provides a comprehensive overview of all features in the EcomoveX platform for test planning and documentation purposes. Each feature is described with its inputs, outputs, key flows, and dependencies to facilitate test case creation.

**Last Updated:** December 5, 2025
