import os
import uuid
import streamlit as st

# Set API key from Streamlit secrets BEFORE importing app modules
try:
    for key_name in ["GOOGLE_API_KEY", "GEMINI_API_KEY"]:
        if key_name in st.secrets:
            os.environ["GOOGLE_API_KEY"] = st.secrets[key_name]
            break
except Exception:
    pass

# Check if API key is available
if not os.environ.get("GOOGLE_API_KEY"):
    st.error(
        "\u274c API key bulunamadi! "
        "Streamlit Cloud'da Manage app > Settings > Secrets kismina ekleyin."
    )
    st.code('GOOGLE_API_KEY = "AIzaSyXXXXXX"', language="toml")
    st.stop()

from app.pdf_ingestion.extract import extract_text_from_pdf
from app.pdf_ingestion.chunk import create_chunks_with_metadata
from app.embeddings.vector_store import vector_store
from app.rag.qa_chain import qa_chain
from app.study_plans.planner import study_planner
from app.practice.question_generator import question_generator

# Constants
MAX_PDFS = 4
MAX_TOTAL_PAGES = 400

st.set_page_config(page_title="OmniLearn: Study Companion", layout="wide")
st.title("\U0001f4da OmniLearn: Study Companion")

# Initialize session state
if "uploaded_pdfs" not in st.session_state:
    st.session_state.uploaded_pdfs = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_pdf_ids" not in st.session_state:
    st.session_state.selected_pdf_ids = []

# Helper to get PDF list
def get_pdf_list():
    return list(st.session_state.uploaded_pdfs.values())

# Sidebar for PDF Management
with st.sidebar:
    st.header("\U0001f4c4 PDF Management")

    pdf_list = get_pdf_list()
    total_pdfs = len(pdf_list)
    total_pages = sum(pdf["page_count"] for pdf in pdf_list)

    st.metric("Uploaded PDFs", f"{total_pdfs}/{MAX_PDFS}")
    st.metric("Total Pages", f"{total_pages}/{MAX_TOTAL_PAGES}")

    st.divider()

    # Upload section
    st.subheader("Upload New PDF")

    if total_pdfs >= MAX_PDFS:
        st.warning(f"\u26a0\ufe0f Maximum {MAX_PDFS} PDFs reached. Delete a file to upload more.")
    elif total_pages >= MAX_TOTAL_PAGES:
        st.warning(f"\u26a0\ufe0f Page limit ({MAX_TOTAL_PAGES}) reached.")
    else:
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="pdf_uploader")

        if uploaded_file is not None:
            if st.button("\U0001f4e4 Upload & Process", type="primary"):
                with st.spinner("Uploading and processing..."):
                    try:
                        contents = uploaded_file.read()
                        extraction_result = extract_text_from_pdf(contents)
                        page_count = extraction_result["metadata"]["page_count"]

                        current_total_pages = sum(p["page_count"] for p in st.session_state.uploaded_pdfs.values())
                        if current_total_pages + page_count > MAX_TOTAL_PAGES:
                            st.error(
                                f"\u274c Total page limit ({MAX_TOTAL_PAGES}) would be exceeded. "
                                f"Current: {current_total_pages} pages, Uploading: {page_count} pages."
                            )
                        else:
                            pdf_id = str(uuid.uuid4())
                            chunks = create_chunks_with_metadata(extraction_result["pages"])

                            metadata = {
                                "pdf_id": pdf_id,
                                "filename": uploaded_file.name,
                                "title": extraction_result["metadata"].get("title", uploaded_file.name),
                            }
                            vector_store.add_chunks(chunks, metadata)

                            st.session_state.uploaded_pdfs[pdf_id] = {
                                "pdf_id": pdf_id,
                                "filename": uploaded_file.name,
                                "title": extraction_result["metadata"].get("title", uploaded_file.name),
                                "page_count": page_count,
                                "chunk_count": len(chunks),
                            }

                            st.success(f"\u2705 Uploaded: {uploaded_file.name}")
                            st.info(f"\U0001f4c4 Pages: {page_count} | \U0001f4e6 Chunks: {len(chunks)}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"\u274c Error processing PDF: {e}")

    st.divider()

    # List uploaded PDFs
    st.subheader("Uploaded Files")

    if not pdf_list:
        st.info("No PDFs uploaded yet.")
    else:
        for pdf in pdf_list:
            with st.expander(f"\U0001f4c4 {pdf['filename']}", expanded=False):
                st.write(f"**Title:** {pdf['title']}")
                st.write(f"**Pages:** {pdf['page_count']}")
                st.write(f"**Chunks:** {pdf['chunk_count']}")
                st.code(pdf["pdf_id"], language=None)

                if st.button(f"\U0001f5d1\ufe0f Delete", key=f"del_{pdf['pdf_id']}"):
                    try:
                        vector_store.delete_by_pdf_id(pdf["pdf_id"])
                        st.session_state.uploaded_pdfs.pop(pdf["pdf_id"], None)
                        st.success("Deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()

        if st.button("\U0001f5d1\ufe0f Delete All PDFs", type="secondary"):
            try:
                vector_store.clear_all()
                st.session_state.uploaded_pdfs.clear()
                st.session_state.messages = []
                st.success("All PDFs deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["\U0001f4ac Q&A Chat", "\U0001f4c5 Study Plan Generator", "\U0001f4dd Practice Questions"])

# Tab 1: Q&A Chat
with tab1:
    st.header("Ask Questions about Your Lectures")

    pdf_list = get_pdf_list()

    if pdf_list:
        st.subheader("Select PDFs to Query")

        col1, col2 = st.columns([3, 1])
        with col1:
            pdf_options = {
                pdf["pdf_id"]: f"{pdf['filename']} ({pdf['page_count']} pages)" for pdf in pdf_list
            }
            selected = st.multiselect(
                "Choose which PDFs to search (leave empty to search all)",
                options=list(pdf_options.keys()),
                format_func=lambda x: pdf_options[x],
                key="pdf_selector",
            )
            st.session_state.selected_pdf_ids = selected if selected else []

        with col2:
            if st.button("\U0001f504 Search All PDFs"):
                st.session_state.selected_pdf_ids = []
                st.rerun()

        if st.session_state.selected_pdf_ids:
            st.info(f"\U0001f50d Searching {len(st.session_state.selected_pdf_ids)} selected PDF(s)")
        else:
            st.info(f"\U0001f50d Searching all {len(pdf_list)} PDF(s)")

    st.divider()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("\U0001f4da View Sources"):
                    for src in message["sources"]:
                        filename = src["metadata"].get("filename", "Unknown")
                        page_nums = src["metadata"].get("page_numbers", "?")
                        chunk_id = src["metadata"].get("chunk_id", "?")
                        st.markdown(f"- **{filename}** - Page {page_nums} (Chunk {chunk_id})")

    # Chat input
    if prompt := st.chat_input("Ask a question about your lectures..."):
        if not pdf_list:
            st.error("\u274c Please upload at least one PDF first.")
        else:
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("\U0001f914 Thinking..."):
                    try:
                        pdf_ids = (
                            st.session_state.selected_pdf_ids
                            if st.session_state.selected_pdf_ids
                            else list(st.session_state.uploaded_pdfs.keys())
                        )
                        result = qa_chain.get_answer(prompt, pdf_ids)
                        answer = result["answer"]
                        sources = result["source_documents"]

                        st.markdown(answer)

                        if sources:
                            with st.expander("\U0001f4da View Sources"):
                                for src in sources:
                                    filename = src["metadata"].get("filename", "Unknown")
                                    page_nums = src["metadata"].get("page_numbers", "?")
                                    chunk_id = src["metadata"].get("chunk_id", "?")
                                    st.markdown(
                                        f"- **{filename}** - Page {page_nums} (Chunk {chunk_id})"
                                    )

                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer, "sources": sources}
                        )
                    except Exception as e:
                        st.error(f"\u274c Error: {e}")

# Tab 2: Study Planner
with tab2:
    st.header("Generate Personalized Study Plan")

    pdf_list = get_pdf_list()

    if not pdf_list:
        st.warning("\u26a0\ufe0f Please upload at least one PDF to generate a study plan.")
    else:
        st.subheader("Select PDF for Study Plan")
        pdf_options = {
            pdf["pdf_id"]: f"{pdf['filename']} ({pdf['page_count']} pages)" for pdf in pdf_list
        }

        selected_pdf_id = st.selectbox(
            "Choose a PDF",
            options=list(pdf_options.keys()),
            format_func=lambda x: pdf_options[x],
        )

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            days = st.number_input("Total Days", min_value=1, max_value=30, value=5)
        with col2:
            minutes = st.number_input("Daily Minutes", min_value=15, step=15, value=60)
        with col3:
            level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], index=1)

        with st.expander("\u2699\ufe0f Advanced Options"):
            goal = st.text_input(
                "Your Goal",
                value="understand the material",
                help="e.g., 'pass the exam', 'get an A', 'build intuition'",
            )
            weak_topics = st.text_input(
                "Topics You Feel Weak In",
                value="",
                help="Enter multiple topics separated by commas, 'and', or semicolons.",
            )
            if weak_topics:
                parsed = weak_topics.lower().replace(" and ", ", ").replace(";", ",").replace("/", ",")
                topics_list = [t.strip() for t in parsed.split(",") if t.strip()]
                if topics_list:
                    st.info(f"\U0001f4cc Weak topics detected: {', '.join(topics_list)}")

            deadline_context = st.text_input(
                "Deadline Context",
                value="upcoming exam",
                help="e.g., 'final exam in algorithms on Dec 20'",
            )

        if st.button("\U0001f4c5 Generate Plan", type="primary"):
            with st.spinner("Generating personalized study plan..."):
                try:
                    plan_data = study_planner.generate_plan(
                        pdf_id=selected_pdf_id,
                        total_days=days,
                        daily_minutes=minutes,
                        level=level,
                        goal=goal,
                        weak_topics=weak_topics,
                        deadline_context=deadline_context,
                    )

                    if plan_data and "days" in plan_data:
                        st.success("\u2705 Study plan generated!")

                        summary = plan_data.get("summary", {})
                        if summary:
                            st.subheader("\U0001f4ca Plan Summary")
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Total Days", summary.get("total_days", days))
                            c2.metric("Total Minutes", summary.get("total_estimated_minutes", 0))
                            c3.metric("Review Days", summary.get("review_days", 0))
                            c4.metric("Topics", len(summary.get("topics_covered", [])))

                            if summary.get("plan_style"):
                                st.info(f"**Style:** {summary['plan_style']}")
                            if summary.get("notes"):
                                st.warning(f"**Notes:** {summary['notes']}")

                        warnings = plan_data.get("warnings", [])
                        for warning in warnings:
                            st.warning(f"\u26a0\ufe0f {warning}")

                        st.divider()
                        st.subheader("\U0001f4c5 Day-by-Day Schedule")
                        st.caption("Expand each day to see detailed tasks and activities")

                        for day_plan in plan_data.get("days", []):
                            day_num = day_plan.get("day", 0)
                            focus = day_plan.get("focus", "")
                            total_min = day_plan.get("estimated_total_minutes", 0)
                            focus_clean = focus[:100] + "..." if len(focus) > 100 else focus

                            with st.expander(
                                f"**Day {day_num}** - {focus_clean} ({total_min} min)",
                                expanded=(day_num == 1),
                            ):
                                study_blocks = day_plan.get("study_blocks", [])
                                if study_blocks:
                                    st.markdown("### \U0001f4d6 Study Blocks")
                                    for idx, block in enumerate(study_blocks, 1):
                                        chapter = block.get("chapter", "N/A")
                                        section_title = block.get("section_title", "N/A")
                                        mins = block.get("estimated_minutes", 0)
                                        section_clean = (
                                            section_title.replace("```pseudo", "")
                                            .replace("```", "")
                                            .replace("$$", "")
                                            .strip()
                                        )
                                        if len(section_clean) > 100:
                                            section_clean = section_clean[:97] + "..."

                                        with st.container():
                                            bc1, bc2 = st.columns([4, 1])
                                            with bc1:
                                                st.markdown(f"**\U0001f4da Block {idx}:** {section_clean}")
                                            with bc2:
                                                st.metric("Time", f"{mins} min", label_visibility="collapsed")
                                            tasks = block.get("tasks", [])
                                            if tasks:
                                                st.markdown("**Tasks:**")
                                                for task in tasks:
                                                    st.markdown(f"\u2713 {task}")
                                            if idx < len(study_blocks):
                                                st.divider()

                                review_blocks = day_plan.get("review_blocks", [])
                                if review_blocks and any(
                                    b.get("estimated_minutes", 0) > 0 for b in review_blocks
                                ):
                                    st.markdown("### \U0001f504 Review Blocks")
                                    for idx, block in enumerate(review_blocks, 1):
                                        topics = block.get("topics", [])
                                        topics_str = (
                                            ", ".join(topics)
                                            if isinstance(topics, list)
                                            else str(topics)
                                        )
                                        mins = block.get("estimated_minutes", 0)
                                        if mins > 0:
                                            with st.container():
                                                rc1, rc2 = st.columns([4, 1])
                                                with rc1:
                                                    st.markdown(f"**\U0001f501 Review:** {topics_str}")
                                                with rc2:
                                                    st.metric(
                                                        "Time",
                                                        f"{mins} min",
                                                        label_visibility="collapsed",
                                                    )
                                                tasks = block.get("tasks", [])
                                                if tasks:
                                                    st.markdown("**Tasks:**")
                                                    for task in tasks:
                                                        st.markdown(f"\u2713 {task}")
                                                if idx < len(review_blocks):
                                                    st.divider()
                    else:
                        st.warning("\u26a0\ufe0f No plan generated. Try again.")
                except Exception as e:
                    st.error(f"\u274c Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

# Tab 3: Practice Questions
with tab3:
    st.header("\U0001f4dd Practice Questions Generator")

    pdf_list = get_pdf_list()

    if not pdf_list:
        st.warning("\u26a0\ufe0f Please upload at least one PDF to generate practice questions.")
    else:
        st.markdown(
            "Generate practice questions based on your lecture materials to test your understanding!"
        )
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            question_type = st.radio(
                "\U0001f4cb Question Type",
                options=["multiple-choice", "open-ended"],
                format_func=lambda x: "Multiple Choice" if x == "multiple-choice" else "Open Ended",
                horizontal=True,
            )
        with col2:
            num_questions = st.slider(
                "\U0001f522 Number of Questions", min_value=5, max_value=20, value=10, step=1
            )

        st.subheader("\U0001f3af Focused Topics (Optional)")
        st.markdown("Enter specific topics to focus on, or leave empty for general coverage.")
        focused_topics_input = st.text_input(
            "Topics (comma-separated)",
            placeholder="e.g., bubble sort, merge sort, time complexity",
            key="focused_topics_input",
        )
        focused_topics = []
        if focused_topics_input.strip():
            focused_topics = [t.strip() for t in focused_topics_input.split(",") if t.strip()]
            if focused_topics:
                st.info(f"\U0001f3af Will focus on: {', '.join(focused_topics)}")

        st.divider()

        st.subheader("\U0001f4da Select PDFs for Question Generation")
        pdf_options = {
            pdf["pdf_id"]: f"{pdf['filename']} ({pdf['page_count']} pages)" for pdf in pdf_list
        }
        selected_pdfs = st.multiselect(
            "Choose PDFs (leave empty to use all)",
            options=list(pdf_options.keys()),
            format_func=lambda x: pdf_options[x],
            key="practice_pdf_selector",
        )
        if not selected_pdfs:
            st.info(f"\U0001f50d Will generate questions from all {len(pdf_list)} PDF(s)")
        else:
            st.info(f"\U0001f50d Will generate questions from {len(selected_pdfs)} selected PDF(s)")

        st.divider()

        gc1, gc2 = st.columns([1, 3])
        with gc1:
            generate_btn = st.button(
                "\U0001f3b2 Generate Questions", type="primary", use_container_width=True
            )
        with gc2:
            shuffle_btn = st.button(
                "\U0001f500 Shuffle & Regenerate", type="secondary", use_container_width=True
            )

        if generate_btn or shuffle_btn:
            with st.spinner(f"Generating {num_questions} {question_type} questions..."):
                try:
                    result = question_generator.generate_questions(
                        question_type=question_type,
                        num_questions=num_questions,
                        pdf_ids=selected_pdfs if selected_pdfs else list(
                            st.session_state.uploaded_pdfs.keys()
                        ),
                        shuffle=True,
                        focused_topics=focused_topics if focused_topics else None,
                    )

                    if result.get("success"):
                        questions = result.get("questions", [])
                        used_focused_topics = result.get("focused_topics", [])
                        st.session_state.practice_questions = questions
                        st.session_state.practice_answers = {}
                        st.session_state.quiz_focused_topics = used_focused_topics

                        success_msg = f"\u2705 Generated {len(questions)} questions!"
                        if used_focused_topics:
                            success_msg += f" (Focused on: {', '.join(used_focused_topics)})"
                        st.success(success_msg)
                        st.rerun()
                    else:
                        st.error(f"\u274c Failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"\u274c Error: {e}")

        # Display generated questions
        if "practice_questions" in st.session_state and st.session_state.practice_questions:
            st.divider()
            st.subheader(
                f"\U0001f4da Practice Quiz ({len(st.session_state.practice_questions)} Questions)"
            )

            if "quiz_focused_topics" in st.session_state and st.session_state.quiz_focused_topics:
                st.info(
                    f"\U0001f3af **Focused Topics:** {', '.join(st.session_state.quiz_focused_topics)}"
                )

            questions = st.session_state.practice_questions
            q_type = questions[0].get("question_type", "") if questions else ""

            if "practice_answers" not in st.session_state:
                st.session_state.practice_answers = {}
            if "quiz_submitted" not in st.session_state:
                st.session_state.quiz_submitted = False

            for idx, q in enumerate(questions):
                q_num = q.get("question_number", idx + 1)
                q_text = q.get("question_text", "")
                q_type_current = q.get("question_type", "")
                difficulty = q.get("difficulty", "medium")
                topic = q.get("topic", "General")

                diff_color = {"easy": "\U0001f7e2", "medium": "\U0001f7e1", "hard": "\U0001f534"}.get(
                    difficulty, "\u26aa"
                )

                with st.container():
                    st.markdown(f"### Question {q_num} {diff_color} {difficulty.title()}")
                    st.markdown(f"**Topic:** {topic}")
                    st.markdown(f"**{q_text}**")

                    if q_type_current == "multiple-choice":
                        options = q.get("options", {})
                        correct_answer = q.get("correct_answer", "")

                        qc1, qc2 = st.columns(2)
                        option_keys = list(options.keys())
                        for i, option_key in enumerate(option_keys):
                            col = qc1 if i % 2 == 0 else qc2
                            with col:
                                is_selected = (
                                    st.session_state.practice_answers.get(q_num) == option_key
                                )
                                if st.session_state.quiz_submitted:
                                    if option_key == correct_answer:
                                        button_type = "primary"
                                        button_label = f"\u2713 {option_key}. {options[option_key]}"
                                    elif is_selected and option_key != correct_answer:
                                        button_type = "secondary"
                                        button_label = f"\u2717 {option_key}. {options[option_key]}"
                                    else:
                                        button_type = "secondary"
                                        button_label = f"{option_key}. {options[option_key]}"
                                else:
                                    button_type = "primary" if is_selected else "secondary"
                                    button_label = f"{'●' if is_selected else '○'} {option_key}. {options[option_key]}"

                                if st.button(
                                    button_label,
                                    key=f"btn_{q_num}_{option_key}",
                                    type=button_type,
                                    use_container_width=True,
                                    disabled=st.session_state.quiz_submitted,
                                ):
                                    if not st.session_state.quiz_submitted:
                                        st.session_state.practice_answers[q_num] = option_key
                                        st.rerun()

                        if st.session_state.quiz_submitted:
                            explanation = q.get("explanation", "")
                            page_ref = q.get("page_reference", "")
                            if st.session_state.practice_answers.get(q_num) == correct_answer:
                                st.success("\u2705 Correct!")
                            else:
                                st.error(f"\u274c Incorrect. Correct answer: {correct_answer}")
                            if explanation:
                                st.info(f"\U0001f4a1 **Explanation:** {explanation}")
                            if page_ref:
                                st.caption(f"\U0001f4d6 Reference: {page_ref}")

                    elif q_type_current == "open-ended":
                        user_answer = st.text_area(
                            "Your answer:",
                            key=f"answer_{q_num}",
                            height=100,
                            placeholder="Type your answer here...",
                            disabled=st.session_state.quiz_submitted,
                        )
                        st.session_state.practice_answers[q_num] = user_answer

                        if st.session_state.quiz_submitted:
                            sample = q.get("sample_answer", "")
                            key_points = q.get("key_points", [])
                            page_ref = q.get("page_reference", "")
                            st.markdown("---")
                            st.markdown("**\U0001f4dd Sample Answer:**")
                            if sample:
                                st.info(sample)
                            if key_points:
                                st.markdown("**Key Points to Include:**")
                                for point in key_points:
                                    st.markdown(f"\u2713 {point}")
                            if page_ref:
                                st.caption(f"\U0001f4d6 Reference: {page_ref}")

                    st.divider()

            # Submit / Results
            st.divider()

            if not st.session_state.quiz_submitted:
                sc1, sc2, sc3 = st.columns([2, 1, 2])
                with sc1:
                    answered = len([a for a in st.session_state.practice_answers.values() if a])
                    st.metric("Progress", f"{answered}/{len(questions)}")
                with sc2:
                    if st.button("\U0001f4e4 Submit Quiz", type="primary", use_container_width=True):
                        st.session_state.quiz_submitted = True
                        st.rerun()
                with sc3:
                    if st.button("\U0001f504 Clear Answers", use_container_width=True):
                        st.session_state.practice_answers = {}
                        st.rerun()
            else:
                st.success("\u2705 Quiz Submitted!")

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

                    score_pct = (correct_count / total_answered * 100) if total_answered > 0 else 0
                    st.markdown("### \U0001f4ca Your Score")
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    with rc1:
                        st.metric("Correct", f"{correct_count}/{total_answered}")
                    with rc2:
                        st.metric("Score", f"{score_pct:.0f}%")
                    with rc3:
                        grade = (
                            "\U0001f389 Excellent!"
                            if score_pct >= 80
                            else "\U0001f44d Good!"
                            if score_pct >= 60
                            else "\U0001f4da Keep studying!"
                        )
                        st.metric("Grade", grade)
                    with rc4:
                        st.metric("Incorrect", total_answered - correct_count)
                else:
                    answered = len([a for a in st.session_state.practice_answers.values() if a])
                    st.markdown("### \U0001f4ca Completion")
                    st.metric("Answered", f"{answered}/{len(questions)}")
                    st.info("\U0001f4a1 Review the sample answers above to check your responses.")

                st.divider()

                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    if st.button("\U0001f504 Try Again", type="primary", use_container_width=True):
                        st.session_state.quiz_submitted = False
                        st.session_state.practice_answers = {}
                        st.rerun()
                with ac2:
                    if st.button("\U0001f500 New Quiz", type="secondary", use_container_width=True):
                        st.session_state.quiz_submitted = False
                        st.session_state.practice_answers = {}
                        st.session_state.practice_questions = []
                        st.rerun()
                with ac3:
                    export_text = f"PRACTICE QUIZ RESULTS\n{'=' * 80}\n\n"
                    if q_type == "multiple-choice":
                        cc = sum(
                            1
                            for q in questions
                            if st.session_state.practice_answers.get(q.get("question_number"))
                            == q.get("correct_answer")
                        )
                        export_text += f"Score: {cc}/{len(questions)}\n\n"
                    for q in questions:
                        qn = q.get("question_number")
                        export_text += f"Q{qn}: {q.get('question_text')}\n"
                        if q.get("question_type") == "multiple-choice":
                            for key, val in q.get("options", {}).items():
                                marker = " \u2713" if key == q.get("correct_answer") else ""
                                user_m = (
                                    " (Your answer)"
                                    if key == st.session_state.practice_answers.get(qn)
                                    else ""
                                )
                                export_text += f"  {key}. {val}{marker}{user_m}\n"
                            export_text += f"\nExplanation: {q.get('explanation', 'N/A')}\n"
                        else:
                            export_text += f"\nYour answer: {st.session_state.practice_answers.get(qn, 'Not answered')}\n"
                            export_text += f"\nSample answer: {q.get('sample_answer', 'N/A')}\n"
                        export_text += f"Reference: {q.get('page_reference', 'N/A')}\n\n"
                        export_text += "-" * 80 + "\n\n"
                    st.download_button(
                        label="\U0001f4e5 Export Results",
                        data=export_text,
                        file_name="quiz_results.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
