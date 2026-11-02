"""
Main Integration Script
Orchestrates all modules for end-to-end vehicle diagnostics
"""

import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent))

import config
from src.obd_reader import OBDReader
from src.safety_checker import SafetyChecker
from src.retrieval import ContextRetriever
from src.llm_generator import DiagnosticExplainer, create_explainer


def setup_knowledge_base():
    """
    Set up knowledge base if not already created
    """
    from src.knowledge_base import KnowledgeBase, create_sample_documents
    
    print("📚 Setting up knowledge base...\n")
    
    # Create sample documents if needed
    if not list(config.RAW_DATA_DIR.glob("*.txt")):
        print("📝 No documents found. Creating sample documents...")
        create_sample_documents(config.RAW_DATA_DIR)
        print()
    
    # Check if index exists
    if not config.FAISS_INDEX_PATH.exists():
        print("🔨 Building FAISS index...")
        kb = KnowledgeBase()
        num_docs = kb.build_from_directory(config.RAW_DATA_DIR)
        
        if num_docs > 0:
            kb.save(config.FAISS_INDEX_PATH, config.DOCUMENTS_PATH)
            print("✅ Knowledge base created successfully!\n")
        else:
            print("❌ Failed to create knowledge base\n")
            return False
    else:
        print("✅ Knowledge base already exists\n")
    
    return True


def run_diagnostic_demo():
    """
    Run a complete diagnostic demo workflow
    """
    print("="*70)
    print("🚗 VEHICLE DIAGNOSTIC ASSISTANT - DEMO MODE")
    print("="*70)
    print()
    
    # Step 1: Initialize components
    print("📦 Initializing components...")
    print()
    
    obd_reader = OBDReader(use_mock=True)
    safety_checker = SafetyChecker()
    retriever = ContextRetriever()
    
    # Check if LLM is available
    explainer = create_explainer()
    llm_available = explainer is not None
    if not llm_available:
        print("⚠️ LLM API key not configured. Demo will show retrieval only.\n")

    # Step 2: Read vehicle data
    print("📡 Reading vehicle data...")
    vehicle_data = obd_reader.read_vehicle_data()
    dtc_codes = obd_reader.read_dtc_codes()
    
    obd_reader.print_data_formatted(vehicle_data, dtc_codes)
    
    # Step 3: Safety checks
    print("🛡️ Running safety checks...")
    safety_report = safety_checker.check_all(vehicle_data, dtc_codes)
    safety_checker.print_safety_report(safety_report)
    
    # Step 4: Interactive query loop
    print("💬 Interactive Diagnostic Mode")
    print("="*70)
    print("Ask questions about your vehicle (or 'quit' to exit)")
    print("Example queries:")
    print("  - Why is my temperature high?")
    print("  - What does error code P0301 mean?")
    print("  - Is it safe to continue driving?")
    print("="*70)
    print()
    
    while True:
        try:
            # Get user query
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            print("\n🔍 Processing query...")
            
            # Step 5: Retrieve context
            retrieval_result = retriever.retrieve_context(query, vehicle_data, dtc_codes)
            
            print(f"📚 Retrieved {retrieval_result['num_sources']} relevant documents")
            
            # Display retrieved sources
            print("\n" + "="*70)
            print("RETRIEVED SOURCES:")
            print("="*70)
            for i, doc in enumerate(retrieval_result['retrieved_documents'], 1):
                print(f"\n{i}. {doc['source']} (Relevance: {doc['relevance_score']:.2%})")
                print(f"   {doc['text'][:200]}...")
            
            # Step 6: Generate LLM explanation
            if llm_available:
                print("\n🤖 Generating AI explanation...")
                llm_result = explainer.generate_explanation(
                    query,
                    retrieval_result['context'],
                    safety_report
                )
                
                print("\n" + "="*70)
                print("AI DIAGNOSTIC EXPLANATION:")
                print("="*70)
                print(explainer.format_for_display(llm_result))
            else:
                print("\n💡 Tip: Configure LLM API key to get AI-generated explanations")
            
            print("\n" + "="*70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def run_web_interface():
    """
    Launch Flask web interface
    """
    from src.app import main as run_flask
    run_flask()


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(
        description='AI-Powered Vehicle Diagnostic Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --setup          # Set up knowledge base
  python main.py --demo           # Run interactive demo
  python main.py --web            # Launch web interface
  python main.py                  # Default: launch web interface
        """
    )
    
    parser.add_argument('--setup', action='store_true',
                       help='Set up knowledge base')
    parser.add_argument('--demo', action='store_true',
                       help='Run interactive demo mode')
    parser.add_argument('--web', action='store_true',
                       help='Launch web interface')
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "="*70)
    print("   🚗 AI-POWERED VEHICLE DIAGNOSTIC ASSISTANT")
    print("   Using OBD-II Data with RAG (Retrieval-Augmented Generation)")
    print("="*70)
    print()
    
    # Setup mode
    if args.setup:
        setup_knowledge_base()
        return
    
    # Ensure knowledge base exists
    if not config.FAISS_INDEX_PATH.exists():
        print("⚠️ Knowledge base not found. Running setup...\n")
        if not setup_knowledge_base():
            print("❌ Setup failed. Please check the error messages above.")
            return
    
    # Demo mode
    if args.demo:
        run_diagnostic_demo()
        return
    
    # Default: Web interface
    run_web_interface()


if __name__ == "__main__":
    main()
