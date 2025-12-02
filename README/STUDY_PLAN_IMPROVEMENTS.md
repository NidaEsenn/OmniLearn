# Enhanced Study Plan Generator

## Overview
The study plan generator has been significantly improved with a comprehensive, university-level coaching prompt that creates realistic, time-bounded study plans.

## Key Improvements

### 1. Enhanced Prompt System
The new prompt is designed as an **expert university-level study coach** specializing in algorithms and theoretical computer science.

### 2. Student Profile Parameters

**New Input Fields:**
- **Level**: Beginner, Intermediate, Advanced
- **Goal**: e.g., "pass the exam", "get an A", "build intuition"
- **Weak Topics**: Topics the student feels weak in (prioritized in the plan)
- **Deadline Context**: e.g., "final exam in algorithms on Dec 20"
- **Total Days**: Number of days available
- **Daily Minutes**: Study time available per day

### 3. Structured Section Analysis

The system now parses lecture content into structured sections with:
- **ID**: Unique identifier
- **Chapter**: Major topic name
- **Title**: Section/subtopic title
- **Pages**: Page range `[start, end]`
- **Difficulty**: 1 (easy), 2 (medium), 3 (hard)
- **Priority**: "core", "important", or "optional"
- **Estimated Minutes**: Time needed for the section

### 4. Intelligent Planning Features

**Time Constraint Respect:**
- Ensures plan fits within `total_days × daily_minutes`
- Prioritizes core and important sections
- Compresses or omits optional sections when time is tight
- Provides warnings when constraints are too tight

**Level Adaptation:**
- **Beginner**: Slower pace, more review, fewer topics per day
- **Intermediate**: Balanced pace, mixed content and review
- **Advanced**: Dense coverage, challenging tasks, less repetition

**Weak Topic Highlighting:**
- Weak topics appear earlier in the plan
- Receive extra time and more review blocks

**Spaced Review:**
- Short review blocks on later days
- At least one of the last two days is review-focused
- Mock-exam style preparation

**Concrete Tasks:**
- Specific, actionable tasks for each day
- Examples:
  - "Read slides 10–18 of Chapter 2 and write a 3-bullet summary"
  - "Solve 3 practice questions on recurrences"
  - "Explain Dijkstra's algorithm in your own words in 5–6 sentences"

### 5. Enhanced Output Format

**New JSON Structure:**
```json
{
  "summary": {
    "total_days": 5,
    "total_estimated_minutes": 300,
    "topics_covered": ["Sorting", "Graph Algorithms"],
    "review_days": 2,
    "plan_style": "Intermediate-level exam-focused plan",
    "notes": "Optional sections on advanced topics were omitted due to time constraints."
  },
  "days": [
    {
      "day": 1,
      "focus": "Introduction to Sorting Algorithms",
      "estimated_total_minutes": 60,
      "study_blocks": [
        {
          "type": "study",
          "chapter": "Chapter 2: Sorting",
          "section_title": "Bubble Sort and Selection Sort",
          "section_ids": [1, 2],
          "estimated_minutes": 50,
          "tasks": [
            "Read slides 10-18 on Bubble Sort",
            "Write pseudocode for Selection Sort",
            "Compare time complexities"
          ]
        }
      ],
      "review_blocks": [
        {
          "type": "review",
          "source_days": [],
          "topics": [],
          "estimated_minutes": 10,
          "tasks": ["Quick review of Big-O notation"]
        }
      ]
    }
  ],
  "warnings": [
    "Available time is low; some optional sections were omitted."
  ]
}
```

### 6. UI Enhancements

**New Frontend Features:**
- Advanced options expander for goal, weak topics, and deadline
- Summary metrics display (total days, minutes, review days, topics)
- Plan style and notes display
- Warning messages for tight constraints
- Day-by-day expandable schedule
- Separate study blocks and review blocks
- Concrete task lists for each block

## API Changes

### Updated Endpoint

**POST /study-plan**

**Request:**
```json
{
  "pdf_id": "uuid",
  "total_days": 5,
  "daily_minutes": 60,
  "level": "Intermediate",
  "goal": "get an A",
  "weak_topics": "dynamic programming, graph algorithms",
  "deadline_context": "final exam on Dec 20"
}
```

**Response:**
```json
{
  "plan": {
    "summary": { ... },
    "days": [ ... ],
    "warnings": [ ... ]
  }
}
```

## Usage Example

### From the UI:

1. **Select a PDF** from the uploaded files
2. **Set basic parameters**:
   - Total Days: 7
   - Daily Minutes: 90
   - Level: Intermediate
3. **Expand Advanced Options**:
   - Goal: "get an A on the final exam"
   - Weak Topics: "dynamic programming, greedy algorithms"
   - Deadline: "final exam on December 15"
4. **Click "Generate Plan"**
5. **Review the plan**:
   - Check summary metrics
   - Read any warnings
   - Expand each day to see specific tasks
   - Follow the concrete, actionable tasks

### From the API:

```python
import requests

payload = {
    "pdf_id": "your-pdf-id",
    "total_days": 7,
    "daily_minutes": 90,
    "level": "Intermediate",
    "goal": "get an A on the final exam",
    "weak_topics": "dynamic programming, greedy algorithms",
    "deadline_context": "final exam on December 15"
}

response = requests.post("http://localhost:8001/study-plan", json=payload)
plan = response.json()["plan"]

# Access summary
print(f"Plan Style: {plan['summary']['plan_style']}")
print(f"Topics Covered: {plan['summary']['topics_covered']}")

# Access daily tasks
for day in plan['days']:
    print(f"\nDay {day['day']}: {day['focus']}")
    for block in day['study_blocks']:
        print(f"  Study: {block['section_title']}")
        for task in block['tasks']:
            print(f"    - {task}")
```

## Quality Checks

The system enforces:
- ✅ Realistic per-day time (adheres to `daily_minutes` ± 15%)
- ✅ Weak topics appear with extra attention
- ✅ At least one final day is review-focused
- ✅ Clear warnings when constraints are tight
- ✅ Only uses sections that exist in the PDF
- ✅ Concrete, actionable tasks (not just topic names)

## Fallback Behavior

If plan generation fails:
- Returns a minimal fallback plan
- Includes error details in summary notes
- Provides warnings array with error message
- Ensures the system doesn't crash

## Future Enhancements

Potential improvements:
- [ ] More sophisticated section parsing (detect headings, TOC)
- [ ] Practice problem recommendations
- [ ] Integration with external resources (YouTube, textbooks)
- [ ] Progress tracking (mark days as complete)
- [ ] Adaptive replanning (adjust based on progress)
- [ ] Export to calendar (iCal, Google Calendar)
- [ ] Collaborative study plans (share with classmates)

