import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
import speech_recognition as sr
from gtts import gTTS
import base64

# --- 1. CONFIGURATION & SECRETS ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# ❄️ SNOWFALL EFFECT
def add_snow_effect():
    snow_css = """
    <style>
    #snow { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1000; }
    </style>
    <div id="snow"></div>
    <script src="https://unpkg.com/magic-snowflakes/dist/snowflakes.min.js"></script>
    <script> var snowflakes = new Snowflakes({ color: '#ffffff', count: 50, minSize: 10, maxSize: 25 }); </script>
    """
    st.components.v1.html(snow_css, height=0)

# --- 2. INITIALIZE AI CLIENT ---
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

# 🚀 MODEL PRIORITIZATION
PRIMARY_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
FALLBACK_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-7b-instruct:free"
]

# --- 3. CORE FUNCTIONS ---

def speak(text):
    if text and text.strip():
        with st.spinner("🔊 Preparing voice output..."):
            try:
                tts = gTTS(text=text, lang='en')
                tts.save("temp.mp3")
                with open("temp.mp3", "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode()
                    st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" autoplay>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"TTS Error: {e}")

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎙️ Listening...")
        audio = r.listen(source)
    try:
        query = r.recognize_google(audio)
        st.info(f"🗨️ You said: {query}")
        return query
    except:
        st.warning("👂 Couldn't hear you. Try again!")
        return None

# --- 4. MAIN UI ---
add_snow_effect() 
st.title("❄️ MindFlow: The PDF Teacher")

if not api_key:
    st.error("❌ OPENROUTER_API_KEY missing in .env file!")
    st.stop()

uploaded_file = st.file_uploader("Upload Study PDF", type="pdf")

if uploaded_file:
    reader = PdfReader(uploaded_file)
    text_content = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
    short_context = text_content[:2000] 

    st.success("✅ PDF Analyzed!")
    st.balloons() 

    col1, col2 = st.columns(2)

    if col1.button("❓ Teacher: Ask Question"):
        with st.spinner("⏳ AI Teacher is thinking..."):
            try:
                response = client.chat.completions.create(
                    model=PRIMARY_MODEL,
                    extra_body={"models": FALLBACK_MODELS},
                    messages=[
                        {"role": "system", "content": "You are a teacher. Ask one short question based on the text. No bold formatting."},
                        {"role": "user", "content": f"Text: {short_context}"}
                    ]
                )
                question = response.choices[0].message.content
                st.session_state['q'] = question
                st.markdown(f"### 👩‍🏫 {question}")
                speak(question)
            except Exception as e:
                st.error(f"API Error: {e}")

    if col2.button("🎤 Answer with Voice"):
        if 'q' in st.session_state:
            user_ans = listen()
            if user_ans:
                with st.spinner("🧠 Checking..."):
                    res = client.chat.completions.create(
                        model=PRIMARY_MODEL,
                        extra_body={"models": FALLBACK_MODELS},
                        messages=[
                            {"role": "system", "content": "Briefly tell the user if they are correct based on the PDF."},
                            {"role": "user", "content": f"Q: {st.session_state['q']}\nAnswer: {user_ans}"}
                        ]
                    )
                    feedback = res.choices[0].message.content
                    st.success(feedback)
                    st.balloons() 
                    speak(feedback)
        else:
            st.warning("Click 'Ask Question' first!")