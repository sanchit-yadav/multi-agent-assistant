import requests

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS  = "https://overpass-api.de/api/interpreter"
HEADERS   = {"User-Agent": "MultiAgentAssistant/1.0 (resume-project)"}


def search_place(query: str) -> dict:
    try:
        resp    = requests.get(
            NOMINATIM,
            params  = {"q": query, "format": "json", "limit": 1},
            headers = HEADERS,
            timeout = 10,
        )
        results = resp.json()
        if not results:
            return {"error": f"No location found for '{query}'"}
        p = results[0]
        return {
            "name":      p.get("display_name", ""),
            "latitude":  p.get("lat", ""),
            "longitude": p.get("lon", ""),
            "map_url":   f"https://www.openstreetmap.org/#map=14/{p['lat']}/{p['lon']}",
        }
    except Exception as e:
        return {"error": str(e)}


def get_nearby_places(lat: str, lon: str, category: str = "tourism") -> list:
    query = f'[out:json];node["{category}"](around:3000,{lat},{lon});out 6;'
    try:
        resp     = requests.post(OVERPASS, data=query, headers=HEADERS, timeout=15)
        elements = resp.json().get("elements", [])
        return [
            {
                "name": e.get("tags", {}).get("name", "Unnamed"),
                "type": e.get("tags", {}).get(category, ""),
            }
            for e in elements
            if e.get("tags", {}).get("name")
        ]
    except Exception:
        return []