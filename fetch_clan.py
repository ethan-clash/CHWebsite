import requests
import json
import os

# ======= CONFIG =======
CLAN_TAG = "%23YQY9R8PP"  # Replace # with %23
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

# ---- Fetch current River Race ----
current_race_url = f"https://api.clashroyale.com/v1/clans/{CLAN_TAG}/currentriverrace"
current_race_response = requests.get(current_race_url, headers=headers)

war_data = {"currentWar": None, "previousWars": []}

if current_race_response.status_code == 200:
    current_race = current_race_response.json()
    participants = current_race.get("clan", {}).get("participants", [])
    if participants:
        war_data["currentWar"] = {
            "startTime": current_race.get("collectionEndTime"),
            "endTime": current_race.get("warEndTime"),
            "participants": [{"name": p["name"], "points": p["fame"]} for p in participants]
        }

# ---- Fetch previous River Races ----
riverrace_log_url = f"https://api.clashroyale.com/v1/clans/{CLAN_TAG}/riverracelog"
log_response = requests.get(riverrace_log_url, headers=headers)
if log_response.status_code == 200:
    log_data = log_response.json()
    previous_races = log_data.get("items", [])[:5]  # last 5 wars
    for race in previous_races:
        participants = race.get("clan", {}).get("participants", [])
        war_data["previousWars"].append({
            "date": race.get("createdDate"),
            "participants": [{"name": p["name"], "points": p["fame"]} for p in participants]
        })

# ---- Save war data ----
with open(WAR_OUTPUT, "w") as f:
    json.dump(war_data, f, indent=4)
print(f"Saved war data to {WAR_OUTPUT}")
