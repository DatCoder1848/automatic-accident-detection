# System Diagrams

## 1. Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Admin[🧑‍💼 Admin]
        Operator[👷 Operator]
        AI[🤖 AI Engine]
    end

    subgraph System["🚨 Accident Detection System"]
        UC1[Login / Register]
        UC2[Manage Users]
        UC3[Manage Cameras]
        UC4[Configure AI Calibration]
        UC5[View Dashboard]
        UC6[View Accidents]
        UC7[Update Accident Status]
        UC8[View Alerts]
        UC9[Mark Alert as Read]
        UC10[Detect Accident]
        UC11[Report Accident via API]
        UC12[Upload Video Evidence]
        UC13[Receive Real-time Notification]
    end

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC13

    Operator --> UC1
    Operator --> UC5
    Operator --> UC6
    Operator --> UC7
    Operator --> UC8
    Operator --> UC9
    Operator --> UC13

    AI --> UC10
    AI --> UC11
    AI --> UC12
```

---

## 2. ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar password
        varchar name
        enum role "ADMIN | OPERATOR | VIEWER"
        datetime created_at
        datetime updated_at
    }

    CAMERAS {
        uuid id PK
        varchar name
        varchar location
        varchar stream_url
        enum status "ACTIVE | INACTIVE | MAINTENANCE"
        jsonb ai_config
        datetime created_at
        datetime updated_at
    }

    ACCIDENTS {
        uuid id PK
        varchar incident_id
        uuid camera_id FK
        datetime detected_at
        float confidence
        enum severity "LOW | MEDIUM | HIGH | CRITICAL"
        enum status "PENDING | CONFIRMED | FALSE_ALARM | RESOLVED"
        varchar video_clip_url
        varchar thumbnail_url
        text[] vehicles_involved
        float latitude
        float longitude
        varchar description
        datetime created_at
        datetime updated_at
    }

    ALERTS {
        uuid id PK
        uuid accident_id FK
        uuid user_id FK
        enum type "NOTIFICATION | EMAIL | SMS"
        enum status "UNREAD | READ | DISMISSED"
        varchar message
        datetime sent_at
        datetime read_at
    }

    CAMERAS ||--o{ ACCIDENTS : "has many"
    ACCIDENTS ||--o{ ALERTS : "triggers"
    USERS ||--o{ ALERTS : "receives"
```

---

## 3. Sequence Diagram — Accident Detection Flow

```mermaid
sequenceDiagram
    participant AI as 🤖 AI Engine
    participant Cloud as ☁️ Cloudinary
    participant BE as 🖥️ Backend API
    participant DB as 🐘 Supabase DB
    participant WS as 📡 WebSocket
    participant FE as 🌐 Frontend

    Note over AI: Vehicle collision detected

    rect rgb(255, 230, 230)
        Note over AI,FE: Thread 1 — Instant Alert (< 1s)
        AI->>BE: POST /accidents (no video)
        BE->>DB: INSERT accident record
        BE->>DB: INSERT alerts for all users
        BE->>WS: emit "new-accident"
        WS->>FE: 🚨 Notification popup
    end

    rect rgb(230, 255, 230)
        Note over AI,FE: Thread 2 — Video Evidence (5-10s later)
        AI->>Cloud: Upload video clip + thumbnail
        Cloud-->>AI: Return URLs
        AI->>BE: POST /accidents (with videoClipUrl + thumbnailUrl)
        BE->>DB: UPDATE accident with video URL
        BE->>WS: emit "accident-video-ready"
        WS->>FE: 📹 Show video player
    end
```

---

## 4. System Architecture Diagram

```mermaid
graph LR
    subgraph AI["🎥 AI Engine (Python)"]
        YOLO[YOLOv8 Detection]
        BEV[Bird's Eye View]
        Track[ByteTrack]
        API_Client[API Client]
    end

    subgraph Backend["🖥️ Backend (NestJS)"]
        Auth[Auth Module]
        Accidents[Accidents Module]
        Cameras[Cameras Module]
        Alerts[Alerts Module]
        Events[WebSocket Gateway]
        Upload[Upload Module]
        Prisma[Prisma Service]
    end

    subgraph Storage["💾 Storage"]
        Supabase[(Supabase PostgreSQL)]
        Cloudinary[(Cloudinary CDN)]
    end

    subgraph Client["🌐 Frontend (React)"]
        Dashboard[Dashboard]
        AccPage[Accidents Page]
        CamPage[Cameras Page]
        AlertPage[Alerts Page]
        Socket[WebSocket Client]
    end

    YOLO --> Track --> BEV --> API_Client
    API_Client -->|POST /accidents| Accidents
    API_Client -->|GET /cameras| Cameras
    API_Client -->|Upload| Cloudinary

    Accidents --> Prisma --> Supabase
    Accidents --> Alerts
    Accidents --> Events
    Cameras --> Prisma
    Auth --> Prisma

    Events -->|socket.io| Socket
    Socket --> Dashboard
    Socket --> AccPage

    Dashboard -->|GET /accidents| Accidents
    CamPage -->|GET /cameras| Cameras
    AlertPage -->|GET /alerts| Alerts
```

---

## 5. State Diagram — Accident Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING : AI detects accident
    PENDING --> CONFIRMED : Operator confirms
    PENDING --> FALSE_ALARM : Operator rejects
    CONFIRMED --> RESOLVED : Operator resolves
    FALSE_ALARM --> [*]
    RESOLVED --> [*]
```

---

## 6. Deployment Diagram

```mermaid
graph TB
    subgraph Client["Client (Browser)"]
        React[React App<br/>localhost:5173]
    end

    subgraph Server["Server (Local/Cloud)"]
        NestJS[NestJS API<br/>localhost:3000]
        WSGateway[WebSocket<br/>Gateway]
    end

    subgraph Cloud["Cloud Services"]
        Supabase[(Supabase<br/>PostgreSQL + Storage)]
        Cloudinary[(Cloudinary<br/>Video/Image CDN)]
    end

    subgraph Edge["Edge Device"]
        Python[Python AI Engine<br/>+ YOLOv8 + OpenCV]
        Camera[IP Camera<br/>RTSP Stream]
    end

    Camera -->|RTSP| Python
    Python -->|REST API| NestJS
    Python -->|Upload| Cloudinary
    NestJS -->|SQL| Supabase
    NestJS -->|socket.io| WSGateway
    WSGateway -->|WS| React
    React -->|HTTP| NestJS
    React -->|Load media| Cloudinary
```

---

## 7. Data Flow Diagram

```mermaid
flowchart LR
    A[📹 Camera Stream] --> B[🤖 AI Detection]
    B -->|accident detected| C{Confidence > threshold?}
    C -->|Yes| D[📤 POST /accidents]
    C -->|No| A
    D --> E[💾 Save to DB]
    E --> F[🔔 Create Alerts]
    E --> G[📡 Emit WebSocket]
    G --> H[🌐 Frontend Popup]
    B -->|render video| I[☁️ Upload to Cloudinary]
    I --> J[📤 Update accident with URL]
    J --> K[📡 Emit video-ready]
    K --> L[🌐 Show Video]
```
