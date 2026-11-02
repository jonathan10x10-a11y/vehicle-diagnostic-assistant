"""
Retrieval Module
Combines user query with vehicle data and retrieves relevant context
from knowledge base for LLM generation
"""

from typing import Dict, List
from pathlib import Path
import config
from src.knowledge_base import KnowledgeBase


class ContextRetriever:
    """
    Retrieves and formats context for LLM from knowledge base
    Combines retrieved documents with live vehicle data
    """
    
    def __init__(self):
        """
        Initialize retriever with knowledge base
        """
        self.kb = KnowledgeBase()
        
        # Try to load existing index
        if config.FAISS_INDEX_PATH.exists() and config.DOCUMENTS_PATH.exists():
            print("📖 Loading existing knowledge base...")
            self.kb.load(config.FAISS_INDEX_PATH, config.DOCUMENTS_PATH)
        else:
            print("⚠️ Knowledge base not found. Run knowledge_base.py first.")
    
    def retrieve_context(
        self, 
        query: str, 
        vehicle_data: Dict, 
        dtc_codes: List[tuple],
        top_k: int = config.TOP_K_DOCUMENTS
    ) -> Dict:
        """
        Retrieve relevant context for user query
        
        Args:
            query: User's diagnostic question
            vehicle_data: Current vehicle sensor readings
            dtc_codes: List of diagnostic trouble codes
            top_k: Number of documents to retrieve
            
        Returns:
            Dictionary with formatted context and metadata
        """
        # Enhance query with vehicle data for better retrieval
        enhanced_query = self._enhance_query(query, vehicle_data, dtc_codes)
        
        # Retrieve relevant documents
        retrieved_docs = self.kb.search(enhanced_query, top_k=top_k)
        
        # Build context string
        context = self._build_context_string(retrieved_docs, vehicle_data, dtc_codes)
        
        return {
            'context': context,
            'retrieved_documents': retrieved_docs,
            'enhanced_query': enhanced_query,
            'num_sources': len(retrieved_docs)
        }
    
    def _enhance_query(
        self, 
        query: str, 
        vehicle_data: Dict, 
        dtc_codes: List[tuple]
    ) -> str:
        """
        Enhance user query with vehicle data keywords
        This improves retrieval accuracy by including relevant context
        
        Args:
            query: Original user query
            vehicle_data: Vehicle sensor data
            dtc_codes: Diagnostic codes
            
        Returns:
            Enhanced query string
        """
        enhancements = []
        
        # Add DTC codes to query
        if dtc_codes:
            codes = [code for code, _ in dtc_codes]
            enhancements.append(' '.join(codes))
        
        # Add temperature-related keywords if relevant
        temp = vehicle_data.get('coolant_temp')
        if temp and temp > config.COOLANT_TEMP_WARNING:
            enhancements.append('overheating high temperature')
        
        # Add RPM-related keywords if relevant
        rpm = vehicle_data.get('rpm')
        if rpm and rpm > 5000:
            enhancements.append('high RPM engine speed')
        
        # Combine original query with enhancements
        if enhancements:
            enhanced = f"{query} {' '.join(enhancements)}"
        else:
            enhanced = query
        
        return enhanced
    
    def _build_context_string(
        self,
        retrieved_docs: List[Dict],
        vehicle_data: Dict,
        dtc_codes: List[tuple]
    ) -> str:
        """
        Build formatted context string for LLM
        Combines retrieved knowledge with live vehicle data
        
        Args:
            retrieved_docs: Documents retrieved from knowledge base
            vehicle_data: Current vehicle sensor readings
            dtc_codes: Diagnostic trouble codes
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Part 1: Current Vehicle Status
        context_parts.append("=== CURRENT VEHICLE STATUS ===")
        context_parts.append(f"RPM: {vehicle_data.get('rpm', 'N/A')} rpm")
        context_parts.append(f"Speed: {vehicle_data.get('speed', 'N/A')} km/h")
        context_parts.append(f"Coolant Temperature: {vehicle_data.get('coolant_temp', 'N/A')} °C")
        context_parts.append(f"Engine Load: {vehicle_data.get('engine_load', 'N/A')} %")
        context_parts.append(f"Throttle Position: {vehicle_data.get('throttle_position', 'N/A')} %")
        context_parts.append("")
        
        # Part 2: Diagnostic Trouble Codes
        if dtc_codes:
            context_parts.append("=== DIAGNOSTIC TROUBLE CODES ===")
            for code, description in dtc_codes:
                context_parts.append(f"{code}: {description}")
            context_parts.append("")
        else:
            context_parts.append("=== DIAGNOSTIC TROUBLE CODES ===")
            context_parts.append("No trouble codes detected")
            context_parts.append("")
        
        # Part 3: Retrieved Knowledge Base Documents
        context_parts.append("=== RELEVANT TECHNICAL INFORMATION ===")
        
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"\n[Source {i}: {doc['source']}]")
            context_parts.append(doc['text'])
        
        # Combine all parts
        full_context = "\n".join(context_parts)
        
        # Truncate if too long
        if len(full_context) > config.MAX_CONTEXT_LENGTH:
            full_context = full_context[:config.MAX_CONTEXT_LENGTH] + "\n\n[Context truncated...]"
        
        return full_context
    
    def format_for_display(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents for user display
        
        Args:
            retrieved_docs: List of retrieved document chunks
            
        Returns:
            Formatted string for display
        """
        if not retrieved_docs:
            return "No relevant documents found."
        
        output = []
        output.append("📚 Sources Referenced:")
        
        for i, doc in enumerate(retrieved_docs, 1):
            output.append(f"\n{i}. {doc['source']}")
            output.append(f"   Relevance: {doc['relevance_score']:.2%}")
            output.append(f"   {doc['text'][:150]}...")
        
        return "\n".join(output)


def main():
    """
    Demonstration of retrieval functionality
    """
    print("🔍 Context Retriever - Demo\n")
    
    # Initialize retriever
    retriever = ContextRetriever()
    
    # Test Case 1: Overheating query
    print("📋 Test Case 1: Overheating Query")
    print("="*60)
    
    query1 = "Why is my temperature gauge reading high?"
    vehicle_data1 = {
        'rpm': 3000,
        'speed': 80,
        'coolant_temp': 115,
        'engine_load': 60,
        'throttle_position': 45
    }
    dtc_codes1 = []
    
    result1 = retriever.retrieve_context(query1, vehicle_data1, dtc_codes1)
    
    print(f"Original Query: {query1}")
    print(f"Enhanced Query: {result1['enhanced_query']}")
    print(f"Sources Retrieved: {result1['num_sources']}")
    print("\nFormatted Context:")
    print(result1['context'][:500] + "...\n")
    
    # Test Case 2: DTC Code query
    print("📋 Test Case 2: DTC Code Query")
    print("="*60)
    
    query2 = "What does error code P0301 mean?"
    vehicle_data2 = {
        'rpm': 800,
        'speed': 0,
        'coolant_temp': 88,
        'engine_load': 15,
        'throttle_position': 5
    }
    dtc_codes2 = [('P0301', 'Cylinder 1 Misfire Detected')]
    
    result2 = retriever.retrieve_context(query2, vehicle_data2, dtc_codes2)
    
    print(f"Original Query: {query2}")
    print(f"Enhanced Query: {result2['enhanced_query']}")
    print(f"Sources Retrieved: {result2['num_sources']}")
    print("\nRetrieved Documents:")
    print(retriever.format_for_display(result2['retrieved_documents']))
    print()
    
    # Test Case 3: General query
    print("📋 Test Case 3: General Maintenance Query")
    print("="*60)
    
    query3 = "Is it safe to drive with high RPM?"
    vehicle_data3 = {
        'rpm': 6200,
        'speed': 120,
        'coolant_temp': 95,
        'engine_load': 85,
        'throttle_position': 75
    }
    dtc_codes3 = []
    
    result3 = retriever.retrieve_context(query3, vehicle_data3, dtc_codes3)
    
    print(f"Original Query: {query3}")
    print(f"Enhanced Query: {result3['enhanced_query']}")
    print(f"Sources Retrieved: {result3['num_sources']}")
    print("\nContext Preview:")
    print(result3['context'][:400] + "...\n")
    
    print("✅ Retrieval demo completed!")


if __name__ == "__main__":
    main()
