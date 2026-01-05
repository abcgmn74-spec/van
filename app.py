import streamlit as st

st.set_page_config(
    page_title="Login App",
    page_icon="🔐",
    layout="centered"
)

# -------------------------
# Dummy user database
# -------------------------
USERS = {
    "admin": "admin123",
    "user": "user123"
}

# -------------------------
# Session state
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# -------------------------
# Login function
# -------------------------
def login(username, password):
    if username in USERS and USERS[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

# -------------------------
# Logout function
# -------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""

# -------------------------
# UI
# -------------------------
st.title("🔐 Login System")

if not st.session_state.logged_in:
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.success("Login successful ✅")
            st.rerun()
        else:
            st.error("Username or Password မှားနေပါတယ် ❌")

else:
    st.success(f"Welcome, {st.session_state.username} 👋")

    st.write("ဒီနေရာက Login ဝင်ပြီးမှ မြင်ရတဲ့ Page ပါ")

    if st.button("Logout"):
        logout()
        st.rerun()
