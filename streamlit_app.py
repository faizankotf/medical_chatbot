import streamlit as st
import requests

st.title("🧠 Medical Chatbot Dashboard")

mrd = st.text_input("Enter MRD Number")
query = st.text_area("Ask your question")

if st.button("Submit"):
    if mrd and query:
        res = requests.post(
            "http://127.0.0.1:8000/query",
            json={"mrd_number": mrd, "query": query}
        )

        data = res.json()

        st.subheader("Answer")
        st.write(data.get("answer"))

        st.subheader("Confidence")
        st.write(data.get("confidence"))
    else:
        st.error("Enter both MRD and Query")