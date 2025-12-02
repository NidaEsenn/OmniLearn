# Focused Topics Feature - Quick Guide

## 🎯 What is Focused Topics?

Focused Topics lets you generate practice questions on **specific topics** instead of general coverage. Perfect for:
- 📚 Exam preparation on specific chapters
- 🎯 Practicing weak areas
- 🔍 Deep dive into challenging concepts
- ⚡ Quick review before quiz

---

## How to Use

### Step 1: Go to Practice Questions Tab

Navigate to the "📝 Practice Questions" tab in the UI.

### Step 2: Enter Your Topics

```
┌─────────────────────────────────────────────────────────────┐
│ 🎯 Focused Topics (Optional)                                │
│ Enter specific topics to focus on, or leave empty for       │
│ general coverage.                                            │
│                                                              │
│ Topics (comma-separated)                                     │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ bubble sort, merge sort, time complexity                ││
│ └─────────────────────────────────────────────────────────┘│
│                                                              │
│ ℹ️ Will focus on: bubble sort, merge sort, time complexity │
└─────────────────────────────────────────────────────────────┘
```

**Format:** Separate topics with commas
**Examples:**
- `bubble sort, insertion sort`
- `time complexity, space complexity, big-o notation`
- `divide and conquer, master theorem`
- `binary search, linear search`

### Step 3: Generate Questions

Click "🎲 Generate Questions" and wait ~10-15 seconds.

### Step 4: Take Your Focused Quiz

```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Practice Quiz (10 Questions)                             │
│ ℹ️ Focused Topics: bubble sort, merge sort, time complexity│
└─────────────────────────────────────────────────────────────┘

Question 1 🟢 Easy
Topic: Bubble Sort
What is the worst-case time complexity of bubble sort?

[● A. O(n²)]              [○ B. O(n log n)]
[○ C. O(n)]               [○ D. O(log n)]

Question 2 🟡 Medium
Topic: Merge Sort
How does merge sort achieve O(n log n) complexity?
...
```

---

## Examples

### Example 1: Sorting Algorithms

**Input:**
```
bubble sort, insertion sort, selection sort
```

**Result:**
- 10 questions all about these three sorting algorithms
- Questions about complexity, implementation, use cases
- Example: "Which sorting algorithm is most efficient for nearly sorted data?"

### Example 2: Complexity Analysis

**Input:**
```
time complexity, space complexity, asymptotic notation
```

**Result:**
- Questions about Big-O, Big-Theta, Big-Omega
- Time vs space tradeoffs
- Analyzing algorithm complexity
- Example: "What is the space complexity of merge sort?"

### Example 3: Divide and Conquer

**Input:**
```
divide and conquer, master theorem, recurrence relations
```

**Result:**
- Questions about the D&C paradigm
- Applying Master Theorem
- Solving recurrences
- Example: "Explain how divide-and-conquer is used in merge sort."

### Example 4: Exam Prep

**Input:**
```
quicksort, heapsort, comparison sorts
```

**Result:**
- Focused questions for exam topics
- All questions relevant to your exam
- No time wasted on other topics

---

## Tips & Best Practices

### ✅ DO:

1. **Be Specific**
   - Good: `bubble sort, insertion sort`
   - Bad: `sorting` (too broad)

2. **Use Comma Separation**
   - Good: `topic1, topic2, topic3`
   - Bad: `topic1 topic2 topic3`

3. **Match Lecture Content**
   - Use terms from your PDF
   - Check topic names in Q&A first

4. **Start with 2-3 Topics**
   - Easier to cover thoroughly
   - Better question quality

5. **Combine with Study Plan**
   - Use weak topics from study plan
   - Target areas you struggle with

### ❌ DON'T:

1. **Too Many Topics**
   - Bad: 10+ topics for 10 questions
   - Result: Only 1 question per topic

2. **Too Vague**
   - Bad: `algorithms, data structures`
   - Result: Questions too general

3. **Misspellings**
   - Bad: `bubblesort` (no space)
   - Better: `bubble sort`

4. **Unrelated Topics**
   - Bad: Topics not in your PDF
   - Result: No relevant content found

---

## Integration with Study Plans

### Workflow:

1. **Generate Study Plan**
   - Identify weak topics: "quadratic sorts, merge sort"

2. **Study the Material**
   - Review lecture pages
   - Watch videos
   - Read notes

3. **Practice with Focused Topics**
   - Go to Practice Questions
   - Enter: `quadratic sorts, merge sort`
   - Generate 10 questions

4. **Take Quiz**
   - Test your understanding
   - Get immediate feedback

5. **Review Mistakes**
   - Read explanations
   - Check page references
   - Go back to Q&A if needed

6. **Retry Until Mastery**
   - Try again → Aim for 90%+
   - Shuffle for new questions
   - Move to next topic

---

## Comparison: General vs Focused

### General Coverage (No Focused Topics)

**Input:** (empty)

**Questions Cover:**
- Sorting algorithms
- Searching algorithms
- Data structures
- Complexity analysis
- Algorithm design
- Mathematical concepts
- Problem solving

**Best For:**
- General review
- Discovering weak areas
- Comprehensive practice
- Before final exam

### Focused Coverage (With Topics)

**Input:** `merge sort, quick sort`

**Questions Cover:**
- Merge sort only
- Quick sort only
- Comparisons between them

**Best For:**
- Targeted practice
- Weak area improvement
- Exam on specific topics
- Quick review

---

## Visual Comparison

### Without Focused Topics

```
Generate 10 Questions → Get diverse topics:
- Q1: Bubble Sort
- Q2: Binary Search
- Q3: Linked Lists
- Q4: Time Complexity
- Q5: Stacks
- Q6: Merge Sort
- Q7: Hash Tables
- Q8: Recursion
- Q9: Arrays
- Q10: Big-O Notation
```

### With Focused Topics: "merge sort, quick sort"

```
Generate 10 Questions → Get focused topics:
- Q1: Merge Sort complexity
- Q2: Quick Sort pivot selection
- Q3: Merge Sort space usage
- Q4: Quick Sort worst case
- Q5: Merge Sort implementation
- Q6: Quick Sort average case
- Q7: Comparing merge and quick
- Q8: Merge Sort stability
- Q9: Quick Sort in-place sorting
- Q10: When to use each algorithm
```

---

## Troubleshooting

### Issue: "No questions generated"

**Possible Causes:**
- Topics not in PDF
- Misspelled topic names
- No content found for topics

**Solutions:**
1. Check topic names in your PDF
2. Try broader topic names
3. Use Q&A to verify topic exists
4. Leave empty for general coverage

### Issue: "Questions not focused enough"

**Possible Causes:**
- Too many topics for question count
- Topics too broad

**Solutions:**
1. Reduce number of topics (2-3 max)
2. Be more specific (e.g., "bubble sort" not "sorting")
3. Increase question count (15-20)

### Issue: "Some questions off-topic"

**Possible Causes:**
- LLM interpretation
- Related concepts included

**Solutions:**
1. Be very specific in topic names
2. Use exact terms from lecture
3. Regenerate with shuffle

---

## Advanced Usage

### Technique 1: Progressive Difficulty

**Day 1:** `bubble sort` (easy algorithm)
**Day 2:** `merge sort` (medium algorithm)
**Day 3:** `quicksort` (harder algorithm)

### Technique 2: Concept Mastery

**Round 1:** `bubble sort` → Score 60%
**Round 2:** `bubble sort` → Score 80%
**Round 3:** `bubble sort` → Score 95% ✓

### Technique 3: Exam Simulation

**Week Before Exam:**
- Monday: `sorting algorithms`
- Tuesday: `searching algorithms`
- Wednesday: `complexity analysis`
- Thursday: `divide and conquer`
- Friday: (empty) - comprehensive review

### Technique 4: Weak Topic Rotation

From Study Plan: "bubble sort, insertion sort, merge sort"

**Session 1:** `bubble sort` (10 questions)
**Session 2:** `insertion sort` (10 questions)
**Session 3:** `merge sort` (10 questions)
**Session 4:** `bubble sort, insertion sort, merge sort` (15 questions)

---

## FAQ

**Q: How many topics should I enter?**
A: 2-4 topics for 10 questions is ideal. More topics = fewer questions per topic.

**Q: Can I use phrases or just single words?**
A: Both! Use whatever matches your PDF: "bubble sort" or "bubblesort" or "bubble sort algorithm"

**Q: What if I misspell a topic?**
A: The system will try to find related content, but correct spelling works best.

**Q: Can I leave it empty?**
A: Yes! Empty = general coverage across all topics in your PDF.

**Q: Does it work with multiple PDFs?**
A: Yes! Select your PDFs, then enter focused topics. Questions will come from selected PDFs.

**Q: How is this different from regular generation?**
A: Regular = diverse topics. Focused = only your specified topics.

**Q: Can I save my favorite topic combinations?**
A: Not yet, but you can copy-paste from previous sessions!

---

## Summary

### Key Points

✅ **Optional Feature** - Leave empty for general coverage
✅ **Comma-Separated** - Use commas between topics
✅ **2-4 Topics Ideal** - For 10 questions
✅ **Match PDF Content** - Use terms from your lectures
✅ **Works with Study Plans** - Use weak topics
✅ **Shuffle for Variety** - Get new questions on same topics

### Quick Start

1. Enter topics: `bubble sort, merge sort`
2. Click Generate
3. Take focused quiz
4. Score 90%+
5. Move to next topic

**Master your weak areas with focused practice!** 🎯

