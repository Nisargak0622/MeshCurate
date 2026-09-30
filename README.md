# MeshCurate — AI-Organized Instagram/Facebook Saves

A web app to organize your saved Instagram and Facebook posts/reels
into categories automatically, using Claude AI to read the caption and sort
it for you — solving the "everything just dumped in one Saved folder"
problem.

## Features
- 🔐 User accounts (register/login, hashed passwords)
- 🔗 Paste any public Instagram or Facebook post/reel link
- 🤖 AI-powered categorization using Claude — reads the caption and picks
  the best category (Recipe, Motivational, Traditional, Fitness, Travel,
  Comedy, Tech, Fashion, Other)
- ✋ Manual category override if you'd rather choose yourself
- 🖼️ Real embedded previews (actual photo/video, not just a link)
- ⭐ Mark favorites
- 🗂️ Filter your saved posts by category
- 📝 Add personal notes to any saved post

## Tech Stack
- Python 3, Flask
- Flask-SQLAlchemy (SQLite database)
- Flask-Login (authentication/sessions)
- Anthropic API (Claude) for caption classification
- Jinja2 templates + plain CSS (no frontend framework needed)

## Setup & Installation

1. Clone/download this project and open a terminal inside the folder.

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Copy `.env.example` to a new file named `.env`
   - Get a free Anthropic API key at [console.anthropic.com](https://console.anthropic.com)
   - Paste it into `.env`:
     ```
     SECRET_KEY=any-random-string-you-want
     ANTHROPIC_API_KEY=your-real-key-here
     ```

5. Run the app:
   ```bash
   python app.py
   ```

6. Open your browser to **http://127.0.0.1:5000**

## How to Use
1. Register an account
2. Click **"+ Save Post"**
3. Paste the Instagram/Facebook post URL
4. Paste the caption (so Claude can read it and classify it)
5. Leave category as "Let AI decide" or pick one manually
6. Save — it now appears on your dashboard, filterable by category

## Notes
- Only **public** posts embed properly (private accounts won't render previews)
- Instagram embeds use their official `embed.js` widget — no scraping involved
- Facebook embeds use their official Page Plugin iframe

## Project Structure
```
savedvault/
├── app.py                 # Flask routes
├── models.py               # Database models
├── ai_classifier.py        # Claude API categorization logic
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── add_post.html
└── static/
    └── style.css
```
