import streamlit as st

# Page config
st.set_page_config(
    page_title="My First Streamlit App",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 Streamlit Web App")
st.write("GitHub + Streamlit Cloud နဲ့ run လို့ရပါတယ်")

# Session state
if "items" not in st.session_state:
    st.session_state.items = []

# Input
item = st.text_input("စာသားတစ်ခုရိုက်ပါ")

# Button
if st.button("Add"):
    if item:
        st.session_state.items.append(item)
        st.success("ထည့်ပြီးပါပြီ ✅")
    else:
        st.warning("စာသားမထည့်ရသေးပါ ⚠️")

# Display items
st.subheader("📋 List")
for i, data in enumerate(st.session_state.items, start=1):
    st.write(f"{i}. {data}")
