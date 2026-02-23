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
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>dog.exe</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root { --black: #0a0a0a; --white: #f0f0f0; --lime: #c8ff00; --pink: #ff2d78; --blue: #00d4ff; --orange: #ff6b00; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--black); color: var(--white); font-family: 'Instrument Sans', sans-serif; min-height: 100vh; overflow-x: hidden; cursor: crosshair; }
  .marquee-wrap { background: var(--lime); color: var(--black); padding: 0.4rem 0; overflow: hidden; white-space: nowrap; }
  .marquee-track { display: inline-block; animation: marquee 12s linear infinite; font-family: 'DM Mono', monospace; font-size: 0.75rem; font-weight: 500; letter-spacing: 1px; }
  @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
  header { padding: 3rem 2rem 1rem; text-align: center; }
  h1 { font-family: 'Bebas Neue', sans-serif; font-size: clamp(5rem, 18vw, 12rem); line-height: 0.9; letter-spacing: -2px; color: var(--white); }
  h1 .accent { color: var(--lime); display: block; }
  h1 .stroke { -webkit-text-stroke: 2px var(--white); color: transparent; display: block; }
  .badge { display: inline-block; background: var(--pink); color: white; font-family: 'DM Mono', monospace; font-size: 0.65rem; padding: 3px 8px; border-radius: 2px; letter-spacing: 2px; vertical-align: super; margin-left: 4px; }
  .tagline { font-family: 'DM Mono', monospace; font-size: 0.8rem; color: #555; letter-spacing: 2px; text-transform: uppercase; margin-top: 1rem; }
  .container { max-width: 720px; margin: 0 auto; padding: 0 1.5rem 6rem; }
  .form-card { border: 1px solid #222; border-radius: 4px; padding: 2.5rem; background: #0f0f0f; margin-top: 2rem; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .form-group { margin-bottom: 1.25rem; }
  label { display: block; font-family: 'DM Mono', monospace; font-size: 0.65rem; color: #555; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 0.5rem; }
  input, select, textarea { width: 100%; padding: 0.75rem 1rem; background: #161616; border: 1px solid #2a2a2a; border-radius: 2px; color: var(--white); font-family: 'DM Mono', monospace; font-size: 0.85rem; outline: none; transition: border-color 0.15s; -webkit-appearance: none; }
  input:focus, select:focus, textarea:focus { border-color: var(--lime); }
  select option { background: #161616; }
  textarea { resize: vertical; min-height: 80px; }
  .checkbox-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; padding: 0.75rem 1rem; border: 1px solid #2a2a2a; border-radius: 2px; cursor: pointer; }
  .checkbox-row input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--lime); cursor: pointer; flex-shrink: 0; }
  .checkbox-row span { font-family: 'DM Mono', monospace; font-size: 0.8rem; color: #aaa; }
  .submit-btn { width: 100%; padding: 1.1rem; background: var(--lime); color: var(--black); border: none; border-radius: 2px; font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; letter-spacing: 3px; cursor: crosshair; transition: background 0.15s; margin-top: 0.75rem; }
  .submit-btn:hover { background: #d4ff1a; }
  .submit-btn:disabled { background: #222; color: #444; cursor: not-allowed; }
  .status { text-align: center; padding: 3rem 2rem; color: #444; font-family: 'DM Mono', monospace; font-size: 0.85rem; }
  .loading-bar { width: 100%; height: 2px; background: #1a1a1a; overflow: hidden; margin-bottom: 1.5rem; }
  .loading-bar-inner { height: 100%; background: linear-gradient(90deg, var(--lime), var(--blue), var(--pink)); animation: loadbar 1.5s ease-in-out infinite; width: 60%; }
  @keyframes loadbar { 0% { transform: translateX(-100%); } 100% { transform: translateX(250%); } }
  .results-header { font-family: 'Bebas Neue', sans-serif; font-size: 2.5rem; letter-spacing: 2px; margin: 2.5rem 0 1.5rem; }
  .results-header .count { color: var(--lime); }
  .dog-card { border: 1px solid #1f1f1f; border-radius: 4px; overflow: hidden; margin-bottom: 1rem; display: flex; background: #0f0f0f; transition: border-color 0.2s, transform 0.2s; }
  .dog-card:hover { border-color: var(--lime); transform: translateX(4px); }
  .dog-photo { width: 130px; min-width: 130px; object-fit: cover; filter: grayscale(20%); transition: filter 0.2s; }
  .dog-card:hover .dog-photo { filter: grayscale(0%); }
  .dog-photo-placeholder { width: 130px; min-width: 130px; background: #161616; display: flex; align-items: center; justify-content: center; font-size: 3rem; }
  .dog-info { padding: 1.25rem 1.5rem; flex: 1; }
  .dog-name { font-family: 'Bebas Neue', sans-serif; font-size: 1.8rem; letter-spacing: 1px; line-height: 1; margin-bottom: 0.25rem; }
  .dog-name a { color: var(--white); text-decoration: none; }
  .dog-name a:hover { color: var(--lime); }
  .dog-shelter { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: var(--lime); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem; }
  .dog-reason { font-size: 0.85rem; color: #666; line-height: 1.6; font-family: 'DM Mono', monospace; margin-bottom: 1rem; }
  .view-btn { display: inline-block; padding: 0.4rem 1rem; border: 1px solid #333; color: #888; border-radius: 2px; font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 1px; text-decoration: none; text-transform: uppercase; }
  .view-btn:hover { border-color: var(--lime); color: var(--lime); }
  .no-results { text-align: center; padding: 4rem 2rem; border: 1px solid #1f1f1f; border-radius: 4px; color: #444; font-family: 'DM Mono', monospace; }
  .no-results .big { font-size: 3rem; margin-bottom: 1rem; }
  .error-msg { background: rgba(255,45,120,0.1); border: 1px solid var(--pink); color: var(--pink); padding: 1rem; border-radius: 2px; margin-top: 1rem; font-family: 'DM Mono', monospace; font-size: 0.8rem; }
  .corner-deco { position: fixed; bottom: 1.5rem; right: 1.5rem; font-family: 'DM Mono', monospace; font-size: 0.6rem; color: #222; letter-spacing: 2px; writing-mode: vertical-rl; }
  #chili { position: fixed; font-size: 2.5rem; cursor: pointer; z-index: 1000; user-select: none; filter: drop-shadow(0 0 8px rgba(255,107,0,0.6)); left: 100px; top: 100px; }
  .chili-modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 2000; align-items: center; justify-content: center; padding: 2rem; }
  .chili-modal.open { display: flex; }
  .chili-modal-inner { background: #0f0f0f; border: 1px solid var(--orange); border-radius: 8px; padding: 2.5rem; max-width: 560px; width: 100%; box-shadow: 0 0 40px rgba(255,107,0,0.2); }
  .chili-modal-title { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: var(--orange); letter-spacing: 2px; margin-bottom: 0.25rem; }
  .chili-modal-subtitle { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #555; margin-bottom: 1.5rem; }
  .chili-modal-body { font-family: 'DM Mono', monospace; font-size: 0.85rem; color: #aaa; line-height: 1.8; }
  .chili-modal-footer { margin-top: 1.5rem; display: flex; gap: 0.75rem; }
  .chili-link { padding: 0.5rem 1.25rem; background: var(--orange); color: var(--black); border: none; border-radius: 2px; font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem; letter-spacing: 2px; text-decoration: none; }
  .chili-close { padding: 0.5rem 1.25rem; background: transparent; color: #555; border: 1px solid #333; border-radius: 2px; font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem; letter-spacing: 2px; cursor: pointer; }
  @media (max-width: 500px) { .form-row { grid-template-columns: 1fr; } .form-card { padding: 1.5rem 1rem; } .dog-card { flex-direction: column; } .dog-photo, .dog-photo-placeholder { width: 100%; height: 200px; min-width: unset; } h1 { font-size: 5rem; } }
</style>
</head>
<body>
<div class="marquee-wrap"><span class="marquee-track">🐾 AI DOG MATCHING &nbsp;★&nbsp; RESCUE ONLY &nbsp;★&nbsp; POWERED BY GPT &nbsp;★&nbsp; FIND YOUR BEST FRIEND &nbsp;★&nbsp; 🐾 AI DOG MATCHING &nbsp;★&nbsp; RESCUE ONLY &nbsp;★&nbsp; POWERED BY GPT &nbsp;★&nbsp; FIND YOUR BEST FRIEND &nbsp;★&nbsp;</span></div>
<header>
  <h1><span>FIND</span><span class="accent">YOUR</span><span class="stroke">DOG<span class="badge">AI</span></span></h1>
  <p class="tagline">// rescue matching · norcal shelters · sf bay area</p>
</header>
<div class="container">
  <div class="form-card">
    <form id="search-form">
      <div class="form-row">
        <div class="form-group"><label>// your name</label><input type="text" id="name" value="Austin"></div>
        <div class="form-group"><label>// your city</label><input type="text" id="location" value="San Francisco, CA"></div>
      </div>
      <div class="form-group"><label>// breed vibe</label><input type="text" id="breed" value="Poodle mix or doodle"></div>
      <div class="form-row">
        <div class="form-group"><label>// size</label><select id="size"><option>Small (under 25 lbs)</option><option>Medium (25-50 lbs)</option><option>Large (50+ lbs)</option><option>Any size</option></select></div>
        <div class="form-group"><label>// age</label><select id="age"><option>Puppy (under 1yr)</option><option>Young (1-3 yrs)</option><option>Adult (3-8 yrs)</option><option>Any age</option></select></div>
      </div>
      <label class="checkbox-row"><input type="checkbox" id="otherDogs" checked><span>// must be good with other dogs</span></label>
      <div class="form-group"><label>// extra requirements</label><textarea id="notes" placeholder="low shedding, apartment ok, chill energy..."></textarea></div>
      <button type="submit" class="submit-btn">RUN SEARCH</button>
    </form>
  </div>
  <div id="results"></div>
</div>
<div class="corner-deco">dog.exe v1.0</div>
<div id="chili">&#127858;</div>
<div class="chili-modal" id="chili-modal">
  <div class="chili-modal-inner">
    <div class="chili-modal-title" id="chili-title">LOADING CHILI...</div>
    <div class="chili-modal-subtitle" id="chili-subtitle"></div>
    <div class="chili-modal-body" id="chili-body">fetching championship recipe...</div>
    <div class="chili-modal-footer">
      <a class="chili-link" id="chili-full-link" href="#" target="_blank">FULL RECIPE</a>
      <button class="chili-close" id="chili-close">CLOSE</button>
    </div>
  </div>
</div>
<script>
var form = document.getElementById('search-form');
var results = document.getElementById('results');
form.addEventListener('submit', function(e) {
  e.preventDefault();
  var btn = form.querySelector('.submit-btn');
  btn.disabled = true;
  btn.textContent = 'LOADING...';
  results.innerHTML = '<div class="status"><div class="loading-bar"><div class="loading-bar-inner"></div></div><p>scraping 8 shelters + running ai filter<br><span style="color:#333">~60 seconds</span></p></div>';
  var payload = { name: document.getElementById('name').value, location: document.getElementById('location').value, breed: document.getElementById('breed').value, size: document.getElementById('size').value, age: document.getElementById('age').value, otherDogs: document.getElementById('otherDogs').checked, notes: document.getElementById('notes').value };
  fetch('/find-dogs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.error) { results.innerHTML = '<div class="error-msg">ERR: ' + data.error + '</div>'; return; }
    var matches = data.matches;
    if (!matches.length) { results.innerHTML = '<div class="no-results"><div class="big">🐕</div><p>no matches today. try loosening filters.</p></div>'; return; }
    var html = '<div class="results-header"><span class="count">' + matches.length + '</span> MATCH' + (matches.length > 1 ? 'ES' : '') + ' FOR ' + payload.name.toUpperCase() + '</div>';
    for (var i = 0; i < matches.length; i++) {
      var dog = matches[i];
      var photo = dog.photo ? '<img class="dog-photo" src="' + dog.photo + '" alt="' + dog.name + '" onerror="this.setAttribute(\'style\',\'display:none\')">' : '<div class="dog-photo-placeholder">&#128054;</div>';
      html += '<div class="dog-card">' + photo + '<div class="dog-info"><div class="dog-name"><a href="' + dog.url + '" target="_blank">' + dog.name + '</a></div><div class="dog-shelter">' + dog.shelter + '</div><p class="dog-reason">' + dog.reason + '</p><a href="' + dog.url + '" target="_blank" class="view-btn">view profile</a></div></div>';
    }
    results.innerHTML = html;
  })
  .catch(function() { results.innerHTML = '<div class="error-msg">ERR: something broke. try again.</div>'; })
  .finally(function() { btn.disabled = false; btn.textContent = 'RUN SEARCH'; });
});
var chili = document.getElementById('chili');
var cx = 100, cy = 100, cvx = 2.5, cvy = 2;
function animateChili() {
  cx += cvx; cy += cvy;
  if (cx <= 0 || cx >= window.innerWidth - 50) cvx *= -1;
  if (cy <= 0 || cy >= window.innerHeight - 50) cvy *= -1;
  chili.style.left = cx + 'px'; chili.style.top = cy + 'px';
  requestAnimationFrame(animateChili);
}
animateChili();
var modal = document.getElementById('chili-modal');
chili.addEventListener('click', function() {
  modal.classList.add('open');
  fetch('/random-chili').then(function(r) { return r.json(); }).then(function(data) {
    document.getElementById('chili-title').textContent = 'CHAMPIONSHIP CHILI';
    document.getElementById('chili-subtitle').textContent = data.name;
    document.getElementById('chili-body').textContent = 'Click below for the full recipe from CASI - the Chili Appreciation Society International.';
    document.getElementById('chili-full-link').href = data.url;
  });
});
document.getElementById('chili-close').addEventListener('click', function() { modal.classList.remove('open'); });
modal.addEventListener('click', function(e) { if (e.target === modal) modal.classList.remove('open'); });
</script>
</body>
</html>"""

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
