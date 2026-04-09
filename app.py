import streamlit as st
from backend.core import run_llm

st.set_page_config(page_title="LangChain Docs Assistant")

st.title("📚 LangChain Documentation Assistant")
st.write("Ask anything about LangChain documentation.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_llm(prompt)

            answer = response["answer"]
            sources = response.get("sources", [])

            st.markdown(answer)

            if sources:
                with st.expander("Sources"):
                    for source in sources:
                        st.write(source)

    # Save assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )