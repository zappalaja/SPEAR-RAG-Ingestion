#!/usr/bin/env python3
"""Ingest merged Markdown into Chroma (no queries, no sanity checks)."""

import argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md_dir", required=True)
    ap.add_argument("--chroma_dir", required=True)
    ap.add_argument("--collection", required=True)
    ap.add_argument("--embedding_model", required=True)
    ap.add_argument("--chunk_size", type=int, default=1200)
    ap.add_argument("--chunk_overlap", type=int, default=150)
    args = ap.parse_args()

    md_dir = Path(args.md_dir).expanduser().resolve()
    chroma_dir = Path(args.chroma_dir).expanduser().resolve()
    chroma_dir.mkdir(parents=True, exist_ok=True)

    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

    loader = DirectoryLoader(
        str(md_dir),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} markdown docs from {md_dir}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    chunks = splitter.split_documents(docs)
    print(f"Chunked into {len(chunks)} total chunks.")

    emb = HuggingFaceEmbeddings(model_name=args.embedding_model)

    ids = []
    for i, d in enumerate(chunks):
        src = (d.metadata.get("source") or "unknown").replace("\\", "/")
        ids.append(f"{src}::chunk{i}")

    vs = Chroma(
        collection_name=args.collection,
        embedding_function=emb,
        persist_directory=str(chroma_dir),
    )

    vs.add_documents(chunks, ids=ids)
    vs.persist()

    print(f"Added/updated {len(chunks)} chunks into collection='{args.collection}'")
    print(f"Persist dir: {chroma_dir}")

if __name__ == "__main__":
    main()
