# Agentic Shopping POC
A Flask web application that uses OpenAI's Chat Completion API for conversational AI interactions with environmental impact tracking.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_KEY=your_flask_secret_key_here

# Database Configuration (optional)
DATABASE_URL=your_database_url_here
```

You can use `.env.example` as a template.

### 3. Run the Application

#### Development
```bash
python server.py
```

#### Production (Render/Heroku)
```bash