"""
Flask Web Application
Provides chat interface for vehicle diagnostics
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

import config
from src.obd_reader import OBDReader
from src.safety_checker import SafetyChecker
from src.retrieval import ContextRetriever
from src.llm_generator import DiagnosticExplainer, create_explainer


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize components
print("🚀 Initializing Vehicle Diagnostic System...")

obd_reader = OBDReader(use_mock=config.USE_MOCK_DATA)
safety_checker = SafetyChecker()
retriever = ContextRetriever()

# Initialize LLM explainer if an API key is configured (None = retrieval only)
explainer = create_explainer()

print("✅ System initialized!")


@app.route('/')
def index():
    """
    Render main chat interface
    """
    return render_template('index.html')


@app.route('/api/vehicle-status', methods=['GET'])
def get_vehicle_status():
    """
    Get current vehicle sensor data
    """
    try:
        # Read vehicle data
        vehicle_data = obd_reader.read_vehicle_data()
        dtc_codes = obd_reader.read_dtc_codes()
        
        # Run safety checks
        safety_report = safety_checker.check_all(vehicle_data, dtc_codes)
        
        return jsonify({
            'success': True,
            'vehicle_data': vehicle_data,
            'dtc_codes': [{'code': code, 'description': desc} for code, desc in dtc_codes],
            'safety_report': safety_report
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """
    Process diagnostic query and return explanation
    """
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400
        
        # Step 1: Read vehicle data
        vehicle_data = obd_reader.read_vehicle_data()
        dtc_codes = obd_reader.read_dtc_codes()
        
        # Step 2: Safety checks
        safety_report = safety_checker.check_all(vehicle_data, dtc_codes)
        
        # Step 3: Retrieve context
        retrieval_result = retriever.retrieve_context(query, vehicle_data, dtc_codes)
        
        # Step 4: Generate LLM explanation
        if explainer:
            llm_result = explainer.generate_explanation(
                query, 
                retrieval_result['context'],
                safety_report
            )
        else:
            # Mock response when LLM not available
            llm_result = {
                'explanation': f"Based on the retrieved information and your query '{query}', please refer to the safety alerts and inspect the mentioned components. For detailed diagnosis, consult a professional mechanic.",
                'severity': safety_report['severity'],
                'confidence': 'LOW',
                'checklist': [
                    'Check dashboard warning lights',
                    'Verify all fluid levels',
                    'Inspect for unusual sounds or smells',
                    'Consult service manual for specific codes'
                ],
                'estimated_urgency': 'Schedule inspection based on severity'
            }
        
        return jsonify({
            'success': True,
            'query': query,
            'vehicle_data': vehicle_data,
            'dtc_codes': [{'code': code, 'description': desc} for code, desc in dtc_codes],
            'safety_report': safety_report,
            'retrieved_sources': [
                {
                    'source': doc['source'],
                    'relevance': doc['relevance_score']
                } 
                for doc in retrieval_result['retrieved_documents']
            ],
            'explanation': llm_result
        })
    
    except Exception as e:
        print(f"Error in diagnose endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Check system health
    """
    return jsonify({
        'status': 'healthy',
        'obd_mode': 'mock' if config.USE_MOCK_DATA else 'real',
        'llm_available': explainer is not None,
        'knowledge_base_loaded': retriever.kb.index is not None
    })


def main():
    """
    Run Flask application
    """
    print("\n" + "="*60)
    print("🚗 Vehicle Diagnostic Assistant - Web Interface")
    print("="*60)
    print(f"\n🌐 Starting server on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"📍 Mode: {'DEMO (Mock Data)' if config.USE_MOCK_DATA else 'REAL VEHICLE'}")
    print(f"🤖 LLM: {'Enabled' if explainer else 'Disabled (using mock responses)'}")
    print("\n💡 Open your browser and navigate to the URL above")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )


if __name__ == '__main__':
    main()
