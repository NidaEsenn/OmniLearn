# RAG System Evaluation Guide

## Overview

This guide explains how to evaluate the Lecture Assistant RAG system using a rigorous, pre-defined rubric. The evaluation follows your professor's guidance: **define clear criteria before evaluation, not during**.

---

## Evaluation Philosophy

### Key Principles

1. **Pre-defined Rubric**: All scoring criteria are defined in `rubric.md` BEFORE running any evaluations
2. **Objective Scoring**: Each dimension has clear 0-2 point criteria
3. **Consistent Application**: Same rubric applied to all questions
4. **No Mid-Evaluation Changes**: Rubric is not modified during scoring to avoid bias
5. **Ground Truth Verification**: Scores based on lecture material, not general knowledge

### Success Criteria

- **Passing Threshold**: Individual answer scores ≥6/8 (75%)
- **Project Goal**: ≥85% of answers pass (13 out of 15 questions)
- **Quality Target**: Average score ≥6.5/8 across all questions

---

## Files Structure

```
app/evaluation/
├── rubric.md                    # Scoring rubric (4 dimensions, 0-2 each)
├── eval_dataset.json            # 15 test questions with ground truth
├── run_eval.py                  # Evaluation script
├── EVALUATION_GUIDE.md          # This file
└── eval_results_YYYYMMDD_HHMMSS.csv  # Generated results (to be scored)
```

---

## Step-by-Step Evaluation Process

### Phase 1: Preparation (Before Running Evaluation)

#### 1.1 Review the Rubric

Read `rubric.md` thoroughly and understand the four scoring dimensions:

**Dimension 1: Relevance (0-2)**
- Does the answer address what was asked?
- 0 = Off-topic
- 1 = Partially relevant
- 2 = Directly relevant

**Dimension 2: Correctness (0-2)**
- Is the information factually accurate?
- 0 = Major errors
- 1 = Mostly correct with minor issues
- 2 = Fully correct

**Dimension 3: Citations (0-2)**
- Does it use lecture material with proper citations?
- 0 = No citations
- 1 = Weak citations
- 2 = Strong, specific citations

**Dimension 4: Detail & Clarity (0-2)**
- Is it clear and appropriately detailed?
- 0 = Too vague or confusing
- 1 = Adequate but flawed
- 2 = Clear and appropriate

#### 1.2 Review the Test Dataset

Examine `eval_dataset.json` to understand:
- 15 questions across 5 categories
- Expected sections/pages for each question
- Reference answers (ground truth)
- Key points that should be covered

#### 1.3 Prepare Ground Truth Materials

Have access to:
- The actual lecture PDF(s)
- Ability to verify page numbers and content
- Reference materials for fact-checking

### Phase 2: Generate Answers

#### 2.1 Ensure System is Running

```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload --port 8001 --reload-dir app

# Terminal 2: Verify PDFs are uploaded
# Use the Streamlit UI or API to check uploaded PDFs
```

#### 2.2 Run the Evaluation Script

```bash
# Run evaluation on all uploaded PDFs
python app/evaluation/run_eval.py

# Or specify particular PDF IDs
python app/evaluation/run_eval.py --pdf-ids <pdf_id_1> <pdf_id_2>

# Or specify custom output file
python app/evaluation/run_eval.py --output my_eval_results.csv
```

**Output**: A CSV file with columns for:
- Question details (ID, category, difficulty, question text)
- Generated answer
- Source information (pages, chunks)
- Expected sections and reference answer
- Empty scoring columns (to be filled manually)

#### 2.3 Verify Generation

Check that:
- All 15 questions were processed
- Answers were generated (no errors)
- Source citations are present
- CSV file is properly formatted

### Phase 3: Manual Scoring

#### 3.1 Open the Results File

```bash
# Open in Excel, Google Sheets, or any CSV editor
open app/evaluation/eval_results_YYYYMMDD_HHMMSS.csv
```

#### 3.2 Score Each Answer

For each of the 15 questions:

**Step 1: Read the Question**
- Understand what is being asked
- Note the expected sections and reference answer

**Step 2: Read the Generated Answer**
- Read the full answer carefully
- Check the cited sources

**Step 3: Verify Against Ground Truth**
- Open the lecture PDF to the cited pages
- Verify facts are correct
- Check if citations match content

**Step 4: Score Each Dimension**

Fill in the scoring columns:

```
relevance_score:    0, 1, or 2
correctness_score:  0, 1, or 2
citation_score:     0, 1, or 2
detail_score:       0, 1, or 2
```

**Step 5: Calculate Total**

```
total_score = relevance + correctness + citation + detail
```

**Step 6: Determine Pass/Fail**

```
pass_fail = "PASS" if total_score >= 6 else "FAIL"
```

**Step 7: Add Notes**

In the `notes` column, add:
- Specific issues found
- Why points were deducted
- Strengths of the answer

#### 3.3 Scoring Tips

**Be Consistent:**
- Use the same criteria for all questions
- Don't adjust standards mid-evaluation
- If unsure, refer back to rubric examples

**Be Objective:**
- Base scores on rubric criteria, not personal preference
- Verify facts against lecture material
- Don't penalize for style differences

**Document Decisions:**
- Use the notes column liberally
- Explain deductions
- Note any edge cases

**Common Pitfalls to Avoid:**
- ❌ Scoring based on answer length
- ❌ Expecting perfect answers (6/8 is passing)
- ❌ Changing rubric interpretation mid-evaluation
- ❌ Scoring based on general knowledge vs. lecture content
- ❌ Forgetting to verify citations

### Phase 4: Analysis

#### 4.1 Run Analysis Script

```bash
python app/evaluation/run_eval.py --analyze app/evaluation/eval_results_YYYYMMDD_HHMMSS.csv
```

**Output**: Statistical summary including:
- Overall pass rate
- Average scores per dimension
- Category breakdown
- Failed questions list
- Areas for improvement

#### 4.2 Interpret Results

**Goal Achievement:**
- ✅ ≥85% pass rate: Goal met
- ⚠️ 70-84% pass rate: Close, needs minor improvements
- ❌ <70% pass rate: Significant issues, major improvements needed

**Dimension Analysis:**
- Identify weakest dimension(s)
- Focus improvements on lowest-scoring areas

**Category Analysis:**
- Which question types perform best/worst?
- Are certain topics problematic?

#### 4.3 Generate Recommendations

Based on analysis, identify:

**If Relevance is Low:**
- Improve retrieval (better embeddings, more chunks)
- Refine system prompt to stay on topic

**If Correctness is Low:**
- Check PDF extraction quality
- Verify chunking preserves context
- Review LLM prompt for accuracy emphasis

**If Citations are Low:**
- Ensure metadata is properly stored
- Update prompt to require citations
- Verify source formatting in qa_chain.py

**If Detail is Low:**
- Adjust prompt for appropriate detail level
- Check if chunks are too small/large
- Balance between brevity and completeness

---

## Example Evaluation Session

### Question Example

**Q4: "What is the time complexity of bubble sort in the worst case?"**

**Generated Answer:**
```
"Bubble sort has O(n²) time complexity in the worst case, which occurs when 
the array is sorted in reverse order. This is because the algorithm makes n-1 
passes through the array, and in each pass performs up to n-1 comparisons. 
[Page 6, Page 8]"
```

### Scoring Process

**1. Relevance: 2/2**
- ✓ Directly answers the question (worst-case time complexity)
- ✓ Stays on topic throughout
- ✓ No irrelevant information

**2. Correctness: 2/2**
- ✓ O(n²) is correct
- ✓ Explanation of "reverse order" is accurate
- ✓ n-1 passes and comparisons is correct
- Verified against Page 6 of lecture PDF

**3. Citations: 2/2**
- ✓ Specific page numbers provided (6, 8)
- ✓ Citations match the content
- Verified: Page 6 contains complexity analysis

**4. Detail: 2/2**
- ✓ Appropriate level of detail for the question
- ✓ Explains WHY it's O(n²)
- ✓ Clear and well-structured
- ✓ Not too brief, not too verbose

**Total: 8/8 - PASS**

**Notes:** "Excellent answer. Correct complexity, good explanation, proper citations."

---

## Quality Assurance Checklist

Before finalizing evaluation:

- [ ] All 15 questions have been scored
- [ ] Each dimension (4 per question) has a score (0-2)
- [ ] Total scores are calculated correctly (sum of 4 dimensions)
- [ ] Pass/Fail is marked correctly (≥6 = PASS)
- [ ] Citations were verified against actual PDF pages
- [ ] Factual claims were checked against lecture material
- [ ] Scoring was consistent across all questions
- [ ] Notes explain any deductions
- [ ] Analysis script ran successfully
- [ ] Results meet or explain deviation from 85% goal

---

## Reporting Results

### For Your Professor

Include:
1. **The scored CSV file** (with all columns filled)
2. **Analysis output** (from the analysis script)
3. **Summary paragraph** explaining:
   - Pass rate achieved
   - Strongest and weakest dimensions
   - Any patterns observed
   - Recommended improvements

### Sample Summary

```
Evaluation Results Summary:

The RAG system achieved an 86.7% pass rate (13/15 questions passed), 
exceeding the 85% goal. Average score was 6.8/8.

Strengths:
- Relevance: 1.93/2 avg - System consistently addresses questions directly
- Correctness: 1.87/2 avg - High factual accuracy

Areas for Improvement:
- Citations: 1.53/2 avg - Some answers lacked specific page references
- Detail: 1.47/2 avg - Occasionally too brief or too verbose

Failed Questions:
- Q9 (Master Theorem): 5/8 - Missing key conditions
- Q14 (Merge pseudocode): 4/8 - Incomplete pseudocode extraction

Recommendations:
1. Improve OCR extraction for pseudocode (Q13, Q14)
2. Strengthen citation formatting in prompts
3. Add examples to answers for complex topics
```

---

## Continuous Improvement

### After Each Evaluation Cycle

1. **Identify Patterns**: What types of questions consistently fail?
2. **Root Cause Analysis**: Why are they failing?
3. **Implement Fixes**: Update extraction, prompts, or retrieval
4. **Re-evaluate**: Run evaluation again on same questions
5. **Track Progress**: Compare scores across evaluation cycles

### Maintaining the Rubric

- Review rubric quarterly
- Update only between evaluation cycles
- Document any changes with rationale
- Keep old versions for comparison

---

## Troubleshooting

### Issue: Low Pass Rate (<70%)

**Possible Causes:**
- Poor PDF extraction quality
- Inadequate chunking strategy
- Weak retrieval (not finding relevant chunks)
- Insufficient system prompt guidance
- LLM not following instructions

**Debugging Steps:**
1. Check extracted text quality
2. Verify chunks contain expected content
3. Test retrieval with sample queries
4. Review system prompt clarity
5. Check LLM temperature and parameters

### Issue: Inconsistent Scores Across Categories

**Possible Causes:**
- Some topics better represented in PDF
- Certain question types harder for RAG
- Uneven chunk distribution

**Solutions:**
- Analyze which categories fail
- Improve extraction for those topics
- Add more context for difficult questions

### Issue: Good Answers But Low Citation Scores

**Possible Causes:**
- Citations not being generated
- Metadata not properly stored
- Formatting issues in output

**Solutions:**
- Check metadata in vector store
- Update prompt to require citations
- Verify citation formatting in qa_chain.py

---

## Best Practices

1. **Score in Batches**: Do all 15 questions in one session for consistency
2. **Take Breaks**: Avoid fatigue affecting judgment
3. **Use Examples**: Refer to rubric examples when uncertain
4. **Document Everything**: Notes help future evaluations
5. **Be Honest**: Don't inflate scores to meet goals
6. **Iterate**: Use results to improve system
7. **Track Changes**: Keep history of evaluation results

---

## Conclusion

This evaluation framework provides:
- ✅ Pre-defined, objective criteria
- ✅ Consistent scoring methodology
- ✅ Clear success metrics
- ✅ Actionable improvement insights
- ✅ Professional documentation

Follow this guide to demonstrate rigorous evaluation of your RAG system and show continuous improvement over time.

