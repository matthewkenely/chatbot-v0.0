import streamlit as st
import os
import google.generativeai as genai
import pandas as pd

# Show title and description
st.title("💬 Caravaggio Chatbot")
st.write(
    "This is a chatbot that simulates a conversation with Caravaggio. "
    "Chat directly with the famous painter about his techniques, inspirations, or artistic philosophy."
)

# Function to load structured prompts from CSV
def load_structured_prompts(character_name):
    try:
        file_path = f"structured_prompts/{character_name}.csv"
        df = pd.read_csv(file_path)
        prompts = []
        for _, row in df.iterrows():
            if 'input' in row and 'output' in row:
                prompts.append({
                    "input": row['input'], 
                    "output": row['output']
                })
        return prompts
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return []

# Use Streamlit secrets for API key
if "GOOGLE_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GOOGLE_API_KEY"]
else:
    gemini_api_key = None

# Passcode authentication
authenticated = False
if "authenticated" in st.session_state:
    authenticated = st.session_state.authenticated

if not authenticated:
    passcode = st.text_input("Enter passcode to access the chatbot", type="password")
    if passcode:
        if "PASSCODE" in st.secrets and passcode == st.secrets["PASSCODE"]:
            st.session_state.authenticated = True
            authenticated = True
            st.experimental_rerun()
        else:
            st.error("Incorrect passcode. Please try again.")
            st.error(f"Passcode entered: {passcode}")
            st.error(f"True passcode: {st.secrets.get('PASSCODE', 'not found')}")

            # print all os.getenvs
            st.write(os.environ)
    st.stop()

# Character name (for loading the appropriate CSV file)
character_name = "caravaggio"

# Load structured prompts from CSV file in the repository
structured_prompts = load_structured_prompts(character_name)

if not gemini_api_key:
    st.error("API key not found in secrets. Please contact the administrator.")
    st.stop()

if not structured_prompts:
    st.error(f"Could not load valid prompts for {character_name}. Please check that the CSV file exists in structured_prompts/ folder.")
    st.stop()

# Configure the Google Generative AI with the API key
genai.configure(api_key=gemini_api_key)

# Create the model with the same configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-pro-exp-02-05",
    generation_config=generation_config,
)

# Create a session state variable to store the chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial system message to set the context
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "I am Caravaggio, the renowned painter. Ask me about my techniques, inspirations, or artistic philosophy."
    })

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Example questions the user can click on
example_questions = [
    "How do you create such dramatic lighting in your paintings?",
    "What inspired your painting 'The Calling of Saint Matthew'?",
    "Tell me about your use of tenebrism technique.",
    "What was your relationship with the Church during your career?"
]

# Create buttons for example questions
st.write("### Example Questions:")
cols = st.columns(2)
for i, question in enumerate(example_questions):
    if cols[i % 2].button(question):
        # Set the clicked question as the user input
        prompt = question
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Force a rerun to process the question
        st.experimental_rerun()

# Create a chat input field
if prompt := st.chat_input("Ask Caravaggio a question..."):
    # Store and display the current prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Prepare the prompt content for the model exactly as shown
                prompt_parts = []
                
                # Format all the structured prompts as input/output pairs
                for prompt_pair in structured_prompts:
                    prompt_parts.append(f"input: {prompt_pair['input']}")
                    prompt_parts.append(f"output: {prompt_pair['output']}")
                
                # Add the user's current question (input only)
                prompt_parts.append(f"input: {prompt}")
                
                # Generate a response using the Gemini model
                response = model.generate_content(prompt_parts)
                response_text = response.text
                
                # Strip "output:" prefix if it appears in the response
                if response_text.startswith("output:"):
                    response_text = response_text[7:].strip()
                
                # If the response is empty, provide a fallback
                if not response_text:
                    response_text = "I apologize, but I couldn't formulate a response. Could you please rephrase your question?"
                
                # Display and store the response
                st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.warning("Please check your connection and try again.")