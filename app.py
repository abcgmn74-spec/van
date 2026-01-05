import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Telegram TXT Parser", page_icon="📄")
st.title("📄 Telegram TXT Parser (Username / Team / User Acc)")

uploaded_file = st.file_uploader("TXT file တင်ပါ", type=["txt"])

# -------------------------------------------------
# Regex patterns
# -------------------------------------------------
USER_HEADER = re.compile(
    r"^(.+?),\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\]$"
)

PHONE_PATTERN = re.compile(r"(?:\+?959|09)\d{7,12}")

USER_ACC_KEYWORDS = re.compile(r"(ok\s*bet|okbet|slot|shank|bet)", re.I)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def extract_username(line):
    m = USER_HEADER.match(line)
    return m.group(1).strip() if m else None

def is_user_acc(line):
    if PHONE_PATTERN.search(line):
        return True
    if USER_ACC_KEYWORDS.search(line):
        return True
    return False

def clean_team(line):
    # remove numbering like 1. 2) -
    line = re.sub(r"^[\d\.\-\)\s]+", "", line)
    return line.strip()

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")

    blocks = re.split(
        r"(?=^.+?,\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\])",
        text,
        flags=re.MULTILINE
    )

    records = []

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        username = extract_username(lines[0])
        if not username:
            continue  # skip non-user messages

        teams = []
        user_acc = []

        for line in lines[1:]:
            if is_user_acc(line):
                user_acc.append(line)
            else:
                team = clean_team(line)
                if team:
                    teams.append(team)

        records.append({
            "Username": username,                # 🟢
            "Teams (Blue)": ", ".join(teams),    # 🔵
            "User Acc (Red)": ", ".join(user_acc) # 🔴
        })

    df = pd.DataFrame(records)

    st.success(f"✅ Parsed users: {len(df)}")

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="telegram_parsed_result.csv",
        mime="text/csv"
    )
