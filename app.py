import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import random

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Rescue Dog Finder", page_icon="🐾", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 3rem !important;
    color: #1a1a1a !important;
    letter-spacing: -1px;
}

.stApp {
    background-color: #faf7f4;
}

section[data-testid="stForm"] {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid #ebe8e3;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}

.stButton > button {
    background-color: #2d6a4f !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    margin-top: 1rem !important;
}

.stButton > button:hover {
    background-color: #1b4332 !important;
}

.dog-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    border: 1px solid #ebe8e3;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.dog-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: #1a1a1a;
    margin-bottom: 0.25rem;
}

.dog-reason {
    color: #555;
    font-size: 0.95rem;
    line-height: 1.5;
}

.tag {
    display: inline-block;
    background: #e9f5ee;
    color: #2d6a4f;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: #888;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    margin-top: -0.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🐾 Rescue Dog Finder</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>AI-powered matching for your perfect rescue dog.</p>", unsafe_allow_html=True)

with st.form("preferences"):
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("Your name", value="Austin")
    with col2:
        location = st.text_input("Your city", value="San Francisco, CA")

    breed_pref = st.text_input("Breed preference", value="Poodle mix or doodle")

    col3, col4 = st.columns(2)
    with col3:
        size_pref = st.selectbox("Size", ["Small (under 25 lbs)", "Medium (25-50 lbs)", "Large (50+ lbs)", "Any"])
    with col4:
        age_pref = st.selectbox("Age", ["Puppy (under 1yr)", "Young (1-3 yrs)", "Adult (3-8 yrs)", "Any"])

    other_dogs = st.checkbox("Must be good with other dogs", value=True)
    extra_notes = st.text_area("Anything else?", placeholder="e.g. low shedding, apartment friendly, calm temperament...")
    submitted = st.form_submit_button("Find My Dog")

if submitted:
    preferences = f"""
- Looking for: {breed_pref} — ONLY dogs, no cats, rabbits, or other animals
- Size: {size_pref}
- Age: {age_pref}
- Good with other dogs: {other_dogs}
- Location: {location}
- Additional notes: {extra_notes}
- IMPORTANT: Only say YES if this is clearly a dog (not a cat, rabbit, or other animal)
"""
    with st.spinner("Fetching available dogs..."):
        resp = requests.get(
            "https://www.adoptapet.com/shelter/73753/available-pets?pet_type_id=1",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        dogs = []
        seen_ids = set()

        # filter out obvious non-dogs by name keywords
        non_dog_keywords = ["rabbit", "bunny", "cat", "kitten", "guinea", "bird", "hamster", "reptile"]

        for card in soup.select("a[href*='/pet/']"):
            href = card.get("href", "")
            pet_id = href.split("/pet/")[-1].strip("/").split("-")[0]
            pet_name = card.get_text(strip=True).lower()
            img = card.find("img")
            photo = img["src"] if img and img.get("src") else None

            if any(kw in pet_name for kw in non_dog_keywords):
                continue

            if pet_id and pet_name and pet_id not in seen_ids:
                seen_ids.add(pet_id)
                dogs.append({
                    "ID": pet_id,
                    "Name": card.get_text(strip=True),
                    "Photo": photo,
                    "URL": f"https://www.adoptapet.com/pet/{pet_id}"
                })

    st.markdown(f"**{len(dogs)} dogs found.** Running AI filter...")

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    matches = []
    progress = st.progress(0)

    for i, dog in enumerate(dogs):
        prompt = f"""Given these preferences:
{preferences}

Is this a dog (not a cat/rabbit/other animal) AND a good match? Start with YES or NO, then one sentence why.

Name: {dog['Name']}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        if answer.upper().startswith("YES"):
            matches.append((dog, answer))
        progress.progress((i + 1) / len(dogs))

    if matches:
        st.markdown(f"### ✨ {len(matches)} match{'es' if len(matches) > 1 else ''} for {user_name}")
        for dog, reason in matches:
            col_img, col_text = st.columns([1, 3])
            with col_img:
                if dog.get("Photo"):
                    st.image(dog["Photo"], width=110)
            with col_text:
                st.markdown(f"<div class='dog-name'><a href='{dog['URL']}' target='_blank' style='color:#1a1a1a;text-decoration:none'>{dog['Name']}</a></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dog-reason'>{reason}</div>", unsafe_allow_html=True)
            st.divider()
    else:
        st.info("No matches found. Try broadening your preferences.")

import random

# Chili recipe footer
chili_recipes = [
    ("2025 - Greg Lindsey", "https://www.casichili.net/2025-greg-lindsey.html"),
    ("2024 - Kevin Casey", "https://www.casichili.net/2024-kevin-casey.html"),
    ("2023 - Rene Chapa", "https://www.casichili.net/2023-rene-chapa.html"),
    ("2022 - Kris Hudspeth", "https://www.casichili.net/2022-kris-hudspeth.html"),
    ("2019 - Kathryn Cavender", "https://www.casichili.net/2019-kathryn-cavender.html"),
    ("2018 - Tom Dozier", "https://www.casichili.net/2018-tom-dozier.html"),
    ("2017 - Brent Allen", "https://www.casichili.net/2017-brent-allen.html"),
    ("2016 - Lisa Stone", "https://www.casichili.net/2016---lisa-stone.html"),
    ("2015 - James Burns", "https://www.casichili.net/2015-james-burns.html"),
    ("2014 - Jason Goains", "https://www.casichili.net/2014-jason-goains.html"),
    ("2013 - Brian Spencer", "https://www.casichili.net/2013-brian-spencer.html"),
    ("2012 - TJ Cannon", "https://www.casichili.net/2012-t-j-cannon.html"),
    ("2006 - Dana Plocheck", "https://www.casichili.net/2006-dana-plocheck.html"),
    ("2005 - Margaret Nadeau", "https://www.casichili.net/2005-margaret-nadeau.html"),
    ("2004 - Roger Foltz", "https://www.casichili.net/2004-roger-foltz.html"),
    ("2003 - Honey Jones", "https://www.casichili.net/2003-honey-jones.html"),
    ("1999 - Bob Coats", "https://www.casichili.net/1999-bob-coats.html"),
    ("1998 - Carol West", "https://www.casichili.net/1998-carol-west.html"),
    ("1992 - Cindy Reed", "https://www.casichili.net/1992-cindy-reed.html"),
]

st.markdown("---")
recipe_name, recipe_url = random.choice(chili_recipes)
st.markdown(f"🌶️ **Today's chili recipe:** [{recipe_name}]({recipe_url})")
