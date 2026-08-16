import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from langchain_groq import ChatGroq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

llm=ChatGroq(
    api_key=GROQ_API_KEY,
    temperature=0.2,
    model="llama-3.3-70b-versatile"
)

basic_prompt=ChatPromptTemplate.from_messages(
    [
(
    "system",
    (
        "You are a helpful AI assistant for"
        "a procurement automation platform."
        "Give clear,accurate and concise answers."
    )
),
(
    "human",
    "{question}"
)
    ]
)

basic_chain=(
    basic_prompt
    |
    llm
)

def ask_langchain(
    question: str
) -> str:
    """
    Sends a question through the LangChain pipeline
    and returns the model's generated text.
    """

    if not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    response = basic_chain.invoke(
        {
            "question": question
        }
    )

    generated_text = response.content

    if not generated_text:
        raise ValueError(
            "LangChain returned an empty response."
        )

    return str(
        generated_text
    )


if __name__ == "__main__":

    answer = ask_langchain(
        "Explain the procurement process in simple terms."
    )

    print("LangChain Response:\n")

    print(answer)




#ChatGroq → LLM
#PromptTemplate → Prompt banata hai
#Chain → Prompt aur LLM ko connect karti hai
#invoke() → Chain execute karta hai
#AIMessage → Response object
#response.content → Final answer


#llm model prepare-prompt basic tempelate created-then chain banaya model aur prompt ka use connect kiya then invoke se chain run ki ai ans ila uska object use krke content nikalla