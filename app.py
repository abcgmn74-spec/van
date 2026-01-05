import streamlit as st
import re
import csv
from io import StringIO

st.set_page_config(page_title="Telegram Prediction Analyzer", layout="wide")
st.title("⚽ Telegram Prediction Analyzer")

# =========================
# TEAM INPUT
# =========================
team_input = st.text_input(
    "✍️ Team names (comma separated)",
    placeholder="Newcastle United, Chelsea, Inter Milan"
)

uploaded = st.file_uploader("📄 Upload TXT file", type="txt")

def build_team_map(team_input):
    teams = [t.strip() for t in team_input.split(",") if t.strip()]
    team_map = {}
    for t in teams:
        key = t.lower()
        team_map[t] = key
    return team_map

def detect_teams(text, team_map):
    text = text.lower()
    found = []
    for standard, key in team_map.items():
        if key in text:
            found.append(standard)
    return found

def detect_phone(text):
    return re.findall(r'(09\d{7,9}|95\d{8,12})', text)

# =========================
# MAIN LOGIC
# =========================
if uploaded and team_input:
    team_map = build_team_map(team_input)

    raw = uploaded.read().decode("utf-8")
    blocks = raw.split("\n\n")

    clean_data = []
    no_team_msgs = []

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue

        user = lines[0].split(",")[0].strip()
        full_text = " ".join(lines)

        teams = detect_teams(full_text, team_map)
        phones = detect_phone(full_text)

        if not teams:
            no_team_msgs.append(block)
            continue

        clean_data.append({
            "User": user,
            "Teams": ", ".join(teams),
            "Phone": ", ".join(phones)
        })

    # =========================
    # DISPLAY
    # =========================
    st.subheader("✅ Clean Predictions")
    st.table(clean_data)

    # =========================
    # FILTER BY TEAM
    # =========================
    st.subheader("🔍 Filter by Team")
    selected_team = st.selectbox("Choose team", list(team_map.keys()))

    filtered = [d for d in clean_data if selected_team in d["Teams"]]
    st.table(filtered)

    # =========================
    # NO TEAM MESSAGES
    # =========================
    st.subheader("❌ Messages without selected teams")
    st.text_area("Filtered messages", "\n\n".join(no_team_msgs), height=200)

    # =========================
    # CSV EXPORT
    # =========================
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["User", "Teams", "Phone"])
    writer.writeheader()
    writer.writerows(clean_data)

    st.download_button(
        "⬇️ Download CSV",
        csv_buffer.getvalue(),
        "predictions_cleaned.csv",
        "text/csv"
    )

elif not team_input:
    st.info("👆 Team name တွေကို အရင်ထည့်ပါ (comma separated)")
else:
    st.info("📄 TXT file upload လုပ်ပါ")
