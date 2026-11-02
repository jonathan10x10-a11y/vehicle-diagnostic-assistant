# AI-Powered Vehicle Diagnostic Assistant

## Project Overview
A college final-year project that combines OBD-II vehicle data reading with AI-powered diagnostics using Retrieval-Augmented Generation (RAG).

## Features
- Real-time OBD-II data reading (RPM, Speed, Temperature, DTCs)
- Rule-based safety checks
- AI-powered diagnostic explanations using RAG
- FAISS-based knowledge base retrieval
- Web-based chat interface

## System Architecture
```
User Query → OBD-II Reader → Safety Checker → RAG Retrieval → LLM Explanation → Flask UI
```

## Project Structure
```
vehicle-diagnostic-assistant/
├── data/                      # Knowledge base documents
│   ├── raw/                   # Raw text files (manuals, DTC docs)
│   └── processed/             # FAISS index and embeddings
├── src/                       # Source code modules
│   ├── obd_reader.py         # OBD-II data collection
│   ├── safety_checker.py     # Rule-based safety logic
│   ├── knowledge_base.py     # RAG knowledge base creation
│   ├── retrieval.py          # Document retrieval logic
│   ├── llm_generator.py      # LLM explanation generation
│   └── app.py                # Flask web application
├── templates/                 # HTML templates
│   └── index.html            # Chat UI
├── static/                    # CSS/JS files
│   └── style.css             # Basic styling
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration settings
├── main.py                   # Main integration script
└── README.md                 # This file
```

## Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Knowledge Base
```bash
# Place your vehicle manuals and DTC docs in data/raw/
python src/knowledge_base.py
```

### 3. Configure API Keys
Edit `config.py` and add your OpenAI API key (or other LLM provider).

### 4. Run the Application
```bash
python main.py
```

Access the web interface at: `http://localhost:5000`

## Hardware Requirements
- ELM327 OBD-II adapter (USB or Bluetooth)
- Vehicle with OBD-II port (most cars after 1996)

## Usage

### Testing Without Vehicle
The system includes mock data for demonstration purposes.

### With Real Vehicle
1. Connect ELM327 adapter to vehicle's OBD-II port
2. Start the vehicle
3. Run the application
4. Ask questions like:
   - "Why is my engine temperature high?"
   - "What does error code P0301 mean?"
   - "Should I continue driving?"

## Technologies Used
- **OBD-II Reading**: python-obd
- **Embeddings**: sentence-transformers
- **Vector Database**: FAISS
- **LLM**: OpenAI GPT / Claude API
- **Web Framework**: Flask
- **Frontend**: HTML/CSS/JavaScript

## Academic References
- OBD-II Protocol: SAE J1979 Standard
- RAG: Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- Vector Search: Johnson et al., "Billion-scale similarity search with GPUs"

## Future Enhancements
- Mobile app integration
- Historical data tracking
- Predictive maintenance ML models
- Multi-language support

## License
Educational Use - College Project

## Contributors
[Your Name] - [Roll Number]
