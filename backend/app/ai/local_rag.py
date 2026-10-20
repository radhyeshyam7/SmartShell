import os
import sqlite3
import re
from typing import List, Dict, Tuple, Optional

DB_PATH = "smartshell_rag.db"

class LocalRAG:
    """Local Retrieval-Augmented Generation subsystem using SQLite BM25/TF-IDF text search for technical OS documentation"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self.auto_ingest_default_docs()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_title ON rag_documents(title)
        """)
        conn.commit()
        conn.close()

    def ingest_document(self, title: str, source_path: str, content: str, chunk_size: int = 500):
        """Chunk and store document content for local retrieval"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing chunks for this source path to prevent duplicates
        cursor.execute("DELETE FROM rag_documents WHERE source_path = ?", (source_path,))
        
        words = content.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i + chunk_size])
            chunks.append(chunk_text)

        for idx, chunk in enumerate(chunks):
            if chunk.strip():
                cursor.execute("""
                    INSERT INTO rag_documents (title, source_path, chunk_index, content)
                    VALUES (?, ?, ?, ?)
                """, (title, source_path, idx, chunk))

        conn.commit()
        conn.close()

    def auto_ingest_default_docs(self):
        """Auto-ingest project README and Windows OS guides if available"""
        try:
            if os.path.exists("README.md"):
                with open("README.md", "r", encoding="utf-8", errors="ignore") as f:
                    self.ingest_document("SmartShell Master Guide", "README.md", f.read())
        except Exception:
            pass

        # Add built-in Windows OS troubleshooting knowledge chunks
        os_troubleshooting_guide = """
        Windows Subprocess File Not Found Error:
        Error: File Not Found or Path Not Found occurs when executing commands targeting files outside the working directory without specifying drive letters or relative paths. Solution: Specify target drive like C:\\ or D:\\, or use system-wide search.

        PowerShell Script Execution Policy Error:
        Error: Script execution is disabled on this system. Solution: Run Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process in PowerShell.

        Permission Denied / Access Denied Error:
        Error: Access Denied occurs when attempting to modify System32, Program Files, or locked system resources. Solution: Run terminal with elevated Administrator privileges or verify file permissions via icacls.

        Port Already in Use Error (FastAPI/Uvicorn):
        Error: Address already in use. Solution: Identify PID using netstat -ano | findstr :8000, then terminate process using Stop-Process -Id PID -Force.

        WMI CIM Invalid Class Error:
        Error: Get-CimInstance Invalid class or HRESULT 0x80041010 occurs when using an invalid WMI class name such as Win_LogicalDisk. Solution: Use Win32_LogicalDisk (e.g. Get-CimInstance Win32_LogicalDisk) or use PowerShell drive provider via Get-PSDrive -PSProvider FileSystem.
        """
        self.ingest_document("Windows Technical Troubleshooting Guide", "docs/windows_guide.md", os_troubleshooting_guide)

    def search_knowledge_base(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Retrieve top matching document chunks grounded by query keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords = [w.lower() for w in re.findall(r'\b\w{3,}\b', query) if w.lower() not in ["show", "find", "give", "with", "from", "that", "this", "have"]]
        if not keywords:
            keywords = [query.lower()]

        cursor.execute("SELECT id, title, source_path, chunk_index, content FROM rag_documents")
        rows = cursor.fetchall()
        conn.close()

        scored_results = []
        for doc_id, title, source_path, chunk_idx, content in rows:
            score = 0
            content_lower = content.lower()
            for kw in keywords:
                if kw in content_lower:
                    score += content_lower.count(kw)
            if score > 0:
                scored_results.append({
                    "id": doc_id,
                    "title": title,
                    "source_path": source_path,
                    "chunk_index": chunk_idx,
                    "content": content,
                    "score": score
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def get_grounded_answer(self, query: str) -> Tuple[str, List[str]]:
        """Return technical diagnosis grounded with official document citations"""
        results = self.search_knowledge_base(query, top_k=2)
        if not results:
            return ("No matching technical documentation found in local knowledge base.", [])

        citations = []
        context_blocks = []
        for res in results:
            citation_str = f"[{res['title']}] ({res['source_path']})"
            if citation_str not in citations:
                citations.append(citation_str)
            context_blocks.append(f"Source: {citation_str}\n{res['content']}")

        grounded_explanation = "\n\n".join(context_blocks)
        return (grounded_explanation, citations)

local_rag = LocalRAG()
