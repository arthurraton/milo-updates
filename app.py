from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import openai
import os
import random

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app = Flask(__name__, static_folder=static_dir)
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

SHELTERS = [
    {"name": "Milo Foundation", "url": "https://www.adoptapet.com/shelter/73753/available-pets?pet_type_id=1"},
    {"name": "SF SPCA", "url": "https://www.adoptapet.com/shelter/77882/available-pets?pet_type_id=1"},
    {"name": "Humane Society Silicon Valley", "url": "https://www.adoptapet.com/shelter/71541/available-pets?pet_type_id=1"},
    {"name": "East Bay SPCA", "url": "https://www.adoptapet.com/shelter/71640/available-pets?pet_type_id=1"},
    {"name": "Napa County Animal Shelter", "url": "https://www.adoptapet.com/shelter/73325/available-pets?pet_type_id=1"},
    {"name": "Central California SPCA", "url": "https://www.adoptapet.com/shelter/73661/available-pets?pet_type_id=1"},
    {"name": "Marin Humane", "url": "https://www.adoptapet.com/shelter/72210/available-pets?pet_type_id=1"},
    {"name": "Peninsula Humane Society", "url": "https://www.adoptapet.com/shelter/71603/available-pets?pet_type_id=1"},
]

CHILI_RECIPES = [
    {"name": "2025 - Greg Lindsey", "url": "https://www.casichili.net/2025-greg-lindsey.html"},
    {"name": "2024 - Kevin Casey", "url": "https://www.casichili.net/2024-kevin-casey.html"},
    {"name": "2023 - Rene Chapa", "url": "https://www.casichili.net/2023-rene-chapa.html"},
    {"name": "2022 - Kris Hudspeth", "url": "https://www.casichili.net/2022-kris-hudspeth.html"},
    {"name": "2021 - Becky Allen", "url": "https://www.casichili.net/2021-becky-allen.html"},
    {"name": "2020 - Chris Pfeiffer", "url": "https://www.casichili.net/2020-chris-pfeiffer.html"},
    {"name": "2019 - Kathryn Cavender", "url": "https://www.casichili.net/2019-kathryn-cavender.html"},
    {"name": "2018 - Cody Lee", "url": "https://www.casichili.net/2018-cody-lee.html"},
]

@app.route("/")
def index():
    return send_from_directory(static_dir, "index.html")

@app.route("/random-chili")
def random_chili():
    return jsonify(random.choice(CHILI_RECIPES))

@app.route("/find-dogs", methods=["POST"])
def find_dogs():
    data = request.json
    preferences = f"""
- Looking for: {data.get('breed', 'any dog')} - ONLY dogs, no cats or rabbits
- Size: {data.get('size', 'any')}
- Age: {data.get('age', 'any')}
- Good with other dogs: {data.get('otherDogs', True)}
- Notes: {data.get('notes', '')}
- IMPORTANT: Only say YES if this is clearly a dog
"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        non_dog_keywords = ["rabbit", "bunny", "cat", "kitten", "guinea", "bird", "hamster"]
        all_dogs = []
        seen_ids = set()

        for shelter in SHELTERS:
            try:
                resp = requests.get(shelter["url"], headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select("a[href*='/pet/']"):
                    href = card.get("href", "")
                    pet_id = href.split("/pet/")[-1].strip("/").split("-")[0]
                    pet_name = card.get_text(strip=True)
                    if any(kw in pet_name.lower() for kw in non_dog_keywords):
                        continue
                    img = card.find("img")
                    photo = img["src"] if img and img.get("src") else None
                    if pet_id and pet_name and pet_id not in seen_ids:
                        seen_ids.add(pet_id)
                        all_dogs.append({
                            "id": pet_id,
                            "name": pet_name,
                            "shelter": shelter["name"],
                            "photo": photo,
                            "url": f"https://www.adoptapet.com/pet/{pet_id}"
                        })
            except Exception:
                continue

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        matches = []

        for dog in all_dogs:
            prompt = f"""Given these preferences:
{preferences}

Is this a dog AND a good match? Start with YES or NO, then one sentence why.
Name: {dog['name']}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content
            if answer.upper().startswith("YES"):
                dog["reason"] = answer
                matches.append(dog)

        return jsonify({"matches": matches, "total": len(all_dogs)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
