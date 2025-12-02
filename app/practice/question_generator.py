"""
Practice Question Generator

Generates practice questions (open-ended or multiple-choice) based on lecture content
using the RAG system and vector database.
"""

import random
from typing import List, Dict, Any, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import LLM_MODEL_NAME, GOOGLE_API_KEY
from app.embeddings.vector_store import vector_store


QUESTION_GENERATION_PROMPT = """You are an expert educator creating practice questions for students studying algorithms and computer science.

Your task: Generate EXACTLY {num_questions} {question_type} questions based on the provided lecture content.

CRITICAL RULES:
1. Questions must be based ONLY on the provided lecture content
2. ALL {num_questions} questions MUST be {question_type} type - NO MIXING OF TYPES
3. Questions should test understanding, not just memorization
4. Cover different topics from the lecture material
5. Vary difficulty levels (easy, medium, hard)
6. Make questions clear and unambiguous
{focused_topics_instruction}

For MULTIPLE CHOICE questions (if that's the type requested):
- EVERY question must have 4 options (A, B, C, D)
- Only ONE correct answer per question
- Make distractors plausible but clearly wrong
- Avoid "all of the above" or "none of the above"
- Include "options", "correct_answer", and "explanation" fields

For OPEN ENDED questions (if that's the type requested):
- Ask questions that require explanation or analysis
- Should be answerable in 2-4 sentences
- Test conceptual understanding
- Include "why" and "how" questions
- Include "sample_answer" and "key_points" fields

Lecture Content:
{context}

OUTPUT FORMAT - MULTIPLE CHOICE (JSON only, no other text):
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "Question text here?",
      "question_type": "multiple-choice",
      "difficulty": "easy|medium|hard",
      "topic": "Topic name",
      "page_reference": "Page X",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A|B|C|D",
      "explanation": "Why this is the correct answer"
    }}
  ]
}}

OUTPUT FORMAT - OPEN ENDED (JSON only, no other text):
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "Question text here?",
      "question_type": "open-ended",
      "difficulty": "easy|medium|hard",
      "topic": "Topic name",
      "page_reference": "Page X",
      "sample_answer": "A good answer would include...",
      "key_points": ["Point 1", "Point 2", "Point 3"]
    }}
  ]
}}

IMPORTANT: Generate EXACTLY {num_questions} questions, ALL of type {question_type}. Do NOT mix question types.
"""


class QuestionGenerator:
    def __init__(self):
        """Initialize the question generator."""
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL_NAME,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,  # Higher temperature for variety
            convert_system_message_to_human=True
        )
        self.parser = JsonOutputParser()
        
    def _retrieve_diverse_content(
        self, 
        pdf_ids: List[str] = None, 
        num_chunks: int = 15,
        focused_topics: List[str] = None
    ) -> List[Any]:
        """
        Retrieve diverse chunks from the vector database.
        
        Args:
            pdf_ids: Optional list of PDF IDs to filter by
            num_chunks: Number of chunks to retrieve
            focused_topics: Optional list of specific topics to focus on
            
        Returns:
            List of document chunks
        """
        # If focused topics provided, use those as queries
        if focused_topics and len(focused_topics) > 0:
            diverse_queries = focused_topics
        else:
            # Use diverse queries to get varied content
            diverse_queries = [
                "algorithm complexity analysis",
                "sorting algorithms",
                "data structures",
                "algorithm design techniques",
                "mathematical concepts",
                "pseudocode and implementation",
                "problem solving strategies"
            ]
        
        all_docs = []
        chunks_per_query = max(1, num_chunks // len(diverse_queries))
        
        for query in diverse_queries:
            search_kwargs = {"k": chunks_per_query}
            if pdf_ids:
                search_kwargs["filter"] = {"pdf_id": {"$in": pdf_ids}}
            
            retriever = vector_store.vector_db.as_retriever(search_kwargs=search_kwargs)
            docs = retriever.invoke(query)
            all_docs.extend(docs)
        
        # Remove duplicates and shuffle
        unique_docs = list({doc.page_content: doc for doc in all_docs}.values())
        random.shuffle(unique_docs)
        
        return unique_docs[:num_chunks]
    
    def _format_context(self, docs: List[Any]) -> str:
        """Format retrieved documents into context string."""
        formatted = []
        for doc in docs:
            page_nums = doc.metadata.get("page_numbers", "Unknown")
            content = doc.page_content
            formatted.append(f"[Page {page_nums}]\n{content}")
        return "\n\n---\n\n".join(formatted)
    
    def generate_questions(
        self,
        question_type: Literal["multiple-choice", "open-ended"],
        num_questions: int = 10,
        pdf_ids: List[str] = None,
        shuffle: bool = True,
        focused_topics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate practice questions.
        
        Args:
            question_type: Type of questions to generate
            num_questions: Number of questions to generate (default: 10)
            pdf_ids: Optional list of PDF IDs to filter by
            shuffle: Whether to shuffle and create new questions
            focused_topics: Optional list of specific topics to focus on
            
        Returns:
            Dictionary containing generated questions
        """
        try:
            # Retrieve diverse content (focused if topics provided)
            docs = self._retrieve_diverse_content(
                pdf_ids, 
                num_chunks=15,
                focused_topics=focused_topics
            )
            
            if not docs:
                return {
                    "success": False,
                    "error": "No content found in vector database",
                    "questions": []
                }
            
            context = self._format_context(docs)
            
            # Add focused topics instruction if provided
            if focused_topics and len(focused_topics) > 0:
                topics_str = ", ".join(focused_topics)
                focused_instruction = f"\n7. Focus questions on these specific topics: {topics_str}"
            else:
                focused_instruction = ""
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", QUESTION_GENERATION_PROMPT),
                ("human", "Generate the questions now. Remember: ALL questions must be {question_type} type.")
            ])
            
            chain = prompt | self.llm | self.parser
            
            # Generate questions
            result = chain.invoke({
                "num_questions": num_questions,
                "question_type": question_type,
                "context": context,
                "focused_topics_instruction": focused_instruction
            })
            
            # Validate and filter to ensure correct type
            if "questions" in result:
                questions = result["questions"]
                
                # Filter out any questions that don't match the requested type
                filtered_questions = [
                    q for q in questions 
                    if q.get("question_type") == question_type
                ]
                
                # If we lost questions due to filtering, log it
                if len(filtered_questions) < len(questions):
                    print(f"Warning: Filtered out {len(questions) - len(filtered_questions)} questions with wrong type")
                
                return {
                    "success": True,
                    "question_type": question_type,
                    "num_questions": len(filtered_questions),
                    "questions": filtered_questions,
                    "focused_topics": focused_topics if focused_topics else []
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid response format",
                    "questions": []
                }
                
        except Exception as e:
            print(f"Error generating questions: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "questions": []
            }
    
    def shuffle_questions(
        self,
        existing_questions: List[Dict[str, Any]],
        num_to_select: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Shuffle existing questions and select a subset.
        
        Args:
            existing_questions: List of questions to shuffle
            num_to_select: Number of questions to select
            
        Returns:
            Shuffled and selected questions
        """
        shuffled = existing_questions.copy()
        random.shuffle(shuffled)
        return shuffled[:num_to_select]


# Global instance
question_generator = QuestionGenerator()

