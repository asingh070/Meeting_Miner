<<<<<<< HEAD
# Meeting-Miner
Repository for meeting miner, a solution to turn transcripts into insightful details.
=======
# MeetingMiner 📊

Turn messy meeting conversations into decisions, projects, risks, and company pulse.

## Overview

MeetingMiner is an intelligent system that processes meeting transcripts and extracts structured intelligence including:

- **Executive Summary**: Sharp, concise summaries of key decisions and outcomes
- **Project Candidates**: Explicit and implicit projects mentioned in meetings
- **Project Health Signals**: Owners, blockers, risks, and commitment tracking
- **Company Pulse**: Sentiment analysis, tone detection, and behavioral cues
- **Multilingual Support**: Handles Hinglish (Hindi-English mix) and other multilingual content
- **RAG Chatbot**: Query meeting history using natural language

## Features

- 📝 **Multiple Input Formats**: Supports plain text and speaker-tagged JSON transcripts
- 🤖 **Configurable LLM Providers**: Groq, Anthropic, or local models (Ollama)
- 🌍 **Multilingual Awareness**: Understands Hinglish and code-switching
- 🔍 **RAG-Powered Chatbot**: Semantic search across meeting history
- 📊 **Rich Visualizations**: Modern web UI with interactive charts and insights
- 💾 **Persistent Storage**: SQLite database with vector embeddings

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd meetingminer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   - `LLM_PROVIDER`: Choose `groq`
   - API keys for your chosen provider
   - Model names (optional, defaults provided)

4. **Initialize the database**:
   The database will be automatically created on first run.

## Usage

### Running the Application

Start the Flask API server:
```bash
python api.py
```

Or use the run script:
```bash
python run.py
```

The application will be available at `http://localhost:5000` (or the PORT specified in environment variables).

Open your browser and navigate to `http://localhost:5000` to access the web interface.

### Using the Application

1. **Upload Meeting**: 
   - Upload a transcript file (.txt or .json) or paste text directly
   - Optionally provide a meeting title
   - Click "Process Meeting" to extract intelligence

2. **View Results**:
   - Browse extracted summaries, projects, health signals, and company pulse
   - Navigate through tabs to see different aspects

3. **Chatbot**:
   - Ask questions about meetings in natural language
   - Query specific meetings or search across all meetings
   - Get answers based on semantic search of transcripts

4. **Meeting History**:
   - Browse all processed meetings
   - Access past meeting data


## Project Structure

```
meetingminer/
├── backend/
│   ├── config.py              # Configuration management
│   ├── models.py              # Database models
│   ├── database.py            # Database utilities
│   ├── transcript_parser.py   # Transcript parsing
│   ├── pipeline.py            # Main processing pipeline
│   ├── embeddings.py          # Vector embeddings
│   ├── chatbot.py             # RAG chatbot
│   ├── extractors/            # Extraction modules
│   │   ├── summary_extractor.py
│   │   ├── project_extractor.py
│   │   ├── health_extractor.py
│   │   └── pulse_extractor.py
│   └── llm/                   # LLM providers
│       ├── base.py
│       ├── groq_client.py
│       ├── anthropic_client.py
│       └── local_client.py
├── frontend/
│   ├── index.html             # Main HTML page
│   ├── styles.css             # CSS styles
│   └── app.js                 # JavaScript application logic
├── api.py                      # Flask API server
├── data/                      # Database and vector store
├── requirements.txt
└── README.md
```

## API Usage (Programmatic)

You can also use the pipeline programmatically:

```python
from backend.pipeline import MeetingPipeline
from backend.chatbot import MeetingChatbot

# Initialize
pipeline = MeetingPipeline()
chatbot = MeetingChatbot()

# Process a transcript
result = pipeline.process(
    transcript="Your meeting transcript here...",
    title="Q4 Planning Meeting"
)

# Query meetings
answer = chatbot.query("What projects were discussed?")
```

## Example Use Cases

1. **Project Management**: Extract project commitments and track blockers
2. **Decision Tracking**: Identify key decisions and action items
3. **Team Health**: Monitor sentiment and engagement patterns
4. **Knowledge Base**: Build searchable repository of meeting insights
5. **Compliance**: Track commitments and follow-ups

## Troubleshooting

### Database Errors
- Ensure the `data/` directory exists and is writable
- Check database path in configuration

### LLM API Errors
- Verify API keys are set correctly
- Check API rate limits and quotas
- For local models, ensure Ollama is running

### Embedding Errors
- First run will download the embedding model (may take time)
- Ensure sufficient disk space for model storage

### HOW TO RUN THE FRONTEND AND BACKEND CODE
- Please refer HOW_TO_RUN.md to get details about running the backend and frontend.

>>>>>>> 22acdbc (Initial commit with files for Meeting Miner solution)
