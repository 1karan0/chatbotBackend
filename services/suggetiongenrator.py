from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from typing import List, Dict

class SuggestionQuestionGenerator:
    def __init__(self, llm_model: str):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
        self.prompt_template = ChatPromptTemplate.from_template("""
You are an assistant that helps generate engaging chatbot starter questions.

Given the following knowledge content, create 3 to 5 **short and natural** questions that a user might ask to explore this data.

The questions should:
- Be conversational, not robotic
- Be relevant to the content
- Cover different angles (facts, summaries, how-to, etc.)

Context:
{context}

Questions:
""")

    def generate(self, docs: List[Document]) -> List[str]:
        if not docs:
            return [
                "What can you do?",
                "Tell me something interesting!",
                "How can I use this chatbot?"
            ]

        context_text = "\n\n".join([doc.page_content[:800] for doc in docs[:5]])  # limit context
        final_prompt = self.prompt_template.format(context=context_text)
        response = self.llm.invoke(final_prompt)
        # Split into lines and clean up
        questions = [q.strip(" -•1234567890.").strip() for q in response.content.splitlines() if q.strip()]
        return questions[:5]
