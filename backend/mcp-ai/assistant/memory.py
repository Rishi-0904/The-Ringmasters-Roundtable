# backend/mcp-ai/assistant/memory.py
import requests
from typing import Dict, Any, List

class UserMemoryManager:
    """Manages multi-turn user profiles including travel styles and budget preferences."""
    
    def __init__(self):
        self.base_url = "http://localhost:3000/api/users"
        self.session_memory = {} # Fallback session memory

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        # Return from session cache if already resolved
        if user_id in self.session_memory:
            return self.session_memory[user_id]
            
        # Base template profile
        profile = {
            "favorite_activities": [],
            "budget_preferences": "Standard",
            "previous_trips": [],
            "travel_style": "Cultural"
        }
        
        try:
            # Query Node.js API to discover previously visited destinations
            response = requests.get(f"{self.base_url}/{user_id}/trips", timeout=5)
            if response.status_code == 200:
                trips_data = response.json()
                destinations = []
                
                if isinstance(trips_data, list):
                    for trip in trips_data:
                        dest = trip.get("destination")
                        if dest:
                            destinations.append(dest)
                elif isinstance(trips_data, dict):
                    for k, v in trips_data.items():
                        if isinstance(v, dict) and v.get("destination"):
                            destinations.append(v.get("destination"))
                            
                profile["previous_trips"] = list(set(destinations))
        except Exception as e:
            print(f"[UserMemoryManager] Connection to Node API failed: {e}")
            pass
            
        self.session_memory[user_id] = profile
        return profile

    def update_preferences_implicitly(self, user_id: str, text: str):
        """Extracts new preferences dynamically and updates in-memory profiles."""
        current = self.get_user_profile(user_id)
        text_lower = text.lower()
        
        # 1. Budget extraction
        if "luxury" in text_lower or "5-star" in text_lower:
            current["budget_preferences"] = "Luxury"
        elif "budget" in text_lower or "cheap" in text_lower or "affordable" in text_lower:
            current["budget_preferences"] = "Budget"
            
        # 2. Travel style extraction
        if "adventure" in text_lower or "trek" in text_lower or "hike" in text_lower:
            current["travel_style"] = "Adventure"
        elif "museum" in text_lower or "history" in text_lower or "culture" in text_lower:
            current["travel_style"] = "Cultural"
            
        # 3. Favorite activity tag extraction
        activities = []
        if "sightseeing" in text_lower or "monument" in text_lower:
            activities.append("sightseeing")
        if "restaurant" in text_lower or "food" in text_lower or "eat" in text_lower or "dinner" in text_lower:
            activities.append("dining")
        if "beach" in text_lower or "sea" in text_lower:
            activities.append("beaches")
            
        if activities:
            current_activities = set(current.get("favorite_activities", []))
            current_activities.update(activities)
            current["favorite_activities"] = list(current_activities)
            
        self.session_memory[user_id] = current
        print(f"[UserMemoryManager] Implicitly updated profile for {user_id}: {current}")
