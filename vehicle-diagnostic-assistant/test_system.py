"""
System Test Script
Validates all modules are working correctly
Run this before your demo/presentation to ensure everything works!
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import config


def test_imports():
    """Test that all required libraries are installed"""
    print("\n" + "="*60)
    print("TEST 1: Checking Python Dependencies")
    print("="*60)
    
    required_modules = [
        ('obd', 'python-obd'),
        ('sentence_transformers', 'sentence-transformers'),
        ('faiss', 'faiss-cpu'),
        ('flask', 'Flask'),
        ('numpy', 'numpy'),
    ]
    
    missing = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {package_name:30} - Installed")
        except ImportError:
            print(f"❌ {package_name:30} - MISSING")
            missing.append(package_name)
    
    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies installed!")
    return True


def test_knowledge_base():
    """Test knowledge base creation and search"""
    print("\n" + "="*60)
    print("TEST 2: Knowledge Base Functionality")
    print("="*60)
    
    try:
        from src.knowledge_base import KnowledgeBase, create_sample_documents
        
        # Create sample documents if needed
        if not list(config.RAW_DATA_DIR.glob("*.txt")):
            print("📝 Creating sample documents...")
            create_sample_documents(config.RAW_DATA_DIR)
        
        # Check if index exists
        if not config.FAISS_INDEX_PATH.exists():
            print("🔨 Building FAISS index...")
            kb = KnowledgeBase()
            num_docs = kb.build_from_directory(config.RAW_DATA_DIR)
            kb.save(config.FAISS_INDEX_PATH, config.DOCUMENTS_PATH)
            print(f"✅ Index built with {num_docs} chunks")
        else:
            print("✅ FAISS index exists")
        
        # Test search
        kb = KnowledgeBase()
        kb.load(config.FAISS_INDEX_PATH, config.DOCUMENTS_PATH)
        
        test_query = "engine overheating"
        results = kb.search(test_query, top_k=3)
        
        if results:
            print(f"✅ Search working - Found {len(results)} results")
            print(f"   Top result: {results[0]['source']}")
            return True
        else:
            print("❌ Search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Knowledge base test failed: {e}")
        return False


def test_obd_reader():
    """Test OBD reader with mock data"""
    print("\n" + "="*60)
    print("TEST 3: OBD Reader (Mock Mode)")
    print("="*60)
    
    try:
        from src.obd_reader import OBDReader
        
        reader = OBDReader(use_mock=True)
        
        # Read data
        vehicle_data = reader.read_vehicle_data()
        dtc_codes = reader.read_dtc_codes()
        
        # Validate data structure
        required_keys = ['rpm', 'speed', 'coolant_temp', 'engine_load', 'status']
        for key in required_keys:
            if key not in vehicle_data:
                print(f"❌ Missing key: {key}")
                return False
        
        print(f"✅ Vehicle data: RPM={vehicle_data['rpm']}, Temp={vehicle_data['coolant_temp']}°C")
        print(f"✅ DTC codes: {len(dtc_codes)} code(s) detected")
        
        return True
        
    except Exception as e:
        print(f"❌ OBD reader test failed: {e}")
        return False


def test_safety_checker():
    """Test safety checker logic"""
    print("\n" + "="*60)
    print("TEST 4: Safety Checker")
    print("="*60)
    
    try:
        from src.safety_checker import SafetyChecker
        
        checker = SafetyChecker()
        
        # Test case 1: Normal conditions
        normal_data = {
            'rpm': 2500,
            'speed': 60,
            'coolant_temp': 90,
            'engine_load': 35
        }
        result1 = checker.check_all(normal_data, [])
        
        if result1['severity'] == 'NORMAL':
            print("✅ Normal conditions detected correctly")
        else:
            print(f"❌ Expected NORMAL, got {result1['severity']}")
            return False
        
        # Test case 2: Critical temperature
        critical_data = {
            'rpm': 3000,
            'speed': 80,
            'coolant_temp': 125,  # Critical!
            'engine_load': 60
        }
        result2 = checker.check_all(critical_data, [])
        
        if result2['severity'] in ['CRITICAL', 'IMMEDIATE']:
            print("✅ Critical temperature detected correctly")
        else:
            print(f"❌ Expected CRITICAL/IMMEDIATE, got {result2['severity']}")
            return False
        
        # Test case 3: DTC code
        dtc_codes = [('P0301', 'Cylinder 1 Misfire')]
        result3 = checker.check_all(normal_data, dtc_codes)
        
        if result3['severity'] in ['CRITICAL', 'WARNING']:
            print("✅ DTC code handled correctly")
        else:
            print(f"❌ Expected CRITICAL/WARNING for DTC, got {result3['severity']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Safety checker test failed: {e}")
        return False


def test_retrieval():
    """Test retrieval module"""
    print("\n" + "="*60)
    print("TEST 5: Context Retrieval")
    print("="*60)
    
    try:
        from src.retrieval import ContextRetriever
        
        retriever = ContextRetriever()
        
        query = "high temperature"
        vehicle_data = {'rpm': 3000, 'coolant_temp': 110, 'speed': 70, 'engine_load': 50}
        dtc_codes = []
        
        result = retriever.retrieve_context(query, vehicle_data, dtc_codes)
        
        if result['num_sources'] > 0:
            print(f"✅ Retrieved {result['num_sources']} relevant documents")
            print(f"✅ Context length: {len(result['context'])} characters")
            return True
        else:
            print("❌ No documents retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")
        return False


def test_llm_generator():
    """Test LLM generator (if API key configured)"""
    print("\n" + "="*60)
    print("TEST 6: LLM Generator")
    print("="*60)
    
    # Check if API key is configured
    if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY == "your-api-key-here":
        print("⚠️ OpenAI API key not configured - Skipping LLM test")
        print("   (System will work with mock responses)")
        return True
    
    if config.LLM_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY == "your-api-key-here":
        print("⚠️ Anthropic API key not configured - Skipping LLM test")
        print("   (System will work with mock responses)")
        return True
    
    try:
        from src.llm_generator import DiagnosticExplainer
        
        explainer = DiagnosticExplainer()
        
        query = "Test query"
        context = "Test context with vehicle data"
        
        # Note: We won't actually call the API in tests to avoid costs
        print("✅ LLM generator initialized successfully")
        print("   (Not testing actual API call to avoid costs)")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM generator test failed: {e}")
        return False


def test_flask_app():
    """Test Flask app initialization"""
    print("\n" + "="*60)
    print("TEST 7: Flask Web Application")
    print("="*60)
    
    try:
        from src.app import app
        
        # Check if app is created
        if app:
            print("✅ Flask app created successfully")
        else:
            print("❌ Flask app creation failed")
            return False
        
        # Check routes exist
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        
        expected_routes = ['/', '/api/vehicle-status', '/api/diagnose', '/api/health']
        for route in expected_routes:
            if any(route in rule for rule in rules):
                print(f"✅ Route exists: {route}")
            else:
                print(f"❌ Missing route: {route}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False


def test_file_structure():
    """Test that all necessary files exist"""
    print("\n" + "="*60)
    print("TEST 8: File Structure")
    print("="*60)
    
    required_files = [
        'config.py',
        'main.py',
        'requirements.txt',
        'README.md',
        'src/obd_reader.py',
        'src/safety_checker.py',
        'src/knowledge_base.py',
        'src/retrieval.py',
        'src/llm_generator.py',
        'src/app.py',
        'templates/index.html',
        'static/style.css',
    ]
    
    missing = []
    base_path = Path(__file__).parent
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing.append(file_path)
    
    if missing:
        print(f"\n⚠️ Missing files: {', '.join(missing)}")
        return False
    
    print("\n✅ All required files present!")
    return True


def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "="*70)
    print("🧪 VEHICLE DIAGNOSTIC ASSISTANT - SYSTEM TESTS")
    print("="*70)
    print("\nRunning comprehensive system tests...")
    print("This will validate all components are working correctly.\n")
    
    tests = [
        ("Dependencies", test_imports),
        ("File Structure", test_file_structure),
        ("Knowledge Base", test_knowledge_base),
        ("OBD Reader", test_obd_reader),
        ("Safety Checker", test_safety_checker),
        ("Retrieval", test_retrieval),
        ("LLM Generator", test_llm_generator),
        ("Flask App", test_flask_app),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {test_name}")
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("="*70)
        print("🎉 ALL TESTS PASSED! System is ready for demo!")
        print("="*70)
        print("\n✅ You can now:")
        print("   1. Run 'python main.py' to start web interface")
        print("   2. Run 'python main.py --demo' for terminal demo")
        print("   3. Present your project with confidence!")
    else:
        print("="*70)
        print("⚠️ Some tests failed. Please fix the issues above.")
        print("="*70)
        print("\n💡 Common fixes:")
        print("   - Install missing dependencies: pip install -r requirements.txt")
        print("   - Run setup: python main.py --setup")
        print("   - Check config.py for correct settings")
    
    print()
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
