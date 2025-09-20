import streamlit as st
from db_utils import get_results

def show_results(student_id):
    st.subheader("Results")
    results = get_results(student_id)
    if not results:
        st.info("No results yet.")
    else:
        for exam, score in results:
            st.write(f"**{exam}** — Score: {score}")
