import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Dog Finder", page_icon="🐾", layout="centered")

st.title("🐾 Dog Finder")
st.markdown("Find your perfect rescue dog, filtered by AI.")

with st.form("preferences"):
    user_name = st.text_input("Your name", value="Austin")
    location = st.text_input("Your city", value="San Francisco, CA")
    breed_pref = st.text_input("Breed preference", value="Poodle mix")
    size_pref = st.selectbox("Size", ["Small (under 25 lbs)", "Medium (25-50 lbs)", "Large (50+ lbs)", "Any"])
    age_pref = st.selectbox("Age", ["Puppy (under 1yr)", "Young (1-3 yrs)", "Adult (3-8 yrs)", "Any"])
    other_dogs = st.checkbox("Must be good with other dogs", value=True)
    extra_notes = st.text_area("Anything else?", placeholder="e.g. low shedding, apartment friendly...")
    submitted = st.form_submit_button("Find Dogs")

if submitted:
    preferences = f"""
- Looking for: {breed_pref}
- Size: {size_pref}
- Age: {age_pref}
- Good with other dogs: {other_dogs}
- Location: {location}
- Additional notes: {extra_notes}
"""
    with st.spinner("Fetching dogs from Adopt-a-Pet..."):
        resp = requests.get(
            "https://www.adoptapet.com/shelter/73753/available-pets",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        dogs = []
        seen_ids = set()
        for card in soup.select("a[href*='/pet/']"):
            href = card.get("href", "")
            pet_id = href.split("/pet/")[-1].strip("/").split("-")[0]
            pet_name = card.get_text(strip=True)
            img = card.find("img")
            photo = img["src"] if img and img.get("src") else None
            if pet_id and pet_name and pet_id not in seen_ids:
                seen_ids.add(pet_id)
                dogs.append({
                    "ID": pet_id,
                    "Name": pet_name,
                    "Photo": photo,
                    "URL": f"https://www.adoptapet.com/pet/{pet_id}"
                })

    st.write(f"Found **{len(dogs)}** dogs. Running AI filter...")

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    matches = []

    progress = st.progress(0)
    for i, dog in enumerate(dogs):
        prompt = f"""Given these preferences:
{preferences}

Is this dog a good match? Start with YES or NO, then one sentence why.

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

    st.success(f"Found **{len(matches)}** matches for {user_name}!")

    if matches:
        for dog, reason in matches:
            col1, col2 = st.columns([1, 3])
            with col1:
                if dog.get("Photo"):
                    st.image(dog["Photo"], width=120)
            with col2:
                st.markdown(f"### [{dog['Name']}]({dog['URL']})")
                st.write(reason)
            st.divider()
    else:
        st.info("No matches found today. Try adjusting your preferences.")
