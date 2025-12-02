"""
Automated Scoring for RAG Evaluation

This script uses an LLM (Gemini) as a judge to automatically score RAG answers
according to the predefined rubric.

Usage:
    python app/evaluation/auto_score.py <results_file.csv>
    python app/evaluation/auto_score.py <results_file.csv> --output scored_results.csv
"""

import json
import sys
import csv
from pathlib import Path
from typing import Dict, Any, List
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import LLM_MODEL_NAME, GOOGLE_API_KEY


# Load rubric
def load_rubric() -> str:
    """Load the rubric markdown file."""
    rubric_path = Path(__file__).parent / "rubric.md"
    with open(rubric_path, 'r') as f:
        return f.read()


# Scoring prompt
SCORING_PROMPT = """You are an expert evaluator for a RAG (Retrieval-Augmented Generation) system used for educational purposes.

Your task is to score a generated answer according to a predefined rubric with 4 dimensions.

---

## RUBRIC

{rubric}

---

## QUESTION CONTEXT

**Question ID:** {question_id}
**Category:** {category}
**Difficulty:** {difficulty}

**Question:**
{question}

**Expected Sections/Pages:**
{expected_sections}

**Reference Answer (Ground Truth):**
{reference_answer}

**Key Points That Should Be Covered:**
{key_points}

---

## GENERATED ANSWER TO EVALUATE

**Answer:**
{generated_answer}

**Sources Cited:**
{source_pages}

---

## YOUR TASK

Score the generated answer on each of the 4 dimensions according to the rubric:

1. **Relevance (0-2):** Does it directly address the question?
2. **Correctness (0-2):** Is the information factually accurate?
3. **Citations (0-2):** Does it properly cite lecture sources?
4. **Detail & Clarity (0-2):** Is it clear and appropriately detailed?

For each dimension:
- Compare the generated answer to the reference answer and key points
- Check if cited sources match expected sections
- Apply the rubric criteria strictly
- Provide a brief justification for each score

**IMPORTANT:**
- Be objective and consistent
- Base scores on rubric criteria, not personal preference
- A score of 6/8 or higher is considered passing
- Verify citations match the expected sections

---

## OUTPUT FORMAT

You must output a valid JSON object with this exact structure:

{{
  "relevance_score": 0-2,
  "relevance_justification": "Brief explanation",
  "correctness_score": 0-2,
  "correctness_justification": "Brief explanation",
  "citation_score": 0-2,
  "citation_justification": "Brief explanation",
  "detail_score": 0-2,
  "detail_justification": "Brief explanation",
  "total_score": 0-8,
  "pass_fail": "PASS or FAIL",
  "overall_notes": "Summary of strengths and weaknesses"
}}

Output ONLY the JSON object, no other text.
"""


class AutoScorer:
    def __init__(self):
        """Initialize the auto-scorer with LLM."""
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL_NAME,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1,  # Low temperature for consistent scoring
            convert_system_message_to_human=True
        )
        self.parser = JsonOutputParser()
        self.rubric = load_rubric()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SCORING_PROMPT),
            ("human", "Score this answer according to the rubric.")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    def score_answer(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single answer using the LLM judge.
        
        Args:
            question_data: Dictionary containing question, answer, and metadata
        
        Returns:
            Dictionary with scores and justifications
        """
        try:
            # Prepare input
            input_data = {
                "rubric": self.rubric,
                "question_id": question_data.get('question_id', 'N/A'),
                "category": question_data.get('category', 'N/A'),
                "difficulty": question_data.get('difficulty', 'N/A'),
                "question": question_data.get('question', ''),
                "expected_sections": question_data.get('expected_sections', ''),
                "reference_answer": question_data.get('reference_answer', ''),
                "key_points": question_data.get('key_points', ''),
                "generated_answer": question_data.get('generated_answer', ''),
                "source_pages": question_data.get('source_pages', '')
            }
            
            # Invoke LLM
            result = self.chain.invoke(input_data)
            
            # Validate result
            required_fields = [
                'relevance_score', 'correctness_score', 
                'citation_score', 'detail_score', 'total_score'
            ]
            
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Calculate total if not provided or incorrect
            calculated_total = (
                result['relevance_score'] + 
                result['correctness_score'] + 
                result['citation_score'] + 
                result['detail_score']
            )
            result['total_score'] = calculated_total
            
            # Determine pass/fail
            result['pass_fail'] = "PASS" if calculated_total >= 6 else "FAIL"
            
            return result
            
        except Exception as e:
            print(f"Error scoring question {question_data.get('question_id', '?')}: {e}")
            # Return error result
            return {
                'relevance_score': 0,
                'relevance_justification': f"Error: {str(e)}",
                'correctness_score': 0,
                'correctness_justification': '',
                'citation_score': 0,
                'citation_justification': '',
                'detail_score': 0,
                'detail_justification': '',
                'total_score': 0,
                'pass_fail': 'ERROR',
                'overall_notes': f'Scoring failed: {str(e)}'
            }


def auto_score_results(input_file: str, output_file: str = None):
    """
    Automatically score all answers in a results CSV file.
    
    Args:
        input_file: Path to the unscored results CSV
        output_file: Path to save scored results (optional)
    """
    # Generate output filename if not provided
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_auto_scored.csv")
    
    print("=" * 80)
    print("AUTOMATED RAG EVALUATION SCORING")
    print("=" * 80)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")
    print(f"\nInitializing LLM judge (Gemini)...")
    
    # Initialize scorer
    scorer = AutoScorer()
    
    # Load results
    print(f"Loading results...")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = list(reader)
    
    print(f"Found {len(results)} answers to score")
    print("\n" + "=" * 80)
    
    # Score each answer
    scored_results = []
    
    for idx, row in enumerate(results, 1):
        question_id = row.get('question_id', '?')
        question = row.get('question', '')[:60] + "..."
        
        print(f"\n[{idx}/{len(results)}] Scoring Q{question_id}: {question}")
        
        # Score the answer
        scores = scorer.score_answer(row)
        
        # Merge scores into row
        row['relevance_score'] = scores['relevance_score']
        row['correctness_score'] = scores['correctness_score']
        row['citation_score'] = scores['citation_score']
        row['detail_score'] = scores['detail_score']
        row['total_score'] = scores['total_score']
        row['pass_fail'] = scores['pass_fail']
        
        # Combine justifications into notes
        notes = f"""Relevance ({scores['relevance_score']}/2): {scores.get('relevance_justification', '')}
Correctness ({scores['correctness_score']}/2): {scores.get('correctness_justification', '')}
Citations ({scores['citation_score']}/2): {scores.get('citation_justification', '')}
Detail ({scores['detail_score']}/2): {scores.get('detail_justification', '')}

{scores.get('overall_notes', '')}"""
        
        row['notes'] = notes
        
        scored_results.append(row)
        
        print(f"  Scores: R={scores['relevance_score']} C={scores['correctness_score']} "
              f"Cit={scores['citation_score']} D={scores['detail_score']} "
              f"Total={scores['total_score']}/8 [{scores['pass_fail']}]")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Save scored results
    print(f"\n{'=' * 80}")
    print(f"Saving scored results to: {output_file}")
    
    fieldnames = list(scored_results[0].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scored_results)
    
    print(f"✓ Scoring complete!")
    
    # Calculate statistics
    total_questions = len(scored_results)
    passed = sum(1 for r in scored_results if r['pass_fail'] == 'PASS')
    failed = sum(1 for r in scored_results if r['pass_fail'] == 'FAIL')
    errors = sum(1 for r in scored_results if r['pass_fail'] == 'ERROR')
    
    pass_rate = (passed / total_questions) * 100 if total_questions > 0 else 0
    
    # Calculate average scores
    valid_scores = [int(r['total_score']) for r in scored_results if r['pass_fail'] != 'ERROR']
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    print(f"\n{'=' * 80}")
    print("AUTOMATED SCORING SUMMARY")
    print("=" * 80)
    print(f"\nTotal Questions: {total_questions}")
    print(f"Passed (≥6/8):   {passed} ({pass_rate:.1f}%)")
    print(f"Failed (<6/8):   {failed}")
    if errors > 0:
        print(f"Errors:          {errors}")
    print(f"Average Score:   {avg_score:.2f}/8")
    
    goal_met = "✅ GOAL MET" if pass_rate >= 85 else "❌ GOAL NOT MET"
    print(f"\n🎯 Goal (≥85% pass rate): {goal_met}")
    
    print(f"\n{'=' * 80}")
    print("\nNext steps:")
    print(f"1. Review the scored results: {output_file}")
    print(f"2. Verify a sample of scores manually for quality check")
    print(f"3. Run detailed analysis:")
    print(f"   python app/evaluation/run_eval.py --analyze {output_file}")
    print(f"\nNote: Automated scoring is consistent but should be spot-checked")
    print(f"against the rubric to ensure quality.")
    
    return output_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automatically score RAG evaluation results using LLM judge"
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to unscored results CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save scored results (default: input_file_auto_scored.csv)'
    )
    
    args = parser.parse_args()
    
    # Run auto-scoring
    auto_score_results(args.input_file, args.output)

