import sys
import re
import json
import hashlib
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
try:
    # Optional fallback if you don't set Pinecone env vars.
    from langchain_community.vectorstores import Chroma  # type: ignore
except Exception:  # pragma: no cover
    Chroma = None  # type: ignore
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import settings
from services.pinecone_vector_store import PineconeVectorStore

# URL patterns that usually indicate non-content images (tracking, logos, icons)
JUNK_IMAGE_PATTERNS = re.compile(
    r"1x1|pixel|tracking|CentralAutoLogin|favicon|logo\.svg|icon\.svg|"
    r"Wikiquote-logo|Wikipedia-logo|commons-logo|wikimedia-button|"
    r"edit.*\.svg|speaker.*\.svg|padlock|disclaimer",
    re.I
)
MAX_IMAGES_TO_SHOW = 8  # cap so the UI stays readable

# Recommended max question length for best results; longer questions get a friendly hint
MAX_RECOMMENDED_QUESTION_LENGTH = 400

# Short openers like "hi" — not answerable from KB but should not get "I don't have that information"
_SIMPLE_GREETING_RE = re.compile(
    r"^(hi|hello|hey|hiya|howdy|yo|sup|good\s+(morning|afternoon|evening|day)|greetings?|namaste)"
    r"[\s!?.,]*$",
    re.I,
)

# ✅ Fix SQLite for ChromaDB compatibility
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass


# Max length for suggested questions (chars) so they stay easy to read and click
MAX_SUGGESTION_QUESTION_LENGTH = 80
# Chunks / chars used to build suggestion + verification context (must stay grounded in KB)
SUGGESTION_POOL_MAX_DOCS = 35
SUGGESTION_CONTEXT_CHARS_PER_CHUNK = 700


# ===============================
# 🚀 Suggestion Question Generator
# ===============================
class SuggestionQuestionGenerator:
    """Generates short, human-friendly chatbot suggestion questions from content."""

    def __init__(self, llm_model: str):
        # Low temperature: avoid hypothetical questions not present in the knowledge text
        self.llm = ChatOpenAI(model=llm_model, temperature=0.15)
        self.prompt_template = ChatPromptTemplate.from_template("""
You write short follow-up questions for a chatbot. The chatbot may ONLY use the KNOWLEDGE TEXT below — no other information.

KNOWLEDGE TEXT:
{context}

Generate 4 to 6 candidate questions. Each question MUST satisfy ALL of these:
- The full answer must be contained in the KNOWLEDGE TEXT above (facts, steps, lists, contact info, etc.). Do not ask about anything not clearly there.
- Do not ask about other companies, generic industry advice, or "best practices" unless the text explicitly discusses them.
- Do not ask meta questions like "What can you do?" or "How do I use this chatbot?" unless the text explicitly describes the chatbot.
- One topic per question. Short and clickable: under 10 words when possible, one line each.

Write only the questions, one per line. No numbering, bullets, or quotes.
""")

    def generate(self, docs: List[Document]) -> List[str]:
        if not docs:
            return []

        context_text = "\n\n".join(
            (doc.page_content or "")[:SUGGESTION_CONTEXT_CHARS_PER_CHUNK].strip()
            for doc in docs
        )
        # Hard cap so the model sees a bounded slice of the KB
        if len(context_text) > 28000:
            context_text = context_text[:28000] + "\n…"

        final_prompt = self.prompt_template.format(context=context_text)
        response = self.llm.invoke(final_prompt)

        # Clean up lines into questions
        questions = [
            q.strip(" -•1234567890.").strip()
            for q in (response.content or "").splitlines()
            if q.strip()
        ]
        # Enforce max length: shorten any suggestion that's still too long for humans
        questions = self._shorten_suggestions(questions)
        return questions[:6]

    def _shorten_suggestions(self, questions: List[str]) -> List[str]:
        """Keep suggestions within MAX_SUGGESTION_QUESTION_LENGTH; shorten if needed."""
        out = []
        for q in questions:
            if len(q) <= MAX_SUGGESTION_QUESTION_LENGTH:
                out.append(q)
                continue
            # Trim to last full word before the limit and add ...
            trimmed = q[: MAX_SUGGESTION_QUESTION_LENGTH - 3].rsplit(maxsplit=1)
            short = (trimmed[0] + "…") if trimmed else q[: MAX_SUGGESTION_QUESTION_LENGTH - 3] + "…"
            if short.strip():
                out.append(short)
        return out


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
        self.pinecone_enabled = bool(settings.pinecone_api_key and settings.pinecone_index_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.dense_chunk_size,
            chunk_overlap=settings.dense_chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Prompt for answering user queries – behavior is injected dynamically
        self.prompt_template = """You are a helpful AI assistant.

Chatbot behavior mode:
{behavior}

Answer using ONLY the numbered excerpts below. Each excerpt may be from a different page or document (source name is shown).

Rules:
- Give a direct, complete answer. Use a short bullet list when the user asks for multiple items, steps, or options.
- Prefer concrete details from the excerpts (names, numbers, dates, URLs) over vague summaries.
- If excerpts only partially answer the question, state what is known from them and what is not covered.
- If nothing in the excerpts answers a factual question, say clearly that you don't have that information. Do not invent facts or use outside knowledge.
- Simple greetings (hi, hello, good morning, etc.) never require facts from the excerpts: reply briefly and warmly in the configured tone. Do not refuse or say you lack information "about" their greeting.
- For links and emails in your answer, use Markdown only: [visible text](https://example.com/path) or [email us](mailto:name@example.com). Do not put a closing parenthesis or period inside the URL; put punctuation after the final `)` of the link.

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
    # 🎛️ Chatbot Behavior Modes
    # --------------------------
    def _build_behavior_instructions(self, behavior: Dict[str, Any] | None) -> str:
        """
        Build a short, focused behavior block based on website/chatbot config.

        Expected behavior dict keys (all optional):
        - website_type: e.g. "service_business", "ecommerce"
        - primary_goal: e.g. "Sales + Support"
        - tone: e.g. "Friendly, professional, slightly persuasive"
        - extra_instructions: long free‑text instructions
        """
        if not behavior:
            return (
                "Website type: General website\n"
                "Primary goal: Answer questions based on the site's content.\n"
                "Tone: Friendly and neutral.\n"
            )

        website_type = (behavior.get("website_type") or "General website").strip()
        primary_goal = (behavior.get("primary_goal") or "Answer questions based on the site's content.").strip()
        tone = (behavior.get("tone") or "Friendly and professional.").strip()
        extra = (behavior.get("extra_instructions") or "").strip()

        lines = [
            f"Website type: {website_type}",
            f"Primary goal: {primary_goal}",
            f"Tone: {tone}",
        ]
        if extra:
            lines.append("Additional instructions:")
            lines.append(extra)
        return "\n".join(lines)

    @staticmethod
    def _is_simple_greeting(question: str) -> bool:
        q = (question or "").strip()
        if not q or len(q) > 72:
            return False
        if _SIMPLE_GREETING_RE.match(q):
            return True
        words = re.sub(r"[^\w\s]", " ", q.lower()).split()
        if not words or len(words) > 5:
            return False
        allowed = {
            "hi", "hello", "hey", "hiya", "howdy", "yo", "sup", "thanks", "thank", "you",
            "morning", "afternoon", "evening", "good", "day", "there", "dear",
        }
        return all(w in allowed for w in words)

    def _tenant_metadata_filter(self, tenant_id_str: str) -> Dict[str, Any]:
        """Chroma filter: this tenant's chunks plus optional shared `tenant_all` index."""
        return {
            "$or": [
                {"tenant_id": tenant_id_str},
                {"tenant_id": "tenant_all"},
            ]
        }

    @staticmethod
    def _dedupe_documents(docs: List[Document]) -> List[Document]:
        """Drop near-duplicate chunks so the model gets distinct evidence."""
        seen: set[str] = set()
        out: List[Document] = []
        for d in docs:
            key = hashlib.sha256(d.page_content.strip().encode("utf-8", errors="ignore")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            out.append(d)
        return out

    @staticmethod
    def _sample_docs_evenly(docs: List[Document], max_docs: int) -> List[Document]:
        """Spread samples across the list so prompts are not biased to the first chunks only."""
        if max_docs <= 0 or not docs:
            return []
        if len(docs) <= max_docs:
            return docs
        step = max(1, len(docs) // max_docs)
        return docs[::step][:max_docs]

    def _docs_for_suggestion_generation(
        self, tenant_id_str: str, retrieved_docs: List[Document]
    ) -> List[Document]:
        """
        Merge chunks from the current answer retrieval with a spread sample of all tenant
        chunks so suggested questions match what is actually in the knowledge base.
        """
        merged: List[Document] = list(retrieved_docs)
        try:
            batch = self.vector_db.get(where={"tenant_id": tenant_id_str})
            if batch and batch.get("documents"):
                metas = batch.get("metadatas") or [{}] * len(batch["documents"])
                for d, m in zip(batch["documents"], metas):
                    merged.append(
                        Document(
                            page_content=d or "",
                            metadata=m if isinstance(m, dict) else {},
                        )
                    )
        except Exception as e:
            print(f"Warning: tenant chunk sample for suggestions failed: {e}")
        merged = self._dedupe_documents(merged)
        return self._sample_docs_evenly(merged, SUGGESTION_POOL_MAX_DOCS)

    def _keep_answerable_suggestions(
        self, questions: List[str], knowledge_docs: List[Document]
    ) -> List[str]:
        """
        Drop any suggestion that cannot be answered strictly from the given knowledge chunks.
        """
        questions = [q.strip() for q in questions if q and str(q).strip()]
        if not questions or not knowledge_docs:
            return []

        picked = self._sample_docs_evenly(knowledge_docs, 18)
        parts: List[str] = []
        total = 0
        for d in picked:
            piece = (d.page_content or "")[:SUGGESTION_CONTEXT_CHARS_PER_CHUNK].strip()
            if not piece:
                continue
            if total + len(piece) > 11000:
                break
            parts.append(piece)
            total += len(piece)
        ctx = "\n---\n".join(parts)
        if not ctx.strip():
            return []

        qlist = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, start=1))
        prompt = f"""The chatbot may ONLY use KNOWLEDGE below. No outside facts.

KNOWLEDGE:
{ctx}

CANDIDATE QUESTIONS (numbered):
{qlist}

Return JSON only with this exact shape: {{"keep":[1,2]}}
Include only the numbers of questions whose answers are fully supported by the KNOWLEDGE (explicitly stated or clear paraphrase). If the knowledge only partially applies, exclude that question. If none qualify, return {{"keep":[]}}."""

        try:
            response = self.llm.invoke(prompt)
            text = (response.content or "").strip()
            if "```" in text:
                text = re.sub(r"^.*?```(?:json)?\s*", "", text, flags=re.DOTALL)
                text = re.sub(r"\s*```.*$", "", text, flags=re.DOTALL)
            parsed = json.loads(text)
            idxs = parsed.get("keep") if isinstance(parsed, dict) else None
            if not isinstance(idxs, list):
                return []
            out: List[str] = []
            for i in idxs:
                if isinstance(i, int) and 1 <= i <= len(questions):
                    out.append(questions[i - 1])
                elif isinstance(i, str) and i.isdigit():
                    j = int(i)
                    if 1 <= j <= len(questions):
                        out.append(questions[j - 1])
            # Dedupe while preserving order
            seen_q: set[str] = set()
            final = []
            for q in out:
                k = q.lower()
                if k in seen_q:
                    continue
                seen_q.add(k)
                final.append(q)
            return final[:5]
        except Exception as e:
            print(f"Suggestion verification failed (dropping suggestions): {e}")
            return []

    def _format_context_for_prompt(self, docs: List[Document]) -> str:
        """Numbered excerpts with source labels for clearer grounding."""
        max_c = min(settings.context_max_chunks, len(docs))
        per_chunk = settings.context_max_chars_per_chunk
        blocks = []
        for i, doc in enumerate(docs[:max_c], start=1):
            src = doc.metadata.get("source") or "unknown source"
            body = doc.page_content.strip()
            if len(body) > per_chunk:
                body = body[: per_chunk - 1].rstrip() + "…"
            blocks.append(f"--- Excerpt {i} (Source: {src}) ---\n{body}")
        return "\n\n".join(blocks)

    def _retrieve_for_tenant(self, question: str, tenant_id_str: str) -> List[Document]:
        """MMR retrieval over tenant + shared docs for better coverage than flat top-k."""
        if not self.vector_db:
            return []
        filt = self._tenant_metadata_filter(tenant_id_str)
        fetch_k = max(settings.retrieval_k, settings.retrieval_fetch_k)
        try:
            retriever = self.vector_db.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": settings.retrieval_k,
                    "fetch_k": fetch_k,
                    "lambda_mult": settings.mmr_lambda,
                    "filter": filt,
                },
            )
            docs = retriever.invoke(question)
        except Exception as e:
            print(f"MMR retrieval failed, using similarity search: {e}")
            retriever = self.vector_db.as_retriever(
                search_kwargs={"k": settings.retrieval_k, "filter": filt},
            )
            docs = retriever.invoke(question)
        docs = self._dedupe_documents(docs)
        # Post-filter in case metadata ever mismatches
        allowed = {tenant_id_str, "tenant_all"}
        return [d for d in docs if (d.metadata or {}).get("tenant_id") in allowed]

    # --------------------------
    # 🧱 Initialize / Load DB
    # --------------------------
    def initialize_database(self) -> bool:
        """Initialize or load the vector database."""
        try:
            if self.pinecone_enabled:
                self.vector_db = PineconeVectorStore(
                    embeddings=self.embeddings,
                    pinecone_api_key=settings.pinecone_api_key,
                    index_name=settings.pinecone_index_name,
                    host=settings.pinecone_host,
                    environment=settings.pinecone_environment,
                    meta_path=settings.pinecone_meta_path,
                    embedding_batch_size=settings.embedding_batch_size,
                )
                print(
                    f"✅ Connected Pinecone index '{settings.pinecone_index_name}' "
                    f"(meta cache at {settings.pinecone_meta_path})"
                )
                return True

            if Chroma is None:
                print("❌ Chroma fallback is unavailable. Install deps or configure Pinecone.")
                return False

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
    def answer_question(
        self,
        question: str,
        tenant_id: str,
        user_asking_for_images: bool = False,
        behavior: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Generate answer for a question using tenant-filtered retrieval and dynamic suggestions."""
        if not self.vector_db:
            self.initialize_database()

        if not self.vector_db:
            return {
                "answer": "Error: Knowledge base not available. Please add some content first.",
                "sources": [],
                "tenant_id": str(tenant_id),
                "suggestions": self.get_tenant_suggestions(str(tenant_id)),
            }

        try:
            tenant_id_str = str(tenant_id)

            docs = self._retrieve_for_tenant(question, tenant_id_str)
            if not docs:
                suggestions = self.get_tenant_suggestions(tenant_id_str)
                if self._is_simple_greeting(question):
                    n_chunks = self.get_tenant_document_count(tenant_id_str)
                    if n_chunks == 0:
                        answer = (
                            "Hello! There are no knowledge sources loaded for this assistant yet, "
                            "so I can't answer detailed questions. Once your team adds website pages or documents, "
                            "I'll be able to help from that content."
                        )
                    else:
                        answer = (
                            "Hello! I can help with questions about our services, contact details, and other topics "
                            "from the information we have on file. What would you like to know?"
                        )
                    return {
                        "answer": answer,
                        "sources": [],
                        "tenant_id": tenant_id_str,
                        "suggestions": suggestions,
                    }
                return {
                    "answer": "I don't have any information to answer that question. Please add relevant content to the knowledge base.",
                    "sources": [],
                    "tenant_id": tenant_id_str,
                    "suggestions": suggestions,
                }

            context_text = self._format_context_for_prompt(docs)
            if self._is_simple_greeting(question):
                context_text = (
                    "[Note: The user's message is a short greeting, not a factual question. "
                    "Reply with a brief friendly greeting; do not say you lack information about their hello. "
                    "You may invite them to ask a specific question.]\n\n"
                ) + context_text
            sources = [doc.metadata.get("source", "Unknown") for doc in docs]

            # When user asks for images, tell the model so it doesn't say "I don't have that information"
            if user_asking_for_images:
                context_text += (
                    "\n\n[Note: The user is asking for images. Relevant images from the knowledge sources are "
                    'being attached to this response. Acknowledge that you are providing the requested images '
                    '(e.g. "Here are the images from the relevant sources" or "Here are the images you asked for") '
                    "rather than saying you don't have that information.]"
                )

            # Build behavior block from admin-selected website type / tone
            behavior_text = self._build_behavior_instructions(behavior)

            # Generate answer
            final_prompt = self.prompt.format(
                behavior=behavior_text,
                context=context_text,
                question=question,
            )
            response = self.llm.invoke(final_prompt)

            # Suggestions: broad KB sample + strict generation + verifier (no unanswerable clicks)
            knowledge_for_suggestions = self._docs_for_suggestion_generation(tenant_id_str, docs)
            raw_suggestions = self.suggestion_generator.generate(knowledge_for_suggestions)
            suggestions = self._keep_answerable_suggestions(raw_suggestions, knowledge_for_suggestions)
            suggestions = [s for s in suggestions if question.lower() not in s.lower()]

            # Update cache for dynamic refresh next time
            self.suggestion_cache[tenant_id_str] = suggestions

            return {
                "answer": response.content.strip(),
                "sources": list(set(sources)),
                "tenant_id": tenant_id_str,
                "suggestions": suggestions,
            }

        except Exception as e:
            print(f"❌ Error answering question: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "tenant_id": str(tenant_id),
                "suggestions": self.get_tenant_suggestions(str(tenant_id)),
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
                metas = tenant_docs.get("metadatas") or [{}] * len(tenant_docs["documents"])
                docs = [
                    Document(
                        page_content=d or "",
                        metadata=m if isinstance(m, dict) else {},
                    )
                    for d, m in zip(tenant_docs["documents"], metas)
                ]
                docs = self._dedupe_documents(docs)
                sampled = self._sample_docs_evenly(docs, SUGGESTION_POOL_MAX_DOCS)
                raw = self.suggestion_generator.generate(sampled)
                filtered = self._keep_answerable_suggestions(raw, sampled)
                self.suggestion_cache[tenant_id] = filtered[:5]
                print(f"✨ Generated {len(filtered)} verified suggestions for tenant {tenant_id}")
        except Exception as e:
            print(f"❌ Error generating suggestions: {e}")

    def get_tenant_suggestions(self, tenant_id: str) -> List[str]:
        """Retrieve stored suggestion questions for a tenant."""
        return self.suggestion_cache.get(str(tenant_id), [])

    # --------------------------
    # 📏 Long-question hint (better UX for humans)
    # --------------------------
    def get_question_length_hint(self, question: str) -> str | None:
        """
        If the question is very long, return a short, friendly hint suggesting the user
        shorten it for better results. Otherwise return None.
        """
        if not question or len(question.strip()) <= MAX_RECOMMENDED_QUESTION_LENGTH:
            return None
        return (
            "Your question is quite long. For clearer answers, try asking one thing at a time "
            "in a short sentence."
        )

    # --------------------------
    # 🖼️ Image relevance (for chat UI)
    # --------------------------

    def user_asks_for_image(self, question: str) -> bool:
        """
        Return True only if the user's question indicates they want to see an image/photo.
        If False, the chat should not include any images in the response.
        """
        if not question or not question.strip():
            return False
        q = question.strip().lower()
        # Word-boundary style check for single words
        for token in ("image", "images", "photo", "photos", "picture", "pictures",
                      "visual", "diagram", "screenshot", "illustration", "graphic", "chart"):
            if token in q:
                return True
        # Phrase checks (simple substring)
        if "show me" in q and ("image" in q or "photo" in q or "picture" in q):
            return True
        if "show " in q and ("image" in q or "photo" in q or "picture" in q):
            return True
        if "send " in q and ("image" in q or "photo" in q or "picture" in q):
            return True
        if "display " in q and ("image" in q or "photo" in q or "picture" in q):
            return True
        if "see the " in q and ("image" in q or "photo" in q or "picture" in q):
            return True
        if "what does" in q and "look like" in q:
            return True
        if "how does" in q and "look" in q:
            return True
        return False

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
            # If we can't confidently select any relevant images, don't send images at all
            return []

        out = [c for c in candidates if c.get("url") in urls_selected]
        return out[:MAX_IMAGES_TO_SHOW]


# Singleton instance
retrieval_service = RetrievalServiceV2()
