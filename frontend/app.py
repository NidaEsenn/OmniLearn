import streamlit as st
import requests
import json
import pandas as pd

# Constants
API_URL = "http://localhost:8001"
MAX_PDFS = 4
MAX_TOTAL_PAGES = 400

st.set_page_config(page_title="Lecture Assistant AI", layout="wide")

st.title("📚 OmniLearn: Study Companion")

# Initialize session state
if "uploaded_pdfs" not in st.session_state:
    st.session_state.uploaded_pdfs = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_pdf_ids" not in st.session_state:
    st.session_state.selected_pdf_ids = []

# Function to fetch uploaded PDFs from backend
def fetch_pdfs():
    try:
        response = requests.get(f"{API_URL}/pdfs")
        if response.status_code == 200:
            st.session_state.uploaded_pdfs = response.json()
        else:
            st.session_state.uploaded_pdfs = []
    except Exception as e:
        st.error(f"Error fetching PDFs: {e}")
        st.session_state.uploaded_pdfs = []

# Fetch PDFs on load
fetch_pdfs()

# Sidebar for PDF Management
with st.sidebar:
    st.header("📄 PDF Management")
    
    # Display current stats
    total_pdfs = len(st.session_state.uploaded_pdfs)
    total_pages = sum(pdf["page_count"] for pdf in st.session_state.uploaded_pdfs)
    
    st.metric("Uploaded PDFs", f"{total_pdfs}/{MAX_PDFS}")
    st.metric("Total Pages", f"{total_pages}/{MAX_TOTAL_PAGES}")
    
    st.divider()
    
    # Upload section
    st.subheader("Upload New PDF")
    
    if total_pdfs >= MAX_PDFS:
        st.warning(f"⚠️ Maximum {MAX_PDFS} PDFs reached. Delete a file to upload more.")
    elif total_pages >= MAX_TOTAL_PAGES:
        st.warning(f"⚠️ Page limit ({MAX_TOTAL_PAGES}) reached.")
    else:
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            key="pdf_uploader"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Upload & Process", type="primary"):
                with st.spinner("Uploading and processing..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                        response = requests.post(f"{API_URL}/upload", files=files)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Uploaded: {data['filename']}")
                            st.info(f"📄 Pages: {data['page_count']} | 📦 Chunks: {data['chunk_count']}")
                            fetch_pdfs()  # Refresh the list
                            st.rerun()
                        else:
                            error_detail = response.json().get("detail", response.text)
                            st.error(f"❌ Upload failed: {error_detail}")
                    except Exception as e:
                        st.error(f"❌ Error connecting to backend: {e}")
    
    st.divider()
    
    # List uploaded PDFs
    st.subheader("Uploaded Files")
    
    if not st.session_state.uploaded_pdfs:
        st.info("No PDFs uploaded yet.")
    else:
        for pdf in st.session_state.uploaded_pdfs:
            with st.expander(f"📄 {pdf['filename']}", expanded=False):
                st.write(f"**Title:** {pdf['title']}")
                st.write(f"**Pages:** {pdf['page_count']}")
                st.write(f"**Chunks:** {pdf['chunk_count']}")
                st.code(pdf['pdf_id'], language=None)
                
                if st.button(f"🗑️ Delete", key=f"del_{pdf['pdf_id']}"):
                    try:
                        response = requests.delete(f"{API_URL}/pdfs/{pdf['pdf_id']}")
                        if response.status_code == 200:
                            st.success("Deleted successfully!")
                            fetch_pdfs()
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        st.divider()
        
        # Clear all button
        if st.button("🗑️ Delete All PDFs", type="secondary"):
            try:
                response = requests.delete(f"{API_URL}/pdfs")
                if response.status_code == 200:
                    st.success("All PDFs deleted!")
                    fetch_pdfs()
                    st.session_state.messages = []  # Clear chat history
                    st.rerun()
                else:
                    st.error(f"Failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["💬 Q&A Chat", "📅 Study Plan Generator", "📝 Practice Questions"])

# Tab 1: Q&A Chat
with tab1:
    st.header("Ask Questions about Your Lectures")
    
    # PDF selection for chat
    if st.session_state.uploaded_pdfs:
        st.subheader("Select PDFs to Query")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            # Multiselect for PDFs
            pdf_options = {pdf['pdf_id']: f"{pdf['filename']} ({pdf['page_count']} pages)" 
                          for pdf in st.session_state.uploaded_pdfs}
            
            selected = st.multiselect(
                "Choose which PDFs to search (leave empty to search all)",
                options=list(pdf_options.keys()),
                format_func=lambda x: pdf_options[x],
                key="pdf_selector"
            )
            
            st.session_state.selected_pdf_ids = selected if selected else []
        
        with col2:
            if st.button("🔄 Search All PDFs"):
                st.session_state.selected_pdf_ids = []
                st.rerun()
        
        if st.session_state.selected_pdf_ids:
            st.info(f"🔍 Searching {len(st.session_state.selected_pdf_ids)} selected PDF(s)")
        else:
            st.info(f"🔍 Searching all {len(st.session_state.uploaded_pdfs)} PDF(s)")
    
    st.divider()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📚 View Sources"):
                    for src in message["sources"]:
                        filename = src['metadata'].get('filename', 'Unknown')
                        page_nums = src['metadata'].get('page_numbers', '?')
                        chunk_id = src['metadata'].get('chunk_id', '?')
                        st.markdown(f"- **{filename}** - Page {page_nums} (Chunk {chunk_id})")

    # Chat input
    if prompt := st.chat_input("Ask a question about your lectures..."):
        if not st.session_state.uploaded_pdfs:
            st.error("❌ Please upload at least one PDF first.")
        else:
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        payload = {
                            "question": prompt,
                            "pdf_ids": st.session_state.selected_pdf_ids if st.session_state.selected_pdf_ids else None
                        }
                        response = requests.post(f"{API_URL}/chat", json=payload)
                        
                        if response.status_code == 200:
                            data = response.json()
                            answer = data["answer"]
                            sources = data["source_documents"]
                            
                            st.markdown(answer)
                            
                            if sources:
                                with st.expander("📚 View Sources"):
                                    for src in sources:
                                        filename = src['metadata'].get('filename', 'Unknown')
                                        page_nums = src['metadata'].get('page_numbers', '?')
                                        chunk_id = src['metadata'].get('chunk_id', '?')
                                        st.markdown(f"- **{filename}** - Page {page_nums} (Chunk {chunk_id})")
                            
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": answer,
                                "sources": sources
                            })
                        else:
                            error_detail = response.json().get("detail", response.text)
                            st.error(f"❌ Error: {error_detail}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")

# Tab 2: Study Planner
with tab2:
    st.header("Generate Personalized Study Plan")
    
    if not st.session_state.uploaded_pdfs:
        st.warning("⚠️ Please upload at least one PDF to generate a study plan.")
    else:
        # Select PDF for study plan
        st.subheader("Select PDF for Study Plan")
        pdf_options = {pdf['pdf_id']: f"{pdf['filename']} ({pdf['page_count']} pages)" 
                      for pdf in st.session_state.uploaded_pdfs}
        
        selected_pdf_id = st.selectbox(
            "Choose a PDF",
            options=list(pdf_options.keys()),
            format_func=lambda x: pdf_options[x]
        )
        
        st.divider()
        
        # Basic parameters
        col1, col2, col3 = st.columns(3)
        with col1:
            days = st.number_input("Total Days", min_value=1, max_value=30, value=5)
        with col2:
            minutes = st.number_input("Daily Minutes", min_value=15, step=15, value=60)
        with col3:
            level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], index=1)
        
        # Advanced parameters
        with st.expander("⚙️ Advanced Options"):
            goal = st.text_input(
                "Your Goal",
                value="understand the material",
                help="e.g., 'pass the exam', 'get an A', 'build intuition'"
            )
            weak_topics = st.text_input(
                "Topics You Feel Weak In",
                value="",
                help="Enter multiple topics separated by commas, 'and', or semicolons. Examples: 'bubble sort, merge sort' or 'dynamic programming and graph algorithms'"
            )
            
            # Show parsed topics
            if weak_topics:
                # Parse topics the same way the backend does
                parsed = weak_topics.lower().replace(" and ", ", ").replace(";", ",").replace("/", ",")
                topics_list = [t.strip() for t in parsed.split(",") if t.strip()]
                if topics_list:
                    st.info(f"📌 Weak topics detected: {', '.join(topics_list)}")
            
            deadline_context = st.text_input(
                "Deadline Context",
                value="upcoming exam",
                help="e.g., 'final exam in algorithms on Dec 20'"
            )
        
        if st.button("📅 Generate Plan", type="primary"):
            with st.spinner("Generating personalized study plan..."):
                try:
                    payload = {
                        "pdf_id": selected_pdf_id,
                        "total_days": days,
                        "daily_minutes": minutes,
                        "level": level,
                        "goal": goal,
                        "weak_topics": weak_topics,
                        "deadline_context": deadline_context
                    }
                    response = requests.post(f"{API_URL}/study-plan", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        plan_data = data.get("plan", {})
                        
                        if plan_data and "days" in plan_data:
                            st.success("✅ Study plan generated!")
                            
                            # Display summary
                            summary = plan_data.get("summary", {})
                            if summary:
                                st.subheader("📊 Plan Summary")
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("Total Days", summary.get("total_days", days))
                                col2.metric("Total Minutes", summary.get("total_estimated_minutes", 0))
                                col3.metric("Review Days", summary.get("review_days", 0))
                                col4.metric("Topics", len(summary.get("topics_covered", [])))
                                
                                if summary.get("plan_style"):
                                    st.info(f"**Style:** {summary['plan_style']}")
                                if summary.get("notes"):
                                    st.warning(f"**Notes:** {summary['notes']}")
                            
                            # Display warnings
                            warnings = plan_data.get("warnings", [])
                            if warnings:
                                for warning in warnings:
                                    st.warning(f"⚠️ {warning}")
                            
                            st.divider()
                            
                            # Display day-by-day plan
                            st.subheader("📅 Day-by-Day Schedule")
                            st.caption("Expand each day to see detailed tasks and activities")
                            
                            for day_plan in plan_data.get("days", []):
                                day_num = day_plan.get("day", 0)
                                focus = day_plan.get("focus", "")
                                total_min = day_plan.get("estimated_total_minutes", 0)
                                
                                # Create a cleaner focus description
                                focus_clean = focus[:100] + "..." if len(focus) > 100 else focus
                                
                                with st.expander(f"**Day {day_num}** - {focus_clean} ({total_min} min)", expanded=(day_num == 1)):
                                    # Study blocks
                                    study_blocks = day_plan.get("study_blocks", [])
                                    if study_blocks:
                                        st.markdown("### 📖 Study Blocks")
                                        for idx, block in enumerate(study_blocks, 1):
                                            chapter = block.get('chapter', 'N/A')
                                            section_title = block.get('section_title', 'N/A')
                                            minutes = block.get('estimated_minutes', 0)
                                            
                                            # Clean up section title - remove code/math fences and truncate
                                            section_clean = section_title.replace('```pseudo', '').replace('```', '').replace('$$', '').strip()
                                            if len(section_clean) > 100:
                                                section_clean = section_clean[:97] + "..."
                                            
                                            # Use a nice container for each block
                                            with st.container():
                                                col1, col2 = st.columns([4, 1])
                                                with col1:
                                                    st.markdown(f"**📚 Block {idx}:** {section_clean}")
                                                with col2:
                                                    st.metric("Time", f"{minutes} min", label_visibility="collapsed")
                                                
                                                tasks = block.get("tasks", [])
                                                if tasks:
                                                    st.markdown("**Tasks:**")
                                                    for task in tasks:
                                                        st.markdown(f"✓ {task}")
                                                
                                                if idx < len(study_blocks):
                                                    st.divider()
                                    
                                    # Review blocks
                                    review_blocks = day_plan.get("review_blocks", [])
                                    if review_blocks and any(block.get('estimated_minutes', 0) > 0 for block in review_blocks):
                                        st.markdown("### 🔄 Review Blocks")
                                        for idx, block in enumerate(review_blocks, 1):
                                            topics = block.get("topics", [])
                                            topics_str = ", ".join(topics) if isinstance(topics, list) else str(topics)
                                            minutes = block.get('estimated_minutes', 0)
                                            
                                            if minutes > 0:  # Only show if there's actual time allocated
                                                with st.container():
                                                    col1, col2 = st.columns([4, 1])
                                                    with col1:
                                                        st.markdown(f"**🔁 Review:** {topics_str}")
                                                    with col2:
                                                        st.metric("Time", f"{minutes} min", label_visibility="collapsed")
                                                    
                                                    tasks = block.get("tasks", [])
                                                    if tasks:
                                                        st.markdown("**Tasks:**")
                                                        for task in tasks:
                                                            st.markdown(f"✓ {task}")
                                                    
                                                    if idx < len(review_blocks):
                                                        st.divider()
                        else:
                            st.warning("⚠️ No plan generated. Try again.")
                    else:
                        error_detail = response.json().get("detail", response.text)
                        st.error(f"❌ Error: {error_detail}")
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# Tab 3: Practice Questions
with tab3:
    st.header("📝 Practice Questions Generator")
    
    if not st.session_state.uploaded_pdfs:
        st.warning("⚠️ Please upload at least one PDF to generate practice questions.")
    else:
        st.markdown("""
        Generate practice questions based on your lecture materials to test your understanding!
        The system will create questions from different topics covered in your PDFs.
        """)
        
        st.divider()
        
        # Question settings
        col1, col2 = st.columns(2)
        
        with col1:
            question_type = st.radio(
                "📋 Question Type",
                options=["multiple-choice", "open-ended"],
                format_func=lambda x: "Multiple Choice" if x == "multiple-choice" else "Open Ended",
                horizontal=True
            )
        
        with col2:
            num_questions = st.slider(
                "🔢 Number of Questions",
                min_value=5,
                max_value=20,
                value=10,
                step=1
            )
        
        # Focused Topics (Optional)
        st.subheader("🎯 Focused Topics (Optional)")
        st.markdown("Enter specific topics to focus on, or leave empty for general coverage.")
        
        focused_topics_input = st.text_input(
            "Topics (comma-separated)",
            placeholder="e.g., bubble sort, merge sort, time complexity",
            help="Enter topics separated by commas. Questions will focus on these topics.",
            key="focused_topics_input"
        )
        
        # Parse focused topics
        focused_topics = []
        if focused_topics_input.strip():
            focused_topics = [topic.strip() for topic in focused_topics_input.split(",") if topic.strip()]
            if focused_topics:
                st.info(f"🎯 Will focus on: {', '.join(focused_topics)}")
        
        st.divider()
        
        # PDF selection
        st.subheader("📚 Select PDFs for Question Generation")
        pdf_options = {pdf['pdf_id']: f"{pdf['filename']} ({pdf['page_count']} pages)" 
                      for pdf in st.session_state.uploaded_pdfs}
        
        selected_pdfs = st.multiselect(
            "Choose PDFs (leave empty to use all)",
            options=list(pdf_options.keys()),
            format_func=lambda x: pdf_options[x],
            key="practice_pdf_selector"
        )
        
        if not selected_pdfs:
            st.info(f"🔍 Will generate questions from all {len(st.session_state.uploaded_pdfs)} PDF(s)")
        else:
            st.info(f"🔍 Will generate questions from {len(selected_pdfs)} selected PDF(s)")
        
        st.divider()
        
        # Generate button
        col1, col2 = st.columns([1, 3])
        with col1:
            generate_btn = st.button("🎲 Generate Questions", type="primary", use_container_width=True)
        with col2:
            shuffle_btn = st.button("🔀 Shuffle & Regenerate", type="secondary", use_container_width=True)
        
        # Generate or shuffle
        if generate_btn or shuffle_btn:
            with st.spinner(f"Generating {num_questions} {question_type} questions..."):
                try:
                    payload = {
                        "question_type": question_type,
                        "num_questions": num_questions,
                        "pdf_ids": selected_pdfs if selected_pdfs else None,
                        "shuffle": True,
                        "focused_topics": focused_topics if focused_topics else None
                    }
                    
                    response = requests.post(f"{API_URL}/practice/generate", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("success"):
                            questions = data.get("questions", [])
                            used_focused_topics = data.get("focused_topics", [])
                            
                            # Store in session state
                            st.session_state.practice_questions = questions
                            st.session_state.practice_answers = {}  # Reset answers
                            st.session_state.quiz_focused_topics = used_focused_topics
                            
                            success_msg = f"✅ Generated {len(questions)} questions!"
                            if used_focused_topics:
                                success_msg += f" (Focused on: {', '.join(used_focused_topics)})"
                            st.success(success_msg)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {data.get('error', 'Unknown error')}")
                    else:
                        error_detail = response.json().get("detail", response.text)
                        st.error(f"❌ Error: {error_detail}")
                        
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")
        
        # Display generated questions
        if "practice_questions" in st.session_state and st.session_state.practice_questions:
            st.divider()
            
            # Show quiz header with focused topics if applicable
            quiz_header = f"📚 Practice Quiz ({len(st.session_state.practice_questions)} Questions)"
            st.subheader(quiz_header)
            
            # Display focused topics if used
            if "quiz_focused_topics" in st.session_state and st.session_state.quiz_focused_topics:
                topics_display = ", ".join(st.session_state.quiz_focused_topics)
                st.info(f"🎯 **Focused Topics:** {topics_display}")
            
            questions = st.session_state.practice_questions
            q_type = questions[0].get("question_type", "") if questions else ""
            
            # Initialize session state
            if "practice_answers" not in st.session_state:
                st.session_state.practice_answers = {}
            if "quiz_submitted" not in st.session_state:
                st.session_state.quiz_submitted = False
            
            # Display each question
            for idx, q in enumerate(questions):
                q_num = q.get("question_number", idx + 1)
                q_text = q.get("question_text", "")
                q_type_current = q.get("question_type", "")
                difficulty = q.get("difficulty", "medium")
                topic = q.get("topic", "General")
                
                # Difficulty badge color
                diff_color = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(difficulty, "⚪")
                
                with st.container():
                    st.markdown(f"### Question {q_num} {diff_color} {difficulty.title()}")
                    st.markdown(f"**Topic:** {topic}")
                    st.markdown(f"**{q_text}**")
                    
                    if q_type_current == "multiple-choice":
                        # Multiple choice options with clickable buttons
                        options = q.get("options", {})
                        correct_answer = q.get("correct_answer", "")
                        
                        # Create columns for options (2x2 grid)
                        col1, col2 = st.columns(2)
                        
                        option_keys = list(options.keys())
                        for i, option_key in enumerate(option_keys):
                            col = col1 if i % 2 == 0 else col2
                            
                            with col:
                                # Check if this option is selected
                                is_selected = st.session_state.practice_answers.get(q_num) == option_key
                                
                                # Button styling based on selection and submission
                                if st.session_state.quiz_submitted:
                                    # After submission, show correct/incorrect
                                    if option_key == correct_answer:
                                        button_type = "primary"
                                        button_label = f"✓ {option_key}. {options[option_key]}"
                                    elif is_selected and option_key != correct_answer:
                                        button_type = "secondary"
                                        button_label = f"✗ {option_key}. {options[option_key]}"
                                    else:
                                        button_type = "secondary"
                                        button_label = f"{option_key}. {options[option_key]}"
                                else:
                                    # Before submission, highlight selected
                                    button_type = "primary" if is_selected else "secondary"
                                    button_label = f"{'●' if is_selected else '○'} {option_key}. {options[option_key]}"
                                
                                if st.button(
                                    button_label,
                                    key=f"btn_{q_num}_{option_key}",
                                    type=button_type,
                                    use_container_width=True,
                                    disabled=st.session_state.quiz_submitted
                                ):
                                    if not st.session_state.quiz_submitted:
                                        st.session_state.practice_answers[q_num] = option_key
                                        st.rerun()
                        
                        # Show explanation after submission
                        if st.session_state.quiz_submitted:
                            explanation = q.get("explanation", "")
                            page_ref = q.get("page_reference", "")
                            
                            if st.session_state.practice_answers.get(q_num) == correct_answer:
                                st.success("✅ Correct!")
                            else:
                                st.error(f"❌ Incorrect. Correct answer: {correct_answer}")
                            
                            if explanation:
                                st.info(f"💡 **Explanation:** {explanation}")
                            if page_ref:
                                st.caption(f"📖 Reference: {page_ref}")
                    
                    elif q_type_current == "open-ended":
                        # Text area for answer
                        user_answer = st.text_area(
                            "Your answer:",
                            key=f"answer_{q_num}",
                            height=100,
                            placeholder="Type your answer here...",
                            disabled=st.session_state.quiz_submitted
                        )
                        
                        st.session_state.practice_answers[q_num] = user_answer
                        
                        # Show sample answer after submission
                        if st.session_state.quiz_submitted:
                            sample = q.get("sample_answer", "")
                            key_points = q.get("key_points", [])
                            page_ref = q.get("page_reference", "")
                            
                            st.markdown("---")
                            st.markdown("**📝 Sample Answer:**")
                            if sample:
                                st.info(sample)
                            
                            if key_points:
                                st.markdown("**Key Points to Include:**")
                                for point in key_points:
                                    st.markdown(f"✓ {point}")
                            
                            if page_ref:
                                st.caption(f"📖 Reference: {page_ref}")
                    
                    st.divider()
            
            # Submit/Results section
            st.divider()
            
            if not st.session_state.quiz_submitted:
                # Before submission - show submit button
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    answered = len([a for a in st.session_state.practice_answers.values() if a])
                    st.metric("Progress", f"{answered}/{len(questions)}")
                
                with col2:
                    if st.button("📤 Submit Quiz", type="primary", use_container_width=True):
                        if answered < len(questions):
                            st.warning(f"⚠️ You've only answered {answered}/{len(questions)} questions. Submit anyway?")
                        st.session_state.quiz_submitted = True
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Clear Answers", use_container_width=True):
                        st.session_state.practice_answers = {}
                        st.rerun()
            
            else:
                # After submission - show results
                st.success("✅ Quiz Submitted!")
                
                # Calculate score for multiple choice
                if q_type == "multiple-choice":
                    correct_count = 0
                    total_answered = 0
                    
                    for q in questions:
                        q_num = q.get("question_number", 0)
                        correct_answer = q.get("correct_answer", "")
                        user_answer = st.session_state.practice_answers.get(q_num)
                        
                        if user_answer:
                            total_answered += 1
                            if user_answer == correct_answer:
                                correct_count += 1
                    
                    # Display score
                    score_percentage = (correct_count / total_answered * 100) if total_answered > 0 else 0
                    
                    st.markdown("### 📊 Your Score")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Correct", f"{correct_count}/{total_answered}")
                    with col2:
                        st.metric("Score", f"{score_percentage:.0f}%")
                    with col3:
                        grade = "🎉 Excellent!" if score_percentage >= 80 else "👍 Good!" if score_percentage >= 60 else "📚 Keep studying!"
                        st.metric("Grade", grade)
                    with col4:
                        wrong = total_answered - correct_count
                        st.metric("Incorrect", wrong)
                
                else:
                    # Open-ended - just show completion
                    answered = len([a for a in st.session_state.practice_answers.values() if a])
                    st.markdown("### 📊 Completion")
                    st.metric("Answered", f"{answered}/{len(questions)}")
                    st.info("💡 Review the sample answers above to check your responses.")
                
                st.divider()
                
                # Action buttons after submission
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 Try Again", type="primary", use_container_width=True):
                        st.session_state.quiz_submitted = False
                        st.session_state.practice_answers = {}
                        st.rerun()
                
                with col2:
                    if st.button("🔀 New Quiz", type="secondary", use_container_width=True):
                        st.session_state.quiz_submitted = False
                        st.session_state.practice_answers = {}
                        st.session_state.practice_questions = []
                        st.rerun()
                
                with col3:
                    # Export with answers
                    export_text = f"PRACTICE QUIZ RESULTS\n{'='*80}\n\n"
                    
                    if q_type == "multiple-choice":
                        correct_count = sum(
                            1 for q in questions 
                            if st.session_state.practice_answers.get(q.get("question_number")) == q.get("correct_answer")
                        )
                        export_text += f"Score: {correct_count}/{len(questions)}\n\n"
                    
                    for q in questions:
                        q_num = q.get('question_number')
                        export_text += f"Q{q_num}: {q.get('question_text')}\n"
                        
                        if q.get('question_type') == 'multiple-choice':
                            for key, val in q.get('options', {}).items():
                                marker = " ✓" if key == q.get('correct_answer') else ""
                                user_marker = " (Your answer)" if key == st.session_state.practice_answers.get(q_num) else ""
                                export_text += f"  {key}. {val}{marker}{user_marker}\n"
                            export_text += f"\nExplanation: {q.get('explanation', 'N/A')}\n"
                        else:
                            export_text += f"\nYour answer: {st.session_state.practice_answers.get(q_num, 'Not answered')}\n"
                            export_text += f"\nSample answer: {q.get('sample_answer', 'N/A')}\n"
                        
                        export_text += f"Reference: {q.get('page_reference', 'N/A')}\n\n"
                        export_text += "-" * 80 + "\n\n"
                    
                    st.download_button(
                        label="📥 Export Results",
                        data=export_text,
                        file_name="quiz_results.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
