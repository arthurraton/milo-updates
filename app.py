from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import openai
import os

app = Flask(__name__, static_folder="static")
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/find-dogs", methods=["POST"])
def find_dogs():
    data = request.json
    preferences = f"""
- Looking for: {data.get('breed', 'any dog')} — ONLY dogs, no cats or rabbits
- Size: {data.get('size', 'any')}
- Age: {data.get('age', 'any')}
- Good with other dogs: {data.get('otherDogs', True)}
- Notes: {data.get('notes', '')}
- IMPORTANT: Only say YES if this is clearly a dog
"""
    try:
        resp = requests.get(
            "https://www.adoptapet.com/shelter/73753/available-pets?pet_type_id=1",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=10
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        dogs = []
        seen_ids = set()
        non_dog_keywords = ["rabbit", "bunny", "cat", "kitten", "guinea", "bird", "hamster"]

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
                dogs.append({
                    "id": pet_id,
                    "name": pet_name,
                    "photo": photo,
                    "url": f"https://www.adoptapet.com/pet/{pet_id}"
                })

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        matches = []

        for dog in dogs:
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

        return jsonify({"matches": matches, "total": len(dogs)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
