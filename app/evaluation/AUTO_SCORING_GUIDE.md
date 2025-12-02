# Automated Scoring Guide

## Overview

The automated scoring system uses **Gemini as an LLM judge** to score RAG answers according to the predefined rubric. This provides consistent, objective scoring at scale while maintaining the rigor of the evaluation framework.

---

## How It Works

### LLM-as-a-Judge Approach

1. **Input**: Unscored evaluation results (CSV from `run_eval.py`)
2. **Process**: For each answer, Gemini receives:
   - The complete rubric
   - Question context (category, difficulty, expected sections)
   - Reference answer and key points
   - Generated answer and sources
3. **Output**: Scores for each dimension (0-2) with justifications
4. **Result**: Fully scored CSV file ready for analysis

### Why Use Automated Scoring?

**Advantages:**
- ✅ **Consistent**: Same criteria applied to every answer
- ✅ **Fast**: Scores 15 questions in ~30 seconds
- ✅ **Objective**: No human bias or fatigue
- ✅ **Scalable**: Easy to re-evaluate after improvements
- ✅ **Documented**: Justifications provided for each score
- ✅ **Reproducible**: Same inputs → same outputs

**Considerations:**
- ⚠️ LLM scoring should be spot-checked against manual scoring
- ⚠️ Works best with clear, well-defined rubrics
- ⚠️ May occasionally misinterpret edge cases
- ⚠️ Requires API calls (small cost per evaluation)

---

## Usage

### Basic Usage

```bash
# Step 1: Generate answers
python app/evaluation/run_eval.py

# Step 2: Auto-score
python app/evaluation/auto_score.py app/evaluation/eval_results_YYYYMMDD_HHMMSS.csv

# Step 3: Analyze
python app/evaluation/run_eval.py --analyze app/evaluation/eval_results_YYYYMMDD_HHMMSS_auto_scored.csv
```

### Advanced Options

```bash
# Specify custom output file
python app/evaluation/auto_score.py input.csv --output my_scored_results.csv

# Score only specific questions (edit CSV first to include only desired rows)
python app/evaluation/auto_score.py filtered_questions.csv
```

---

## Output Format

The auto-scorer adds these columns to your CSV:

- **`relevance_score`**: 0-2 points
- **`correctness_score`**: 0-2 points
- **`citation_score`**: 0-2 points
- **`detail_score`**: 0-2 points
- **`total_score`**: Sum of above (0-8)
- **`pass_fail`**: "PASS" (≥6) or "FAIL" (<6)
- **`notes`**: Detailed justifications for each dimension

### Example Output

```
question_id,question,generated_answer,relevance_score,correctness_score,citation_score,detail_score,total_score,pass_fail,notes
1,"What is bubble sort?","Bubble sort is...",2,2,2,2,8,PASS,"Relevance (2/2): Directly answers..."
```

---

## Scoring Process

### For Each Answer

1. **Load Rubric**: Full rubric.md content provided to LLM
2. **Provide Context**:
   - Question and metadata
   - Expected sections/pages
   - Reference answer
   - Key points to cover
3. **Present Answer**: Generated answer and sources
4. **Request Scoring**: LLM scores each dimension with justification
5. **Validate**: Ensure scores are 0-2, calculate total, determine pass/fail
6. **Save**: Add scores and notes to CSV

### Temperature Setting

The auto-scorer uses **temperature=0.1** for:
- Consistent scoring across runs
- Reduced randomness
- More deterministic evaluations

---

## Quality Assurance

### Spot-Check Recommendations

After automated scoring, manually verify a sample:

**Minimum Sample:**
- 3 random questions (20%)
- 1 passed question
- 1 failed question  
- 1 borderline question (score = 6)

**What to Check:**
- ✅ Scores align with rubric criteria
- ✅ Justifications make sense
- ✅ Citations were properly evaluated
- ✅ No obvious errors or misinterpretations

### If Discrepancies Found

**Minor Differences (±1 point):**
- Acceptable - LLM and human may weigh factors slightly differently
- Document the difference
- Consider if rubric needs clarification

**Major Differences (≥2 points):**
- Review the LLM's justification
- Check if rubric is ambiguous
- Consider manual override for that question
- May indicate need for rubric refinement

---

## Comparison: Manual vs. Automated

| Aspect | Manual Scoring | Automated Scoring |
|--------|---------------|-------------------|
| **Time** | ~30-45 min for 15 questions | ~30 seconds for 15 questions |
| **Consistency** | May vary with fatigue | Highly consistent |
| **Objectivity** | Subject to human bias | Objective within LLM's interpretation |
| **Scalability** | Limited by human time | Easily scales to 100s of questions |
| **Cost** | Free (your time) | Small API cost (~$0.10 per evaluation) |
| **Justifications** | Must write manually | Automatically generated |
| **Spot-checking** | N/A | Recommended |
| **Best For** | Final validation, edge cases | Rapid iteration, large-scale testing |

---

## Best Practices

### 1. Use for Rapid Iteration

```bash
# Make improvement to RAG system
# Re-run evaluation
python app/evaluation/run_eval.py
python app/evaluation/auto_score.py eval_results_new.csv
# Compare scores to previous evaluation
```

### 2. Combine with Manual Validation

- Use automated scoring for initial evaluation
- Manually verify a sample (20%)
- Use manual scoring for final, official evaluation

### 3. Track Scores Over Time

```bash
# Keep history of evaluations
eval_results_v1_auto_scored.csv  # Baseline
eval_results_v2_auto_scored.csv  # After OCR improvements
eval_results_v3_auto_scored.csv  # After prompt refinement
```

### 4. Use for A/B Testing

```bash
# Test different prompts
python app/evaluation/run_eval.py --output eval_prompt_a.csv
# Change prompt
python app/evaluation/run_eval.py --output eval_prompt_b.csv
# Score both
python app/evaluation/auto_score.py eval_prompt_a.csv
python app/evaluation/auto_score.py eval_prompt_b.csv
# Compare results
```

---

## Troubleshooting

### Issue: Scores Seem Too High/Low

**Possible Causes:**
- LLM is being too lenient/strict
- Rubric interpretation differs from yours
- Reference answers are unclear

**Solutions:**
1. Spot-check several answers manually
2. Review LLM justifications in notes column
3. If systematic bias found, consider manual scoring
4. Refine rubric for clarity

### Issue: Inconsistent Scores

**Possible Causes:**
- Temperature too high (should be 0.1)
- Ambiguous rubric criteria
- Edge cases in questions

**Solutions:**
1. Verify temperature setting in code
2. Clarify rubric criteria
3. Run scoring twice and compare

### Issue: API Errors

**Possible Causes:**
- Rate limiting
- API key issues
- Network problems

**Solutions:**
1. Check API key in `.env`
2. Increase delay between requests (edit `time.sleep()` in code)
3. Retry failed questions

### Issue: Parsing Errors

**Possible Causes:**
- LLM didn't return valid JSON
- Unexpected response format

**Solutions:**
1. Check error messages in output
2. Questions marked with "ERROR" in pass_fail column
3. Manually score problematic questions
4. Report pattern if multiple questions fail

---

## Cost Estimation

**Per Evaluation Run:**
- 15 questions × ~2000 tokens per question = ~30,000 tokens
- Gemini 2.0 Flash: ~$0.10 per million tokens
- **Cost per run: ~$0.003 (less than a penny)**

**For 100 Evaluation Runs:**
- Total cost: ~$0.30

**Conclusion:** Automated scoring is extremely cost-effective!

---

## Example Session

```bash
$ python app/evaluation/run_eval.py
Loading evaluation dataset...
Running evaluation on 15 questions...
[1/15] Q1: What is bubble sort?
✓ Answer generated (234 chars)
...
✓ Results saved: eval_results_20241201_143022.csv

$ python app/evaluation/auto_score.py eval_results_20241201_143022.csv
================================================================================
AUTOMATED RAG EVALUATION SCORING
================================================================================

Input:  eval_results_20241201_143022.csv
Output: eval_results_20241201_143022_auto_scored.csv

Initializing LLM judge (Gemini)...
Found 15 answers to score

[1/15] Scoring Q1: What is bubble sort?...
  Scores: R=2 C=2 Cit=2 D=2 Total=8/8 [PASS]

[2/15] Scoring Q2: What is the divide-and-conquer paradigm?...
  Scores: R=2 C=2 Cit=1 D=2 Total=7/8 [PASS]

...

[15/15] Scoring Q15: What are the key steps in merge sort?...
  Scores: R=2 C=2 Cit=2 D=1 Total=7/8 [PASS]

================================================================================
AUTOMATED SCORING SUMMARY
================================================================================

Total Questions: 15
Passed (≥6/8):   13 (86.7%)
Failed (<6/8):   2
Average Score:   6.9/8

🎯 Goal (≥85% pass rate): ✅ GOAL MET

$ python app/evaluation/run_eval.py --analyze eval_results_20241201_143022_auto_scored.csv
[Detailed analysis output...]
```

---

## When to Use Manual vs. Automated

### Use Automated Scoring When:
- ✅ Rapid iteration and testing
- ✅ Comparing multiple versions
- ✅ Initial evaluation
- ✅ Large number of questions (>15)
- ✅ Frequent re-evaluation needed

### Use Manual Scoring When:
- ✅ Final, official evaluation
- ✅ Edge cases or ambiguous questions
- ✅ Validating automated scores
- ✅ Demonstrating rigor to stakeholders
- ✅ Building confidence in rubric

### Best Approach:
**Hybrid**: Automated for speed, manual validation for quality assurance

---

## Integration with Development Workflow

```bash
# 1. Develop/improve RAG system
# ... make changes to extraction, prompts, etc ...

# 2. Quick evaluation
python app/evaluation/run_eval.py
python app/evaluation/auto_score.py eval_results_latest.csv

# 3. Check if improvement worked
python app/evaluation/run_eval.py --analyze eval_results_latest_auto_scored.csv

# 4. If scores improved, continue. If not, iterate.

# 5. Before final submission, validate with manual spot-check
# ... manually verify 3-5 answers ...

# 6. If spot-check confirms automated scores, you're good!
```

---

## Conclusion

Automated scoring with LLM-as-a-judge provides:
- ✅ Fast, consistent evaluation
- ✅ Objective scoring at scale
- ✅ Detailed justifications
- ✅ Cost-effective solution
- ✅ Enables rapid iteration

**Recommendation:** Use automated scoring for development and iteration, with manual spot-checking for quality assurance. This combines the best of both approaches: speed and rigor.

