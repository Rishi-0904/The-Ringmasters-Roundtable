# 🎪 Ringmaster's Roundtable
**Live Demo**: https://the-ringmasters-roundtable.vercel.app/
An AI-powered travel planning platform that orchestrates your perfect journey. Built with React, Node.js, Python microservices, and Firebase, this application leverages intelligent agents to create personalized travel experiences with real-time insights.

## 🌟 Features

### Core Travel Planning
- 🗓️ **Smart Itinerary Generation** - AI-powered daily activity planning with 5-8 activities per day
- 💰 **Budget Optimization** - Real-time flight, hotel, and train pricing with cheapest combo finder
- ⛅ **Weather Intelligence** - 7-day forecasts integrated into your itinerary
- 🛣️ **Multi-Modal Routes** - Driving, train, and flight route planning with intermediate stops
- 🎉 **Local Events Discovery** - AI-curated events at your destination
- 🏨 **Accommodation Finder** - OSM-powered hotel and guest house recommendations
- 🍽️ **Restaurant Suggestions** - Local cuisine recommendations with price levels
- 🔮 **Crystal Ball** - AI-powered trip comparison and recommendation engine that analyzes multiple destinations

### AI & Automation
- 🤖 **Pip Digital Agent** - Proactive travel assistant that monitors your trips and surfaces opportunities
- 🔄 **MCP Microservices** - Distributed agent architecture (Map, Weather, Itinerary, Event, Budget)
- 🧠 **Cohere AI Integration** - Natural language event generation and insights
- 📊 **Real-time Orchestration** - RabbitMQ-powered agent communication

### User Experience
- 🔐 **Firebase Authentication** - Secure Google Sign-In
- 💾 **Cloud Storage** - Firestore for trips, opportunities, and user data
- 🔔 **Smart Notifications** - Context-aware Pip alerts every 30 seconds
- 📱 **Responsive Design** - Beautiful UI that works on all devices
- ⚡ **Live Updates** - Socket.IO for real-time trip planning status

## 🛠️ Tech Stack

### Frontend
- ⚛️ React 18
- 🚀 Vite
- 🎨 Tailwind CSS
- 🛣️ React Router v6
- 📅 Date-fns (for date manipulation)
- 🌐 React Icons & Lucide Icons
- 🔄 Socket.IO Client (for real-time features)
- 📱 Framer Motion (for animations)

### Backend
- 🟢 **Node.js** with Express
- 🔌 **Socket.IO** - Real-time bidirectional communication
- 🔥 **Firebase Admin SDK** - Firestore, Authentication
- 🐰 **RabbitMQ** - Message queue for agent orchestration
- 🔄 **RESTful API** - Trip, budget, weather, and opportunity endpoints

### MCP Agents (Python)
- 🐍 **Python 3.13** with Pika (RabbitMQ client)
- 🗺️ **Map Agent** - OpenRouteService route calculation
- ⛅ **Weather Agent** - OpenWeather API integration
- 📋 **Itinerary Agent** - OSM data + AI-powered activity planning
- 🎪 **Event Agent** - Cohere AI event generation
- 💵 **Budget Agent** - Amadeus flight/hotel pricing + Indian Railways API
- 🎯 **Orchestrator** - Coordinates all agents via message passing

### External APIs
- 🌍 **OpenRouteService** - Route planning and geocoding
- ☁️ **OpenWeather** - Weather forecasts
- ✈️ **Amadeus** - Flight and hotel pricing
- 🚂 **Indian Railways API** - Train schedules and pricing
- 🤖 **Cohere** - AI-powered event generation
- 🗺️ **OpenStreetMap/Overpass** - POI data (attractions, restaurants, hotels)
- 🖼️ **Unsplash** - Event imagery

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or later)
- **Python** (v3.13 or later)
- **RabbitMQ** (running on localhost:5672)
- **Firebase Project** (for authentication and Firestore)
- **API Keys** (see Environment Variables section)
- **Git**

### macOS/Linux Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Webster-2025/The-Ringmasters-Roundtable.git
cd The-Ringmasters-Roundtable

# 2. Install frontend dependencies
npm install

# 3. Install backend dependencies
cd backend && npm install && cd ..

# 4. Set up Python environment for MCP agents
cd backend/mcp-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../..

# 5. Configure environment variables (see .env.example)
cp .env.example .env
cp backend/.env.example backend/.env

# 6. Start RabbitMQ (if not running)
brew services start rabbitmq  # macOS
# or: sudo systemctl start rabbitmq-server  # Linux

# 7. Start all services
./launch_app.sh  # Starts frontend, backend, and MCP agents
```

This will start:
- **Frontend** at [http://localhost:5173](http://localhost:5173)
- **Backend API** at [http://localhost:3000](http://localhost:3000)
- **6 MCP Agents** in separate Terminal windows (Orchestrator + 5 workers)

## ⚙️ Environment Variables

### Root `.env` (Frontend)
```bash
# Firebase Configuration
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id

# API Configuration
API_BASE_URL=http://localhost:3000

# External APIs
OPENWEATHER_API_KEY=your_openweather_key
ORS_API_KEY=your_openrouteservice_key
COHERE_API_KEY=your_cohere_key
AMADEUS_CLIENT_ID=your_amadeus_id
AMADEUS_CLIENT_SECRET=your_amadeus_secret

# Pip Agent Configuration
PIP_AGENT_ENABLED=false
VITE_PIP_POLL_INTERVAL_MS=30000

# Firestore Quota Management
USE_FIRESTORE=true
OPPORTUNITIES_CACHE_TTL_MS=120000
MAX_OPPORTUNITIES_PER_USER=20
```

### `backend/.env`
```bash
PORT=3000
ENABLE_RABBITMQ=true

# Firebase Admin SDK
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# External APIs (same as root .env)
OPENWEATHER_API_KEY=your_key
ORS_API_KEY=your_key
COHERE_API_KEY=your_key
AMADEUS_CLIENT_ID=your_id
AMADEUS_CLIENT_SECRET=your_secret
UNSPLASH_ACCESS_KEY=your_unsplash_key

# Pip Agent
PIP_AGENT_ENABLED=false
PIP_AGENT_CRON=*/2 * * * *
PIP_AGENT_MAX_TRIPS_PER_RUN=5

# Firestore
USE_FIRESTORE=true
OPPORTUNITIES_CACHE_TTL_MS=120000
MAX_OPPORTUNITIES_PER_USER=20
```

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐
│   React Frontend│ ← User Interface
│   (Port 5173)   │
└────────┬────────┘
         │ HTTP/WebSocket
         ↓
┌─────────────────┐
│  Node.js Backend│ ← API Server + Socket.IO
│   (Port 3000)   │
└────────┬────────┘
         │ RabbitMQ Messages
         ↓
┌─────────────────────────────────────────┐
│         MCP Agent Orchestrator          │
│  (Coordinates distributed microservices)│
└──┬──────┬──────┬──────┬──────┬─────────┘
   │      │      │      │      │
   ↓      ↓      ↓      ↓      ↓
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
│ Map  ││Weather││Itinerary││Event││Budget│
│Agent ││Agent ││Agent ││Agent││Agent │
└──────┘└──────┘└──────┘└──────┘└──────┘
   │      │      │      │      │
   └──────┴──────┴──────┴──────┘
              │
              ↓
   ┌──────────────────────┐
   │   External APIs      │
   │ • OpenRouteService   │
   │ • OpenWeather        │
   │ • Amadeus            │
   │ • Cohere AI          │
   │ • Indian Railways    │
   │ • OpenStreetMap      │
   └──────────────────────┘
```

### Agent Workflow
1. **User** submits trip request via frontend
2. **Backend** publishes to `trip_requests_queue`
3. **Orchestrator** receives request and coordinates agents:
   - Sends to **Map Agent** → calculates route
   - Sends to **Weather Agent** → fetches forecasts
   - Sends to **Itinerary Agent** → generates activities
   - Sends to **Event Agent** → finds local events
   - Sends to **Budget Agent** → calculates costs
4. **Orchestrator** aggregates results and sends back to backend
5. **Backend** emits to frontend via Socket.IO
6. **Frontend** displays complete trip plan
## 📁 Project Structure

```
The-Ringmasters-Roundtable/
├── src/                          # Frontend React application
│   ├── components/               # Reusable UI components
│   │   ├── ui/                   # Shadcn UI components
│   │   ├── CircusCard.jsx        # Trip card component
│   │   ├── PipNotification.jsx   # Pip agent notifications
│   │   └── ...
│   ├── pages/                    # Page components
│   │   ├── Dashboard.jsx         # Main dashboard
│   │   ├── PlanTrip.jsx          # Trip planning interface
│   │   ├── Itinerary.jsx         # Itinerary viewer
│   │   ├── Budget.jsx            # Budget breakdown
│   │   ├── Compare.jsx           # Crystal Ball comparison
│   │   └── ...
│   ├── context/                  # React context providers
│   │   ├── AuthContext.jsx       # Firebase auth state
│   │   └── PipContext.jsx        # Pip notifications
│   ├── config/                   # Configuration
│   │   └── firebase.js           # Firebase initialization
│   └── App.jsx                   # Main app component
│
├── backend/                      # Node.js backend
│   ├── routes/                   # API routes
│   │   ├── tripRoutes.js         # Trip CRUD operations
│   │   ├── budgetRoutes.js       # Budget calculations
│   │   ├── itineraryRoutes.js    # Itinerary generation
│   │   ├── opportunityRoutes.js  # Pip opportunities
│   │   └── ...
│   ├── services/                 # Business logic
│   │   ├── firebaseAdmin.js      # Firebase Admin SDK
│   │   ├── opportunitiesStore.js # Opportunity management
│   │   ├── ai.js                 # AI integrations
│   │   └── ...
│   ├── mcp-ai/                   # Python MCP agents
│   │   ├── orchestrator_mcp.py   # Main orchestrator
│   │   ├── map_agent_mcp.py      # Route planning
│   │   ├── weather_agent_mcp.py  # Weather forecasts
│   │   ├── itinerary_agent_mcp.py # Activity generation
│   │   ├── event_agent_mcp.py    # Event discovery
│   │   ├── budget_agent_mcp.py   # Cost calculation
│   │   ├── freeDataService.py    # OSM data fetcher
│   │   └── requirements.txt      # Python dependencies
│   └── server.js                 # Express server entry
│
├── public/                       # Static assets
│   ├── assets/images/            # Image files
│   └── circus-bg.svg             # Background graphics
│
├── launch_app.sh                 # Start all services (macOS/Linux)
├── start_mcp_agents.sh           # Start MCP agents only
├── package.json                  # Frontend dependencies
└── README.md                     # This file
```

## 📝 Available Scripts

### All-in-One (Recommended)
```bash
./launch_app.sh              # Start frontend + backend + MCP agents (macOS/Linux)
./start_mcp_agents.sh        # Start only MCP agents in separate terminals
```

### Frontend
```bash
npm run dev                  # Start Vite dev server (port 5173)
npm run build                # Build for production
npm run preview              # Preview production build
```

### Backend
```bash
cd backend
nodemon server.js            # Start backend with auto-reload (port 3000)
node server.js               # Start backend (production)
```

### MCP Agents (Python)
```bash
cd backend/mcp-ai
source venv/bin/activate     # Activate virtual environment

# Start individual agents (for debugging)
python orchestrator_mcp.py   # Main orchestrator
python map_agent_mcp.py      # Map agent
python weather_agent_mcp.py  # Weather agent
python itinerary_agent_mcp.py # Itinerary agent
python event_agent_mcp.py    # Event agent
python budget_agent_mcp.py   # Budget agent
```

### Utilities
```bash
# Kill all MCP agent processes
pkill -f "_mcp.py"

# Check RabbitMQ queues
rabbitmqctl list_queues

# View agent logs
tail -f backend/mcp-ai/*.log
```

## 🎯 Key Features Explained

### 🤖 Pip Digital Agent
Pip is your proactive travel assistant that:
- Monitors your saved trips in the background
- Generates contextual opportunities (weather alerts, price drops, local events)
- Surfaces notifications every 30 seconds via polling
- Runs as a cron job every 2 minutes analyzing up to 5 trips per run

### 🔄 MCP Agent Architecture
The Multi-Agent Collaborative Planning (MCP) system:
- **Orchestrator** coordinates 5 specialized agents via RabbitMQ
- Each agent is a separate Python process listening to dedicated queues
- Agents respond asynchronously and send results back to orchestrator
- Enables horizontal scaling and fault tolerance

### 💰 Budget Optimization
- Fetches **real-time flight prices** from Amadeus API
- Queries **Indian Railways API** for train schedules and pricing
- Searches **hotels via Amadeus** with fallback to OSM data
- Calculates **cheapest combination** of transport + accommodation
- Displays detailed breakdown with flight numbers, timings, and prices

### 📋 Rich Itineraries
Each day includes:
- **Check-in/Check-out** activities (first/last day)
- **Breakfast, Lunch, Dinner** with restaurant recommendations
- **Morning, Afternoon, Evening** sightseeing activities
- **Duration, Price, Status** badges (confirmed/recommended/optional)
- **Includes** lists (e.g., "Room keys, Welcome amenities")

### 🔮 Crystal Ball Feature
The Crystal Ball is an intelligent trip comparison tool that:
- **Analyzes multiple destinations** simultaneously (e.g., "Goa vs Manali vs Udaipur")
- **Compares weather conditions** across all destinations for your travel dates
- **Evaluates budget** - shows cheapest vs most expensive options
- **Highlights unique experiences** - what makes each destination special
- **AI-powered recommendations** - suggests the best destination based on your preferences
- **Side-by-side comparison** - visual cards showing key metrics for each location
- **Smart insights** - "Best for beach lovers", "Budget-friendly option", "Adventure seeker's paradise"

## 🐛 Troubleshooting

### RabbitMQ Connection Issues
```bash
# Check if RabbitMQ is running
rabbitmqctl status

# Start RabbitMQ
brew services start rabbitmq  # macOS
sudo systemctl start rabbitmq-server  # Linux
```

### MCP Agents Not Responding
```bash
# Kill duplicate processes
pkill -f "_mcp.py"

# Restart agents
./start_mcp_agents.sh
```

### Firestore Quota Exceeded
```bash
# Switch to JSON fallback in .env
USE_FIRESTORE=false

# Increase cache TTL to reduce reads
OPPORTUNITIES_CACHE_TTL_MS=300000  # 5 minutes
```

### Cohere API Rate Limit
The free tier has 1000 calls/month. Event agent will use fallback data when limit is reached.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **React** & **Vite** - Frontend framework and build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Firebase** - Authentication and Firestore database
- **RabbitMQ** - Message broker for agent communication
- **Cohere** - AI-powered event generation
- **Amadeus** - Flight and hotel data
- **OpenStreetMap** - Free geographic data
- **OpenRouteService** - Route planning API
- **OpenWeather** - Weather forecasts

## 👥 Team

**The Ringmasters Roundtable** - Webster 2025

---

Made with ❤️ and 🎪 circus magic by The Ringmasters Roundtable
