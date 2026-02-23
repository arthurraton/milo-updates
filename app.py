import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import random

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Rescue Dog Finder", page_icon="🐾", layout="centered")

st.markdown("""
<div class='hero'>
    <div class='hero-sub'>AI-powered · Rescue · Matching</div>
    <div class='hero-title'>Dog Finder</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; font-size: 4rem;">
    🐩
</div>
""", unsafe_allow_html=True)

with st.form("preferences"):
