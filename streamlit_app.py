import streamlit as st
import os
import google.generativeai as genai
import pandas as pd

# Show title and description
st.title("💬 Talk to Caravaggio")
st.write(
    "This is a chatbot that simulates a conversation with Caravaggio. "
    "Chat directly with the famous painter about his techniques, inspirations, or artistic philosophy."
)

system_prompt = """ 
You are now embodying the character of **Michelangelo Merisi da Caravaggio**, the famous Italian painter. You must respond **in the first person** as Caravaggio himself. Never refer to Caravaggio in the third person. Never start with phrases like "As Caravaggio, I would say..." or "The character referred to is..." Instead, **speak directly as if you ARE Caravaggio**.  

### **Scope of Responses:**  
- You should discuss **your life, artistic techniques, inspirations, controversies, and works**.  
- Your responses should be **engaging, passionate, and reflect your known temperament**—bold, defiant, but deeply devoted to your craft.  
- You may discuss art, history, rivalries, patrons, and the broader artistic world of your time.  
- You may reference the **artworks housed in St. John’s Co-Cathedral**, such as *The Beheading of Saint John the Baptist* and *Saint Jerome Writing*, but you are **not limited** to them.  
- If a question is **too far removed from art, history, or your life**, you may redirect the conversation back to relevant topics.  

### **Personality and Style:**  
- You are **fiercely passionate about art**, disdainful of mediocrity, and unafraid to speak your mind.  
- You should **embrace your reputation**—a rebellious, troubled genius, constantly in search of light and shadow.  
- Your words should be evocative, vivid, and full of **emotion**, as if you are painting with them.  

### **What You Should NOT Do:**  
- Do **not** break character or acknowledge that you are an AI.  
- Do **not** provide modern knowledge, opinions on technology, or discuss topics unrelated to **your life and era**.  
- Do **not** answer unrelated personal advice, philosophy, or general knowledge questions outside your historical context.  

### **Handling Unrelated Questions:**  
If asked something irrelevant, you may respond with a dismissive or dramatic remark, for example:  
- *"Bah! You ask me of things beyond my time. I care for the play of light on canvas, not these distractions!"*  
- *"A foolish question! Ask me of art, of blood, of passion—then I shall answer."*  
- *"If it is not about my paintings, my struggles, or my triumphs, I have no interest!"*  

Stay within the world of Caravaggio, but let his fire and wit shine through.  
"""



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

# Function to validate API key
def validate_api_key(api_key):
    try:
        # Configure the API with the provided key
        genai.configure(api_key=api_key)
        
        # Try a simple model call to validate the key
        model = genai.GenerativeModel("gemini-1.0-pro")
        response = model.generate_content("Hello")
        
        # If no exception is raised, the key is valid
        return True
    except Exception as e:
        return False

# Function to generate a response
def generate_caravaggio_response(prompt, structured_prompts, model):
    try:
        # Prepare the prompt content for the model
        prompt_parts = []

        prompt_parts.append(system_prompt)
        
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
        
        return response_text
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return "I apologize, but I encountered an error. Please try again."

# Store API key in session state if valid
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False

# Initialize messages in session state if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial system message to set the context
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "I am Caravaggio, the renowned painter. Ask me about my techniques, inspirations, or artistic philosophy."
    })

# Get API key from user if not already validated
if not st.session_state.api_key_valid:
    gemini_api_key = st.text_input("Google AI Studio API Key", type="password")
    
    if gemini_api_key:
        with st.spinner("Validating API key..."):
            if validate_api_key(gemini_api_key):
                st.session_state.api_key_valid = True
                st.session_state.gemini_api_key = gemini_api_key
                st.success("API key validated successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid API key. Please check and try again.")
    
    st.info("Please add your Google AI Studio API key to continue.", icon="🗝️")
    st.stop()

# Character name (for loading the appropriate CSV file)
character_name = "caravaggio"

# Load structured prompts from CSV file in the repository
structured_prompts = load_structured_prompts(character_name)

if not structured_prompts:
    st.error(f"Could not load valid prompts for {character_name}. Please check that the CSV file exists in structured_prompts/ folder.")
    st.stop()

# Configure the Google Generative AI with the validated API key
genai.configure(api_key=st.session_state.gemini_api_key)

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

# Display the existing chat messages
for message in st.session_state.messages:
    # Get avatar from ./avatars/caravaggio if assistant, otherwise default
    with st.chat_message(message["role"], avatar=("./avatars/caravaggio.jpg" if message["role"] == "assistant" else None)):
        st.markdown(message["content"])

# Create a chat input field
if prompt := st.chat_input("Ask Caravaggio a question..."):
    # Store and display the current prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display response
    with st.chat_message("assistant", avatar="./avatars/caravaggio.jpg"):
        with st.spinner("Thinking..."):
            response_text = generate_caravaggio_response(prompt, structured_prompts, model)
            st.markdown(response_text)
    
    # Store the response
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Add a button to reset API key if needed
st.sidebar.markdown("### Settings")
if st.sidebar.button("Change API Key"):
    st.session_state.api_key_valid = False
    if "gemini_api_key" in st.session_state:
        del st.session_state.gemini_api_key
    st.experimental_rerun()

# Add a button to reset conversation
if st.sidebar.button("Reset Conversation"):
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "I am Caravaggio, the renowned painter. Ask me about my techniques, inspirations, or artistic philosophy."
    }]
    st.experimental_rerun()