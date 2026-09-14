# YouTube RAG Chatbot

A secure Streamlit application where users can register or log in, load a
YouTube video, and ask questions from its transcript using RAG.

## Features

- Email/OTP login and Google OIDC login
- YouTube transcript loading
- ChromaDB vector search and Hugging Face LLM responses
- Answers restricted to the selected video's transcript

## Tech stack

Streamlit, LangChain, ChromaDB, Hugging Face, PostgreSQL/Neon, and Google OIDC.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Akshay-3210/YouTube-RAG-Chatbot.git
cd YouTube-RAG-Chatbot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Neon and SMTP credentials

Create a `.env` file inside the `streamlit` folder:

```env
DATABASE_URL="postgresql://USERNAME:PASSWORD@HOST/DATABASE?sslmode=require"
SMTP_EMAIL="your-email@gmail.com"
SMTP_PASSWORD="your-gmail-app-password"
```

- Get `DATABASE_URL` from your [Neon](https://neon.tech) project dashboard.
- For Gmail, use a [Google App Password](https://myaccount.google.com/apppasswords), not your normal Gmail password.
- Never commit `.env` to GitHub.

### 5. Configure YouTube chatbot credentials

Copy `ytchatbot/.env.example` to `ytchatbot/.env`, then add your Hugging Face
and Chroma credentials:

```bash
cp ytchatbot/.env.example ytchatbot/.env
```

This file is separate from `.env`: `.env` contains database/SMTP values and
`ytchatbot/.env` contains YouTube chatbot service values.

### 6. Configure Google OIDC login

Create `.streamlit/secrets.toml`:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "generate-a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

In Google Cloud Console:

1. Create an OAuth 2.0 Client ID.
2. Add this authorized redirect URI:

   ```text
   http://localhost:8501/oauth2callback
   ```

3. Copy the Client ID and Client Secret into `.streamlit/secrets.toml`.

Never commit `.streamlit/secrets.toml` to GitHub.

### 7. Run the app locally

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Deploy on Streamlit Community Cloud

1. Deploy the repository with `app.py` as the main file.
2. In **App settings → Secrets**, add all values from both local `.env` files
   and the Google OIDC configuration. Use TOML format:

```toml
DATABASE_URL = "your-neon-database-url"
SMTP_EMAIL = "your-email@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
HUGGINGFACEHUB_API_TOKEN = "your-hugging-face-token"
CHROMA_API_KEY = "your-chroma-api-key"
CHROMA_TENANT = "your-chroma-tenant"
CHROMA_DATABASE = "your-chroma-database"

[auth]
redirect_uri = "https://your-app.streamlit.app/oauth2callback"
cookie_secret = "a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

3. In Google Cloud Console, add this exact value as an **Authorized redirect
   URI** (replace it with your deployed app URL):

```text
https://your-app.streamlit.app/oauth2callback
```

`Authlib` is listed in `requirements.txt` because Streamlit requires it for
`st.login()`.
