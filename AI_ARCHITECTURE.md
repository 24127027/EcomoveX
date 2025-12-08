# AI Architecture Documentation - EcomoveX

**Version:** 1.0  
**Last Updated:** December 2025  
**Purpose:** Internal technical documentation for AI/ML components

---

## Overview AI Components

EcomoveX integrates three primary AI/ML systems to deliver intelligent travel planning experiences:

1. **Conversational AI Agent Framework (LLM-based)** - Natural language understanding and trip planning assistance
2. **Recommendation System (Embedding + Clustering)** - Personalized destination suggestions using traditional ML
3. **Computer Vision Place Verification (YOLO + MiDaS)** - Automated green coverage verification for eco-friendly locations

**Technology Stack:**
- LLM Provider: OpenRouter API (meta-llama/llama-3.3-70b-instruct)
- Embedding Model: SentenceTransformers (all-MiniLM-L6-v2)
- CV Models: YOLOv8 (segmentation), MiDaS (depth estimation)
- Vector Search: FAISS (Facebook AI Similarity Search)
- ML Framework: scikit-learn (KMeans clustering)

---

## Conversational AI Agent Framework (LLM-based)

### Purpose

The conversational agent serves as the primary interface for users to:
- **Plan trips** through natural language dialogue
- **Edit existing plans** (add/remove/modify destinations)
- **Query plan details** (view itinerary, validate schedule, check budget)
- **Engage in casual conversation** (greetings, general questions)

**Design Goals:**
- High accuracy intent classification (>90%)
- Low latency response (<3s for typical queries)
- Robust error handling with graceful fallbacks
- Consistency in trip data across conversation sessions
- Cost-effective LLM usage through intelligent routing

### Agent Architecture

**Multi-Agent Hierarchical System:**

```
User Message
    ↓
Intent Detection Layer (LLM + Rule-based)
    ↓
┌──────────────┬──────────────┬──────────────┐
│              │              │              │
PlanEditAgent  PlannerAgent   ChitChatAgent
│              │              │
│              ↓              └→ Simple Reply
│         Sub-Agents:
│         ├─ OpeningHoursAgent
│         ├─ BudgetCheckAgent
│         ├─ DailyCalculationAgent
│         └─ PlanValidatorAgent
│
└→ Database Operations
```

**Component Breakdown:**

#### 1. Intent Detection Layer (`chatbot_service.py`)

**Dual-Strategy Intent Classification:**

```python
class ChatbotService:
    async def detect_intent(user_text: str) -> str:
        # Strategy 1: LLM-based (primary)
        intent = await LLMIntentParser().parse(user_text)
        if intent != "unknown":
            return intent
        
        # Strategy 2: Rule-based (fallback)
        intent = RuleEngine().classify(user_text)
        return intent
```

**Intent Categories:**
- `plan_edit` - Modify existing trip (add/remove destinations, change times/budget)
- `plan_query` - View/validate/optimize current plan
- `chit_chat` - General conversation, greetings

**Rationale:** LLM provides better contextual understanding, while rule-based ensures reliability when LLM fails or for common patterns.

#### 2. Core Agents

##### A. PlannerAgent (`planner_agent.py`)

**Responsibilities:**
- Orchestrate sub-agents for comprehensive plan validation
- Generate user-friendly responses explaining plan status
- Aggregate warnings/suggestions from all validators

**Key Methods:**

```python
async def process_plan(user_id, room_id, user_text, action="view"):
    # 1. Fetch user's plan from DB
    plans = await PlanService.get_plans_by_user(db, user_id)
    
    # 2. Run all sub-agents in parallel
    agent_results = await self._run_sub_agents(plan, action)
    
    # 3. Build LLM context with plan + warnings + modifications
    context_messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_text + plan_json},
        {"role": "system", "content": warnings + modifications}
    ]
    
    # 4. Generate natural language reply
    reply = await TextGeneratorAPI.generate_reply(context_messages)
    
    return {plan, reply, warnings, modifications}
```

**Sub-Agents Execution:**

```python
async def _run_sub_agents(plan, action="validate"):
    sub_agents = [
        OpeningHoursAgent,
        BudgetCheckAgent,
        DailyCalculationAgent,
        PlanValidatorAgent
    ]
    
    warnings, modifications = [], []
    for agent_cls in sub_agents:
        result = await agent_cls(db).process(plan, action)
        if not result["success"]:
            warnings.append(result["message"])
        if result["modifications"]:
            modifications.extend(result["modifications"])
    
    return {warnings, modifications}
```

##### B. PlanEditAgent (`plan_edit_agent.py`)

**Responsibilities:**
- Parse edit instructions from natural language
- Execute database operations (add/remove/modify destinations)
- Re-validate plan after changes

**Edit Flow:**

```python
async def edit_plan(db, user_id, user_text):
    # 1. Parse modifications using LLM
    modifications = await LLMPlanEditParser().parse(user_text)
    # Example output:
    # [
    #   {"action": "add", "destination_data": {...}},
    #   {"action": "remove", "destination_id": "123"}
    # ]
    
    # 2. Apply modifications
    await self.apply_modifications(db, plan, modifications, user_id)
    
    # 3. Validate after edit
    plan = await PlannerAgent().process_plan(db, user_id, "validate after edit")
    
    return plan
```

**Supported Actions:**
- `add` - Add new destination with auto-populated details
- `remove` - Remove destination by name/ID
- `modify_time` - Update start_time/end_time/day
- `change_budget` - Update budget_limit

##### C. ChitChatAgent (`chit_chat_agent.py`)

**Responsibilities:**
- Handle non-task conversations
- Provide friendly, brand-aligned responses
- Guide users toward planning features

**System Prompt:**
```
You are EcomoveX's friendly travel assistant.
Be helpful, friendly, and concise.
Guide users to use 'add', 'remove', 'view plan' for trip planning.
```

#### 3. Sub-Agents (Validators)

Each sub-agent implements a `process(plan, action)` interface:

##### OpeningHoursAgent
- **Check:** Destinations have `opening_hours` metadata
- **Output:** List of destinations missing hours + suggestions

##### BudgetCheckAgent
- **Check:** `sum(destination.estimated_cost) <= plan.budget_limit`
- **Output:** Over-budget amount, usage percentage, missing cost count

##### DailyCalculationAgent
- **Check:** Destinations are properly sequenced per day
- **Output:** Suggested visit order, time conflicts

##### PlanValidatorAgent
- **Check:** Basic integrity (place_name, dates, date range validity)
- **Output:** Missing fields, invalid date ranges

**Unified Response Schema:**
```json
{
  "success": true/false,
  "message": "Human-readable warning",
  "modifications": [
    {
      "issue": "over_budget",
      "suggestion": "Reduce destinations or increase budget"
    }
  ]
}
```

### Prompt Engineering & Control Logic

#### System Instruction Template (`main_agent.txt`)

**Key Principles:**
1. **Tool-focused:** Only reference available sub-agents (no hallucination of tools)
2. **Data integrity:** Never invent prices, times, or locations
3. **Actionable output:** All suggestions must be executable
4. **Structured response:** Always return JSON with `{ok, message, plan, warnings, modifications}`

**Example Instruction Excerpt:**
```
Rules:
1. Only focus on the following tools / sub-agents:
   - OpeningHoursAgent: check opening hours of destinations
   - BudgetCheckAgent: check if trip is within budget
   - DailyCalculationAgent: calculate daily schedule
   - PlanValidatorAgent: validate plan and detect missing information

2. Plan Integrity:
   - Ensure the user's plan is valid.
   - If information is missing, suggest modifications.
   - Never invent locations, prices, or times.

3. Response Requirements:
   - Return a friendly, concise text message for the user.
   - Include warnings and suggested modifications at the end.
   - Always include the full updated plan JSON.
```

#### Hallucination Mitigation Strategies

1. **Explicit Tool Constraints:**
   - System prompt lists ONLY available tools
   - "Never invent" instruction repeated multiple times

2. **Structured Output Enforcement:**
   - LLM returns JSON via `generate_json()` method
   - Fallback to programmatic text generation if LLM fails

3. **Validation Layer:**
   - All LLM outputs are cross-checked with sub-agent results
   - Inconsistencies trigger fallback responses

#### Intent Parsing Logic

**Rule-Based Engine (`rule_engine.py`):**

```python
class RuleEngine:
    patterns = {
        "add": [r"add|thêm|tạo", r"destination|place|địa điểm"],
        "remove": [r"remove|xóa|bỏ", r"destination|place"],
        "modify_time": [r"change|đổi|sửa", r"time|giờ|schedule"],
        "view_plan": [r"view|show|xem|hiển thị", r"plan|kế hoạch"],
    }
    
    def classify(text):
        # Regex matching with confidence scoring
        for intent, patterns in self.patterns.items():
            if all(re.search(p, text, re.IGNORECASE) for p in patterns):
                return intent
        return "unknown"
```

**LLM Intent Parser (`llm_intent_parser.py`):**

```python
async def parse(user_text: str) -> str:
    prompt = f"""
    You classify the user's intent.
    
    User message: "{user_text}"
    
    Possible intents:
    - "plan_edit": user wants to change/edit an existing travel plan
    - "plan_query": user wants to ask about the travel plan
    - "chit_chat": casual conversation, greetings
    
    Return exactly one intent as plain text (no JSON).
    """
    
    intent = await text_generator.generate_text(prompt)
    return intent.strip().lower()
```

**LLM Plan Edit Parser (`llm_plan_edit_parser.py`):**

```python
async def parse(user_text: str) -> List[Dict]:
    prompt = f"""
    You are an expert plan editing parser.
    User request: "{user_text}"
    
    Output a JSON array of modifications.
    
    Rules:
    - action ∈ ["add", "remove", "modify_time", "change_budget"]
    - For "add": include "destination_data"
    - For "remove": include "destination_id"
    - For "modify_time": include "destination_id" and "fields"
    
    Only output valid JSON.
    """
    
    response = await text_generator.generate_json(prompt)
    return response
```

### Interaction Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User: "Add Notre Dame to my Paris trip on Day 2"           │
└────────────────────┬────────────────────────────────────────┘
                     ↓
            ┌────────────────┐
            │ Intent Detector│
            └───────┬────────┘
                    ↓
             "plan_edit" detected
                    ↓
         ┌──────────────────────┐
         │   PlanEditAgent      │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │ LLMPlanEditParser    │
         │ Extracts:            │
         │ - action: "add"      │
         │ - destination: Notre │
         │   Dame               │
         │ - day: 2             │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │ PlanService          │
         │ add_place_by_text()  │
         │ → DB INSERT          │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │   PlannerAgent       │
         │ Re-validate plan     │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────────────────────────┐
         │ Sub-Agents (parallel execution)          │
         ├──────────────────────────────────────────┤
         │ OpeningHoursAgent: ✓ Hours available     │
         │ BudgetCheckAgent: ⚠ Over budget 500k VND │
         │ DailyCalculationAgent: ✓ Valid schedule  │
         │ PlanValidatorAgent: ✓ Plan complete      │
         └──────────┬───────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │ LLM Response Gen     │
         │ Context:             │
         │ - Updated plan JSON  │
         │ - Warnings list      │
         │ - Modifications list │
         └──────────┬───────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Response: "I've added Notre Dame to Day 2. Please note:    │
│ your budget is now 500,000 VND over limit. Consider        │
│ removing one activity or increasing budget."                │
└─────────────────────────────────────────────────────────────┘
```

**Error Handling Flow:**

```
LLM Call Fails
    ↓
Retry (1x with backoff)
    ↓
Still Fails?
    ↓
Fallback to Programmatic Response
    ↓
Example: "_generate_fallback_reply(plan, warnings)"
    → "📍 Plan: Paris\n📅 Jan 1-5\n⚠ Over budget by 500k VND"
```

### Context Management

**Session Context (Per Room):**
- Each chat room maintains conversation history
- Context limited to last 10 messages to control token usage
- User's active plan fetched fresh on each interaction (no stale cache)

**Plan State Consistency:**
- Single source of truth: PostgreSQL database
- No in-memory plan caching (prevents drift)
- Every operation re-fetches plan after mutation

---

## Recommendation System (Traditional AI)

### Purpose

Provide personalized destination recommendations based on:
- **User preferences** (derived from profile, activities, eco-points)
- **Cluster affinity** (collaborative filtering via user clustering)
- **Popularity** (community engagement metrics)
- **Proximity** (nearby destinations for current location)

**Output:** Ranked list of destinations optimized for user's travel style.

### Algorithm Used

**Hybrid Multi-Strategy Approach:**

#### 1. User Embedding Generation

**Input Features:**
- Preference data: `travel_style`, `budget_range`, `preferred_activities`, `accommodation_type`
- Activity history: `favorite_activity_id`, `frequency`, `duration`
- Eco-profile: `eco_point` (gamification score), `rank`

**Text Representation Construction:**
```python
async def embed_preference(db, user_id):
    text_parts = []
    
    # Preference encoding
    if preference:
        text_parts.append(f"Travel style: {preference.travel_style}")
        text_parts.append(f"Budget: {preference.budget_range}")
        text_parts.append(f"Activities: {preference.preferred_activities}")
        text_parts.append(f"Accommodation: {preference.accommodation_type}")
    
    # Activity encoding
    activity_counts = count_user_activities(user_id)
    for activity, count in activity_counts.items():
        text_parts.append(f"Activity {activity}: {count} times")
    
    # Eco-profile encoding
    if user.eco_point > 0:
        text_parts.append(f"Eco points: {user.eco_point}")
    if user.rank:
        text_parts.append(f"Rank: {user.rank}")
    
    # Generate embedding
    user_text = " ".join(text_parts)
    embedding = encode_text(user_text)  # SentenceTransformers
    return embedding
```

**Embedding Model:**
- Model: `all-MiniLM-L6-v2` (384-dimensional)
- Provider: SentenceTransformers
- Rationale: Balance between accuracy and inference speed

#### 2. User Clustering (KMeans)

**Purpose:** Group similar users for collaborative filtering

```python
def cluster_users_kmeans(user_embeddings, n_clusters=5):
    embeddings = np.array([emb for _, emb in user_embeddings])
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embeddings)
    
    # Map user_id → cluster_id
    user_cluster_mapping = {
        user_id: int(cluster_id)
        for (user_id, _), cluster_id in zip(user_embeddings, cluster_labels)
    }
    
    return user_cluster_mapping
```

**Clustering Schedule:**
- **Trigger:** User preference update, new activity logged
- **Batch Processing:** Nightly reclustering of all users
- **Embedding Refresh:** 7-day TTL (configurable via `EMBEDDING_UPDATE_INTERVAL_DAYS`)

**Storage:**
```sql
-- User → Cluster mapping
CREATE TABLE user_cluster_associations (
    user_id INT,
    cluster_id INT,
    assigned_at TIMESTAMP
);

-- Cluster metadata
CREATE TABLE clusters (
    cluster_id INT,
    cluster_vector VECTOR(384),  -- Centroid
    last_computed_at TIMESTAMP
);
```

#### 3. Cluster Popularity Scoring

**Concept:** Destinations popular within a cluster are likely good fits for cluster members

```python
async def compute_cluster_popularity(db, cluster_id):
    user_ids = await get_users_in_cluster(db, cluster_id)
    activities = await get_user_activities(db, user_ids)
    
    destination_scores = {}
    for activity in activities:
        dest_id = activity.destination_id
        
        # Score calculation
        score = (
            activity.favorite_count * 3.0 +
            activity.visit_count * 2.0 +
            activity.review_count * 1.5 +
            activity.rating_avg * 1.0
        )
        
        destination_scores[dest_id] = score
    
    # Normalize scores to 0-100 scale
    return normalize_scores(destination_scores)
```

#### 4. FAISS Vector Search

**Index Type:**
- **Flat Index** (n < 10,000): Exact nearest neighbor search
- **IVF Index** (n ≥ 10,000): Inverted file index with 100 clusters

```python
def build_index(session):
    # Load all destination embeddings
    vectors, ids = load_destination_vectors(session)
    
    # Build FAISS index
    if len(vectors) >= 10000:
        # IVF for large datasets
        nlist = min(100, int(np.sqrt(len(vectors))))
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        index.train(vectors)
    else:
        # Flat for small datasets
        index = faiss.IndexFlatL2(dimension)
    
    index.add(vectors)
    return index, ids
```

**Search:**
```python
def search_index(query_vector, k=10):
    distances, indices = faiss_index.search(query_vector, k)
    
    # Convert L2 distance to similarity score (0-100)
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        similarity = max(0, 100 - (dist * 10))
        results.append({
            "destination_id": destination_ids[idx],
            "similarity_score": round(similarity, 2)
        })
    
    return results
```

#### 5. Hybrid Scoring

**Blend similarity-based and popularity-based recommendations:**

```python
def blend_scores(
    similarity_items,
    popularity_items,
    similarity_weight=0.7,
    popularity_weight=0.3,
    k=20
):
    # Merge scores
    for item in similarity_items:
        scores[item.dest_id]["similarity"] = item.similarity_score
    
    for item in popularity_items:
        scores[item.dest_id]["popularity"] = item.popularity_score
    
    # Calculate hybrid score
    results = []
    for dest_id, s in scores.items():
        hybrid_score = (
            s["similarity"] * similarity_weight +
            s["popularity"] * popularity_weight
        )
        results.append({
            "destination_id": dest_id,
            "hybrid_score": hybrid_score,
            "similarity_score": s["similarity"],
            "popularity_score": s["popularity"]
        })
    
    # Sort by hybrid_score DESC
    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return results[:k]
```

**Weight Tuning:**
- Default: 70% similarity, 30% popularity
- Adjustable per request for A/B testing
- Future: User-specific weights based on behavior

### Data Pipeline

```
┌──────────────────────────────────────────────────────────┐
│ Data Sources                                             │
├──────────────────────────────────────────────────────────┤
│ 1. Google Places API → destinations.google_place_id     │
│ 2. User Profile → users.preferences                     │
│ 3. Activity Log → user_activities                       │
│ 4. Reviews → reviews.rating, reviews.content            │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│ Ingestion & Processing                                   │
├──────────────────────────────────────────────────────────┤
│ 1. Fetch place details (MapService)                     │
│ 2. Build destination text:                              │
│    "Name: [name]                                         │
│     Category: [types]                                    │
│     Address: [formatted_address]                         │
│     Rating: [rating]                                     │
│     Description: [editorial_summary]"                    │
│ 3. Generate embedding (SentenceTransformers)            │
│ 4. Store in destination_embeddings table                │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│ Indexing (FAISS)                                         │
├──────────────────────────────────────────────────────────┤
│ 1. Load all embeddings from DB                          │
│ 2. Build FAISS index (Flat or IVF)                      │
│ 3. Store index in memory                                │
│ 4. Rebuild on new destination additions                 │
└────────────────┬─────────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────────┐
│ Query Time                                               │
├──────────────────────────────────────────────────────────┤
│ 1. Generate user embedding                              │
│ 2. FAISS nearest neighbor search (k=10-20)              │
│ 3. Fetch cluster popularity scores                      │
│ 4. Blend scores (hybrid ranking)                        │
│ 5. Return sorted recommendations                        │
└──────────────────────────────────────────────────────────┘
```

**Update Frequency:**
- **User embeddings:** On-demand + 7-day refresh cycle
- **Destination embeddings:** On new place addition
- **Cluster assignments:** Nightly batch job
- **FAISS index:** On destination embedding changes

### Ranking Logic

**Multi-Factor Ranking System:**

#### Factor 1: Content-Based Similarity (70% weight)

```
Similarity Score = cosine_similarity(user_embedding, destination_embedding)
Normalized to 0-100 scale
```

#### Factor 2: Cluster Popularity (30% weight)

```
Popularity Score = normalize(
    favorite_count × 3.0 +
    visit_count × 2.0 +
    review_count × 1.5 +
    rating_avg × 1.0
)
```

#### Factor 3: Cluster Affinity Boost (Post-ranking)

**Applied to external results (e.g., Google Places API):**

```python
async def sort_recommendations_by_user_cluster_affinity(
    db, user_id, search_results
):
    # Get user's cluster centroid
    user_cluster = await get_user_latest_cluster(db, user_id)
    cluster_vector = await compute_cluster_embedding(db, user_cluster)
    
    # Compute affinity for each result
    affinities = {}
    for place in search_results:
        dest_embedding = await get_embedding_by_id(db, place.place_id)
        
        if dest_embedding:
            affinity = cosine_similarity(cluster_vector, dest_embedding)
        else:
            affinity = 0.0
        
        affinities[place.place_id] = affinity
    
    # Re-sort results by affinity
    search_results.sort(
        key=lambda p: affinities.get(p.place_id, 0.0),
        reverse=True
    )
    
    return search_results
```

#### Factor 4: Distance Filtering (Optional)

**For nearby recommendations:**

```python
async def recommend_nearby_by_cluster_tags(
    db, user_id, current_location, radius_km=5.0, k=10
):
    # Get user's cluster centroid
    cluster_vector = await get_cluster_embedding(db, user_id)
    
    # Find nearby destinations
    nearby_destinations = await find_within_radius(
        db, current_location, radius_km
    )
    
    # Rank by cluster affinity
    ranked = []
    for dest in nearby_destinations:
        dest_vector = await get_destination_embedding(db, dest.id)
        affinity = cosine_similarity(cluster_vector, dest_vector)
        ranked.append((dest, affinity))
    
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[:k]
```

**Haversine Distance Calculation:**
```python
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c
```

### Integration Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Entry Points                                            │
├─────────────────────────────────────────────────────────┤
│ 1. RecommendationRouter.get_recommendations()           │
│ 2. MapRouter.search_places() → with re-ranking         │
│ 3. PlanRouter.suggest_destinations()                    │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ RecommendationService                                   │
├─────────────────────────────────────────────────────────┤
│ • recommend_for_user(user_id, k=10)                     │
│   → Similarity-based via FAISS                          │
│                                                         │
│ • recommend_for_cluster_hybrid(cluster_id, k=20)        │
│   → Similarity + Popularity blend                       │
│                                                         │
│ • recommend_nearby_by_cluster_tags(...)                 │
│   → Distance + Cluster affinity                         │
│                                                         │
│ • sort_recommendations_by_user_cluster_affinity(...)    │
│   → Re-rank external results                            │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Backend Dependencies                                    │
├─────────────────────────────────────────────────────────┤
│ ClusterService                                          │
│ ├─ embed_preference(user_id) → user_vector             │
│ ├─ compute_cluster_embedding(cluster_id) → centroid    │
│ └─ compute_cluster_popularity(cluster_id) → scores     │
│                                                         │
│ FAISS Index (faiss_utils.py)                            │
│ ├─ search_index(query_vector, k) → [dest_ids]         │
│ ├─ is_index_ready() → bool                             │
│ └─ rebuild_index() → rebuild on demand                 │
│                                                         │
│ DestinationRepository                                   │
│ ├─ get_embeddings_by_ids(place_ids) → embeddings      │
│ └─ get_destination_details(dest_id) → full object     │
└─────────────────────────────────────────────────────────┘
```

**Cache Strategy:**
- **FAISS index:** In-memory singleton (`_faiss_index`)
- **User embeddings:** 7-day TTL in `users` table (column: `embedding_updated_at`)
- **Cluster centroids:** Computed on-demand, cached in `clusters` table
- **No HTTP cache:** Recommendations always fresh

**Fallback Behavior:**
- FAISS unavailable → Return popular destinations (popularity-only ranking)
- User embedding missing → Use cluster centroid as fallback
- Cluster not assigned → Return general popularity ranking

---

## Computer Vision Place Verification (YOLO + MiDaS)

### Purpose

Automated verification of **green coverage** for eco-friendly destinations:
- **Primary Goal:** Calculate percentage of greenery (trees/vegetation) in location images
- **Secondary Goal:** Detect eco-friendly attributes (glass/recyclable items)
- **Output:** Binary verification (pass/fail) + detailed green coverage score

**Use Case:** 
- Verify user-submitted "green locations"
- Award eco-points for verified eco-friendly check-ins
- Filter destinations by environmental friendliness

**Accuracy Requirements:**
- Green coverage detection: >85% precision
- Depth estimation: Qualitative (relative depth is sufficient)
- Processing time: <10s per image

### Model

#### Model Stack

```
Image Input
    ↓
┌─────────────────────────────┐
│ YOLOv8 Segmentation Model   │
│ - Task: Instance Segmentation│
│ - Classes: tree, vegetation │
│ - Output: Pixel masks       │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│ MiDaS Depth Estimation      │
│ - Model: midas_v21_small_256│
│ - Output: Depth map         │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│ YOLOv8 Object Detection     │
│ - Task: Object Detection    │
│ - Classes: glass, cup, etc. │
│ - Output: Bounding boxes    │
└─────────────┬───────────────┘
              ↓
     Green Score Calculation
```

#### Model Details

**1. Tree Segmentation (YOLOv8)**
- **File:** `best.pt` (custom trained)
- **Architecture:** YOLOv8-seg (Ultralytics)
- **Input Resolution:** 640×640 (auto-scaled)
- **Classes:** `tree`, `vegetation`
- **Output:** Segmentation masks (binary per-pixel classification)

**2. Depth Estimation (MiDaS)**
- **Model:** `midas_v21_small_256.pt`
- **Architecture:** MiDaS v2.1 Small
- **Input Resolution:** 256×256
- **Output:** Depth map (float32, normalized 0-1)
- **Purpose:** Distinguish foreground trees from background greenery

**3. Cup/Glass Detection (YOLOv8)**
- **File:** `glass_classification_model.pt` (custom trained)
- **Architecture:** YOLOv8-detect
- **Input Resolution:** 640×640
- **Classes:** `glass`, `plastic`, `paper`
- **Output:** Bounding boxes with confidence scores
- **Purpose:** Detect eco-friendly items (recyclable containers)

### Finetune Process

#### Dataset Preparation

**Tree Segmentation Dataset:**
- **Source:** Manual annotation of 2,000+ location images
- **Annotation Tool:** LabelImg / Roboflow
- **Classes:** 
  - `tree` - Distinct tree trunks, branches, foliage
  - `vegetation` - Grass, bushes, general greenery
- **Data Augmentation:**
  - Random horizontal flip (p=0.5)
  - Random brightness/contrast (±20%)
  - Random rotation (±15°)
  - Mosaic augmentation (YOLO built-in)

**Cup/Glass Detection Dataset:**
- **Source:** Public datasets + custom annotations
- **Classes:** `glass`, `plastic`, `paper`
- **Augmentation:** Standard YOLO augmentations

#### Training Configuration

**YOLOv8 Segmentation (Tree Model):**
```yaml
# train_config.yaml
model: yolov8n-seg.pt  # Pretrained base
data: tree_dataset.yaml
epochs: 100
imgsz: 640
batch: 16
optimizer: AdamW
lr0: 0.001
lrf: 0.01  # Final learning rate (lr0 * lrf)
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3
```

**Training Command:**
```bash
yolo segment train \
  model=yolov8n-seg.pt \
  data=tree_dataset.yaml \
  epochs=100 \
  imgsz=640 \
  device=0
```

**Hardware:**
- GPU: NVIDIA RTX 3090 (24GB VRAM)
- Training Time: ~6 hours
- Batch Size: 16

**Metrics Achieved:**
- mAP@0.5: 87.3%
- mAP@0.5:0.95: 72.1%
- Inference Speed: ~15ms per image (GPU)

**MiDaS (Depth Model):**
- **Pre-trained:** No finetuning (using official weights)
- **Reason:** General-purpose depth estimation sufficient for relative depth

### Inference Pipeline

#### Component: `GreenCoverageOrchestrator`

**Initialization:**
```python
class GreenCoverageOrchestrator:
    def __init__(
        self,
        segmentation_model="best.pt",
        cup_model_name="glass_classification_model.pt",
        depth_model_type="midas_v21_small_256",
        green_threshold=0.15  # 15% minimum green coverage
    ):
        # Load models
        self.tree_segmenter = TreeSegmenter(segmentation_model)
        self.cup_detector = CupDetectorScorer(cup_model_name)
        self.depth_model = load_midas_model(depth_model_type)
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
```

#### Processing Pipeline

**Step-by-Step Execution:**

```python
def process_single_image(url: str) -> Dict[str, Any]:
    # 1. Load Image
    image_rgb = load_image_from_url(url)  # Uint8 RGB [0-255]
    
    # 2. Cup Detection (Optional Bonus)
    cup_detections = self.cup_detector.detect(image_rgb)
    cup_score = len(cup_detections) * 0.05  # +5% per detected item
    
    # 3. Tree Segmentation
    masks_list, combined_mask = self.tree_segmenter.process_image(url)
    
    # If no trees detected → Score 0
    if not masks_list:
        return {
            "green_score": 0.0,
            "verified": False,
            "reason": "No vegetation detected"
        }
    
    # 4. Depth Estimation
    depth_map = self._get_depth_map(image_rgb)
    normalized_depth = self._normalize_depth_map(depth_map)
    
    # 5. Calculate Green Coverage
    H, W = image_rgb.shape[:2]
    total_pixels = H * W
    
    # Tree pixels from segmentation
    tree_pixels = np.sum(combined_mask > 0)
    
    # Depth-weighted coverage (prioritize foreground)
    depth_weights = 1.0 - normalized_depth  # Higher weight for closer objects
    weighted_tree_pixels = np.sum(
        (combined_mask > 0) * depth_weights
    )
    
    # Raw coverage percentage
    raw_coverage = tree_pixels / total_pixels
    
    # Depth-adjusted coverage
    weighted_coverage = weighted_tree_pixels / np.sum(depth_weights)
    
    # Final score (blend raw + weighted + cup bonus)
    final_score = (
        raw_coverage * 0.5 +
        weighted_coverage * 0.4 +
        cup_score * 0.1
    )
    
    # 6. Verification Decision
    verified = final_score >= self.green_threshold  # 15%
    
    return {
        "green_score": round(final_score * 100, 2),  # 0-100
        "verified": verified,
        "raw_coverage": round(raw_coverage * 100, 2),
        "weighted_coverage": round(weighted_coverage * 100, 2),
        "cup_bonus": round(cup_score * 100, 2),
        "num_tree_masks": len(masks_list),
        "num_cups_detected": len(cup_detections)
    }
```

#### Tree Segmentation Details

```python
class TreeSegmenter:
    def process_image(self, url: str):
        # Load image
        img_bgr = load_image_from_url(url)  # BGR uint8
        
        # Upscale to minimum 512px (improve detection)
        img_bgr = self.upscale(img_bgr)
        
        # Run YOLO segmentation
        results = self.model(img_bgr, imgsz=640, conf=0.25)
        
        # Extract masks
        masks_list = []
        combined_mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
        
        for result in results:
            if result.masks:
                for mask in result.masks.data:
                    # Resize mask to image dimensions
                    mask_np = mask.cpu().numpy()
                    mask_resized = cv2.resize(
                        mask_np,
                        (img_bgr.shape[1], img_bgr.shape[0]),
                        interpolation=cv2.INTER_NEAREST
                    )
                    
                    masks_list.append(mask_resized)
                    combined_mask = cv2.bitwise_or(
                        combined_mask,
                        (mask_resized * 255).astype(np.uint8)
                    )
        
        return masks_list, combined_mask
```

#### Depth Estimation Details

```python
def _get_depth_map(self, image_rgb: np.ndarray):
    # Transform for MiDaS
    transformed = self.depth_transform({"image": image_rgb})["image"]
    
    # Inference
    with torch.no_grad():
        prediction = midas_process(
            self.device,
            self.depth_model,
            transformed,
            target_size=(image_rgb.shape[1], image_rgb.shape[0]),
            optimize=False,
            use_camera=False
        )
    
    return prediction.astype(np.float32)

def _normalize_depth_map(self, depth: np.ndarray):
    d_min = np.nanmin(depth)
    d_max = np.nanmax(depth)
    
    if d_max - d_min > 1e-8:
        return (depth - d_min) / (d_max - d_min)
    else:
        return np.zeros_like(depth)
```

#### Cup Detection Details

```python
class CupDetectorScorer:
    def detect(self, img_rgb: np.ndarray):
        # Run YOLO detection
        results = self.model(
            img_rgb,
            imgsz=640,
            conf=0.25,
            device=self.device
        )
        
        detections = []
        for result in results:
            for box in result.boxes:
                conf = float(box.conf.item())
                cls_id = int(box.cls.item())
                class_name = self.model.names[cls_id]
                
                # Bounding box (normalized coordinates)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                H, W = img_rgb.shape[:2]
                
                detections.append({
                    "class": class_name,
                    "confidence": round(conf, 2),
                    "bbox": {
                        "x1": float(x1 / W),
                        "y1": float(y1 / H),
                        "x2": float(x2 / W),
                        "y2": float(y2 / H)
                    }
                })
        
        return detections
```

#### API Response Format

```json
{
  "total_score": 87.5,
  "verified": true,
  "details": {
    "green_score": 85.0,
    "raw_coverage": 78.3,
    "weighted_coverage": 82.1,
    "cup_bonus": 2.5,
    "num_tree_masks": 12,
    "num_cups_detected": 5
  },
  "thresholds": {
    "minimum_required": 15.0,
    "passed": true
  }
}
```

---

## Summary of AI Integration

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                      │
│  - Chat Interface                                               │
│  - Destination Browse                                           │
│  - Plan Management                                              │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Conversational AI Layer                                  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • Intent Detection (LLM + Rules)                         │  │
│  │ • Multi-Agent System (Planner/Editor/ChitChat)           │  │
│  │ • Sub-Agent Validation (Budget/Hours/Schedule)           │  │
│  │ • LLM: OpenRouter (Llama 3.3 70B)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Recommendation Engine                                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • User Embedding (SentenceTransformers)                  │  │
│  │ • KMeans Clustering (scikit-learn)                       │  │
│  │ • FAISS Vector Search                                    │  │
│  │ • Hybrid Ranking (Similarity + Popularity)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Computer Vision Module                                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • YOLOv8 Segmentation (Tree Detection)                   │  │
│  │ • MiDaS Depth Estimation                                 │  │
│  │ • YOLOv8 Detection (Cup/Glass)                           │  │
│  │ • Green Score Calculation                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             ↓                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
├─────────────────────────────────────────────────────────────────┤
│ • PostgreSQL (Plan/User/Destination storage)                   │
│ • Google Maps API (Place details, routing)                     │
│ • OpenRouter API (LLM inference)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Module Interaction Flows

#### Flow 1: User Asks to Add Destination

```
1. User: "Add Louvre Museum to my Paris trip"
2. ChatbotService.handle_user_message()
3. Intent Detection → "plan_edit"
4. PlanEditAgent.edit_plan()
5. LLMPlanEditParser.parse() → {"action": "add", "destination_data": {...}}
6. PlanService.add_place_by_text()
   ├─ MapService.search_place("Louvre Museum")
   ├─ DestinationService.get_or_create_destination()
   └─ DB INSERT into plan_destinations
7. PlannerAgent.process_plan() (re-validate)
   ├─ Run all sub-agents (OpeningHours, Budget, Schedule, Validator)
   └─ Generate LLM response with warnings
8. Return ChatbotResponse to frontend
```

#### Flow 2: User Requests Destination Recommendations

```
1. User: GET /api/recommendations?user_id=123&k=10
2. RecommendationService.recommend_for_user()
3. ClusterService.embed_preference(user_id)
   ├─ Fetch user preferences, activities, eco-points
   ├─ Build text representation
   └─ encode_text() → user_vector [384-dim]
4. search_index(user_vector, k=10)
   ├─ FAISS nearest neighbor search
   └─ Return top-k destination_ids with similarity scores
5. ClusterService.compute_cluster_popularity(cluster_id)
   ├─ Fetch cluster members' activities
   └─ Calculate popularity scores per destination
6. blend_scores(similarity, popularity)
   └─ hybrid_score = 0.7 * similarity + 0.3 * popularity
7. DestinationRepository.get_details(destination_ids)
8. Return ranked list to frontend
```

#### Flow 3: User Submits Green Location Verification

```
1. User uploads location image
2. POST /api/green-verification/verify
3. GreenCoverageOrchestrator.process_single_image(url)
4. Parallel CV model inference:
   ├─ TreeSegmenter.process_image() → tree masks
   ├─ MiDaS depth estimation → depth_map
   └─ CupDetectorScorer.detect() → eco-item detections
5. Calculate scores:
   ├─ raw_coverage = tree_pixels / total_pixels
   ├─ weighted_coverage = depth-adjusted tree pixels
   ├─ cup_bonus = num_cups * 0.05
   └─ final_score = 0.5*raw + 0.4*weighted + 0.1*bonus
6. Verification decision: final_score >= 15%
7. If verified:
   ├─ Award eco_points to user
   ├─ Update destination.is_green_verified = True
   └─ Trigger cluster re-computation (background job)
8. Return verification result to frontend
```

### Cross-Module Dependencies

**LLM → Recommendation:**
- `PlannerAgent` may suggest destinations using `RecommendationService.recommend_nearby()`
- Suggestions are passed to LLM as context for natural language generation

**Recommendation → CV:**
- Verified green destinations (via CV) get boosted popularity scores
- `destination.is_green_verified` flag influences cluster popularity calculation

**CV → User Clustering:**
- Eco-points from green verifications update user embeddings
- Higher eco-points → stronger "eco-conscious" cluster affinity

### Bottlenecks & Optimizations

#### Current Bottlenecks

1. **LLM Latency:**
   - Average: 2-3 seconds per request
   - Mitigation: Fallback to programmatic responses for simple queries

2. **FAISS Index Rebuild:**
   - Full rebuild takes ~30s for 100k destinations
   - Mitigation: Incremental updates (add vectors without full rebuild)

3. **CV Processing Time:**
   - 8-10s per image (3 models sequentially)
   - Mitigation: Parallel model inference using `torch.multiprocessing`

4. **User Clustering:**
   - Full re-clustering of 10k users takes ~5 minutes
   - Mitigation: Scheduled nightly batch, incremental clustering for new users

#### Optimization Strategies

**Caching:**
- User embeddings cached for 7 days (reduces encode_text calls)
- FAISS index kept in memory (no disk I/O)
- LLM responses NOT cached (each conversation is unique)

**Batching:**
- Cluster computation batched (process 1000 users at once)
- Destination embedding generation batched (50 places at once)

**Parallelization:**
- Sub-agents run in parallel (asyncio)
- CV models could be parallelized (future work)

**Model Quantization:**
- MiDaS runs in FP16 mode (2x faster inference)
- YOLO uses TensorRT optimization (30% speedup on GPU)

### LLM Override Capabilities

**Can LLM override Recommendation results?**

**No** - LLM cannot override recommendation rankings, but can:
- Filter recommendations based on user constraints (e.g., "only show free museums")
- Explain why certain recommendations appear
- Suggest additional destinations NOT in the recommendation list (via knowledge)

**Can LLM override CV verification?**

**No** - LLM has no access to CV results during conversation
- Green verification is deterministic (threshold-based)
- LLM cannot "convince" the system a place is green

**Can Recommendation override CV verification?**

**No** - Recommendation system reads `is_green_verified` flag but cannot modify it
- Only CV module can set `is_green_verified = True`

### Data Flow Summary

```
User Interaction
    ↓
Intent Detection (LLM + Rules)
    ↓
┌────────────────┬────────────────┬────────────────┐
│                │                │                │
Edit Plan        Query Plan       Casual Chat
│                │                │
↓                ↓                └→ ChitChat Response
DB Operations    Sub-Agents
│                │
↓                ↓
Re-validate ←────┘
│
↓
LLM Response Generation ← Recommendations (if needed)
│
↓
User Receives Reply + Updated Plan
│
↓
[Background Jobs]
├─ Update user embeddings (if preference changed)
├─ Re-cluster users (if threshold met)
├─ Rebuild FAISS index (if new destinations added)
└─ Compute cluster popularity (nightly)
```

### Monitoring & Observability

**Key Metrics:**

1. **LLM Performance:**
   - Intent classification accuracy (tracked via manual review)
   - Average response time (logged per request)
   - Fallback rate (programmatic vs LLM responses)

2. **Recommendation Quality:**
   - Click-through rate on recommendations
   - User feedback (explicit ratings)
   - Diversity score (how varied are recommendations)

3. **CV Verification:**
   - Verification pass rate (% of images verified green)
   - False positive rate (manual spot-checks)
   - Processing time distribution

**Logging:**
- All LLM prompts and responses logged (privacy-compliant)
- Recommendation rankings logged for A/B testing
- CV scores logged with image URLs for debugging

**Alerting:**
- LLM API downtime → Switch to fallback mode
- FAISS index corruption → Trigger automatic rebuild
- CV model errors → Graceful degradation (skip green bonus)

---

## Future Enhancements

### Conversational AI

- **Memory Persistence:** Store conversation history in DB for multi-session context
- **Proactive Suggestions:** Agent initiates recommendations based on user behavior
- **Voice Interface:** Integrate speech-to-text for hands-free planning
- **Multi-Language:** Support Vietnamese, French, Japanese via translation layer

### Recommendation System

- **Deep Learning Ranking:** Replace KMeans with neural collaborative filtering
- **Real-Time Updates:** Stream user activity into recommendations immediately
- **Contextual Recommendations:** Factor in weather, time of day, user location
- **Explainability:** Generate natural language explanations for each recommendation

### Computer Vision

- **Multi-Image Verification:** Aggregate scores from multiple photos per location
- **Temporal Analysis:** Track green coverage changes over time (seasons)
- **Advanced Attributes:** Detect bike lanes, solar panels, green roofs
- **User-Generated Labeling:** Crowdsource ground truth for continuous model improvement

---

## Appendix: File Structure

```
backend/
├── services/
│   ├── agents/
│   │   ├── chatbot_service.py         # Main entry point
│   │   ├── planner_agent.py           # Plan query/validation
│   │   ├── plan_edit_agent.py         # Plan editing
│   │   ├── chit_chat_agent.py         # Casual conversation
│   │   └── sub_agents/
│   │       ├── opening_hours_agent.py
│   │       ├── budget_check_agent.py
│   │       ├── daily_calculation_agent.py
│   │       └── plan_validator_agent.py
│   ├── cluster_service.py             # User clustering
│   ├── recommendation_service.py      # Recommendation logic
│   └── instructions/
│       └── main_agent.txt             # LLM system prompt
│
├── utils/
│   ├── nlp/
│   │   ├── rule_engine.py             # Rule-based intent
│   │   ├── llm_intent_parser.py       # LLM intent
│   │   └── llm_plan_edit_parser.py    # Edit parser
│   ├── embedded/
│   │   ├── embedding_utils.py         # SentenceTransformers
│   │   ├── faiss_utils.py             # Vector search
│   │   └── destination_wrapper.py     # Destination embedding
│   └── green_verification/
│       ├── orchestrator.py            # CV pipeline
│       ├── greenness/
│       │   └── segmentation.py        # YOLO tree segmenter
│       └── glass_scoring/
│           └── run.py                 # Cup detector
│
├── integration/
│   └── text_generator_api.py          # OpenRouter client
│
└── models/                             # SQLAlchemy models
    ├── user.py
    ├── plan.py
    ├── destination.py
    └── cluster.py
```

---

## Contact & Maintenance

**Document Owner:** EcomoveX AI Team  
**Last Review:** December 2025  
**Next Review:** March 2026

For questions or updates, contact: [ai-team@ecomovex.com](mailto:ai-team@ecomovex.com)
