# Vera Bot

A merchant AI assistant built for the MagicPin AI Challenge.

## Quick Start

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the bot
```bash
python main.py
```

The server will start on http://localhost:8080

### Test endpoints
```bash
# Health check
curl http://localhost:8080/v1/healthz

# Metadata
curl http://localhost:8080/v1/metadata
```

### Run against judge simulator
```bash
# First, start the bot in one terminal
python main.py

# Then in another terminal, run the judge
cd ..
python judge_simulator.py
```

## Project Structure

```
bot/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI app and endpoints
    ├── models.py        # Pydantic models
    ├── storage.py       # Context storage and conversation management
    └── composer.py      # LLM-based message composition (TODO)
```

## Implementation Status

- [x] Project structure
- [x] HTTP server setup
- [x] All 5 endpoints (skeleton)
- [ ] Context storage (idempotent by version)
- [ ] LLM message composer
- [ ] Trigger-based conversation initiation
- [ ] Reply handling
- [ ] Conversation state management
- [ ] Testing with dataset
- [ ] Judge simulator testing
