# RAG System Troubleshooting Guide

## Why Performance Varies Between UI and Evaluation

### Common Causes

#### 1. **Different Question Phrasing**
**Problem:** Evaluation questions may be phrased differently than how you test in UI.

**Example:**
- UI: "Tell me about bubble sort complexity"
- Eval: "What is the time complexity of bubble sort in the worst case?"

**Why It Matters:**
- Different phrasings create different embeddings
- May retrieve different chunks
- More specific questions need more precise retrieval

**Solution:**
```bash
# Test with exact evaluation question
python app/evaluation/diagnose_rag.py --question "What is the time complexity of bubble sort in the worst case?"
```

#### 2. **Retrieval Quality Issues**
**Problem:** The right chunks aren't being retrieved.

**Symptoms:**
- Answer says "I cannot provide..." or "Based on the provided context..."
- Citations missing or wrong pages
- Answer is generic, not specific to lecture

**Diagnosis:**
```bash
python app/evaluation/diagnose_rag.py --question "YOUR_QUESTION" --expected-pages "6, 8"
```

**Common Causes:**

a) **K value too low (only 5 chunks)**
```python
# In qa_chain.py, line 54
self.retriever = vector_store.as_retriever(search_kwargs={"k": 5})
```
**Fix:** Increase to 7-10 chunks
```python
self.retriever = vector_store.as_retriever(search_kwargs={"k": 10})
```

b) **Embedding mismatch**
- Question embeddings don't match chunk embeddings
- Content was chunked poorly
- Important keywords split across chunks

**Fix:** Re-chunk with better boundaries or increase overlap

c) **Content not in vector store**
- PDF wasn't uploaded
- Extraction failed for that section
- OCR didn't capture the content

**Fix:** Verify PDF upload and re-ingest

#### 3. **Chunking Issues**
**Problem:** Important information split across multiple chunks.

**Example:**
```
Chunk 1: "Bubble sort has time complexity"
Chunk 2: "of O(n²) in the worst case"
```

**Result:** Neither chunk alone answers the question well.

**Solution:**
- Increase chunk overlap (currently 200 chars)
- Adjust chunk size (currently ~1000 chars)
- Keep related content together

#### 4. **Prompt Sensitivity**
**Problem:** LLM interprets prompt differently for different questions.

**Check your prompt:**
```bash
cat app/rag/prompts.py
```

**Common Issues:**
- Prompt too restrictive ("only answer if explicitly stated")
- Not encouraging synthesis across chunks
- Missing instructions for specific question types

**Solution:** Update prompt to be more flexible while maintaining accuracy.

#### 5. **Context Window Limitations**
**Problem:** Too much retrieved context, important parts get lost.

**Symptoms:**
- Works for simple questions
- Fails for complex questions needing multiple pieces of info

**Diagnosis:**
Check total context length:
```python
# In diagnose_rag.py output, look for total characters in retrieved chunks
```

**Solution:**
- Retrieve fewer but more relevant chunks
- Improve retrieval precision
- Summarize chunks before passing to LLM

---

## Diagnostic Workflow

### Step 1: Run System Check
```bash
python app/evaluation/diagnose_rag.py --check-config
```

**What it checks:**
- ✅ LLM temperature (should be 0.0)
- ✅ Retrieval settings
- ✅ Vector store accessibility
- ✅ System prompt loading

### Step 2: Test Specific Question
```bash
python app/evaluation/diagnose_rag.py --question "What is bubble sort?"
```

**What it shows:**
- Retrieved chunks (top 5)
- Page numbers and chunk IDs
- Content preview
- Generated answer
- Sources used

### Step 3: Compare with Expected Pages
```bash
python app/evaluation/diagnose_rag.py \
  --question "What is the time complexity of bubble sort?" \
  --expected-pages "6, 8"
```

**What it checks:**
- Are expected pages in retrieved chunks?
- If not → retrieval problem
- If yes → generation problem

### Step 4: Compare UI vs Eval
```bash
python app/evaluation/diagnose_rag.py \
  --question "What is bubble sort?" \
  --compare
```

**What it reveals:**
- If answers are identical → no difference
- If answers differ → non-deterministic behavior

---

## Common Issues and Fixes

### Issue 1: "I cannot provide pseudocode..."

**Diagnosis:**
```bash
python app/evaluation/diagnose_rag.py --question "Provide the pseudocode for bubble sort"
```

**Possible Causes:**
1. Pseudocode is in an image (OCR not working)
2. Pseudocode chunks not retrieved
3. Prompt too restrictive

**Fixes:**
1. **Check OCR:**
   ```bash
   python debug_extraction.py /path/to/pdf.pdf 6
   ```
   Verify OCR extracted the pseudocode

2. **Check retrieval:**
   Look at retrieved chunks - do they contain code?

3. **Update prompt:**
   Ensure prompt allows quoting pseudocode from context

### Issue 2: Wrong or Missing Citations

**Diagnosis:**
Check if metadata is preserved:
```bash
python app/evaluation/diagnose_rag.py --question "YOUR_QUESTION"
# Look at "Sources used" section
```

**Possible Causes:**
1. Metadata not passed to LLM
2. Prompt doesn't require citations
3. Format_docs function not working

**Fixes:**
1. **Check format_docs in qa_chain.py:**
   ```python
   def format_docs(docs):
       # Should include page numbers and chunk IDs
   ```

2. **Update prompt to require citations:**
   ```python
   "Always cite your sources with [Page X]"
   ```

### Issue 3: Answers Too Short/Vague

**Diagnosis:**
```bash
python app/evaluation/diagnose_rag.py --question "Explain bubble sort"
# Check answer length and detail
```

**Possible Causes:**
1. Retrieved chunks lack detail
2. Prompt encourages brevity
3. LLM not synthesizing across chunks

**Fixes:**
1. **Increase k (retrieve more chunks):**
   ```python
   search_kwargs={"k": 10}  # Instead of 5
   ```

2. **Update prompt:**
   ```python
   "Provide a comprehensive answer with appropriate detail..."
   ```

3. **Check chunk quality:**
   Ensure chunks contain complete information

### Issue 4: Inconsistent Performance

**Diagnosis:**
```bash
# Run same question twice
python app/evaluation/diagnose_rag.py --question "What is bubble sort?" --compare
```

**Possible Causes:**
1. Temperature > 0 (should be 0.0)
2. Vector store returning different results
3. Caching issues

**Fixes:**
1. **Verify temperature:**
   ```python
   # In qa_chain.py
   temperature=0.0  # Must be exactly 0.0
   ```

2. **Clear cache:**
   ```bash
   rm -rf ./chroma_db
   # Re-upload PDFs
   ```

---

## Improving Retrieval Quality

### Strategy 1: Increase K
```python
# In qa_chain.py
search_kwargs={"k": 10}  # Retrieve more chunks
```

**Pros:** More context, higher chance of finding answer
**Cons:** More noise, longer context

### Strategy 2: Better Chunking
```python
# In chunk.py
TARGET_CHUNK_SIZE = 1500  # Larger chunks
OVERLAP = 300  # More overlap
```

**Pros:** More complete information per chunk
**Cons:** Fewer chunks, less granular

### Strategy 3: Hybrid Search
Add keyword search alongside semantic search:
```python
# Combine dense (semantic) + sparse (keyword) retrieval
```

**Pros:** Better for specific terms (like "O(n²)")
**Cons:** More complex implementation

### Strategy 4: Query Expansion
Expand user query before retrieval:
```python
# Original: "bubble sort complexity"
# Expanded: "bubble sort time complexity worst case O(n²)"
```

**Pros:** Better semantic matching
**Cons:** May retrieve irrelevant chunks

---

## Improving Answer Quality

### Strategy 1: Better Prompts
```python
# Add examples to prompt
"Example: For 'What is X?', provide definition, properties, and examples."
```

### Strategy 2: Multi-Step Reasoning
```python
# Step 1: Retrieve relevant chunks
# Step 2: Synthesize information
# Step 3: Generate answer with citations
```

### Strategy 3: Answer Validation
```python
# After generating answer, check:
# - Does it address the question?
# - Are citations present?
# - Is it based on retrieved context?
```

---

## Quick Fixes for Common Problems

### Fix 1: Low Scores on Complexity Questions
```bash
# Ensure math/complexity chunks are tagged
# Check contains_math metadata
python debug_extraction.py /path/to/pdf.pdf 6
```

### Fix 2: Low Scores on Pseudocode Questions
```bash
# Verify OCR is working
# Check contains_code metadata
python test_ocr_extraction.py /path/to/pdf.pdf 6
```

### Fix 3: Low Scores on Comparison Questions
```bash
# Increase k to get chunks from both topics
# Update prompt to encourage comparison
```

### Fix 4: Missing Citations
```python
# In prompts.py, add:
"ALWAYS cite sources using [Page X] format."
"Include page numbers for every claim."
```

---

## Testing Your Fixes

### 1. Test Individual Question
```bash
python app/evaluation/diagnose_rag.py --question "YOUR_QUESTION"
```

### 2. Re-run Evaluation
```bash
python app/evaluation/run_eval.py
python app/evaluation/auto_score.py eval_results_new.csv
python app/evaluation/run_eval.py --analyze eval_results_new_auto_scored.csv
```

### 3. Compare Before/After
```bash
# Keep old results
mv eval_results_old_auto_scored.csv results_before_fix.csv

# Run new evaluation
python app/evaluation/run_eval.py
python app/evaluation/auto_score.py eval_results_new.csv

# Compare pass rates
python app/evaluation/run_eval.py --analyze results_before_fix.csv
python app/evaluation/run_eval.py --analyze eval_results_new_auto_scored.csv
```

---

## Recommended Improvement Path

### Phase 1: Diagnose (30 minutes)
1. Run system check
2. Test 3-5 failed questions with diagnostic tool
3. Identify patterns (retrieval? generation? specific topics?)

### Phase 2: Fix Retrieval (1-2 hours)
1. Increase k from 5 to 10
2. Verify OCR working for pseudocode
3. Check chunk quality for failed questions
4. Re-ingest PDFs if needed

### Phase 3: Fix Generation (1 hour)
1. Update prompts for clarity
2. Ensure citations required
3. Add examples for complex questions
4. Test with diagnostic tool

### Phase 4: Re-evaluate (30 minutes)
1. Run full evaluation
2. Auto-score results
3. Compare to baseline
4. Iterate if needed

---

## Success Metrics

After fixes, you should see:
- ✅ Pass rate increases (target: ≥85%)
- ✅ Citation scores improve
- ✅ Consistent performance across question types
- ✅ UI and evaluation performance aligned

---

## Getting Help

If issues persist:
1. Share diagnostic output
2. Show specific failed questions
3. Provide retrieved chunks vs expected pages
4. Check if it's a systematic issue or edge cases

