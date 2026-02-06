import requests
import json
import os
from datetime import datetime

# ======= CONFIG =======
CLAN_TAG = "%23YQY9R8PP"  # Replace # with %23 for API URLs
CLAN_TAG_DECODED = "#YQY9R8PP"  # Decoded version for comparison
API_KEY = os.getenv("CLASH_API_KEY")  # Must be set as an environment variable
CLAN_OUTPUT = "clan_data.json"
WAR_OUTPUT = "war_data.json"
DONATION_OUTPUT = "donation_history.json"
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

# ---- Handle Donation Tracking ----
# Load existing donation history or create new one
if os.path.exists(DONATION_OUTPUT):
    with open(DONATION_OUTPUT, "r") as f:
        donation_data = json.load(f)
else:
    donation_data = {
        "trackingStartDate": datetime.now().isoformat(),
        "weeklySnapshots": [],
        "allTimeTotals": {}
    }
    print("Created new donation tracking file")

# Get current donations from members
current_donations = {}
for member in members_data["items"]:
    member_name = member["name"]
    donations = member.get("donations", 0)
    current_donations[member_name] = donations

# Check if we should save a weekly snapshot
# This should be run BEFORE Sunday 8pm EST (before reset)
# You can modify this logic based on when you run the script
current_time = datetime.now()
should_save_snapshot = False

# Option 1: Always save current week as "last week" 
# (Assumes you run this script right before reset on Sunday)
# Uncomment the line below if you want to force a snapshot every run
# should_save_snapshot = True

# Option 2: Check if we haven't saved a snapshot this week yet
if donation_data["weeklySnapshots"]:
    last_snapshot_date = donation_data["weeklySnapshots"][0]["date"]
    last_snapshot_time = datetime.fromisoformat(last_snapshot_date)
    days_since_last_snapshot = (current_time - last_snapshot_time).days
    
    # If it's been 6+ days since last snapshot, save a new one
    # This assumes you run the script weekly
    if days_since_last_snapshot >= 6:
        should_save_snapshot = True
else:
    # No snapshots yet, save the first one
    should_save_snapshot = True

if should_save_snapshot:
    # Save current donations as "last week"
    weekly_snapshot = {
        "date": current_time.isoformat(),
        "donations": current_donations.copy()
    }
    
    # Add to beginning of list (most recent first)
    donation_data["weeklySnapshots"].insert(0, weekly_snapshot)
    
    # Keep only last 12 weeks of snapshots (3 months)
    donation_data["weeklySnapshots"] = donation_data["weeklySnapshots"][:12]
    
    print(f"Saved weekly donation snapshot with {len(current_donations)} members")
    
    # Update all-time totals
    for member_name, donations in current_donations.items():
        if member_name in donation_data["allTimeTotals"]:
            donation_data["allTimeTotals"][member_name] += donations
        else:
            donation_data["allTimeTotals"][member_name] = donations
    
    print(f"Updated all-time donation totals")
else:
    print(f"Skipped weekly snapshot (last snapshot was {days_since_last_snapshot} days ago)")

# Save donation history
with open(DONATION_OUTPUT, "w") as f:
    json.dump(donation_data, f, indent=4)
print(f"Saved donation history to {DONATION_OUTPUT}")