"""
Knowledge Base Builder Module
Creates embeddings from vehicle diagnostic documents
Stores them in FAISS index for efficient retrieval
"""

import os
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import config


class KnowledgeBase:
    """
    Manages document embeddings and FAISS vector database
    """
    
    def __init__(self, model_name: str = config.EMBEDDING_MODEL):
        """
        Initialize knowledge base with embedding model
        
        Args:
            model_name: Name of sentence-transformer model to use
        """
        print(f"📚 Initializing Knowledge Base...")
        print(f"🤖 Loading embedding model: {model_name}")
        
        # Load pre-trained sentence transformer model
        # This model converts text into vector embeddings
        self.model = SentenceTransformer(model_name)
        self.dimension = config.EMBEDDING_DIMENSION
        
        # FAISS index for fast similarity search
        self.index = None
        
        # Store original documents
        self.documents = []
        
        print("✅ Knowledge Base initialized")
    
    def build_from_directory(self, data_dir: Path) -> int:
        """
        Read all text files from directory and create FAISS index
        
        Args:
            data_dir: Path to directory containing text files
            
        Returns:
            Number of documents processed
        """
        print(f"\n📂 Reading documents from: {data_dir}")
        
        # Collect all text files
        text_files = list(data_dir.glob("*.txt"))
        
        if not text_files:
            print("⚠️ No .txt files found in directory")
            return 0
        
        print(f"📄 Found {len(text_files)} text files")
        
        # Read and chunk documents
        all_chunks = []
        
        for file_path in text_files:
            print(f"  📖 Processing: {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8', errors="ignore") as f:
                content = f.read()
            
            # Split document into chunks for better retrieval
            chunks = self._chunk_document(content, file_path.name)
            all_chunks.extend(chunks)
        
        print(f"✂️  Created {len(all_chunks)} text chunks")
        
        # Generate embeddings
        print("🔢 Generating embeddings...")
        embeddings = self._generate_embeddings(all_chunks)
        
        # Build FAISS index
        print("🗄️  Building FAISS index...")
        self._build_index(embeddings)
        
        # Store documents
        self.documents = all_chunks
        
        print(f"✅ Knowledge base built with {len(all_chunks)} chunks")
        
        return len(all_chunks)
    
    def _chunk_document(self, text: str, source: str, chunk_size: int = 500) -> List[Dict]:
        """
        Split document into smaller chunks for better retrieval
        
        Args:
            text: Full document text
            source: Source filename
            chunk_size: Approximate characters per chunk
            
        Returns:
            List of chunk dictionaries
        """
        # Split by paragraphs (double newline)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds chunk_size, save current chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'source': source,
                    'chunk_id': len(chunks)
                })
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'source': source,
                'chunk_id': len(chunks)
            })
        
        return chunks
    
    def _generate_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """
        Convert text chunks to vector embeddings
        
        Args:
            chunks: List of document chunks
            
        Returns:
            NumPy array of embeddings
        """
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings in batches for efficiency
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def _build_index(self, embeddings: np.ndarray):
        """
        Build FAISS index from embeddings
        
        Args:
            embeddings: NumPy array of vector embeddings
        """
        # Ensure embeddings are float32 (required by FAISS)
        embeddings = embeddings.astype('float32')
        
        # Create FAISS index
        # Using IndexFlatL2 for exact nearest neighbor search
        # Good for small to medium datasets (< 1M vectors)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        print(f"✅ FAISS index built with {self.index.ntotal} vectors")
    
    def search(self, query: str, top_k: int = config.TOP_K_DOCUMENTS) -> List[Dict]:
        """
        Search for most relevant documents given a query
        
        Args:
            query: User's search query
            top_k: Number of results to return
            
        Returns:
            List of most relevant document chunks with scores
        """
        if self.index is None:
            raise ValueError("Knowledge base not built. Call build_from_directory() first.")
        
        # Convert query to embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype('float32')
        
        # Search FAISS index
        # Returns: distances (L2 distance), indices (document IDs)
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):  # Valid index
                doc = self.documents[idx].copy()
                doc['relevance_score'] = float(1 / (1 + dist))  # Convert distance to similarity
                doc['rank'] = i + 1
                results.append(doc)
        
        return results
    
    def save(self, index_path: Path, docs_path: Path):
        """
        Save FAISS index and documents to disk
        
        Args:
            index_path: Path to save FAISS index
            docs_path: Path to save documents JSON
        """
        if self.index is None:
            raise ValueError("No index to save")
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save documents
        with open(docs_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2)
        
        print(f"💾 Saved index to: {index_path}")
        print(f"💾 Saved documents to: {docs_path}")
    
    def load(self, index_path: Path, docs_path: Path):
        """
        Load FAISS index and documents from disk
        
        Args:
            index_path: Path to FAISS index file
            docs_path: Path to documents JSON file
        """
        # Load FAISS index
        self.index = faiss.read_index(str(index_path))
        
        # Load documents
        with open(docs_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        
        print(f"📖 Loaded {self.index.ntotal} vectors from index")
        print(f"📄 Loaded {len(self.documents)} documents")


def create_sample_documents(output_dir: Path):
    """
    Create sample vehicle diagnostic documents for testing
    
    Args:
        output_dir: Directory to save sample documents
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample Document 1: Engine Overheating
    doc1 = """Engine Overheating - Causes and Solutions

Engine overheating is a serious condition that requires immediate attention. The cooling system is designed to maintain optimal engine temperature between 85-95°C under normal operating conditions.

Common Causes of Overheating:
1. Low coolant level - Check coolant reservoir and refill if needed
2. Faulty thermostat - May stick closed preventing coolant circulation
3. Damaged water pump - Reduces coolant flow through engine
4. Blocked radiator - Debris or corrosion restricts airflow
5. Broken cooling fan - Fan should activate when temperature rises

Warning Signs:
- Temperature gauge reading above normal range
- Steam coming from under hood
- Sweet smell (coolant leak)
- Loss of engine power

Immediate Actions:
If temperature exceeds 120°C, pull over immediately and turn off engine. Continuing to drive can cause catastrophic engine damage including warped cylinder head or blown head gasket. Allow engine to cool for at least 30 minutes before checking coolant level.

Prevention:
Regular maintenance including coolant flushes every 30,000 km and inspection of hoses and clamps can prevent most overheating issues."""
    
    # Sample Document 2: DTC Code P0301
    doc2 = """Diagnostic Trouble Code P0301 - Cylinder 1 Misfire Detected

DTC P0301 indicates that the engine control module (ECM) has detected a misfire in cylinder number 1. A misfire occurs when combustion in the cylinder is incomplete or absent.

Symptoms:
- Rough idle and engine vibration
- Loss of power and acceleration
- Increased fuel consumption
- Check engine light illuminated
- Possible engine damage if left unaddressed

Common Causes:
1. Faulty spark plug or ignition coil
2. Fuel injector malfunction
3. Low compression in cylinder
4. Vacuum leaks affecting air-fuel mixture
5. Damaged spark plug wire

Diagnostic Steps:
1. Scan for additional codes
2. Inspect spark plugs for wear or fouling
3. Check ignition coil resistance
4. Test fuel injector operation
5. Perform compression test

Severity: CRITICAL - Service required within 1-2 days to prevent catalytic converter damage. Do not ignore this code as continued driving with misfire can cause expensive repairs.

Repair Typically Involves:
Replacing spark plugs, ignition coils, or fuel injectors. Average repair cost ranges from $100-500 depending on component."""
    
    # Sample Document 3: High RPM Operation
    doc3 = """High RPM Operation and Engine Protection

Modern engines have a redline typically between 6000-7000 RPM. The redline represents the maximum safe engine speed before mechanical damage can occur.

Risks of Excessive RPM:
- Increased wear on pistons and bearings
- Valve float causing loss of control
- Connecting rod failure at extreme speeds
- Excessive oil consumption
- Reduced engine lifespan

Safe Operating Guidelines:
Most efficient operation occurs between 2000-4000 RPM for highway cruising. Sport driving should keep RPM below 5500 RPM unless on a track.

RPM Warning Zones:
- 0-2000 RPM: Economy range, best fuel efficiency
- 2000-4000 RPM: Normal driving range
- 4000-5500 RPM: Spirited driving, occasional use acceptable
- 5500-6500 RPM: High stress zone, avoid sustained operation
- Above 6500 RPM: Danger zone, immediate damage risk

Engine Protection Systems:
Most modern vehicles have rev limiters that cut fuel or spark when approaching redline. However, these are emergency systems and should not be relied upon regularly.

If you accidentally over-rev the engine, monitor for unusual noises, vibrations, or oil consumption in following days."""
    
    # Sample Document 4: DTC Code P0420
    doc4 = """DTC P0420 - Catalyst System Efficiency Below Threshold

Code P0420 indicates the catalytic converter is not operating at optimal efficiency. The catalyst converts harmful emissions (CO, HC, NOx) into less harmful substances (CO2, H2O, N2).

What This Code Means:
The oxygen sensors before and after the catalytic converter should show different readings. When readings are too similar, it suggests the catalyst is not effectively cleaning emissions.

Possible Causes:
1. Worn out catalytic converter (most common in high-mileage vehicles)
2. Faulty oxygen sensors giving incorrect readings
3. Engine running too rich or too lean
4. Exhaust leaks before catalytic converter
5. Use of wrong engine oil or fuel additives

Immediate Concerns:
This code typically does NOT require immediate action. You can continue driving, but the vehicle will not pass emissions testing.

Severity: WARNING - Schedule service within 1-2 weeks

Diagnosis Steps:
1. Check oxygen sensor readings with scan tool
2. Inspect for exhaust leaks
3. Review fuel trim data
4. Consider catalyst replacement if vehicle has high mileage (>100,000 km)

Cost Considerations:
Catalytic converter replacement can be expensive ($500-2000) so proper diagnosis is essential to avoid unnecessary repairs."""
    
    # Save documents
    with open(output_dir / "engine_overheating.txt", 'w') as f:
        f.write(doc1)
    
    with open(output_dir / "dtc_p0301_misfire.txt", 'w') as f:
        f.write(doc2)
    
    with open(output_dir / "high_rpm_operation.txt", 'w') as f:
        f.write(doc3)
    
    with open(output_dir / "dtc_p0420_catalyst.txt", 'w') as f:
        f.write(doc4)
    
    print(f"✅ Created 4 sample documents in {output_dir}")


def main():
    """
    Demonstration of knowledge base creation
    """
    print("📚 Knowledge Base Builder - Demo\n")
    
    # Create sample documents if they don't exist
    if not list(config.RAW_DATA_DIR.glob("*.txt")):
        print("📝 Creating sample documents...")
        create_sample_documents(config.RAW_DATA_DIR)
        print()
    
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Build index from documents
    num_docs = kb.build_from_directory(config.RAW_DATA_DIR)
    
    if num_docs == 0:
        print("❌ No documents to process")
        return
    
    # Save the index
    kb.save(config.FAISS_INDEX_PATH, config.DOCUMENTS_PATH)
    
    # Test search functionality
    print("\n🔍 Testing Search Functionality\n")
    
    test_queries = [
        "Why is my engine overheating?",
        "What does code P0301 mean?",
        "Is high RPM dangerous?",
        "Catalyst efficiency low"
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = kb.search(query, top_k=2)
        
        print(f"Top {len(results)} Results:")
        for result in results:
            print(f"  📄 {result['source']} (Score: {result['relevance_score']:.3f})")
            print(f"     {result['text'][:100]}...")
        print()
    
    print("✅ Knowledge base demo completed!")


if __name__ == "__main__":
    main()
