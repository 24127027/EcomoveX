EcomoveX is a full-stack platform that supports eco-friendly navigation, sustainable travel habits, and environmental awareness. It helps users explore greener routes, complete sustainability missions, earn rewards, and view detailed place information powered by multiple integrated APIs.

---

## **📚 Table of Contents**

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)

---

## **✨ Features**

- 🔐 **Secure user authentication** with role-based permissions  
- 🗺️ **Eco-navigation map** powered by Google Maps  
- 🎯 **Mission & reward system** to encourage sustainability  
- 📍 **Place details** including distance, photos, and reviews  
- 🧭 **Route planning workflow** for trip organization  
- 🔄 **Seamless integrations** with backend and external APIs  

---

## **🧰 Tech Stack**

### **Frontend**
- Framework: **Next.js (React)**
- Styling: **CSS Modules**
- State Management: **React Hooks**
- APIs Used:
  - **Google Maps SDK**
  - **Custom Backend Services**

### **Backend**
- Framework: **FastAPI**
- Database: **PostgreSQL**
- ORM: **SQLAlchemy**
- Authentication: **OAuth2 + JWT**
- External Integrations:
  - Google **Place**, **Weather**, **Air Quality** APIs  
  - **BREEAM** Green Building Certification  
  - **Climatiq** carbon emission estimation  
  - **HuggingFace** LLM inference  

---

## **📁 Folder Structure**

### **Frontend**
```
src/
 ├─ app/          # Next.js pages, layouts & routing
 ├─ lib/          # Utilities & API clients
```

### **Backend**
```
routers/          # API route definitions
services/         # Business logic & core functionalities
schemas/          # Pydantic request/response models
integration/      # External API clients
models/           # SQLAlchemy database models
repository/       # Database operations
utils/            # Config, helpers, and common utilities
```

---

## **🚀 Setup Instructions**

### **Prerequisites**
Make sure the following are installed:
- Node.js **v16+**
- Python **v3.10**
- PostgreSQL
- Virtual environment tool (**uv**, venv, etc.)

---

### **1. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

---

### **2. Backend Setup**
#### 1. Initialize Database:
- Ensure your PostgreSQL service is running.
- Run the database initialization script in virtual enviroment.
```bash
    cd backend
    python database/create_all_database.py
```
#### 2. Start the Backend Server:
```bash
cd backend
uv venv -p 3.10
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn main:app --reload
```

---

## **🔐 Environment Variables**

### **Frontend `.env`**
Create a `.env` file inside the **frontend** folder:

```
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=
```

---

### **Backend `.env`**
Create a `.env` file inside the **backend** folder:

```
DB_HOST=                 # Database host (e.g. localhost)
DB_PORT=                 # Database port (e.g. 5432)
DB_NAME=                 # PostgreSQL database name
DB_USER=                 # Database username
DB_PASS=                 # Database password

CORS_ORIGINS=            # Comma-separated list of allowed frontend origins

GOOGLE_API_KEY=          # Google Maps + Place + Weather API key
CLIMATIQ_API_KEY=        # Carbon emission API key (from Climatiq)

HUGGINGFACE_API_KEY=     # API key for HuggingFace text generation
OPEN_ROUTER_API_KEY=     # API key for OpenRouter (LLMs)
OPEN_ROUTER_MODEL_NAME=  # Model name used for LLM queries

GCS_BUCKET_NAME=         # Google Cloud Storage bucket name
GOOGLE_APPLICATION_CREDENTIALS=  # Path to your GCP service account JSON file

BREEAM_USERNAME=         # BREEAM API username
BREEAM_PASSWORD=         # BREEAM API password

```

---

## **📡 API Endpoints**

### **Missions**
- `GET /rewards/missions` — Retrieve all missions  
- `POST /rewards/missions` — Create a mission *(Admin only)*  

### **Users**
- `POST /auth/login` — Authenticate user  
- `GET /users/{user_id}` — Get user profile  

> Full endpoint list available in the `routers/` directory.

---