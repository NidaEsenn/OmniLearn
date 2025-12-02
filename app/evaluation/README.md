# RAG System Evaluation

This folder contains everything needed to evaluate the Lecture Assistant RAG system using a rigorous, pre-defined rubric.

## Quick Start

### 1. Review the Rubric (FIRST!)
```bash
cat app/evaluation/rubric.md
```
**Read this completely before running any evaluations.**

### 2. Run Evaluation
```bash
# Make sure backend is running and PDFs are uploaded
python app/evaluation/run_eval.py
```

### 3. Score the Answers

**Option A: Automated Scoring (Recommended)**
```bash
python app/evaluation/auto_score.py app/evaluation/eval_results_YYYYMMDD_HHMMSS.csv
```
Uses Gemini as an LLM judge to score answers automatically according to the rubric.

**Option B: Manual Scoring**
Open the generated CSV file and score each answer manually (0-2 points per dimension).

### 4. Analyze Results
```bash
python app/evaluation/run_eval.py --analyze app/evaluation/eval_results_YYYYMMDD_HHMMSS_auto_scored.csv
```

## Files

- **`rubric.md`** - Scoring criteria (4 dimensions, 0-2 points each)
- **`eval_dataset.json`** - 15 test questions with ground truth
- **`run_eval.py`** - Evaluation script (generate + analyze)
- **`auto_score.py`** - Automated scoring using LLM judge
- **`EVALUATION_GUIDE.md`** - Comprehensive evaluation guide
- **`README.md`** - This file

## Scoring Rubric Summary

Each answer is scored on 4 dimensions (0-2 points each):

1. **Relevance** - Does it address the question?
2. **Correctness** - Is the information accurate?
3. **Citations** - Does it cite lecture sources properly?
4. **Detail & Clarity** - Is it clear and appropriately detailed?

**Total Score:** 0-8 points
**Passing:** ≥6 points (75%)
**Goal:** ≥85% of answers pass (13/15)

## Evaluation Process

```
1. Pre-defined Rubric → 2. Generate Answers → 3. Manual Scoring → 4. Analysis
```

### Phase 1: Preparation
- Read `rubric.md` thoroughly
- Review `eval_dataset.json`
- Have lecture PDF ready for verification

### Phase 2: Generation
```bash
python app/evaluation/run_eval.py
```
Generates: `eval_results_YYYYMMDD_HHMMSS.csv`

### Phase 3: Scoring
- Open CSV in spreadsheet editor
- For each question:
  - Read question and generated answer
  - Verify facts against lecture PDF
  - Score each dimension (0-2)
  - Calculate total (sum of 4 dimensions)
  - Mark PASS (≥6) or FAIL (<6)
  - Add notes explaining scores

### Phase 4: Analysis
```bash
python app/evaluation/run_eval.py --analyze eval_results_YYYYMMDD_HHMMSS.csv
```
Shows:
- Pass rate (goal: ≥85%)
- Average scores per dimension
- Category breakdown
- Failed questions
- Improvement recommendations

## Example Scoring

**Question:** "What is the time complexity of bubble sort in the worst case?"

**Answer:** "Bubble sort has O(n²) time complexity in the worst case... [Page 6]"

**Scores:**
- Relevance: 2/2 (directly answers question)
- Correctness: 2/2 (O(n²) is correct)
- Citations: 2/2 (specific page reference)
- Detail: 2/2 (clear explanation)
- **Total: 8/8 - PASS**

## Command Reference

```bash
# 1. Generate answers
python app/evaluation/run_eval.py

# Generate with specific PDFs
python app/evaluation/run_eval.py --pdf-ids <id1> <id2>

# Generate with custom output
python app/evaluation/run_eval.py --output my_results.csv

# 2. Auto-score (recommended)
python app/evaluation/auto_score.py eval_results_YYYYMMDD_HHMMSS.csv

# Auto-score with custom output
python app/evaluation/auto_score.py input.csv --output scored.csv

# 3. Analyze results
python app/evaluation/run_eval.py --analyze eval_results_YYYYMMDD_HHMMSS_auto_scored.csv
```

## Tips

- ✅ Define criteria BEFORE evaluation (rubric is pre-written)
- ✅ Score all questions in one session for consistency
- ✅ Verify facts against actual lecture PDF
- ✅ Use notes column to explain deductions
- ✅ Don't modify rubric during evaluation
- ✅ Be objective - base scores on criteria, not preference

## Success Criteria

- **Individual Answer:** ≥6/8 points to pass
- **Overall System:** ≥85% pass rate (13/15 questions)
- **Quality Target:** Average score ≥6.5/8

## For More Details

See `EVALUATION_GUIDE.md` for:
- Complete evaluation philosophy
- Step-by-step walkthrough
- Scoring examples
- Troubleshooting guide
- Best practices
- Reporting templates

## Questions?

Refer to:
1. `rubric.md` - For scoring criteria
2. `EVALUATION_GUIDE.md` - For process details
3. `eval_dataset.json` - For ground truth

