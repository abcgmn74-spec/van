import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Pro Extractor", layout="wide")

# ၁။ Standard Teams စာရင်း (Premiere, Laliga, Serie A အစုံ)
STANDARD_TEAMS = [
    "Arsenal", "Aston Villa", "Barcelona", "Brighton", "Chelsea", 
    "Everton", "Liverpool", "Manchester City", "Manchester United", 
    "Newcastle United", "Real Madrid", "Sevilla", "Tottenham Hotspur", 
    "Villarreal", "Atletico Madrid", "Inter Milan", "AC Milan", "Juventus", "Napoli"
]

# ၂။ ဖိုင်ထဲမှာပါတဲ့ မြန်မာလို ရေးထုံးမျိုးစုံကို Standard Name သို့ ပြောင်းလဲခြင်း
TEAM_MAP = {
    # Manchester City & United
    "မန်စီး": "Manchester City", "မန်စီးတီး": "Manchester City", "mancity": "Manchester City",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "man u": "Manchester United",
    # Liverpool & Arsenal
    "လီပါပူး": "Liverpool", "လီဗာပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal",
    # Barcelona & Real Madrid
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "ဘာကာ": "Barcelona", "ဘာဂါ": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "ရီးရယ်": "Real Madrid", "ရီရဲ": "Real Madrid", "real madrid": "Real Madrid",
    # Newcastle & Brighton
    "နယူကာဆယ်": "Newcastle United", "နယူး": "Newcastle United", "newcastle": "Newcastle United",
    "ဘရိုက်တန်": "Brighton", "brighton": "Brighton",
    # Aston Villa & Everton
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "aston villa": "Aston Villa",
    "အဲဗာတန်": "Everton", "အက်ဗာတန်": "Everton", "everton": "Everton", "ဝက်ဟမ်း": "West Ham",
    # Others
    "စပါး": "Tottenham Hotspur", "ဆီးဗီလာ": "Sevilla", "ဆီဗီလာ": "Sevilla", "sevilla": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "villareal": "Villarreal"
}

def get_std_team(text):
    text_lower = text.strip().lower()
    # Dictionary မှာ အရင်စစ်မယ်
    for key, val in TEAM_MAP.items():
        if key.lower() == text_lower or key.lower() in text_lower:
            return val
    # Fuzzy Match (၈၅% ကျော်မှ ယူမယ်)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    return None

st.title("⚽ Football Data Pro Extractor")
st.write("Upload လုပ်ထားသော File ထဲက အသင်းအမည်များကို Standard အမည်များဖြင့် အလိုအလျောက် ခွဲခြားပေးပါမည်။")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    # Telegram pattern: Name, [Date Time]
    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    for line in lines:
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
            is_phone = (len(clean_num) >= 6 and (line.startswith('09') or line.startswith('959') or 
                        any(x in line.lower() for x in ['ok', 'bet', 'best', 'ph']))) or (len(clean_num) >= 9)

            if is_phone:
                current_user["Phone"] = clean_num
            else:
                # အသင်းအမည် ဟုတ်/မဟုတ် စစ်ခြင်း
                cleaned_text = re.sub(r'^\d+[\s\.\)]+', '', line) # 1. 2. စတဲ့ နံပါတ်စဉ်ဖယ်ထုတ်ခြင်း
                if cleaned_text and cleaned_text != current_user["Name"]:
                    std_name = get_std_team(cleaned_text)
                    if std_name:
                        if std_name not in current_user["Teams"]:
                            current_user["Teams"].append(std_name)
                    else:
                        current_user["Other_Comments"].append(cleaned_text)

    if current_user: parsed_data.append(current_user)

    # Sidebar Filter
    st.sidebar.header("စစ်ထုတ်ရန် Settings")
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန် (Standard Name):", sorted(STANDARD_TEAMS))

    final_list = []
    for u in parsed_data:
        if selected_teams:
            if not any(t in u['Teams'] for t in selected_teams): continue

        final_list.append({
            "User Name": u['User Name' if 'User Name' in u else 'Name'],
            "Phone Number": u['Phone'],
            "Football Teams": ", ".join(u['Teams']),
            "Other Comments": ", ".join(u['Other_Comments'])
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"တွေ့ရှိသူစုစုပေါင်း: {len(final_list)} ဦး")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_final_data.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
