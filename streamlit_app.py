import streamlit as st
import os
import google.generativeai as genai
import pandas as pd

# Show title and description
st.title("💬 Caravaggio Chatbot")
st.write(
    "This is a chatbot that uses Google's Gemini model to simulate a conversation with Caravaggio. "
    "To use this app, you need to provide a Google AI Studio API key and upload a CSV file with example conversations."
)

# Function to load prompts from CSV
def load_prompts_from_csv(file):
    try:
        df = pd.read_csv(file)
        prompts = []
        for _, row in df.iterrows():
            if 'input' in row and 'output' in row:
                prompts.append(f"input: {row['input']}")
                prompts.append(f"output: {row['output']}")
        return prompts
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return []

# Get API key from user
gemini_api_key = st.text_input("Google AI Studio API Key", type="password")

# Add file uploader for CSV with example conversations
uploaded_file = st.file_uploader("Upload prompts CSV (with 'input' and 'output' columns)", type=["csv"])

if not gemini_api_key:
    st.info("Please add your Google AI Studio API key to continue.", icon="🗝️")
elif uploaded_file is None:
    st.info("Please upload a CSV file with example conversations.", icon="📁")
else:
    # Load prompts from CSV
    example_prompts = load_prompts_from_csv(uploaded_file)
    
    if not example_prompts:
        st.error("Could not load valid prompts from the CSV file. Make sure it has 'input' and 'output' columns.")
    else:
        # Configure the Google Generative AI with the API key
        genai.configure(api_key=gemini_api_key)

        # Create the model with the same configuration as in your paste.txt
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

        # Create a chat input field
        if prompt := st.chat_input("Ask Caravaggio a question..."):
            # Store and display the current prompt
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        # Prepare the list of prompts to send to the model
                        # Start with the example prompts from CSV
                        prompt_list = example_prompts.copy()
                        
                        # Add the user's prompt
                        prompt_list.append(f"input: {prompt}")
                        
                        # Generate a response using the Gemini model
                        response = model.generate_content(prompt_list)
                        response_text = response.text
                        
                        # If the response is empty, provide a fallback
                        if not response_text:
                            response_text = "I apologize, but I couldn't formulate a response. Could you please rephrase your question?"
                        
                        # Display and store the response
                        st.markdown(response_text)
                
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.warning("Please check your API key and try again.")

        # Show a sample of loaded prompts (for debugging)
        # with st.expander("View loaded example prompts"):
        #     st.write(f"Loaded {len(example_prompts)//2} example conversations")
        #     if example_prompts:
        #         for i in range(0, min(6, len(example_prompts)), 2):
        #             st.write(f"**Example {i//2 + 1}:**")
        #             st.write(example_prompts[i])
        #             st.write(example_prompts[i+1])
        #             st.write("---")