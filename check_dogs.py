import requests
import sqlite3
import os
import re
from datetime import datetime

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PUSHOVER_USER_KEY = os.environ["PUSHOVER_USER_KEY"]
PUSHOVER_API_TOKEN = os.environ["PUSHOVER_API_TOKEN"]

YOUR_PREFERENCES = """
- Small to medium sized dog (under 40 lbs preferred)
- Good with other dogs (I have two dachshunds)
- Under 5 years old preferred
- Generally cute, friendly-looking face
"""

def init_db():
    conn = sqlite3.connect("seen_dogs.db")
    conn.execute("CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY, name TEXT, seen_at TEXT)")
    conn.commit()
    return conn

def is_new(conn, dog_id):
    cur = conn.execute("SELECT id FROM seen WHERE id = ?", (str(dog_id),))
    return cur.fetchone() is None

def mark_seen(conn, dog_id, name):
    conn.execute("INSERT INTO seen VALUES (?, ?, ?)", (str(dog_id), name, datetime.now().isoformat()))
    conn.commit()

def fetch_dogs():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        dogs = []

        def handle_response(response):
            if "shelterluv.com/api" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "animals" in data:
                        for a in data["animals"]:
                            dogs.append({
                                "ID": a.get("ID") or a.get("InternalID"),
                                "Name": a.get("Name"),
                                "Breed": a.get("Breed") or a.get("PrimaryBreed"),
                                "Age": a.get("Age"),
                                "Weight": a.get("Weight", "unknown"),
                                "Description": a.get("Description", "")
                            })
                except:
                    pass

        page.on("response", handle_response)
        page.goto("https://www.shelterluv.com/matchme/available/MILO/Dog")
        page.wait_for_timeout(5000)
        browser.close()

    print(f"Found {len(dogs)} available dogs")
    return dogs

def is_good_match(dog):
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""Given these preferences:
{YOUR_PREFERENCES}

Is this dog a good match? Start with YES or NO, then one sentence why.

Name: {dog.get('Name')}
Breed: {dog.get('Breed')}
Age: {dog.get('Age')}
Weight: {dog.get('Weight')} lbs
Description: {str(dog.get('Description', ''))[:500]}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    return answer.upper().startswith("YES"), answer

def send_notification(matches):
    for dog, reason in matches:
        message = f"{dog.get('Name')} ({dog.get('Breed')}, {dog.get('Age')})\n{reason}"
        url = f"https://www.shelterluv.com/matchme/available/MILO/Dog/{dog.get('ID')}"
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message,
            "url": url,
            "url_title": f"View {dog.get('Name')} on Shelterluv"
        })
    print(f"Sent {len(matches)} Pushover notifications")

def main():
    conn = init_db()
    dogs = fetch_dogs()
    matches = []

    for dog in dogs:
        dog_id = dog.get("ID")
        if not is_new(conn, dog_id):
            continue
        mark_seen(conn, dog_id, dog.get("Name", "Unknown"))
        good, reason = is_good_match(dog)
        if good:
            matches.append((dog, reason))

    if matches:
        send_notification(matches)
    else:
        print("No new matches")

if __name__ == "__main__":
    main()
