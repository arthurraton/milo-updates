import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import random

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Rescue Dog Finder", page_icon="🐾", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0a !important;
    color: #e8e8e8 !important;
}

.stApp {
    background-color: #0a0a0a !important;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: #ffffff !important;
}

.hero {
    padding: 3rem 0 2rem 0;
    border-bottom: 1px solid #222;
    margin-bottom: 2rem;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -2px;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.hero-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #555;
    letter-spacing: 2px;
    text-transform: uppercase;
}

section[data-testid="stForm"] {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 4px !important;
    padding: 2rem !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #0a0a0a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 4px !important;
    color: #e8e8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

.stTextInput > label,
.stTextArea > label,
.stSelectbox > label,
.stCheckbox > label {
    color: #666 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}

.stButton > button {
    background-color: #ffffff !important;
    color: #0a0a0a !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.75rem 2rem !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    width: 100% !important;
    margin-top: 1rem !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background-color: #e0e0e0 !important;
}

.stProgress > div > div {
    background-color: #ffffff !important;
}

.stProgress {
    background-color: #1a1a1a !important;
}

.dog-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 4px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}

.dog-card:hover {
    border-color: #444;
}

.dog-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.5rem;
}

.dog-reason {
    font-family: 'DM Sans', sans-serif;
    color: #888;
    font-size: 0.9rem;
    line-height: 1.6;
}

.meta-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    border: 1px solid #222;
    padding: 2px 8px;
    border-radius: 2px;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 8px;
}

.footer {
    border-top: 1px solid #1a1a1a;
    margin-top: 3rem;
    padding-top: 1.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #333;
}

.footer a {
    color: #555 !important;
    text-decoration: none !important;
}

.footer a:hover {
    color: #999 !important;
}

.results-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #1a1a1a;
}

div[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
}

hr {
    border-color: #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='hero'>
    <div class='hero-sub'>AI-powered · Rescue · Matching</div>
    <div class='hero-title'>Dog Finder</div>
</div>
""", unsafe_allow_html=True)

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
    submitted = st.form_submit_button("— Search —")

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
        non_dog_keywords = ["rabbit", "bunny", "cat", "kitten", "guinea", "bird", "hamster", "reptile"]

        for card in soup.select("a[href*='/pet/']"):
            href = card.get("href", "")
            pet_id = href.split("/pet/")[-1].strip("/").split("-")[0]
            pet_name = card.get_text(strip=True)
            img = card.find("img")
            photo = img["src"] if img and img.get("src") else None

            if any(kw in pet_name.lower() for kw in non_dog_keywords):
                continue

            if pet_id and pet_name and pet_id not in seen_ids:
                seen_ids.add(pet_id)
                dogs.append({
                    "ID": pet_id,
                    "Name": pet_name,
                    "Photo": photo,
                    "URL": f"https://www.adoptapet.com/pet/{pet_id}"
                })

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    matches = []
    progress = st.progress(0)

    for i, dog in enumerate(dogs):
        prompt = f"""Given these preferences:
{preferences}

Is this a dog AND a good match? Start with YES or NO, then one sentence why.

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

    st.markdown(f"<div class='results-header'>{len(matches)} match{'es' if len(matches) != 1 else ''} found for {user_name} · {len(dogs)} dogs scanned</div>", unsafe_allow_html=True)

    if matches:
        for dog, reason in matches:
            col_img, col_text = st.columns([1, 3])
            with col_img:
                if dog.get("Photo"):
                    st.image(dog["Photo"], width=110)
            with col_text:
                st.markdown(f"<div class='dog-name'><a href='{dog['URL']}' target='_blank' style='color:#fff;text-decoration:none'>{dog['Name']}</a></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dog-reason'>{reason}</div>", unsafe_allow_html=True)
            st.divider()
    else:
        st.markdown("<div class='dog-reason'>No matches found. Try broadening your preferences.</div>", unsafe_allow_html=True)

# Footer
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

recipe_name, recipe_url = random.choice(chili_recipes)
st.markdown(f"""
<div class='footer'>
    🌶️ &nbsp; CHILI RECIPE OF THE DAY &nbsp;·&nbsp; <a href='{recipe_url}' target='_blank'>{recipe_name}</a>
</div>
""", unsafe_allow_html=True)
