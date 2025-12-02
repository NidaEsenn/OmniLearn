from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import LLM_MODEL_NAME, GOOGLE_API_KEY
from app.embeddings.vector_store import vector_store
import json

PLANNER_SYSTEM_PROMPT = """You are an expert university-level study coach specializing in algorithms and theoretical computer science.

Your task is to design a realistic, time-bounded study plan for a student, based on:

* The structure of a lecture PDF (chapters, sections, page ranges, difficulty, priority, estimated time).
* The student's available days and daily study time.
* The student's level (beginner, intermediate, advanced) and goal (e.g., pass, get A, build intuition).

---

### Student Profile

* Level: **{level}**
* Goal: **{goal}**  (e.g., "pass the exam", "get an A", "build intuition")
* Total days available: **{total_days}**
* Daily study time (minutes): **{daily_minutes}**
* Topics they feel weak in: **{weak_topics}** (IMPORTANT: These topics MUST be prioritized and appear early in the plan with extra time allocated)
* Deadline context: **{deadline_context}**  (e.g., "final exam in algorithms on Dec 20")

---

### Lecture Sections (parsed from the PDF)

You are given a JSON array of sections. Each section has:

* `id`: unique integer ID
* `chapter`: chapter or major topic name
* `title`: section or subtopic title
* `pages`: `[start_page, end_page]` (inclusive)
* `difficulty`: integer in {{1, 2, 3}}, where 1 = easiest, 3 = hardest
* `priority`: `"core"`, `"important"`, or `"optional"`
* `estimated_minutes`: estimated minutes needed for this section at intermediate level

Sections JSON:

```json
{sections_json}
```

---

### What You Must Do

Using the student profile and the sections data:

1. **Respect time constraints**

   * The plan must be feasible within the total available time: `total_days × daily_minutes`.
   * If time is not enough for everything:

     * Prioritize `"core"` and `"important"` sections.
     * Compress or omit `"optional"` sections.
     * Clearly mention these compromises in `summary.notes` and `warnings`.
2. **Adapt to the student's level**

   * **Beginner:** slower pace, more explanation and review, fewer topics per day.
   * **Intermediate:** balanced pace, both new content and review.
   * **Advanced:** denser coverage, more challenging tasks, fewer repeated reviews.
3. **Highlight weak topics (CRITICAL REQUIREMENT)**

   * If `{weak_topics}` is not empty, you MUST ensure ALL mentioned weak topics:

     * Appear in the first half of the study plan (earlier days).
     * Receive 20-30% MORE time than normal sections.
     * Get at least TWO review blocks throughout the plan.
     * Are explicitly called out in the day's focus when they appear.
   * If a weak topic is mentioned but not found in the sections, note this in warnings.
   * Parse weak topics carefully - they may be comma-separated or use "and" (e.g., "bubble sort, merge sort" or "bubble sort and merge sort").
4. **Include spaced review**

   * Add short review blocks on later days that revisit earlier sections.
   * Ensure that at least one of the last two days is primarily review-focused (e.g., global review or mock-exam style).
5. **Make tasks concrete**

   * For each day, break the plan into specific tasks, not just topic names, for example:

     * "Read slides 10–18 of Chapter 2 and write a 3-bullet summary."
     * "Solve 3 practice questions on recurrences."
     * "Explain Dijkstra's algorithm in your own words in 5–6 sentences."
   * Use clear, simple language suitable for a real student.
6. **Do not invent new sections**

   * Only use chapters/sections that actually exist in the provided `sections_json`.

---

### Output Format (Important)

You **must** output a single valid JSON object and nothing else.
Use this exact structure:

```json
{{
  "summary": {{
    "total_days": 0,
    "total_estimated_minutes": 0,
    "topics_covered": [],
    "review_days": 0,
    "plan_style": "",
    "notes": ""
  }},
  "days": [
    {{
      "day": 1,
      "focus": "",
      "estimated_total_minutes": 0,
      "study_blocks": [
        {{
          "type": "study",
          "chapter": "",
          "section_title": "",
          "section_ids": [],
          "estimated_minutes": 0,
          "tasks": [
            "task 1",
            "task 2"
          ]
        }}
      ],
      "review_blocks": [
        {{
          "type": "review",
          "source_days": [],
          "topics": [],
          "estimated_minutes": 0,
          "tasks": [
            "review task 1",
            "review task 2"
          ]
        }}
      ]
    }}
  ],
  "warnings": []
}}
```

**Field semantics:**

* `summary.total_days`: total number of days actually used in the plan.
* `summary.total_estimated_minutes`: approximate total minutes for the whole plan.
* `summary.topics_covered`: list of main topics/chapters that appear in the plan.
* `summary.review_days`: number of days that contain significant review_blocks.
* `summary.plan_style`: short phrase like `"Beginner-friendly with high review density"` or `"Intensive exam-focused plan"`.
* `summary.notes`: important notes such as dropped optional sections or compressed content.
* `days[*].focus`: one-sentence description of the main focus for that day.
* `days[*].estimated_total_minutes`: sum of study + review minutes for that day (keep within daily_minutes ± ~15%).
* `days[*].study_blocks[*].section_ids`: list of `id` values from the given `sections_json` that this block covers.
* `warnings`: array of human-readable warning strings, e.g.

  * `"Available time is low; some optional sections were omitted."`
  * `"Plan is dense even after compression; consider adding more days."`

---

### Constraints and Quality Checks

* Ensure the total per-day time is realistic and adheres to `{daily_minutes}` as much as possible.
* **CRITICAL**: Ensure ALL weak_topics (if any) appear in the plan with SIGNIFICANT extra attention:
  * Each weak topic should appear in at least one study block
  * Each weak topic should have at least one dedicated review block
  * Weak topics should be in the first 60% of days
* Ensure at least one of the final two days is predominantly review.
* If constraints are too tight, you **must** state this clearly in both `summary.notes` and `warnings`.
* If a weak topic cannot be found in the available sections, explicitly mention this in `warnings`.
* Do **not** include any explanation or commentary outside the JSON. Only return the JSON object.

Context from Lecture Notes:
{context}
"""

class StudyPlanner:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL_NAME,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        self.parser = JsonOutputParser()

    def _parse_weak_topics(self, weak_topics: str) -> List[str]:
        """
        Parse weak topics string into a list of individual topics.
        Handles various separators: commas, "and", semicolons, etc.
        """
        if not weak_topics or weak_topics.strip().lower() == "none":
            return []
        
        # Replace common separators with commas
        normalized = weak_topics.lower()
        normalized = normalized.replace(" and ", ", ")
        normalized = normalized.replace(";", ",")
        normalized = normalized.replace("/", ",")
        
        # Split by comma and clean up
        topics = [topic.strip() for topic in normalized.split(",")]
        topics = [topic for topic in topics if topic and topic != "none"]
        
        return topics
    
    def _extract_sections_from_context(self, docs: List[Any]) -> List[Dict[str, Any]]:
        """
        Parse retrieved documents to extract section structure.
        This is a heuristic approach - in production, you'd want more robust parsing.
        """
        sections = []
        section_id = 1
        
        for doc in docs:
            content = doc.page_content
            page_nums_raw = doc.metadata.get("page_numbers", "1")
            
            # Parse page numbers safely
            try:
                # Handle different formats: "1", "[1, 2, 3]", "1-5", etc.
                page_nums_str = str(page_nums_raw).strip()
                
                if page_nums_str.startswith('[') and page_nums_str.endswith(']'):
                    # It's a list string like "[75, 76, 77, 78]"
                    import ast
                    page_list = ast.literal_eval(page_nums_str)
                    if isinstance(page_list, list) and page_list:
                        start_page = min(page_list)
                        end_page = max(page_list)
                    else:
                        start_page = end_page = 1
                elif '-' in page_nums_str:
                    # Range format like "1-5"
                    parts = page_nums_str.split('-')
                    start_page = int(parts[0].strip())
                    end_page = int(parts[1].strip())
                elif ',' in page_nums_str:
                    # Comma-separated like "1,2,3"
                    nums = [int(n.strip()) for n in page_nums_str.split(',')]
                    start_page = min(nums)
                    end_page = max(nums)
                else:
                    # Single number
                    start_page = end_page = int(page_nums_str)
            except (ValueError, SyntaxError, AttributeError) as e:
                # Fallback to page 1 if parsing fails
                print(f"Warning: Could not parse page numbers '{page_nums_raw}': {e}")
                start_page = end_page = 1
            
            # Extract section title from content
            lines = content.split('\n')
            section_title = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip code/math fences
                if line.startswith('```') or line.startswith('$$'):
                    continue
                
                # Use first meaningful line as title
                if len(line) > 10 and not line.startswith('---'):
                    section_title = line
                    break
            
            # Clean up title - remove code/math markers and limit length
            if not section_title:
                section_title = content[:100].strip()
            
            section_title = section_title.replace('```pseudo', '').replace('```', '').replace('$$', '')
            section_title = section_title.replace('\n', ' ').strip()
            
            # Limit title length
            if len(section_title) > 100:
                section_title = section_title[:97] + "..."
                
            # Create a section entry (chapter field kept for compatibility but not used in display)
            sections.append({
                "id": section_id,
                "chapter": "Content",  # Generic placeholder
                "title": section_title,
                "pages": [start_page, end_page],
                "difficulty": 2,  # Default to intermediate
                "priority": "important",  # Default priority
                "estimated_minutes": 30  # Default estimate
            })
            section_id += 1
        
        return sections

    def generate_plan(
        self, 
        pdf_id: str, 
        total_days: int, 
        daily_minutes: int, 
        level: str,
        goal: str = "understand the material",
        weak_topics: str = "",
        deadline_context: str = "upcoming exam"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive study plan.
        
        Args:
            pdf_id: ID of the PDF to create plan for
            total_days: Number of days available
            daily_minutes: Minutes available per day
            level: Student level (Beginner/Intermediate/Advanced)
            goal: Student's goal (optional)
            weak_topics: Topics student feels weak in (optional)
            deadline_context: Context about deadline (optional)
        
        Returns:
            Dict containing the study plan with summary, days, and warnings
        """
        # 1. Parse and normalize weak topics
        weak_topics_normalized = self._parse_weak_topics(weak_topics)
        
        # 2. Retrieve context - if weak topics specified, also search for them
        retriever = vector_store.as_retriever(search_kwargs={"k": 10, "filter": {"pdf_id": pdf_id}})
        
        # Get general structure
        docs = retriever.invoke("Table of Contents Syllabus Course Schedule Chapters Topics Overview")
        
        # If weak topics specified, also retrieve content about those topics
        if weak_topics_normalized:
            for topic in weak_topics_normalized:
                topic_docs = retriever.invoke(topic)
                docs.extend(topic_docs[:2])  # Add top 2 results for each weak topic
        
        context_text = "\n\n".join([d.page_content for d in docs[:10]])  # Limit to first 10 for context
        
        # 3. Extract sections structure
        sections = self._extract_sections_from_context(docs)
        sections_json = json.dumps(sections, indent=2)
        
        # 4. Build Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", "Generate the study plan based on the provided information. IMPORTANT: Make sure to include ALL weak topics mentioned: {weak_topics_list}")
        ])
        
        chain = prompt | self.llm | self.parser
        
        # 5. Invoke
        try:
            result = chain.invoke({
                "total_days": total_days,
                "daily_minutes": daily_minutes,
                "level": level,
                "goal": goal,
                "weak_topics": ", ".join(weak_topics_normalized) if weak_topics_normalized else "none specified",
                "weak_topics_list": ", ".join(weak_topics_normalized) if weak_topics_normalized else "none",
                "deadline_context": deadline_context,
                "sections_json": sections_json,
                "context": context_text
            })
            
            # Ensure result has the expected structure
            if isinstance(result, dict) and "days" in result:
                return result
            elif isinstance(result, list):
                # Old format compatibility
                return {
                    "summary": {
                        "total_days": total_days,
                        "total_estimated_minutes": sum(day.get("estimated_minutes", 0) for day in result),
                        "topics_covered": list(set(topic for day in result for topic in day.get("topics", []))),
                        "review_days": sum(1 for day in result if day.get("review")),
                        "plan_style": f"{level} level plan",
                        "notes": "Generated using legacy format"
                    },
                    "days": result,
                    "warnings": []
                }
            else:
                raise ValueError(f"Unexpected result format: {type(result)}")
                
        except Exception as e:
            # Fallback if JSON parsing fails
            print(f"Error generating plan: {e}")
            import traceback
            traceback.print_exc()
            
            # Return a minimal fallback plan
            return {
                "summary": {
                    "total_days": total_days,
                    "total_estimated_minutes": total_days * daily_minutes,
                    "topics_covered": ["General Topics"],
                    "review_days": 1,
                    "plan_style": "Fallback plan",
                    "notes": f"Error occurred during generation: {str(e)}"
                },
                "days": [
                    {
                        "day": i + 1,
                        "focus": f"Study day {i + 1}",
                        "estimated_total_minutes": daily_minutes,
                        "study_blocks": [
                            {
                                "type": "study",
                                "chapter": "General",
                                "section_title": "Review lecture materials",
                                "section_ids": [],
                                "estimated_minutes": daily_minutes,
                                "tasks": ["Review lecture materials", "Take notes", "Practice problems"]
                            }
                        ],
                        "review_blocks": []
                    }
                    for i in range(total_days)
                ],
                "warnings": [f"Plan generation failed: {str(e)}. Using fallback plan."]
            }

study_planner = StudyPlanner()

