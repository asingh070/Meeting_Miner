"""Vector embeddings and similarity search for RAG."""
import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from backend.config import Config
from backend.logger import logger


class EmbeddingStore:
    """Store and retrieve embeddings for meeting transcripts."""
    
    def __init__(self):
        """Initialize embedding store."""
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        # Initialize ChromaDB
        db_path = os.path.join("data", "chroma_db")
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="meeting_transcripts",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_meeting(self, meeting_id: int, transcript_text: str, chunks: Optional[List[str]] = None) -> None:
        """
        Add meeting transcript to vector store.
        
        Args:
            meeting_id: Meeting ID
            transcript_text: Full transcript text
            chunks: Optional pre-chunked text. If not provided, will chunk automatically.
        """
        if chunks is None:
            chunks = self._chunk_text(transcript_text)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        
        # Prepare documents for ChromaDB
        ids = [f"meeting_{meeting_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "meeting_id": meeting_id,
                "chunk_index": i,
                "text": chunk[:200]  # Store first 200 chars as metadata
            }
            for i, chunk in enumerate(chunks)
        ]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas
        )
    
    def search(self, query: str, meeting_id: Optional[int] = None, meeting_ids: Optional[List[int]] = None, top_k: int = 5) -> List[Dict]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query
            meeting_id: Optional meeting ID to filter results (single meeting)
            meeting_ids: Optional list of meeting IDs to filter results (multiple meetings)
            top_k: Number of results to return
        
        Returns:
            List of dictionaries with chunk text, metadata, and similarity score
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
        
        # Build where clause if filtering by meeting(s)
        # ChromaDB doesn't support $in directly, so we need to filter results after querying
        where = None
        if meeting_id is not None:
            # Filter by single meeting ID
            where = {"meeting_id": meeting_id}
        # Note: For multiple meeting_ids, we'll filter results after querying
        
        # Search
        # If filtering by multiple meeting_ids, query more results and filter afterward
        query_top_k = top_k * 3 if meeting_ids and len(meeting_ids) > 1 else top_k
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=query_top_k,
            where=where
        )
        
        # Format results and filter by meeting_ids if needed
        formatted_results = []
        if results["documents"] and len(results["documents"][0]) > 0:
            meeting_ids_set = set(meeting_ids) if meeting_ids else None
            for i in range(len(results["documents"][0])):
                metadata = results["metadatas"][0][i]
                chunk_meeting_id = metadata.get("meeting_id")
                
                # Filter by meeting_ids if provided
                if meeting_ids_set is not None:
                    if chunk_meeting_id not in meeting_ids_set:
                        continue
                
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": metadata,
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
                
                # Stop if we have enough results
                if len(formatted_results) >= top_k:
                    break
        
        return formatted_results
    
    def delete_meeting(self, meeting_id: int) -> None:
        """
        Delete all chunks for a meeting.
        
        Args:
            meeting_id: Meeting ID to delete
        """
        # ChromaDB doesn't have a direct delete by metadata, so we need to query first
        # For now, we'll use a workaround by querying and deleting by IDs
        try:
            # Get all chunks for this meeting
            results = self.collection.get(
                where={"meeting_id": meeting_id}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
        except Exception as e:
            error_msg = f"Error deleting meeting {meeting_id} from vector store: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (in characters)
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for break_char in ['. ', '.\n', '! ', '?\n', '?\n']:
                    last_break = text.rfind(break_char, start, end)
                    if last_break != -1:
                        end = last_break + 2
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks


