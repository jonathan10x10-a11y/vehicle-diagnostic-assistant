# 🚀 Quick Start Guide

Get your Vehicle Diagnostic Assistant running in 5 minutes!

## ⚡ Installation (3 minutes)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Knowledge Base
```bash
python main.py --setup
```

This creates sample documents and builds the FAISS index.

### Step 3: Configure API Key (Optional)
For AI-powered explanations, add your API key to `config.py`:

```python
OPENAI_API_KEY = "sk-proj-your-key-here"
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

**Note**: System works in demo mode without API keys!

---

## 🎮 Running the System

### Option 1: Web Interface (Recommended)
```bash
python main.py
```

Open browser to: **http://localhost:5000**

### Option 2: Terminal Demo
```bash
python main.py --demo
```

---

## 📋 Testing Individual Modules

### Test OBD Reader (Mock Data)
```bash
cd src
python obd_reader.py
```

Output shows simulated sensor readings and DTCs.

### Test Safety Checker
```bash
python safety_checker.py
```

Runs test cases with different scenarios.

### Test Knowledge Base
```bash
python knowledge_base.py
```

Creates sample documents and tests retrieval.

---

## 🎯 Example Queries

Once the web interface is running, try these questions:

1. **"Why is my engine temperature high?"**
   - Shows overheating information
   - Provides safety recommendations

2. **"What does error code P0301 mean?"**
   - Explains cylinder misfire
   - Lists inspection steps

3. **"Is it safe to continue driving?"**
   - Analyzes current vehicle state
   - Gives clear yes/no answer

4. **"What should I check first?"**
   - Prioritized checklist
   - Based on current symptoms

---

## 🛠️ Configuration

### Demo Mode (No Hardware Needed)
Edit `config.py`:
```python
USE_MOCK_DATA = True  # Uses simulated data
```

### Real Vehicle Mode
```python
USE_MOCK_DATA = False  # Connects to ELM327
OBD_PORT = "/dev/ttyUSB0"  # Or "COM3" on Windows
```

### Adjust Safety Thresholds
```python
COOLANT_TEMP_WARNING = 100    # °C
COOLANT_TEMP_CRITICAL = 120   # °C
RPM_MAX_SAFE = 6000          # rpm
```

---

## 📁 Project Structure (Simplified)

```
vehicle-diagnostic-assistant/
├── src/                  # All Python modules
│   ├── obd_reader.py    # Reads vehicle data
│   ├── safety_checker.py # Safety rules
│   ├── knowledge_base.py # RAG system
│   ├── retrieval.py     # Document search
│   ├── llm_generator.py # AI explanations
│   └── app.py           # Web server
├── templates/           # HTML UI
├── static/              # CSS styling
├── data/                # Knowledge base
├── config.py            # Settings
├── main.py              # Run this!
└── requirements.txt     # Dependencies
```

---

## 🔍 Troubleshooting

### Problem: "No module named 'X'"
```bash
pip install -r requirements.txt
```

### Problem: "Knowledge base not found"
```bash
python main.py --setup
```

### Problem: "LLM not working"
- Check API key in `config.py`
- System still works without LLM (shows retrieved docs)

### Problem: Web page not loading
- Check if Flask is running (should see messages in terminal)
- Try: http://127.0.0.1:5000 instead of localhost
- Check firewall settings

---

## 💡 Tips for Demo/Viva

### Before Presentation:
1. ✅ Run `python main.py --setup` to build knowledge base
2. ✅ Test web interface before demo
3. ✅ Have 2-3 example queries ready
4. ✅ Understand the flow diagram in GUIDE.md

### During Demo:
1. Show live dashboard with mock data
2. Ask a question and explain each step:
   - Safety check (instant)
   - Document retrieval (showing sources)
   - AI explanation (structured response)
3. Show the code for safety_checker.py rules
4. Explain why you chose RAG over fine-tuning

### Key Talking Points:
- ✅ "Works with real OBD-II standard"
- ✅ "Rule-based safety for explainability"
- ✅ "RAG for knowledge-grounded responses"
- ✅ "Modular design for easy maintenance"

---

## 📊 What Each Module Does (One-Liner)

| Module | Purpose |
|--------|---------|
| `obd_reader.py` | Reads sensor data from vehicle |
| `safety_checker.py` | Applies expert rules for alerts |
| `knowledge_base.py` | Creates searchable document database |
| `retrieval.py` | Finds relevant docs for queries |
| `llm_generator.py` | Generates AI explanations |
| `app.py` | Web server for user interface |
| `main.py` | Orchestrates everything |

---

## 🎓 For Your Report

### Technologies Used:
- **OBD-II**: Vehicle data protocol
- **Python**: Backend development
- **FAISS**: Vector similarity search
- **Sentence-Transformers**: Text embeddings
- **Flask**: Web framework
- **OpenAI/Anthropic**: LLM APIs
- **HTML/CSS/JS**: Frontend

### Key Concepts:
- **RAG (Retrieval-Augmented Generation)**
- **Semantic Search with Embeddings**
- **Rule-Based Expert Systems**
- **RESTful API Design**
- **Real-Time Data Processing**

---

## ✅ Verification Checklist

Before submitting/presenting, verify:

- [ ] All dependencies installed
- [ ] Knowledge base created (4 sample docs)
- [ ] Web interface loads successfully
- [ ] Can ask questions and get responses
- [ ] Safety alerts display correctly
- [ ] Sample DTCs show up
- [ ] Code is well-commented
- [ ] README.md is complete
- [ ] Can explain system architecture
- [ ] Understand each module's purpose

---

## 🎉 You're Ready!

Your system is now fully functional. You have:
- ✅ Complete working prototype
- ✅ Modular, clean code
- ✅ Professional web interface
- ✅ Mock data for demos
- ✅ Real OBD-II support ready
- ✅ Comprehensive documentation

**Go ace that project presentation! 🚀**

---

## 📞 Need Help?

Check these resources:
- **GUIDE.md** - Detailed documentation
- **README.md** - Project overview
- **Code comments** - Inline explanations

Common issues and solutions in GUIDE.md troubleshooting section.

Good luck! 🎓
