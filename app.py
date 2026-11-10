import io
import json
import streamlit.components.v1 as components
import re

import requests
import streamlit as st
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS

st.set_page_config(page_title="Language Translation Tool", page_icon="🌐", layout="centered")

FALLBACK = {"english": "en-GB", "hindi": "hi-IN", "marathi": "mr-IN", "french": "fr-FR",
            "german": "de-DE", "spanish": "es-ES", "japanese": "ja-JP", "arabic": "ar-SA",
            "konkani": "kok-IN"}


@st.cache_data
def get_languages():
    """Fetch supported languages {name: code}; fall back to a small list if it fails."""
    try:
        langs = dict(MyMemoryTranslator(source="en-GB", target="hi-IN").get_supported_languages(as_dict=True))
    except Exception:
        langs = dict(FALLBACK)
    langs.setdefault("konkani", "kok-IN")  # make sure Konkani is always selectable
    return langs


def is_konkani(code):
    return bool(code) and (code.lower().startswith("kok") or code.lower() == "gom")


def short_code(code):
    """'hi-IN' -> 'hi' (Google / TTS style). Konkani -> 'gom' (Google's code for it)."""
    if is_konkani(code):
        return "gom"
    if code.lower().startswith("zh"):
        return code
    return code.split("-")[0].lower()


def chunk_text(text, limit=450):
    """Split long text on sentence boundaries (MyMemory accepts ~500 chars per request)."""
    sentences = re.split(r"(?<=[.!?।])\s+", text.strip())
    chunks, current = [], ""
    for s in sentences:
        while len(s) > limit:
            cut = s.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if current:
                chunks.append(current)
                current = ""
            chunks.append(s[:cut])
            s = s[cut:].strip()
        if len(current) + len(s) + 1 <= limit:
            current = f"{current} {s}".strip()
        else:
            chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks


def google_gtx(text, source, target):
    """Direct call to Google's public translate endpoint (different from deep-translator's)."""
    r = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    return "".join(seg[0] for seg in data[0] if seg and seg[0])


def translate_chunk(part, source, target):
    g_src = "auto" if source == "auto" else short_code(source)
    g_tgt = short_code(target)
    konkani = is_konkani(source) or is_konkani(target)

    providers = {
        "Google": lambda: google_gtx(part, g_src, g_tgt),
        "MyMemory": lambda: MyMemoryTranslator(source=source, target=target).translate(part),
        "Google-2": lambda: GoogleTranslator(source=g_src, target=g_tgt).translate(part),
    }
    # Konkani and auto-detect need Google; everything else works best with MyMemory first.
    order = ["Google", "Google-2", "MyMemory"] if (konkani or source == "auto") \
        else ["MyMemory", "Google", "Google-2"]

    errors = []
    for name in order:
        try:
            res = providers[name]()
            if not res or not res.strip():
                raise ValueError("empty result")
            if konkani and res.strip().lower() == part.strip().lower() and len(part) > 3:
                raise ValueError("language not actually translated")
            return res
        except Exception as e:
            errors.append(f"{name}: {str(e).strip()[:80] or 'failed'}")
    raise RuntimeError(" | ".join(errors))


def translate_text(text, source, target):
    return " ".join(translate_chunk(p, source, target) for p in chunk_text(text))

def speak_button(text, lang):
    """Speak text using the browser's built-in speech synthesis (no network call)."""
    payload = json.dumps(text).replace("</", "<\\/")
    lang_js = json.dumps(lang)
    html = f"""
    <button id="speak" style="padding:8px 16px;border-radius:8px;border:1px solid #ccc;
            background:#fff;cursor:pointer;font-size:15px;">🔊 Listen</button>
    <span id="msg" style="font-family:sans-serif;font-size:13px;color:#888;margin-left:8px;"></span>
    <script>
      const text = {payload};
      const lang = {lang_js};
      const msg = document.getElementById('msg');
      document.getElementById('speak').onclick = () => {{
        const synth = window.speechSynthesis;
        if (!synth) {{ msg.textContent = 'Speech is not supported in this browser.'; return; }}
        synth.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        const voices = synth.getVoices();
        const want = lang.toLowerCase();
        const v = voices.find(x => x.lang.replace('_','-').toLowerCase() === want)
               || voices.find(x => x.lang.toLowerCase().startsWith(want.split('-')[0]));
        if (v) {{ u.voice = v; msg.textContent = ''; }}
        else {{ msg.textContent = 'No voice installed for this language; trying default voice.'; }}
        synth.speak(u);
      }};
    </script>
    """
    components.html(html, height=60)

LANGS = get_languages()
NAMES = sorted(LANGS.keys())
AUTO = "auto detect"

# ---- session state defaults ----
st.session_state.setdefault("src", "english" if "english" in LANGS else NAMES[0])
st.session_state.setdefault("tgt", "hindi" if "hindi" in LANGS else NAMES[0])
st.session_state.setdefault("result", "")
st.session_state.setdefault("audio", None)
st.session_state.setdefault("audio_note", "")


def swap_languages():
    if st.session_state.src != AUTO:
        st.session_state.src, st.session_state.tgt = st.session_state.tgt, st.session_state.src


st.title("🌐 Language Translation Tool")
st.caption("Enter text, choose source & target languages, and translate.")

col1, col2, col3 = st.columns([5, 1, 5])
with col1:
    st.selectbox("From", [AUTO] + NAMES, key="src", format_func=str.title)
with col2:
    st.write("")
    st.write("")
    st.button("⇄", on_click=swap_languages, help="Swap languages (not available for auto detect)")
with col3:
    st.selectbox("To", NAMES, key="tgt", format_func=str.title)

text = st.text_area("Enter text to translate", height=150, max_chars=5000,
                    placeholder="Type or paste your text here...")

if st.button("Translate", type="primary"):
    st.session_state.audio = None
    st.session_state.audio_note = ""
    if not text.strip():
        st.warning("Please enter some text first.")
        st.session_state.result = ""
    else:
        try:
            source = "auto" if st.session_state.src == AUTO else LANGS[st.session_state.src]
            target = LANGS[st.session_state.tgt]
            with st.spinner("Translating..."):
                st.session_state.result = translate_text(text, source, target)
        except Exception as e:
            st.session_state.result = ""
            st.error("Translation failed. The services may be temporarily rate-limiting your "
                     f"network; wait a minute and retry.\n\nDetails: {e}")

if st.session_state.result:
    st.subheader("Translated text")
    # st.code shows a built-in copy-to-clipboard icon (top right of the box)
    st.code(st.session_state.result, language=None, wrap_lines=True)

    code = LANGS[st.session_state.tgt]
    if is_konkani(code):
        speak_lang = "mr-IN"  # no Konkani voice exists; Marathi uses the same Devanagari script
        st.caption("Konkani voice is not available; the Marathi voice will read it.")
    else:
        speak_lang = code
    speak_button(st.session_state.result, speak_lang)

