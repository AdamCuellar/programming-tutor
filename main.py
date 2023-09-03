import streamlit as st
import openai

def get_assistant_response(messages, model, message_placeholder):
    """
    Get the assistant's response using the OpenAI API.

    Parameters:
    - messages: List of message history to be sent to the model.
    - model: Model name to be used.
    - message_placeholder: Streamlit placeholder to display streaming text.

    Returns:
    - Assistant's response as a string.
    """
    full_response = ""
    for response in openai.ChatCompletion.create(
        model=model,
        messages=messages,
        stream=True,
    ):
        full_response += response.choices[0].delta.get("content", "")
        message_placeholder.markdown(full_response + "▌")
    
    message_placeholder.markdown(full_response)
    return full_response

def resend_edited_user_message(index, edited_message):
    st.session_state.chat_history[index]["content"] = edited_message

def main():
    # define default settings
    chosen_language = "Python"
    chosen_level = "beginner"
    chosen_model = "gpt-3.5-turbo"
    api_key = None

    # set page title
    st.set_page_config(page_title=f"Programming Tutor")

    # sidebar inputs
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password", placeholder="OpenAI API key here")

    model = st.sidebar.radio("Select a Model:", options=["gpt-3.5-turbo", "gpt-4"])
    language = st.sidebar.selectbox("Select a Language:", options=["Python", "JavaScript", "Rust", "Go", "HTML/CSS/JS"], on_change=lambda: st.session_state.update(chat_history=[]))
    level = st.sidebar.radio("Select Your Level:", options=["beginner", "intermediate", "advanced"])

    st.title(f"Programming Tutor for {language}")
    
    # set default api key
    if "OPENAI_API_KEY" not in st.session_state:
        st.session_state["OPENAI_API_KEY"] = None

    # set default model
    if "model" not in st.session_state:
        st.session_state.model = chosen_model

    # create a chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # set default language
    if "language" not in st.session_state:
        st.session_state.language = chosen_language
    
    # set default level
    if "level" not in st.session_state:
        st.session_state.level = chosen_level

    if api_key:
        st.session_state["OPENAI_API_KEY"] = api_key
        openai.api_key = st.session_state["OPENAI_API_KEY"]

    # Display chat history (Including Edit button only next to the last user message)
    last_user_msg_index = st.session_state.get("last_user_message_index", None)

    for idx, message in enumerate(st.session_state.chat_history):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if message["role"] == "user" and idx == last_user_msg_index:
            with col2:
                if st.button("Edit", key=f"edit_user_{idx}"):
                    st.session_state.edit_mode = True
                    st.session_state.edit_index = idx

    # Editing mode for the last user message
    if "edit_mode" in st.session_state and st.session_state.edit_mode:
        edited_message = st.text_input(
            "Edit User Message:", 
            value=st.session_state.chat_history[st.session_state.edit_index]["content"],
            key="unique_edit_text_input"
        )
        if st.button("Save", key="unique_save_button"):
            # Update user's message
            resend_edited_user_message(st.session_state.edit_index, edited_message)

            # Remove the assistant's last response
            st.session_state.chat_history.pop()

            # Get a new placeholder for the assistant's response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                # Get the new response from the assistant and update the placeholder
                assistant_response = get_assistant_response(st.session_state.chat_history, st.session_state["model"], message_placeholder)

            # Append the new assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

            # Exit editing mode
            del st.session_state.edit_mode
            del st.session_state.edit_index

            # Force rerun to refresh UI and get new response
            st.experimental_rerun()

    # accept user input
    if prompt := st.chat_input("Share your code/Ask a question"):
        if st.session_state["OPENAI_API_KEY"] is None:
            st.error("Please enter your OpenAI API key in the sidebar.")
            st.stop()

        # add user input to chat history
        message = {"role": "user", "content": prompt}
        st.session_state.chat_history.append(message)

        col1, col2 = st.columns([4, 1])  # Create columns for the chat message and edit button

        with col1:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # increment last user message index if it exists otherwise create it
        if "last_user_message_index" in st.session_state:
            # add 2 to the last user message index to account for the user message and the assistant message
            st.session_state.last_user_message_index += 2
        else:
            st.session_state.last_user_message_index = 0
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            # Get the new response from the assistant and update the placeholder
            assistant_response = get_assistant_response(st.session_state.chat_history, st.session_state["model"], message_placeholder)

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

        with col2:
            if st.button("Edit", key=f"edit_user_{st.session_state.last_user_message_index}"):
                st.session_state.edit_mode = True
                st.session_state.edit_index = st.session_state.last_user_message_index

    return

if __name__ == "__main__":
    main()