import gradio as gr
import pandas as pd
import re
import json
import os
import tempfile
from difflib import get_close_matches
from collections import Counter

# =================================================
# FILE PATH
# =================================================
LEARN_FILE = "team_learning.json"

# =================================================
# LOAD / SAVE
# =================================================
def load_mapping():
    if os.path.exists(LEARN_FILE):
        with open(LEARN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def atomic_save_mapping(data: dict):
    d = os.path.dirname(LEARN_FILE) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=d, encoding="utf-8") as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        temp = tf.name
    os.replace(temp, LEARN_FILE)

LEARNED_MAP = load_mapping()

# =================================================
# STANDARD TEAMS
# =================================================
STANDARD_TEAMS = [
    "Real Madrid","Barcelona","Manchester United","Manchester City",
    "Liverpool","Arsenal","Chelsea","Tottenham","Newcastle",
    "Brighton","Aston Villa","Everton","West Ham","Sevilla",
    "Villarreal","Athletic Club","Wolves","Brentford","Leeds",
    "Fulham","Forest","Burnley","Bournemouth","Celta Vigo"
]

# =================================================
# MYANMAR / COMMON ALIAS
# =================================================
MYANMAR_TEAM_ALIAS = {
    "man city": "Manchester City",
    "man united": "Manchester United",
    "man u": "Manchester United",
    "မန်စီးတီး": "Manchester City",
    "ရီးရဲ": "Real Madrid",
    "ရီးရဲလ်": "Real Madrid",
    "ရီးရဲမက်ဒရစ်": "Real Madrid",
    "လီပါပူး": "Liverpool",
    "ဗီလာရီးရဲလ်": "Villarreal",
    "နယူး": "Newcastle",
    "ဘရိုက်တန်": "Brighton",
    "aston villa": "Aston Villa",
    "west ham": "West Ham",
    "wolves": "Wolves",
    "athletic club": "Athletic Club",
    "tottenham hotspur": "Tottenham",
    "celta vigo": "Celta Vigo"
}

# =================================================
# REGEX
# =================================================
USER_HEADER = re.compile(
    r"^(.+?),\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\]$"
)
PHONE_PATTERN = re.compile(r"(?:\+?959|09)\d{7,12}")
USER_ACC_KEYWORDS = re.compile(r"(ok\s*bet|okbet|slot|shank|bet)", re.I)

# =================================================
# HELPERS
# =================================================
def extract_username(line):
    m = USER_HEADER.match(line)
    return m.group(1).strip() if m else None

def is_user_acc(line):
    return bool(PHONE_PATTERN.search(line) or USER_ACC_KEYWORDS.search(line))

def normalize_raw_token(text: str) -> str:
    cleaned = re.sub(r"^[^က-႟A-Za-z]+|[^က-႟A-Za-z]+$", "", text)
    return cleaned.strip().lower()

def is_other_comment(text: str) -> bool:
    if not text:
        return True
    if len(text) > 20:
        return True
    if " " in text and text.lower() not in MYANMAR_TEAM_ALIAS:
        return True
    if re.fullmatch(r"[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){1,2}", text):
        return True
    return False

def normalize_team(raw_text):
    raw = normalize_raw_token(raw_text)

    if raw in LEARNED_MAP:
        return LEARNED_MAP[raw], "team"

    if raw in MYANMAR_TEAM_ALIAS:
        return MYANMAR_TEAM_ALIAS[raw], "team"

    match = get_close_matches(raw.title(), STANDARD_TEAMS, n=1, cutoff=0.85)
    if match:
        return match[0], "team"

    if is_other_comment(raw_text):
        return raw_text, "other"

    return raw_text, "unknown"

# =================================================
# MAIN PARSER
# =================================================
def parse_txt(file):
    if file is None:
        return None, None, None, None, None

    text = file.read().decode("utf-8")

    blocks = re.split(
        r"(?=^.+?,\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\])",
        text,
        flags=re.MULTILINE
    )

    records = []
    unknown_list = []

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        username = extract_username(lines[0])
        if not username:
            continue

        teams, others, accounts = [], [], []

        for line in lines[1:]:
            if is_user_acc(line):
                accounts.append(line)
                continue

            value, kind = normalize_team(line)

            if kind == "team":
                teams.append(value)
            elif kind == "other":
                others.append(line)
            else:
                unknown_list.append(line)

        records.append({
            "Username": username,
            "Teams (STANDARD)": ", ".join(dict.fromkeys(teams)),
            "Other Comment": ", ".join(dict.fromkeys(others)),
            "User Acc": ", ".join(dict.fromkeys(accounts))
        })

    df = pd.DataFrame(records)

    unknown_counter = Counter(unknown_list)
    unknown_df = pd.DataFrame(
        [{"Unknown": k, "Count": v} for k, v in unknown_counter.items()]
    ).sort_values("Count", ascending=False)

    return (
        df,
        unknown_df,
        unknown_df["Unknown"].tolist(),
        None,
        "Parsed users: {}".format(len(df))
    )

# =================================================
# ADMIN APPLY
# =================================================
def apply_mapping(selected_unknowns, correct_team):
    if not selected_unknowns:
        return "No unknown selected"

    for raw in selected_unknowns:
        key = normalize_raw_token(raw)
        LEARNED_MAP[key] = correct_team

    atomic_save_mapping(LEARNED_MAP)
    return f"Saved {len(selected_unknowns)} mappings → {correct_team}"

# =================================================
# UI
# =================================================
with gr.Blocks(title="Telegram TXT Parser (Gradio Stable)") as demo:
    gr.Markdown("## 📄 Telegram TXT Parser (Stable · No AI · Free)")

    file_input = gr.File(label="Upload TXT file", file_types=[".txt"])

    parse_btn = gr.Button("▶ Parse")

    status = gr.Markdown()

    df_out = gr.Dataframe(label="User Data", interactive=False)

    gr.Markdown("### 🔴 Admin Roll – Unknown Teams")

    unknown_table = gr.Dataframe(label="Unknown Teams (Frequency)")
    unknown_select = gr.CheckboxGroup(label="Select Unknown")
    team_select = gr.Dropdown(STANDARD_TEAMS, label="Correct Standard Team")
    save_btn = gr.Button("💾 Apply & Save")
    save_status = gr.Markdown()

    parse_btn.click(
        parse_txt,
        inputs=file_input,
        outputs=[df_out, unknown_table, unknown_select, team_select, status]
    )

    save_btn.click(
        apply_mapping,
        inputs=[unknown_select, team_select],
        outputs=save_status
    )

demo.launch()
