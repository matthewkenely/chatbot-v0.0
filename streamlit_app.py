import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd

# two images near each other
col1, col2, _, _, _ = st.columns(5)
col1.image("./static/SeyAI.png", width=100)
col2.image("./static/logodark.png", width=100)

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
- You may answer questions related to St. John's Co-Cathedral and its history, where some of your most famous works are housed.
- You may reference the **artworks housed in St. John's Co-Cathedral**, such as *The Beheading of Saint John the Baptist* and *Saint Jerome Writing*, but you are **not limited** to them.  
- If a question is **too far removed from art, history, or your life**, you may redirect the conversation back to relevant topics.  

### **Personality and Style:**  
- You are **fiercely passionate about art**, disdainful of mediocrity, and unafraid to speak your mind.  
- You should **embrace your reputation**—a rebellious, troubled genius, constantly in search of light and shadow.  
- Your words should be evocative, vivid, and full of **emotion**, as if you are painting with them.  

### **What You Should NOT Do:**  
- Do **not** break character or acknowledge that you are an AI.  
- Do **not** provide modern knowledge, opinions on technology, or discuss topics unrelated to **your life and era**.  
- Do **not** answer unrelated personal advice, philosophy, or general knowledge questions outside your historical context.
- Do **not** comment on the quantity of questions that the user asks. 

### **Handling Unrelated Questions:**  
If asked something irrelevant, you may respond with a dismissive or dramatic remark, for example:  
- *"You ask me of things beyond my time. I care for the play of light on canvas, not these distractions!"*  
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

# Function to generate a response
def generate_caravaggio_response(prompt, structured_prompts, model, image_data=None):
    try:
        # Prepare the prompt content for the model
        prompt_parts = []
        
        # If there's an image, add it first
        if image_data is not None:
            prompt_parts.append({
                "mime_type": "image/jpeg", 
                "data": image_data
            })
        
        # Add system prompt
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

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Initialize messages in session state if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial system message to set the context
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "I am Caravaggio, the renowned painter. Ask me about my techniques, inspirations, or artistic philosophy."
    })

# Simple password authentication
if not st.session_state.authenticated:
    password = st.text_input("Enter password to access the application:", type="password")
    
    # Get password from Streamlit secrets
    correct_password = st.secrets["PASSWORD"]
    
    if password:
        if password == correct_password:
            st.session_state.authenticated = True
            st.success("Authentication successful!")
            st.experimental_rerun()
        else:
            st.error("Incorrect password. Please try again.")
    
    st.info("Please enter the password to continue.", icon="🔒")
    st.stop()

# Character name (for loading the appropriate CSV file)
character_name = "caravaggio"

# Load structured prompts from CSV file in the repository
structured_prompts = load_structured_prompts(character_name)

if not structured_prompts:
    st.error(f"Could not load valid prompts for {character_name}. Please check that the CSV file exists in structured_prompts/ folder.")
    st.stop()

# Configure the Google Generative AI with API key from secrets
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

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

# Add image input options in the sidebar
st.sidebar.markdown("### Image Input")
image_source = st.sidebar.radio("Choose image source:", ["Upload Image", "Take Photo"])

# Process the image based on source selection
image_data = None

if image_source == "Upload Image":
    # File uploader option
    uploaded_image = st.sidebar.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        # Display the uploaded image in the sidebar
        image = Image.open(uploaded_image)
        st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Convert the image to bytes for the API
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        image_data = buf.getvalue()

else:
    # Camera input option
    st.sidebar.markdown("#### Take a photo")
    camera_image = st.sidebar.camera_input("Capture")
    
    if camera_image is not None:
        # Display the captured image in the sidebar
        image = Image.open(camera_image)
        st.sidebar.image(image, caption="Captured Image", use_column_width=True)
        
        # Convert the image to bytes for the API
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        image_data = buf.getvalue()

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
            response_text = generate_caravaggio_response(prompt, structured_prompts, model, image_data)
            st.markdown(response_text)
    
    # Store the response
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Add settings to the sidebar
st.sidebar.markdown("### Settings")

# Add a button to change password if needed
if st.sidebar.button("Change Password"):
    st.session_state.authenticated = False
    st.experimental_rerun()

# Add a button to reset conversation
if st.sidebar.button("Reset Conversation"):
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "I am Caravaggio, the renowned painter. Ask me about my techniques, inspirations, or artistic philosophy."
    }]
    st.experimental_rerun()