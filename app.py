import streamlit as st

st.set_page_config(
    page_title="My First Streamlit App",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 Streamlit Web App")
st.write("GitHub + Streamlit Cloud နဲ့ run လို့ရပါတယ်")

# ✅ FIX: change key name
if "item_list" not in st.session_state:
    st.session_state.item_list = []

item = st.text_input("စာသားတစ်ခုရိုက်ပါ")

if st.button("Add"):
    if item:
        st.session_state.item_list.append(item)
        st.success("ထည့်ပြီးပါပြီ ✅")
    else:
        st.warning("စာသားမထည့်ရသေးပါ ⚠️")

st.subheader("📋 List")
for i, data in enumerate(st.session_state.item_list, start=1):
    st.write(f"{i}. {data}")
