"""RAG-based chatbot for querying meeting history."""
from typing import List, Dict, Optional
from backend.embeddings import EmbeddingStore
from backend.llm import get_llm_client
from backend.database import get_db_session
from backend.models import Meeting, ChatHistory
from backend.logger import logger


class MeetingChatbot:
    """Chatbot for querying meeting transcripts using RAG."""
    
    SYSTEM_PROMPT = """You are a helpful assistant that answers questions about meeting transcripts.

You have access to relevant meeting chunks that have been retrieved based on the user's query.
Use the provided context to answer questions accurately. If the context doesn't contain enough information, say so.

Be concise but comprehensive. Focus on:
- Specific details mentioned in meetings
- Decisions and commitments
- Project status and health
- People and responsibilities
- Timeline and deadlines"""

    def __init__(self):
        """Initialize chatbot."""
        self.llm = get_llm_client()
        self.embedding_store = EmbeddingStore()
    
    def query(self, question: str, meeting_id: Optional[int] = None, project_name: Optional[str] = None, top_k: int = 5) -> str:
        """
        Answer a question about meeting(s).
        
        Args:
            question: User's question
            meeting_id: Optional specific meeting ID (deprecated, use project_name instead)
            project_name: Optional project name to filter by
            top_k: Number of relevant chunks to retrieve
        
        Returns:
            Answer string
        """
        # Get meeting IDs for the project if project_name is provided
        meeting_ids = None
        if project_name:
            db = get_db_session()
            try:
                meetings = db.query(Meeting).filter(Meeting.project_name == project_name).all()
                meeting_ids = [m.id for m in meetings]
                db.close()
                if not meeting_ids:
                    return f"I couldn't find any meetings for the project '{project_name}'."
            except Exception as e:
                error_msg = f"Error querying meetings by project: {str(e)}"
                logger.error(error_msg, exc_info=True)
                db.close()
        
        # Use meeting_id if provided (backward compatibility) or meeting_ids from project
        filter_meeting_id = meeting_id if meeting_id else (meeting_ids[0] if meeting_ids and len(meeting_ids) == 1 else None)
        
        # Retrieve relevant chunks
        chunks = self.embedding_store.search(question, meeting_id=filter_meeting_id, meeting_ids=meeting_ids, top_k=top_k)
        
        if not chunks:
            return "I couldn't find any relevant information in the meeting transcripts to answer your question."
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_meeting_id = chunk["metadata"].get("meeting_id", "unknown")
            context_parts.append(f"[Meeting {chunk_meeting_id}, Chunk {i}]:\n{chunk['text']}")
        
        context = "\n\n".join(context_parts)
        
        # Build prompt
        if meeting_ids and len(meeting_ids) == 1:
            prompt = f"""Based on the following meeting transcript chunks, answer the user's question.

Context from Meeting {meeting_ids[0]}:
{context}

Question: {question}

Answer:"""
        elif meeting_ids:
            prompt = f"""Based on the following meeting transcript chunks from meetings related to project '{project_name}', answer the user's question.

Context from meetings:
{context}

Question: {question}

Answer:"""
        elif meeting_id:
            prompt = f"""Based on the following meeting transcript chunks, answer the user's question.

Context from Meeting {meeting_id}:
{context}

Question: {question}

Answer:"""
        else:
            prompt = f"""Based on the following meeting transcript chunks from various meetings, answer the user's question.

Context from meetings:
{context}

Question: {question}

Answer:"""
        
        # Generate response
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7
        )
        
        # Store in chat history (use first meeting_id from project if available)
        store_meeting_id = meeting_id if meeting_id else (meeting_ids[0] if meeting_ids else None)
        self._store_chat_history(question, response, store_meeting_id)
        
        return response
    
    def query_stream(self, question: str, meeting_id: Optional[int] = None, project_name: Optional[str] = None, top_k: int = 5):
        """
        Answer a question with streaming response.
        
        Args:
            question: User's question
            meeting_id: Optional specific meeting ID (deprecated, use project_name instead)
            project_name: Optional project name to filter by
            top_k: Number of relevant chunks to retrieve
        
        Yields:
            Response chunks
        """
        # Get meeting IDs for the project if project_name is provided
        meeting_ids = None
        if project_name:
            db = get_db_session()
            try:
                meetings = db.query(Meeting).filter(Meeting.project_name == project_name).all()
                meeting_ids = [m.id for m in meetings]
                db.close()
                if not meeting_ids:
                    yield f"I couldn't find any meetings for the project '{project_name}'."
                    return
            except Exception as e:
                error_msg = f"Error querying meetings by project: {str(e)}"
                logger.error(error_msg, exc_info=True)
                db.close()
        
        # Use meeting_id if provided (backward compatibility) or meeting_ids from project
        filter_meeting_id = meeting_id if meeting_id else (meeting_ids[0] if meeting_ids and len(meeting_ids) == 1 else None)
        
        # Retrieve relevant chunks
        chunks = self.embedding_store.search(question, meeting_id=filter_meeting_id, meeting_ids=meeting_ids, top_k=top_k)
        
        if not chunks:
            yield "I couldn't find any relevant information in the meeting transcripts to answer your question."
            return
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_meeting_id = chunk["metadata"].get("meeting_id", "unknown")
            context_parts.append(f"[Meeting {chunk_meeting_id}, Chunk {i}]:\n{chunk['text']}")
        
        context = "\n\n".join(context_parts)
        
        # Build prompt
        if meeting_ids and len(meeting_ids) == 1:
            prompt = f"""Based on the following meeting transcript chunks, answer the user's question.

Context from Meeting {meeting_ids[0]}:
{context}

Question: {question}

Answer:"""
        elif meeting_ids:
            prompt = f"""Based on the following meeting transcript chunks from meetings related to project '{project_name}', answer the user's question.

Context from meetings:
{context}

Question: {question}

Answer:"""
        elif meeting_id:
            prompt = f"""Based on the following meeting transcript chunks, answer the user's question.

Context from Meeting {meeting_id}:
{context}

Question: {question}

Answer:"""
        else:
            prompt = f"""Based on the following meeting transcript chunks from various meetings, answer the user's question.

Context from meetings:
{context}

Question: {question}

Answer:"""
        
        # Generate streaming response
        full_response = ""
        for chunk in self.llm.generate_stream(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7
        ):
            full_response += chunk
            yield chunk
        
        # Store in chat history (use first meeting_id from project if available)
        store_meeting_id = meeting_id if meeting_id else (meeting_ids[0] if meeting_ids else None)
        self._store_chat_history(question, full_response, store_meeting_id)
    
    def _store_chat_history(self, question: str, response: str, meeting_id: Optional[int]) -> None:
        """Store chat interaction in database."""
        try:
            db = get_db_session()
            chat_entry = ChatHistory(
                meeting_id=meeting_id,
                query=question,
                response=response
            )
            db.add(chat_entry)
            db.commit()
            db.close()
        except Exception as e:
            error_msg = f"Error storing chat history: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")


