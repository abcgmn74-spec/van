import streamlit as st
import pandas as pd
import re
import google.generativeai as genai

st.set_page_config(page_title="Football Data AI Pro", layout="wide")

# --- Gemini API Setup ---
# Sidebar မှာ API Key ထည့်ခိုင်းမယ် (လုံခြုံရေးအတွက်)
api_key = st.sidebar.text_input("Gemini API Key ကိုထည့်ပါ:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.sidebar.warning("API Key မရှိရင် Mapping Dictionary နဲ့ပဲ အလုပ်လုပ်ပါမယ်။")

# Standard Dictionary (Backup အနေနဲ့ ထည့်ထားဆဲဖြစ်သည်)
TEAM_MAP = {
    "မန်စီး": "Manchester City", "မန်ယူ": "Manchester United", "လီဗာပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "ဘာစီ": "Barcelona", "ရီးရဲ": "Real Madrid",
    "ဗီလာ": "Aston Villa", "ဘရိုက်တန်": "Brighton", "နယူး": "Newcastle United"
}

def translate_team_with_ai(text):
    # ၁။ အရင်ဆုံး Dictionary ထဲမှာ ပါလားကြည့်မယ် (API ခေါ်တာ သက်သာအောင်)
    for key, val in TEAM_MAP.items():
        if key in text:
            return val
    
    # ၂။ Dictionary ထဲမှာမပါရင် Gemini API ကို မေးမယ်
    if api_key:
        try:
            prompt = f"Convert this Myanmar football team name or informal text to its standard English professional name. Return ONLY the English name. If not a team, return 'Other'. Text: {text}"
            response = model.generate_content(prompt)
            result = response.text.strip()
            if result != "Other":
                return result
        except:
            pass
    return None

st.title("⚽ Football Data Extractor (Gemini AI Powered)")

uploaded_file = st.file_uploader("Telegram File (.txt) ကို Upload တင်ပါ", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    # Loading bar ပြပေးမယ်
    progress_bar = st.progress(0)
    total_lines = len(lines)

    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        
        match = user_pattern.match(line)
        if match:
            if current_user: parsed_data.append(current_user)
            current_user = {"Name": match.group(1), "Phone": "-", "Teams": [], "Other_Comments": []}
            continue
        
        if current_user:
            # ဖုန်းနံပတ် စစ်ဆေးခြင်း
            clean_num = re.sub(r'[^0-9]', '', line)
            if len(clean_num) >= 6 and (line.startswith('09') or line.startswith('959') or 'bet' in line.lower()):
                current_user["Phone"] = clean_num
            else:
                # AI သုံးပြီး အသင်းအမည် ပြောင်းလဲခြင်း
                team_name = translate_team_with_ai(line)
                if team_name and team_name != "Other":
                    if team_name not in current_user["Teams"]:
                        current_user["Teams"].append(team_name)
                else:
                    if line != current_user["Name"]:
                        current_user["Other_Comments"].append(line)
        
        progress_bar.progress((i + 1) / total_lines)

    if current_user: parsed_data.append(current_user)

    # --- Filter Section ---
    st.sidebar.header("🔍 Filters")
    show_only_five = st.sidebar.checkbox("နှစ်ခုပေါင်း ၅ ခု ရှိသူများသာ", value=True)

    final_list = []
    for u in parsed_data:
        total_count = len(u['Teams']) + len(u['Other_Comments'])
        if show_only_five and total_count != 5:
            continue

        final_list.append({
            "User Name": u['Name'],
            "Phone Number": u['Phone'],
            "Football Teams": ", ".join(u['Teams']),
            "Other Comments": ", ".join(u['Other_Comments']),
            "Count": total_count
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 CSV ဒေါင်းလုဒ်ဆွဲရန်", df.to_csv(index=False).encode('utf-8-sig'), "ai_report.csv")
