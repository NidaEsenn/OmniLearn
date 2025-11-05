# OmniLearn
Low-cost AI education system using RAG and OmniAvatar to create interactive Q&amp;A, study plans, and lifelike video lectures.

<h1 align="center">🎓 Lecture Assistant: AI-Powered Study Companion</h1>

<p align="center">
  <em>Turning static lecture PDFs into interactive AI-driven learning experiences.</em>
</p>

<p align="center">
  <b>Taha Oguzhan Ucar</b> — M.S. in Artificial Intelligence, Northeastern University  
  📧 ucar.t@northeastern.edu | NUID: 003158954  
  <br>
  <b>Nida Esen</b> — M.S. in Artificial Intelligence, Northeastern University  
  📧 esen.n@northeastern.edu | NUID: 002594922  
</p>

---

## 🧩 Problem Overview

Students often struggle to learn efficiently from static lecture PDFs.  
Key challenges include:  
- 🔍 Difficulty locating specific information quickly.  
- 🧠 Lack of **personalized study plans** matching knowledge and available time.  
- 🌐 Limited access to **interactive and engaging content**, especially for international students.  

This project asks:  
> **Can we build a low-cost (< $15) AI system that transforms lecture PDFs into interactive, multimodal study companions with Q&A, personalized plans, and avatar-generated lessons?**

---

## 💡 System Overview

**Lecture Assistant** combines **Retrieval-Augmented Generation (RAG)** and **AI Avatar Technology** to create a fully interactive study environment — all running on **free Google Colab GPU tiers**.

### 🎯 Objectives
- Convert lecture PDFs into **Q&A-based chat systems** using RAG.
- Generate **personalized study plans** based on course structure and difficulty.
- Create **AI Avatar Video Lessons** for an engaging, human-like learning experience.

---

## 🧠 Core Architecture

| Module | Description |
|--------|--------------|
| **Text Extraction** | Extracts clean text, equations, and code blocks from PDFs using **PyMuPDF**. |
| **Chunking & Embeddings** | Splits content into 1000-character chunks (200 overlap) and embeds with **bge-small-en-v1.5** vectors. |
| **Retrieval + Generation (RAG)** | Retrieves relevant content using **ChromaDB + cosine similarity**, generates answers via **Gemini 2.0 Flash**. |
| **Study Plan Generator** | Uses structured prompts to design adaptive spaced-repetition schedules. |
| **AI Avatar Creation** | Generates 2–3 minute teaching videos using **OmniAvatar** with **gTTS** audio and gesture control. |

---

## 🧪 Data Description

We test the pipeline on **CS 5800: Algorithms Lecture Notes (85 pages)**:  
- 5 chapters, 15+ sections with equations and code examples.  
- Extracted into ~100 text chunks (1000 chars each).  
- Evaluated by **retrieval accuracy**, **Q&A relevance**, and **study plan usability**.

| Metric | Target |
|--------|--------|
| PDF Extraction | >95% accuracy |
| Chunking Time | <3 seconds (100 chunks) |
| Q&A Relevance | >85% |
| Response Time | <5 seconds |
| Avatar Video Duration | 2–3 minutes |
| Budget | ≤ $15 (Free APIs + Colab) |

---

## ⚙️ Methods

- 🧱 **Frameworks:** LangChain, ChromaDB, PyMuPDF, bge-small-en-v1.5  
- 🤖 **LLM:** Gemini 2.0 Flash (via API)  
- 🔉 **Avatar Generation:** OmniAvatar (lip-sync + gestures)  
- 🗣️ **Audio:** gTTS (Google Text-to-Speech)  
- 🧮 **Evaluation:** Manual scoring of 50 Q&A pairs + user feedback on video clarity and study plan quality.

---

## 🧠 Architecture Diagram

<p align="center">
  <img src="docs/architecture_pipeline.png" width="85%" alt="Lecture Assistant System Pipeline" />
</p>

---

## 🌟 Expected Outcomes

- 95%+ text extraction accuracy.  
- Sub-5 second Q&A response time.  
- 85%+ relevant answers on manual evaluation.  
- Realistic AI Avatar videos with natural gestures and lip-sync.  
- Fully functional **AI study assistant under $15** cost limit.

---

## 🧩 Key Challenges

- Finding optimal **chunk size** and overlap for context retention.  
- Avoiding **hallucinations** with strict prompt templating.  
- Managing **Google Colab GPU time limits**.  
- Staying within **free API quotas (1,500 Gemini requests/day)**.  

---

## 📚 References

1. P. Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS, 2020.  
2. S. Xiao et al., *C-Pack: Packaged Resources to Advance General Chinese Embedding*, arXiv:2309.07597, 2023.  
3. Q. Gan et al., *OmniAvatar: Efficient Audio-Driven Avatar Video Generation with Adaptive Body Animation*, arXiv:2506.18866, 2025.

---

## 👩‍💻 Future Work

- Integrate **speech recognition** for live Q&A with the avatar.  
- Expand to **multimodal course content** (slides, code demos, diagrams).  
- Deploy via **Streamlit Web App** for browser-based access.  
- Add **learning analytics dashboard** for progress tracking and quiz scoring.

---

<p align="center">
  <i>“AI should make learning not only smarter, but more human.”</i> ✨
</p>
