# Tutorial: Build Your First App

Build a simple chatbot using AI Gateway in 15 minutes.

---

## What You'll Build

A Python chatbot that:
- Connects to AI Gateway
- Sends messages to GPT-4
- Handles streaming responses

---

## Prerequisites

- AI Gateway running (see [Installation](installation.md))
- Python 3.8+
- An API key (see [Quickstart](quickstart.md))

---

## Step 1: Install Dependencies

```bash
pip install openai
```

---

## Step 2: Create the Chatbot

Create `chatbot.py`:

```python
import openai

# Configure client to use AI Gateway
client = openai.OpenAI(
    api_key="sk-gw-your-api-key",  # Your AI Gateway key
    base_url="http://localhost:8000/api/v1"
)

def chat(message: str) -> str:
    """Send a message and get a response."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

# Interactive loop
print("Chatbot ready! Type 'quit' to exit.\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == 'quit':
        break
    
    response = chat(user_input)
    print(f"Bot: {response}\n")
```

---

## Step 3: Run the Chatbot

```bash
python chatbot.py
```

```
Chatbot ready! Type 'quit' to exit.

You: Hello!
Bot: Hello! How can I help you today?

You: What is Python?
Bot: Python is a popular programming language...
```

---

## Step 4: Add Streaming

For real-time responses, enable streaming:

```python
def chat_stream(message: str):
    """Stream responses in real-time."""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ],
        stream=True
    )
    
    print("Bot: ", end="")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")
```

---

## Next Steps

- [API Reference](../develop/api-reference/chat.md) - Explore all parameters
- [Guardrails](../develop/concepts/guardrails.md) - Add security
- [Routing](../develop/concepts/routing.md) - Use multiple providers
