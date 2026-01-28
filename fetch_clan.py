import requests
import json
import os

# ======= CONFIG =======
CLAN_TAG = "%23YQY9R8PP"  # Replace # with %23 for API URLs
CLAN_TAG_DECODED = "#YQY9R8PP"  # Decoded version for comparison
API_KEY = os.getenv("CLASH_API_KEY")  # Must be set as an environment variable
CLAN_OUTPUT = "clan_data.json"
WAR_OUTPUT = "war_data.json"
# =====================

if not API_KEY:
    raise ValueError("CLASH_API_KEY environment variable is not set!")

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# ---- Fetch clan info ----
clan_url = f"https://api.clashroyale.com/v1/clans/{CLAN_TAG}"
clan_response = requests.get(clan_url, headers=headers)
clan_response.raise_for_status()
clan_data = clan_response.json()

# ---- Fetch clan members ----
members_url = f"https://api.clashroyale.com/v1/clans/{CLAN_TAG}/members"
members_response = requests.get(members_url, headers=headers)
members_response.raise_for_status()
members_data = members_response.json()
clan_data["memberList"] = members_data["items"]

# ---- Save clan info + members ----
with open(CLAN_OUTPUT, "w") as f:
    json.dump(clan_data, f, indent=4)
print(f"Saved clan info + {len(members_data['items'])} members to {CLAN_OUTPUT}")

# ---- Fetch River Race Log (last 2 wars) ----
riverrace_log_url = f"https://api.clashroyale.com/v1/clans/{CLAN_TAG}/riverracelog?limit=2"
log_response = requests.get(riverrace_log_url, headers=headers)

war_data = {"previousWars": []}

if log_response.status_code == 200:
    log_data = log_response.json()
    previous_races = log_data.get("items", [])
    
    print(f"Found {len(previous_races)} previous wars")
    
    for race in previous_races:
        # Find your clan in the standings
        standings = race.get("standings", [])
        your_clan_data = None
        
        for standing in standings:
            clan_info = standing.get("clan", {})
            if clan_info.get("tag") == CLAN_TAG_DECODED:
                your_clan_data = clan_info
                break
        
        if your_clan_data:
            participants = your_clan_data.get("participants", [])
            print(f"War on {race.get('createdDate')}: {len(participants)} participants")
            
            war_data["previousWars"].append({
                "date": race.get("createdDate"),
                "participants": [{"name": p["name"], "points": p["fame"]} for p in participants]
            })
        else:
            print(f"Warning: Could not find clan {CLAN_TAG_DECODED} in standings for war on {race.get('createdDate')}")
            war_data["previousWars"].append({
                "date": race.get("createdDate"),
                "participants": []
            })
else:
    print(f"Error fetching river race log: {log_response.status_code}")

# ---- Save war data ----
with open(WAR_OUTPUT, "w") as f:
    json.dump(war_data, f, indent=4)
print(f"Saved war data to {WAR_OUTPUT}")