import sys
import re
import json
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import settings

# URL patterns that usually indicate non-content images (tracking, logos, icons)
JUNK_IMAGE_PATTERNS = re.compile(
    r"1x1|pixel|tracking|CentralAutoLogin|favicon|logo\.svg|icon\.svg|"
    r"Wikiquote-logo|Wikipedia-logo|commons-logo|wikimedia-button|"
    r"edit.*\.svg|speaker.*\.svg|padlock|disclaimer",
    re.I
)
MAX_IMAGES_TO_SHOW = 8  # cap so the UI stays readable

# ✅ Fix SQLite for ChromaDB compatibility
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass


# ===============================
# 🚀 Suggestion Question Generator
# ===============================
class SuggestionQuestionGenerator:
    """Generates relevant chatbot starter questions from content."""

    def __init__(self, llm_model: str):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
        self.prompt_template = ChatPromptTemplate.from_template("""
You are an assistant that creates engaging chatbot starter questions.

Given the following knowledge content, generate 3 to 5 short, natural, and diverse questions that a user might ask to explore this content.

The questions should:
- Be conversational, not robotic
- Be relevant to the content
- Cover different types (facts, how-to, summaries, etc.)

Context:
{context}

Questions:
""")

    def generate(self, docs: List[Document]) -> List[str]:
        if not docs:
            return [
                "What can you do?",
                "Tell me something interesting.",
                "How can I use this chatbot?",
            ]

        # Limit context length for prompt
        context_text = "\n\n".join([doc.page_content[:800] for doc in docs[:5]])
        final_prompt = self.prompt_template.format(context=context_text)
        response = self.llm.invoke(final_prompt)

        # Clean up lines into questions
        questions = [
            q.strip(" -•1234567890.").strip()
            for q in response.content.splitlines()
            if q.strip()
        ]
        return questions[:5]


# ===============================
# 📌 RetrievalServiceV2
# ===============================
class RetrievalServiceV2:
    """Enhanced retrieval service with dynamic knowledge & suggestions."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        self.llm = ChatOpenAI(model=settings.chat_model, temperature=settings.temperature)
        self.chroma_path = settings.chroma_path
        self.vector_db = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.dense_chunk_size,
            chunk_overlap=settings.dense_chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # prompt for answering user queries
        self.prompt_template = """You are a helpful AI assistant. Answer the user's question using only the provided context.
If the answer is not in the context, politely say you don't have that information.

Context:
{context}

Question: {question}

Answer:"""
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)

        # Suggestion question generator
        self.suggestion_generator = SuggestionQuestionGenerator(settings.chat_model)

        # Temporary in-memory store for suggestions
        # In production, replace this with a database or Redis
        self.suggestion_cache: Dict[str, List[str]] = {}

    # --------------------------
    # 🧱 Initialize / Load DB
    # --------------------------
    def initialize_database(self) -> bool:
        """Initialize or load the vector database."""
        try:
            self.vector_db = Chroma(
                persist_directory=self.chroma_path,
                embedding_function=self.embeddings
            )
            print(f"✅ Loaded/Created Chroma DB at {self.chroma_path}")
            return True
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            return False

    # --------------------------
    # ➕ Add Documents
    # --------------------------
    async def add_documents_to_index(self, text: str, source: str, tenant_id: str) -> bool:
        """Add documents to the vector index and update suggestions."""
        try:
            if not self.vector_db:
                self.initialize_database()

            tenant_id_str = str(tenant_id)
            document = Document(
                page_content=text,
                metadata={"source": source, "tenant_id": tenant_id_str}
            )

            chunks = self.text_splitter.split_documents([document])
            if chunks:
                self.vector_db.add_documents(chunks)
                self.vector_db.persist()
                print(f"🟢 Added {len(chunks)} chunks for tenant {tenant_id_str} from {source}")

                # Generate suggestions after adding
                self.update_tenant_suggestions(tenant_id_str)
                return True

            return False
        except Exception as e:
            print(f"❌ Error adding documents to index: {e}")
            return False

    # --------------------------
    # 🧹 Clear Documents
    # --------------------------
    def clear_tenant_documents(self, tenant_id: str) -> bool:
        """Clear all documents for a specific tenant."""
        try:
            if not self.vector_db:
                return False

            tenant_id_str = str(tenant_id)
            results = self.vector_db.get(where={"tenant_id": tenant_id_str})

            if results and results['ids']:
                self.vector_db.delete(ids=results['ids'])
                self.vector_db.persist()
                print(f"🧼 Cleared {len(results['ids'])} documents for tenant {tenant_id_str}")

            # Clear suggestions too
            self.suggestion_cache.pop(tenant_id_str, None)
            return True
        except Exception as e:
            print(f"❌ Error clearing tenant documents: {e}")
            return False

    # --------------------------
    # 🧠 Answer Questions
    # --------------------------
    def answer_question(self, question: str, tenant_id: str) -> Dict[str, Any]:
     """Generate answer for a question using tenant-filtered retrieval and dynamic suggestions."""
     if not self.vector_db:
        self.initialize_database()

     if not self.vector_db:
        return {
            "answer": "Error: Knowledge base not available. Please add some content first.",
            "sources": [],
            "tenant_id": str(tenant_id),
            "suggestions": self.get_tenant_suggestions(str(tenant_id))
        }

     try:
         tenant_id_str = str(tenant_id)
         tenant_filter = {"tenant_id": tenant_id_str}

         retriever = self.vector_db.as_retriever(
            search_kwargs={
                "k": settings.retrieval_k,
                "filter": tenant_filter
            }
        )

         docs = retriever.invoke(question)
         if not docs:
            suggestions = self.get_tenant_suggestions(tenant_id_str)
            return {
                "answer": "I don't have any information to answer that question. Please add relevant content to the knowledge base.",
                "sources": [],
                "tenant_id": tenant_id_str,
                "suggestions": suggestions
            }

         context_text = "\n\n".join([doc.page_content for doc in docs])
         sources = [doc.metadata.get("source", "Unknown") for doc in docs]

        # Generate answer
         final_prompt = self.prompt.format(context=context_text, question=question)
         response = self.llm.invoke(final_prompt)

        # Generate suggestions from docs
         suggestions = self.suggestion_generator.generate(docs)

        # Remove the user's question if it matches a suggestion
         suggestions = [s for s in suggestions if question.lower() not in s.lower()]

        # Regenerate if too few suggestions
         if len(suggestions) < 3:
            suggestions = self.suggestion_generator.generate(docs)

        # Update cache for dynamic refresh next time
         self.suggestion_cache[tenant_id_str] = suggestions

         return {
            "answer": response.content.strip(),
            "sources": list(set(sources)),
            "tenant_id": tenant_id_str,
            "suggestions": suggestions
        }

     except Exception as e:
        print(f"❌ Error answering question: {e}")
        return {
            "answer": f"Error processing question: {str(e)}",
            "sources": [],
            "tenant_id": str(tenant_id),
            "suggestions": self.get_tenant_suggestions(str(tenant_id))
        }

    # --------------------------
    # 📊 Document Count
    # --------------------------
    def get_tenant_document_count(self, tenant_id: str) -> int:
        """Get the number of documents for a tenant."""
        try:
            if not self.vector_db:
                return 0

            tenant_id_str = str(tenant_id)
            results = self.vector_db.get(where={"tenant_id": tenant_id_str})
            return len(results['ids']) if results and results['ids'] else 0
        except Exception as e:
            print(f"❌ Error getting document count: {e}")
            return 0

    # --------------------------
    # 💡 Suggestion Handling
    # --------------------------
    def update_tenant_suggestions(self, tenant_id: str):
        """Generate and store suggestion questions for a tenant."""
        try:
            tenant_docs = self.vector_db.get(where={"tenant_id": tenant_id})
            if tenant_docs and tenant_docs['documents']:
                docs = [
                    Document(page_content=d, metadata=m)
                    for d, m in zip(tenant_docs['documents'], tenant_docs['metadatas'])
                ]
                suggestions = self.suggestion_generator.generate(docs)
                self.suggestion_cache[tenant_id] = suggestions
                print(f"✨ Generated {len(suggestions)} suggestions for tenant {tenant_id}")
        except Exception as e:
            print(f"❌ Error generating suggestions: {e}")

    def get_tenant_suggestions(self, tenant_id: str) -> List[str]:
        """Retrieve stored suggestion questions for a tenant."""
        return self.suggestion_cache.get(str(tenant_id), [
            "What can you do?",
            "Tell me something interesting.",
            "How can I use this chatbot?"
        ])

    # --------------------------
    # 🖼️ Image relevance (for chat UI)
    # --------------------------
    def _is_junk_image_url(self, url: str) -> bool:
        """True if URL looks like tracking pixel, logo, icon, etc."""
        return bool(JUNK_IMAGE_PATTERNS.search(url))

    def filter_relevant_images(
        self, question: str, answer: str, images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter images to only those relevant to the user's question and the bot's answer.
        - Drops junk (tracking pixels, logos, icons) by URL.
        - Uses LLM to select images that actually help answer the question (e.g. photos of
          the person/thing asked about). Returns a small, relevant subset for the chat UI.
        """
        if not images:
            return []

        # 1) Remove junk by URL
        candidates = [
            img for img in images
            if isinstance(img, dict) and img.get("url") and not self._is_junk_image_url(img["url"])
        ]
        if not candidates:
            return []
        if len(candidates) <= 3:
            return candidates[:MAX_IMAGES_TO_SHOW]

        # 2) Ask LLM which image URLs are relevant to the question/answer
        list_for_prompt = "\n".join(
            f"{i}. {c.get('url', '')} (alt: {c.get('alt') or 'none'})"
            for i, c in enumerate(candidates[:25], start=1)
        )
        prompt = f"""Given the user question and the bot's answer, select only the image URLs that are directly relevant (e.g. photos of the person/thing asked about, diagrams that illustrate the answer). Exclude logos, flags, icons, and decorative images.

User question: {question[:300]}
Bot answer: {answer[:400]}

Images (index, url, alt):
{list_for_prompt}

Return a JSON array of the selected image URLs only, e.g. ["https://...", "https://..."]. Return at most {MAX_IMAGES_TO_SHOW} URLs. If none are relevant, return []."""

        try:
            response = self.llm.invoke(prompt)
            text = (response.content or "").strip()
            # Extract JSON array (handle markdown code blocks)
            if "```" in text:
                text = re.sub(r"^.*?```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```.*$", "", text)
            parsed = json.loads(text)
            urls_selected = set(parsed) if isinstance(parsed, list) else set()
            # Keep only strings that look like URLs
            urls_selected = {u for u in urls_selected if isinstance(u, str) and u.startswith("http")}
        except Exception:
            urls_selected = set()

        if not urls_selected:
            # Fallback: return first few non-junk candidates
            return candidates[:MAX_IMAGES_TO_SHOW]

        out = [c for c in candidates if c.get("url") in urls_selected]
        return out[:MAX_IMAGES_TO_SHOW]


# Singleton instance
retrieval_service = RetrievalServiceV2()
