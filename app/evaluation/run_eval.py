"""
RAG System Evaluation Script

This script runs the evaluation dataset through the RAG system and generates
an output file for manual scoring according to the rubric.

Usage:
    python app/evaluation/run_eval.py [--pdf-id PDF_ID] [--output OUTPUT_FILE]
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rag.qa_chain import qa_chain
from app.embeddings.vector_store import vector_store


def load_evaluation_dataset(dataset_path: str = "app/evaluation/eval_dataset.json") -> Dict[str, Any]:
    """Load the evaluation dataset from JSON file."""
    with open(dataset_path, 'r') as f:
        return json.load(f)


def run_evaluation(pdf_ids: List[str] = None, output_file: str = None) -> str:
    """
    Run all questions through the RAG system and save results.
    
    Args:
        pdf_ids: List of PDF IDs to query. If None, queries all PDFs.
        output_file: Path to save results. If None, generates timestamped filename.
    
    Returns:
        Path to the output file
    """
    # Load dataset
    print("Loading evaluation dataset...")
    dataset = load_evaluation_dataset()
    questions = dataset['questions']
    
    # Generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"app/evaluation/eval_results_{timestamp}.csv"
    
    # Prepare results
    results = []
    
    print(f"\nRunning evaluation on {len(questions)} questions...")
    print("=" * 80)
    
    for idx, question_data in enumerate(questions, 1):
        question_id = question_data['id']
        question = question_data['question']
        category = question_data['category']
        difficulty = question_data['difficulty']
        
        print(f"\n[{idx}/{len(questions)}] Q{question_id}: {question}")
        print(f"Category: {category} | Difficulty: {difficulty}")
        
        try:
            # Query the RAG system
            result = qa_chain.get_answer(question, pdf_ids)
            answer = result['answer']
            sources = result['source_documents']
            
            # Extract source information
            source_pages = []
            source_chunks = []
            for doc in sources:
                page_nums = doc['metadata'].get('page_numbers', 'Unknown')
                chunk_id = doc['metadata'].get('chunk_id', 'Unknown')
                source_pages.append(str(page_nums))
                source_chunks.append(chunk_id)
            
            # Prepare result row
            result_row = {
                'question_id': question_id,
                'category': category,
                'difficulty': difficulty,
                'question': question,
                'generated_answer': answer,
                'source_pages': ', '.join(source_pages),
                'source_chunks': ', '.join(source_chunks),
                'expected_sections': ', '.join(question_data['expected_sections']),
                'reference_answer': question_data['reference_answer'],
                'key_points': ' | '.join(question_data['key_points']),
                # Scoring columns (to be filled manually)
                'relevance_score': '',
                'correctness_score': '',
                'citation_score': '',
                'detail_score': '',
                'total_score': '',
                'pass_fail': '',
                'notes': ''
            }
            
            results.append(result_row)
            
            print(f"✓ Answer generated ({len(answer)} chars)")
            print(f"  Sources: {', '.join(source_pages)}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            # Add error row
            result_row = {
                'question_id': question_id,
                'category': category,
                'difficulty': difficulty,
                'question': question,
                'generated_answer': f"ERROR: {str(e)}",
                'source_pages': '',
                'source_chunks': '',
                'expected_sections': ', '.join(question_data['expected_sections']),
                'reference_answer': question_data['reference_answer'],
                'key_points': ' | '.join(question_data['key_points']),
                'relevance_score': '',
                'correctness_score': '',
                'citation_score': '',
                'detail_score': '',
                'total_score': '',
                'pass_fail': '',
                'notes': 'ERROR DURING GENERATION'
            }
            results.append(result_row)
    
    # Save results to CSV
    print(f"\n{'=' * 80}")
    print(f"Saving results to: {output_file}")
    
    fieldnames = [
        'question_id', 'category', 'difficulty', 'question', 
        'generated_answer', 'source_pages', 'source_chunks',
        'expected_sections', 'reference_answer', 'key_points',
        'relevance_score', 'correctness_score', 'citation_score', 'detail_score',
        'total_score', 'pass_fail', 'notes'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Results saved successfully!")
    print(f"\nNext steps:")
    print(f"1. Open {output_file}")
    print(f"2. Review app/evaluation/rubric.md")
    print(f"3. Score each answer according to the rubric:")
    print(f"   - relevance_score (0-2)")
    print(f"   - correctness_score (0-2)")
    print(f"   - citation_score (0-2)")
    print(f"   - detail_score (0-2)")
    print(f"4. Calculate total_score (sum of above)")
    print(f"5. Mark pass_fail (PASS if ≥6, FAIL if <6)")
    print(f"6. Add any notes in the notes column")
    print(f"\nGoal: ≥85% (13/15) should PASS")
    
    return output_file


def analyze_results(results_file: str):
    """
    Analyze scored results and generate statistics.
    
    Args:
        results_file: Path to the CSV file with scores filled in
    """
    print(f"\nAnalyzing results from: {results_file}")
    
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = list(reader)
    
    # Filter out rows without scores
    scored_results = [r for r in results if r['total_score'].strip()]
    
    if not scored_results:
        print("⚠ No scores found in the file. Please score the answers first.")
        return
    
    # Calculate statistics
    total_questions = len(scored_results)
    total_scores = [int(r['total_score']) for r in scored_results]
    passes = sum(1 for score in total_scores if score >= 6)
    fails = total_questions - passes
    pass_rate = (passes / total_questions) * 100
    
    # Dimension averages
    relevance_avg = sum(int(r['relevance_score']) for r in scored_results) / total_questions
    correctness_avg = sum(int(r['correctness_score']) for r in scored_results) / total_questions
    citation_avg = sum(int(r['citation_score']) for r in scored_results) / total_questions
    detail_avg = sum(int(r['detail_score']) for r in scored_results) / total_questions
    overall_avg = sum(total_scores) / total_questions
    
    # Category breakdown
    category_stats = {}
    for result in scored_results:
        cat = result['category']
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'passed': 0, 'scores': []}
        category_stats[cat]['total'] += 1
        category_stats[cat]['scores'].append(int(result['total_score']))
        if int(result['total_score']) >= 6:
            category_stats[cat]['passed'] += 1
    
    # Print report
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"\n📊 Overall Performance:")
    print(f"  Total Questions: {total_questions}")
    print(f"  Passed (≥6/8):   {passes} ({pass_rate:.1f}%)")
    print(f"  Failed (<6/8):   {fails}")
    print(f"  Average Score:   {overall_avg:.2f}/8")
    
    goal_met = "✅ GOAL MET" if pass_rate >= 85 else "❌ GOAL NOT MET"
    print(f"\n🎯 Goal: ≥85% pass rate - {goal_met}")
    
    print(f"\n📈 Dimension Averages:")
    print(f"  Relevance:    {relevance_avg:.2f}/2")
    print(f"  Correctness:  {correctness_avg:.2f}/2")
    print(f"  Citations:    {citation_avg:.2f}/2")
    print(f"  Detail:       {detail_avg:.2f}/2")
    
    print(f"\n📂 Category Breakdown:")
    for cat, stats in category_stats.items():
        cat_pass_rate = (stats['passed'] / stats['total']) * 100
        cat_avg = sum(stats['scores']) / len(stats['scores'])
        print(f"  {cat:20s}: {stats['passed']}/{stats['total']} passed ({cat_pass_rate:.0f}%) | Avg: {cat_avg:.2f}/8")
    
    # Identify weakest areas
    print(f"\n🔍 Areas for Improvement:")
    dimensions = [
        ('Relevance', relevance_avg),
        ('Correctness', correctness_avg),
        ('Citations', citation_avg),
        ('Detail', detail_avg)
    ]
    dimensions.sort(key=lambda x: x[1])
    
    for dim, score in dimensions[:2]:  # Show bottom 2
        if score < 1.5:
            print(f"  ⚠ {dim}: {score:.2f}/2 - Needs improvement")
    
    # Show failed questions
    failed_questions = [r for r in scored_results if int(r['total_score']) < 6]
    if failed_questions:
        print(f"\n❌ Failed Questions ({len(failed_questions)}):")
        for r in failed_questions:
            print(f"  Q{r['question_id']} ({r['category']}): {r['total_score']}/8 - {r['question'][:60]}...")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG system evaluation")
    parser.add_argument('--pdf-ids', nargs='+', help='PDF IDs to query (default: all)')
    parser.add_argument('--output', type=str, help='Output CSV file path')
    parser.add_argument('--analyze', type=str, help='Analyze existing results file')
    
    args = parser.parse_args()
    
    if args.analyze:
        # Analyze mode
        analyze_results(args.analyze)
    else:
        # Evaluation mode
        output_path = run_evaluation(pdf_ids=args.pdf_ids, output_file=args.output)
        print(f"\n✓ Evaluation complete!")
        print(f"\nTo analyze results after scoring:")
        print(f"  python app/evaluation/run_eval.py --analyze {output_path}")

