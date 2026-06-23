# backend/mcp-ai/assistant/vector_store.py
import requests
from typing import List, Dict, Any

class VectorItineraryStore:
    """Vector database indexer to search previously generated trip plans."""
    
    def __init__(self):
        self.base_url = "http://localhost:3000/api/users"

    def similarity_search(self, query: str, user_id: str = "default_guest", limit: int = 2) -> List[Dict[str, Any]]:
        """Queries the user's saved trips from Node API and performs a simple keyword filter."""
        matched_trips = []
        query_words = set(query.lower().split())
        
        try:
            response = requests.get(f"{self.base_url}/{user_id}/trips", timeout=5)
            if response.status_code == 200:
                trips_data = response.json()
                
                trips_list = []
                if isinstance(trips_data, list):
                    trips_list = trips_data
                elif isinstance(trips_data, dict):
                    for k, v in trips_data.items():
                        if isinstance(v, dict):
                            trips_list.append({**v, "id": k})
                            
                for trip in trips_list:
                    destination = str(trip.get("destination", "")).lower()
                    origin = str(trip.get("origin", "")).lower()
                    title = str(trip.get("title", "")).lower()
                    
                    searchable_text = f"{destination} {origin} {title}"
                    match_score = sum(1 for word in query_words if word in searchable_text)
                    
                    if match_score > 0:
                        matched_trips.append((match_score, {
                            "trip_id": trip.get("id") or trip.get("trip_id"),
                            "destination": trip.get("destination"),
                            "origin": trip.get("origin"),
                            "start_date": trip.get("startDate") or trip.get("start_date"),
                            "end_date": trip.get("endDate") or trip.get("end_date"),
                            "num_days": trip.get("numDays") or trip.get("num_days"),
                            "itinerary": trip.get("itinerary", []),
                            "budget": trip.get("budget", {}),
                            "notes": trip.get("notes", [])
                        }))
        except Exception as e:
            print(f"[VectorItineraryStore] Error fetching trips from Node API: {e}")
            pass
            
        matched_trips.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in matched_trips[:limit]]
