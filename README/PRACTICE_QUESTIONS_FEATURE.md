# Practice Questions Feature

## Overview

The Practice Questions feature generates customized practice questions based on your uploaded lecture PDFs using the RAG system. Students can test their understanding with either multiple-choice or open-ended questions.

---

## Features

### 1. **Two Question Types**

#### Multiple Choice
- 4 options (A, B, C, D)
- One correct answer
- Immediate feedback (correct/incorrect)
- Explanation provided
- Page reference for review

#### Open Ended
- Free-text response
- Sample answer provided
- Key points to include
- Page reference for review

### 2. **Intelligent Question Generation**

**Based on lecture content:**
- Questions derived from actual PDF content
- Covers different topics automatically
- Varies difficulty (easy, medium, hard)
- Tests understanding, not just memorization

**Shuffle functionality:**
- Generate new set of questions each time
- Retrieves diverse content from vector database
- Creates fresh questions from different sections

### 3. **Customization Options**

**Question Type:** Choose multiple-choice or open-ended
**Number:** Generate 5-20 questions
**PDF Selection:** Generate from specific PDFs or all uploaded files
**Shuffle:** Create new questions each time

---

## How It Works

### Question Generation Pipeline

1. **Diverse Content Retrieval**
   - Uses 7 different queries to get varied content:
     - "algorithm complexity analysis"
     - "sorting algorithms"
     - "data structures"
     - "algorithm design techniques"
     - "mathematical concepts"
     - "pseudocode and implementation"
     - "problem solving strategies"
   - Retrieves ~15 chunks total
   - Removes duplicates and shuffles

2. **LLM Question Generation**
   - Gemini analyzes the retrieved content
   - Creates questions based on key concepts
   - Ensures questions are clear and unambiguous
   - Generates plausible distractors (for MC)
   - Provides explanations and sample answers

3. **Quality Assurance**
   - Questions must be based on lecture content
   - Each question tagged with topic and difficulty
   - Page references included for review
   - Varied difficulty distribution

---

## User Interface

### Practice Page Layout

```
📝 Practice Questions Generator

[Question Type: ○ Multiple Choice  ○ Open Ended]
[Number of Questions: ━━━━●━━━━━ 10]

Select PDFs for Question Generation:
[☐ lecture_1.pdf (85 pages)]
[☐ lecture_2.pdf (60 pages)]
🔍 Will generate from all 2 PDFs

[🎲 Generate Questions]  [🔀 Shuffle & Regenerate]

────────────────────────────────────────────

📚 Practice Quiz (10 Questions)

Question 1 🟢 Easy
Topic: Sorting Algorithms
What is the time complexity of bubble sort in the worst case?

[● A. O(n)]              [○ B. O(n log n)]
[○ C. O(n²)]             [○ D. O(log n)]

────────────────────────────────────────────

Question 2 🟡 Medium
Topic: Divide and Conquer
Explain how the merge operation works in merge sort.

[Your answer:]
_________________________________
_________________________________

────────────────────────────────────────────

Progress: 2/10        [📤 Submit Quiz]        [🔄 Clear Answers]

────────────────────────────────────────────
AFTER SUBMISSION:

✅ Quiz Submitted!

📊 Your Score
Correct: 8/10    Score: 80%    Grade: 🎉 Excellent!    Incorrect: 2

[🔄 Try Again]  [🔀 New Quiz]  [📥 Export Results]
```

---

## API Endpoint

### POST /practice/generate

**Request:**
```json
{
  "question_type": "multiple-choice",
  "num_questions": 10,
  "pdf_ids": ["uuid1", "uuid2"],
  "shuffle": true
}
```

**Response:**
```json
{
  "success": true,
  "question_type": "multiple-choice",
  "num_questions": 10,
  "questions": [
    {
      "question_number": 1,
      "question_text": "What is the time complexity of bubble sort?",
      "question_type": "multiple-choice",
      "difficulty": "easy",
      "topic": "Sorting Algorithms",
      "page_reference": "Page 6",
      "options": {
        "A": "O(n)",
        "B": "O(n log n)",
        "C": "O(n²)",
        "D": "O(log n)"
      },
      "correct_answer": "C",
      "explanation": "Bubble sort has nested loops..."
    }
  ]
}
```

---

## Usage Examples

### Example 1: Multiple Choice Quiz

**Settings:**
- Type: Multiple Choice
- Number: 10 questions
- PDFs: All

**Generated Questions:**
1. Time complexity questions
2. Algorithm definition questions
3. Comparison questions
4. Best/worst case scenarios
5. Space complexity questions

**Student Experience:**
- Click option buttons to select answers (A, B, C, or D)
- Selected option is highlighted with ●
- Answer all questions
- Click "📤 Submit Quiz"
- Get instant score (e.g., 8/10 = 80%)
- See correct answers highlighted in green (✓)
- See your wrong answers marked (✗)
- Read explanations for each question
- Review page references
- Try again or generate new quiz

### Example 2: Open-Ended Practice

**Settings:**
- Type: Open Ended
- Number: 5 questions
- PDFs: lecture_2.pdf only

**Generated Questions:**
1. "Explain how merge sort works"
2. "Why is divide-and-conquer effective?"
3. "Describe the Master Theorem"
4. "Compare bubble sort and insertion sort"
5. "Analyze the space complexity of merge sort"

**Student Experience:**
- Type detailed answers in text areas
- Answer all questions
- Click "📤 Submit Quiz"
- See all sample answers revealed
- Compare your answers with samples
- Review key points for each question
- Check page references
- Try again or generate new quiz

### Example 3: Targeted Practice

**Settings:**
- Type: Multiple Choice
- Number: 15 questions
- PDFs: Select only "Sorting Algorithms" lecture

**Result:**
- All questions about sorting
- Covers bubble, selection, insertion, merge, quick sort
- Tests complexity, implementation, use cases

---

## Question Quality

### Multiple Choice Questions

**Good Question Example:**
```
Q: What is the worst-case time complexity of merge sort?
A. O(n)
B. O(n log n)  ← Correct
C. O(n²)
D. O(2ⁿ)

Explanation: Merge sort divides the array log n times and merges 
in O(n) time at each level, giving O(n log n) in all cases.
```

**Quality Criteria:**
- ✅ Clear, unambiguous question
- ✅ One definitively correct answer
- ✅ Plausible distractors (not obviously wrong)
- ✅ Tests understanding, not just recall
- ✅ Explanation provided

### Open-Ended Questions

**Good Question Example:**
```
Q: Explain how the divide-and-conquer paradigm works and give an example.

Sample Answer: Divide-and-conquer breaks a problem into smaller 
subproblems, solves them recursively, and combines the solutions. 
For example, merge sort divides an array in half, sorts each half, 
and merges them back together.

Key Points:
- Break problem into subproblems
- Solve recursively
- Combine solutions
- Example with merge sort
```

**Quality Criteria:**
- ✅ Requires explanation, not just facts
- ✅ Tests conceptual understanding
- ✅ Sample answer provides guidance
- ✅ Key points help self-assessment

---

## Features in Detail

### 1. Shuffle & Regenerate

**How it works:**
- Retrieves different chunks from vector database
- Uses randomization for variety
- Generates completely new questions
- Same topics but different questions

**Use cases:**
- Practice multiple times
- Get fresh questions for review
- Test understanding from different angles

### 2. Difficulty Levels

**Easy (🟢):**
- Definition questions
- Basic concepts
- Direct recall

**Medium (🟡):**
- Application questions
- Comparisons
- Analysis

**Hard (🔴):**
- Complex explanations
- Multi-step reasoning
- Synthesis across topics

### 3. Topic Coverage

**Automatic topic detection:**
- Sorting algorithms
- Algorithm analysis
- Design paradigms
- Data structures
- Mathematical concepts
- Implementation details

### 4. Export Functionality

**Export format:**
```
Q1: What is the time complexity of bubble sort?
  A. O(n)
  B. O(n log n)
  C. O(n²)
  D. O(log n)

Topic: Sorting Algorithms
Difficulty: easy
Reference: Page 6

────────────────────────────────────────────
```

**Use cases:**
- Print for offline study
- Share with classmates
- Create study guides
- Save for later review

---

## Integration with Other Features

### With Study Plans
1. Generate study plan
2. For each day's topics, generate practice questions
3. Test understanding before moving to next day

### With Q&A Chat
1. Generate practice questions
2. If you get one wrong, ask the chat for explanation
3. Review the specific page referenced

### With Evaluation
- Use same question generation for creating test sets
- Validate RAG system with generated questions
- Ensure consistent quality

---

## Performance

### Generation Time
- Multiple choice: ~10-15 seconds for 10 questions
- Open-ended: ~10-15 seconds for 10 questions
- Depends on content complexity

### Cost
- ~$0.01-0.02 per 10 questions
- Very affordable for practice
- Gemini 2.0 Flash pricing

### Quality
- Questions based on actual lecture content
- Varied difficulty and topics
- Professional quality
- Suitable for exam preparation

---

## Best Practices

### For Students

1. **Start with Multiple Choice**
   - Quick feedback
   - Build confidence
   - Identify weak areas

2. **Progress to Open-Ended**
   - Deeper understanding
   - Practice explanations
   - Prepare for essay questions

3. **Use Shuffle Regularly**
   - Don't memorize questions
   - Test true understanding
   - Get varied practice

4. **Review Wrong Answers**
   - Read explanation
   - Check page reference
   - Ask chat for more details

### For Instructors

1. **Generate Question Banks**
   - Create large sets of questions
   - Export and curate
   - Use for quizzes or exams

2. **Assess Coverage**
   - Generate questions from each chapter
   - Ensure all topics covered
   - Identify gaps in materials

3. **Difficulty Balancing**
   - Mix of easy, medium, hard
   - Appropriate for student level
   - Progressive difficulty

---

## Troubleshooting

### Issue: Questions Too Easy/Hard

**Solution:**
- Regenerate with shuffle
- System automatically varies difficulty
- Try different PDF selections

### Issue: Questions Repetitive

**Solution:**
- Click "Shuffle & Regenerate"
- Retrieves different chunks
- Creates new questions

### Issue: Questions Not Relevant

**Solution:**
- Check PDF selection
- Ensure PDFs uploaded correctly
- Verify vector database has content

### Issue: No Questions Generated

**Solution:**
- Check backend logs
- Verify PDFs are uploaded
- Ensure API connection working
- Try with fewer questions first

---

## Future Enhancements

Potential improvements:
- [ ] Difficulty level selector
- [ ] Topic-specific question generation
- [ ] Timed quiz mode
- [ ] Score tracking and analytics
- [ ] Spaced repetition scheduling
- [ ] Collaborative quizzes
- [ ] Question quality voting
- [ ] Custom question templates

---

## Conclusion

The Practice Questions feature:
- ✅ Generates high-quality questions from your PDFs
- ✅ Supports multiple question types
- ✅ Provides immediate feedback
- ✅ Helps students test understanding
- ✅ Integrates with study plans
- ✅ Fully automated and intelligent

**Result:** A complete practice system for effective learning! 📚

