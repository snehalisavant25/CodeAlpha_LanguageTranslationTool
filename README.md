\# 🌐 Language Translation Tool



Built for the \*\*CodeAlpha Artificial Intelligence Internship, Task 1\*\*.



A web app where users enter text, choose source and target languages, and get the translation instantly.



\## Features

\- Text input with source and target language selection

\- Auto-detect source language

\- Swap languages button

\- Translation using multiple services with automatic fallback (MyMemory, Google Translate)

\- Supports Indian languages including Hindi, Marathi and Konkani

\- Clear output display with a one-click copy button

\- Text-to-speech playback using the browser's built-in voices

\- Handles long text by splitting it into chunks

\- Error handling for empty input and service or network failures



\## Tech Stack

Python, Streamlit, deep-translator, requests, Web Speech API (browser text-to-speech)



\## Setup

```bash

git clone https://github.com/snehalisavant25/CodeAlpha\_LanguageTranslationTool.git

cd CodeAlpha\_LanguageTranslationTool

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python -m streamlit run app.py

```



\## How it works

1\. The user enters text and selects the source and target languages.

2\. The app sends the text to a translation service (MyMemory first; Google for Konkani and auto-detect), and falls back to another service if one fails.

3\. The translated text is displayed, and can be copied or read aloud.



\## Screenshots

!\[Hindi translation](screenshots/hindi.png)

!\[Konkani translation](screenshots/konkani.png)



\## Notes

\- Free translation services have rate limits; if a request fails, wait a minute and retry.

\- No Konkani voice exists in browsers, so the Marathi voice reads Konkani text.

