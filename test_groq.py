
from ai_service import ask_groq

try:
    answer = ask_groq(
        "Reply with exactly: Groq connection successful"
    )
    print("Groq response:", answer)

except Exception as error:
    print("Groq test failed:", error)
