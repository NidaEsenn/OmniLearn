# Study Plan UI Display Fix

## Problem
The study plan output was showing raw content with:
- Code fences: ` ```pseudo `
- Math delimiters: `$$`
- Very long, truncated section titles
- Poor visual hierarchy
- Cluttered layout

**Example of the issue:**
```
Chapter 4 - $$ Discussion 1: Utilize the provided algorithms for three sorting methods, execute them line by li (40 min)
```

## Solution

### 1. Content Cleaning
**Frontend (`frontend/app.py`):**
- Strip code fences (` ```pseudo `, ` ``` `)
- Remove math delimiters (`$$`)
- Truncate long titles to 100 characters with "..."
- Clean up newlines and extra whitespace

**Backend (`app/study_plans/planner.py`):**
- Skip code/math fence lines when extracting titles
- Use first meaningful line as section title
- Clean titles before adding to sections JSON
- Limit title length at source

### 2. Visual Improvements

**Before:**
```
📖 Study Blocks:
Chapter 4 - $$ Discussion 1: Utilize... (40 min)
- Task 1
- Task 2
```

**After:**
```
### 📖 Study Blocks

📚 Block 1: Discussion on sorting algorithms
📂 Chapter 4                                    Time: 40 min

Tasks:
✓ Task 1
✓ Task 2
─────────────────────────────────────────────────────
```

### 3. Layout Enhancements

**New Structure:**
- **Headers**: Clear section headers with icons (📖, 🔄)
- **Containers**: Each block in its own visual container
- **Two-column layout**: Title on left, time metric on right
- **Chapter badges**: Optional chapter info as caption
- **Task lists**: Checkmark bullets (✓) for tasks
- **Dividers**: Clean separation between blocks
- **Smart filtering**: Only show review blocks with time > 0

### 4. Better Organization

**Day Expander:**
```
Day 1 - Understanding quadratic sorting algorithms... (60 min)
  ↓ [Expand]
  
  ### 📖 Study Blocks
  [Block 1 container]
  [Block 2 container]
  
  ### 🔄 Review Blocks
  [Review 1 container]
```

## Code Changes

### Frontend (`frontend/app.py`)

**Key improvements:**
1. **Title cleaning:**
```python
section_clean = section_title.replace('```pseudo', '').replace('```', '').replace('$$', '').strip()
if len(section_clean) > 100:
    section_clean = section_clean[:97] + "..."
```

2. **Two-column layout:**
```python
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f"**📚 Block {idx}:** {section_clean}")
with col2:
    st.metric("Time", f"{minutes} min")
```

3. **Task formatting:**
```python
for task in tasks:
    st.markdown(f"✓ {task}")
```

### Backend (`app/study_plans/planner.py`)

**Key improvements:**
1. **Skip fence lines:**
```python
if line.startswith('```') or line.startswith('$$'):
    continue
```

2. **Clean titles:**
```python
section_title = section_title.replace('```pseudo', '').replace('```', '').replace('$$', '')
section_title = section_title.replace('\n', ' ').strip()
```

3. **Length limits:**
```python
if len(section_title) > 100:
    section_title = section_title[:97] + "..."
```

## Visual Comparison

### Before:
```
Day 1 - Understanding quadratic sorting algorithms (Bubble, Insertion, Selection Sort) and Merge Sort fundamentals. (60 min)

📖 Study Blocks:

Chapter 4 - $$ Discussion 1: Utilize the provided algorithms for three sorting methods, execute them line by li (40 min)

Read the section on quadratic sorts (Bubble, Insertion, Selection).
Implement each of the three sorting algorithms...
```

### After:
```
Day 1 - Understanding quadratic sorting algorithms... (60 min)

### 📖 Study Blocks

📚 Block 1: Discussion on sorting algorithms
📂 Chapter 4                                    Time: 40 min

Tasks:
✓ Read the section on quadratic sorts (Bubble, Insertion, Selection)
✓ Implement each of the three sorting algorithms...
─────────────────────────────────────────────────────
```

## Benefits

1. **Cleaner**: No raw markup visible to users
2. **Readable**: Better visual hierarchy and spacing
3. **Professional**: Polished, modern UI
4. **Scannable**: Easy to quickly review the plan
5. **Organized**: Clear separation between blocks
6. **Informative**: Time metrics prominently displayed

## Testing

### Test the fix:
1. Restart backend and frontend
2. Generate a study plan
3. Verify:
   - ✅ No `$$` or ` ```pseudo ` visible
   - ✅ Titles are truncated nicely
   - ✅ Time is shown as a metric on the right
   - ✅ Tasks have checkmark bullets
   - ✅ Clean dividers between blocks
   - ✅ Chapter info shown as caption

## Files Modified

1. **frontend/app.py**
   - Content cleaning logic
   - Two-column layout with metrics
   - Better container structure
   - Task formatting with checkmarks
   - Smart filtering for review blocks

2. **app/study_plans/planner.py**
   - Skip fence lines during extraction
   - Clean titles at source
   - Better title selection logic
   - Length limits enforced

## Future Enhancements

- [ ] Collapsible task lists for long blocks
- [ ] Progress tracking (mark tasks as done)
- [ ] Export to PDF with formatting
- [ ] Print-friendly view
- [ ] Color coding by difficulty
- [ ] Icons for different block types

