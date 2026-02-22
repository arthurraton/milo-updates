import requests
import sqlite3
import os
from datetime import datetime
from bs4 import BeautifulSoup

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PUSHOVER_USER_KEY = os.environ["PUSHOVER_USER_KEY"]
PUSHOVER_API_TOKEN = os.environ["PUSHOVER_API_TOKEN"]

YOUR_PREFERENCES = """
- Small to medium-sized dog (under 25 lbs preferred)
- Good with other dogs (I have two dachshunds)
- Under 5 years old preferred
- Poodle preferred
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
    resp = requests.get(
        "https://www.adoptapet.com/shelter/73753/available-pets",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    dogs = []

    for card in soup.select("a[href*='/pet/']"):
        name = card.get_text(strip=True)
        href = card.get("href", "")
        pet_id = href.split("/pet/")[-1].strip("/").split("-")[0]
        if pet_id and name:
            dogs.append({
                "ID": pet_id,
                "Name": name,
                "Breed": "Unknown",
                "Age": "Unknown",
                "Weight": "unknown",
                "Description": ""
            })

    seen_ids = set()
    unique = []
    for d in dogs:
        if d["ID"] not in seen_ids:
            seen_ids.add(d["ID"])
            unique.append(d)

    print(f"Found {len(unique)} available dogs")
    return unique

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
        url = f"https://www.adoptapet.com/pet/{dog.get('ID')}"
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message,
            "url": url,
            "url_title": f"View {dog.get('Name')} on Adopt-a-Pet"
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
