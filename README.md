# 📊 Financial Report Summarizer using RAG, LlamaIndex, and Flask

This AI-powered application automates the summarization of financial reports, transforming lengthy 10-K or analyst PDFs into professionally formatted **1-page** and **2-page summaries**, and evaluating them for factual accuracy and relevance using **RAGAS metrics**.

---

## 🚩 Problem Statement

Reviewing financial reports is complex and time-consuming. This project builds a solution that:
- Parses financial PDFs
- Extracts and summarizes key sections
- Generates structured summaries
- Evaluates outputs on relevance, recall, and factuality

---

## 🎯 Objectives

- Ingest financial documents and convert them to vector embeddings
- Retrieve relevant chunks via semantic search
- Generate targeted summaries using prompt-driven LLMs
- Create downloadable `.docx` summaries (1-page & 2-page)
- Evaluate outputs with **RAGAS** (Relevance, Faithfulness, Recall)

---

## 🧠 Methodology

### 1. **Data Ingestion & Indexing** (via `LlamaIndex`)
- **`document_ingester.py`**
  - `load_documents()`: Load and validate PDF documents
  - `create_index()`: Parse to nodes → embed → store in FAISS vector index

### 2. **Retrieval-Augmented Summarization** (via `LangChain`)
- **`summary_generator.py`**
  - `generate_section_summary()`: Extracts specific sections like SWOT, YoY, etc.
  - `generate_two_page_summary()`: Compiles full-length (2-page) report
  - `generate_one_page_summary()`: Compresses into an executive summary
  - `_create_docx_document()`: Generates styled `.docx` output

### 3. **Quality Evaluation** (via `RAGAs`)
- **`RagaEvaluator.py`**
  - `run_evaluation()`: Scores summaries on Relevance, Faithfulness, and Recall
  - Uses ground truth Q&A (currently supported: Apple Inc.)

### 4. **User Interface** (via `Flask`)
- **`app.py` or `run.py`**
  - Upload PDF(s), trigger summarization, view/download results
  - Optional: Run evaluation for metrics

---

## ⚙️ Setup & Installation

### ✅ Prerequisites
- Python 3.8+
- OpenAI API Key

### 📦 Installation Steps
```bash
# Clone the repository or extract the zip
cd financial-summarizer

# Install dependencies
python -m pip install -r requirements.txt

# Add your OpenAI API key in the .env file
echo "OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" > .env
