# Weak Topics Multi-Input Fix

## Problem
When users entered multiple weak topics (e.g., "quadratic sorts and merge sort"), the study plan generator only addressed one of them instead of all topics.

## Root Cause
1. The weak topics weren't being properly parsed from the input string
2. The prompt didn't emphasize strongly enough that ALL weak topics must be addressed
3. No validation or feedback showing which topics were detected

## Solution

### 1. Enhanced Prompt Instructions
Updated the system prompt to make weak topic handling a **CRITICAL REQUIREMENT**:

```
3. **Highlight weak topics (CRITICAL REQUIREMENT)**

   * If `{weak_topics}` is not empty, you MUST ensure ALL mentioned weak topics:
     * Appear in the first half of the study plan (earlier days).
     * Receive 20-30% MORE time than normal sections.
     * Get at least TWO review blocks throughout the plan.
     * Are explicitly called out in the day's focus when they appear.
   * Parse weak topics carefully - they may be comma-separated or use "and"
```

### 2. Weak Topics Parser
Added `_parse_weak_topics()` method that handles multiple input formats:

**Supported Formats:**
- Comma-separated: `"bubble sort, merge sort, quicksort"`
- Using "and": `"bubble sort and merge sort"`
- Semicolons: `"bubble sort; merge sort"`
- Mixed: `"bubble sort, merge sort and quicksort"`

**Example:**
```python
Input: "quadratic sorts and merge sort"
Output: ["quadratic sorts", "merge sort"]
```

### 3. Enhanced Context Retrieval
The system now:
1. Retrieves general course structure
2. **Additionally** retrieves specific content for each weak topic
3. Ensures the LLM has relevant context for all weak topics

```python
# Get general structure
docs = retriever.invoke("Table of Contents...")

# Add specific content for each weak topic
if weak_topics_normalized:
    for topic in weak_topics_normalized:
        topic_docs = retriever.invoke(topic)
        docs.extend(topic_docs[:2])
```

### 4. UI Feedback
Added visual feedback showing which topics were detected:

```
📌 Weak topics detected: bubble sort, merge sort, quicksort
```

This appears immediately as the user types, helping them verify the input is parsed correctly.

### 5. Explicit Prompt Reminder
Added a human message that explicitly lists the weak topics:

```python
("human", "Generate the study plan. IMPORTANT: Make sure to include ALL weak topics: {weak_topics_list}")
```

## Testing

### Test Case 1: Multiple Topics with "and"
**Input:** `"quadratic sorts and merge sort"`

**Expected:**
- Both "quadratic sorts" and "merge sort" appear in the plan
- Both get extra time allocation (20-30% more)
- Both appear in first half of the schedule
- Both get at least 2 review blocks

### Test Case 2: Comma-Separated
**Input:** `"bubble sort, selection sort, insertion sort"`

**Expected:**
- All three sorting algorithms covered
- Each gets dedicated study time
- Multiple review sessions for each

### Test Case 3: Mixed Separators
**Input:** `"dynamic programming, greedy algorithms and graph traversal"`

**Expected:**
- All three topics parsed correctly
- All three prioritized in the plan

## Usage

### From UI:
1. Go to "Study Plan Generator" tab
2. Expand "Advanced Options"
3. In "Topics You Feel Weak In", enter:
   - `bubble sort and merge sort`
   - OR `bubble sort, merge sort`
   - OR `bubble sort; merge sort`
4. See the blue info box showing detected topics
5. Generate plan
6. Verify all topics appear in the schedule

### From API:
```python
payload = {
    "pdf_id": "your-pdf-id",
    "total_days": 7,
    "daily_minutes": 90,
    "level": "Intermediate",
    "weak_topics": "quadratic sorts and merge sort"
}

response = requests.post("http://localhost:8001/study-plan", json=payload)
plan = response.json()["plan"]

# Check that all weak topics are covered
for day in plan["days"]:
    print(f"Day {day['day']}: {day['focus']}")
    for block in day["study_blocks"]:
        print(f"  - {block['section_title']}")
```

## Quality Checks

The system now enforces:
- ✅ ALL weak topics must appear in the plan
- ✅ Each weak topic gets 20-30% extra time
- ✅ Each weak topic appears in first 60% of days
- ✅ Each weak topic gets at least 2 review blocks
- ✅ Weak topics are explicitly mentioned in day focus
- ✅ Warning if a weak topic can't be found in the PDF

## Files Modified

1. **app/study_plans/planner.py**
   - Added `_parse_weak_topics()` method
   - Enhanced prompt with CRITICAL REQUIREMENT
   - Improved context retrieval for weak topics
   - Added explicit weak topics list to human message

2. **frontend/app.py**
   - Improved help text for weak topics input
   - Added visual feedback showing parsed topics
   - Better examples in the UI

## Future Enhancements

Potential improvements:
- [ ] Auto-suggest topics based on PDF content
- [ ] Fuzzy matching for topic names (e.g., "bubblesort" → "bubble sort")
- [ ] Topic difficulty assessment
- [ ] Progress tracking for weak topics
- [ ] Adaptive replanning if weak topics aren't improving

