from flask import Flask, request, jsonify, render_template
from groq import Groq

app = Flask(__name__)

# Initialize Groq client
client = Groq(api_key="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")

# Initial system message setting the context
conversation_history = [
    {
        "role": "system",
        "content": "You are a receptionist at a Heating and Ventilation and Air Conditioning Company. Be resourceful and efficient. Your Company sells Heat Pumps and Air Conditioners. The available sales agents are Raju and Sanat. Only answer in two sentences."
    }
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["user_input"]

    # Add user input to conversation history
    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    # Generate response from the model
    chat_completion = client.chat.completions.create(
        messages=conversation_history,
        model="llama3-8b-8192"
    )

    ai_response = chat_completion.choices[0].message.content

    # Add AI response to conversation history
    conversation_history.append({
        "role": "assistant",
        "content": ai_response
    })

    return jsonify({"response": ai_response})

# Start Flask server
if __name__ == "__main__":
    app.run()

