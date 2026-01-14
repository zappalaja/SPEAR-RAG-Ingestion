# SPEAR-RAG-Ingestion
Tools needed to take pdf files, convert them to markdown, and the embed them in ChromaDB on Linux. Designed for SPEAR.

## Setup

### Nougat environment
```bash
conda env create -f envs/nougat.conda.yml
conda activate nougat
pip install -r envs/nougat.pip.txt
```

### RAG environment
```bash
conda env create -f envs/rag.conda.yml
conda activate rag_new
pip install -r envs/rag.pip.txt
```
