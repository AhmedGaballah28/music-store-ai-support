# 🎵 Digital Music Store Support System

A multi-agent AI-powered customer support system for a digital music store, built with LangGraph, Google Gemini, and Streamlit.

## 📋 Overview

This application provides an intelligent customer support interface for a digital music store. It uses a multi-agent architecture to handle:

- **Music Catalog Queries**: Search for artists, albums, songs, and genres
- **Invoice Management**: View purchase history and invoice details
- **Customer Verification**: Secure identity verification via email, phone, or customer ID
- **Personalized Recommendations**: Music suggestions based on user preferences and history

## 🏗️ Architecture

The system uses a LangGraph-based state machine with the following agents:

```
┌─────────────┐
│   Entry     │
│   Node      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Supervisor │
│    Node     │
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
┌─────┐  ┌─────┐
│Music│  │Invoice│
│Agent│  │Agent │
└──┬──┘  └──┬──┘
   │        │
   └───┬────┘
       ▼
┌─────────────┐
│  Combine    │
│  Responses  │
└─────────────┘
```

## 🚀 Features

- **Multi-Agent System**: Intelligent routing between music catalog and invoice agents
- **Customer Verification**: Secure verification using email, phone, or customer ID
- **Long-Term Memory**: Persistent storage of user preferences and interaction history
- **Real-Time Database**: Uses the Chinook sample database for music catalog data
- **Modern UI**: Beautiful Streamlit interface with responsive design

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- A Google API key for Gemini

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Final\ Project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example env file
   cp .env.example .env
   
   # Edit .env and add your Google API key
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🐳 Docker

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)

### Run with Docker Compose

1. **Create your environment file**
   ```bash
   cp .env.example .env
   ```

2. **Set your Gemini API key in `.env`**
   ```bash
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. **Build and start the container**
   ```bash
   docker compose up --build
   ```

4. **Open the app**
   ```
   http://localhost:8501
   ```

### Run with Docker Only

```bash
docker build -t music-store-ai-support .
docker run --rm -p 8501:8501 --env-file .env music-store-ai-support
```

## 📁 Project Structure

```
Final Project/
├── app.py              # Main Streamlit application
├── config.py           # Configuration and environment variables
├── database.py         # Database connection and management
├── graph.py            # LangGraph workflow definition
├── agents.py           # Agent implementations (Music, Invoice, Verification)
├── tools.py            # Database query tools with security measures
├── state.py            # State definition for the graph
├── memory_mangement.py # Long-term memory storage
├── .env                # Environment variables (not committed)
├── .env.example        # Example environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 🔧 Configuration

| Variable         | Description                | Default                |
|------------------|----------------------------|------------------------|
| `GOOGLE_API_KEY` | Google Gemini API key      | Required               |
| `DATABASE_URL`   | Database connection string | `sqlite:///chinook.db` |
| `LOG_LEVEL`      | Logging level              | `INFO`                 |

## 🛡️ Security Features

This application implements several security measures:

### Input Validation & Sanitization
- All user inputs are validated and sanitized before database queries
- SQL injection prevention through input escaping and validation
- Customer ID validation ensures numeric values within expected ranges

### XSS Protection
- HTML content is escaped using `html.escape()` before rendering
- User-provided content is sanitized before being displayed in the UI

### Authentication & Authorization
- Customer verification required for sensitive operations (invoices)
- Multiple verification methods: email, phone, customer ID
- Session-based state management

### Data Protection
- Sensitive API keys stored in environment variables
- `.gitignore` prevents accidental commit of sensitive files
- Memory storage isolated per customer

## 📖 Usage Examples

### Music Queries
- "What albums do you have by The Beatles?"
- "Show me some jazz music"
- "Find songs by Led Zeppelin"
- "What rock albums do you have?"

### Invoice Queries (requires verification)
- "What was my most recent purchase?"
- "Show me all my invoices"
- "How much did I spend last time?"

### Verification
- "My email is user@example.com"
- "My phone number is +1-555-123-4567"
- "My customer ID is 42"

## 🧪 Testing

To test the application with the sample database:

1. Start the application
2. Use one of the sample customers from the Chinook database:
   - Email: `luisg@embraer.com.br`
   - Customer ID: `1`

## 📚 Dependencies

- `streamlit` - Web UI framework
- `langchain` - LLM framework
- `langchain-google-genai` - Google Gemini integration
- `langgraph` - Graph-based agent workflows
- `sqlalchemy` - Database ORM
- `python-dotenv` - Environment variable management

## ⚠️ Important Notes

1. **Never commit your `.env` file** - It contains sensitive API keys
2. **Verify customer identity** before accessing invoice information
3. **Rate limits** - Be aware of Google API rate limits
4. **Database** - The Chinook database is downloaded on first run

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Chinook Database](https://github.com/lerocha/chinook-database) - Sample database
- [LangChain](https://langchain.com/) - LLM framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Streamlit](https://streamlit.io/) - Web UI framework
