import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Extractor", layout="wide")

# Standard Teams
STANDARD_TEAMS = [
    "Liverpool", "Arsenal", "Manchester United", "Manchester City", 
    "Chelsea", "Tottenham Hotspur", "Aston Villa", "Newcastle United", 
    "Brighton", "Real Madrid", "Barcelona", "Sevilla", "Villarreal"
]

TEAM_MAP = {
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United",
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City",
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "ရီရဲ": "Real Madrid",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa",
    "ဘရိုက်တန်": "Brighton", "နယူး": "Newcastle United",
    "စပါး": "Tottenham Hotspur", "ဆီးဗီလာ": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal"
}

def get_std_name(text):
    text = text.strip()
    if not text: return None
    for key, val in TEAM_MAP.items():
        if key in text or text in key: return val
    match, score = process.extractOne(text, STANDARD_TEAMS)
    return match if score > 80 else None

st.title("⚽ Football User Scanner (၄၀၀+ အကုန်ဖတ်ရန်)")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    # ဖိုင်ကို ဖတ်ပြီး စာကြောင်းအလိုက် ခွဲထုတ်ခြင်း
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    
    # Telegram Format: "Name, [Date Time]" ကို ရှာရန် Regex
    user_pattern = re.compile(r'(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # User အသစ် စတင်ကြောင်း စစ်ဆေးခြင်း
        match = user_pattern.search(line)
        if match:
            if current_user and len(current_user['Teams']) > 0:
                parsed_data.append(current_user)
            
            current_user = {
                "Name": match.group(1),
                "Phone": "မသိပါ",
                "Teams": []
            }
            continue
        
        if current_user:
            # ဖုန်းနံပတ် ရှာခြင်း
            phone_match = re.search(r'(959\d{8,10}|09\d{7,9})', line)
            if phone_match:
                current_user["Phone"] = phone_match.group(1)
            else:
                # အသင်းအမည် ဖြစ်နိုင်ခြေရှိသည်ကို စစ်ထုတ်ခြင်း
                clean_name = re.sub(r'^\d+[\s\.\)]+', '', line)
                std_name = get_std_name(clean_name)
                if std_name and std_name not in current_user["Teams"]:
                    current_user["Teams"].append(std_name)

    # နောက်ဆုံး User ကို ထည့်သွင်းခြင်း
    if current_user and len(current_user['Teams']) > 0:
        parsed_data.append(current_user)

    # --- Filtering Section ---
    st.sidebar.header("စစ်ထုတ်ခြင်း")
    only_5 = st.sidebar.checkbox("၅ သင်းအတိအကျ ရွေးထားသူများသာ", value=True)
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန်", STANDARD_TEAMS)

    final_list = []
    for u in parsed_data:
        count = len(u['Teams'])
        # ၅ သင်း filter
        if only_5 and count != 5: continue
        
        # အသင်း filter
        if selected_teams:
            if not any(t in u['Teams'] for t in selected_teams):
                continue

        final_list.append({
            "နာမည်": u['Name'],
            "ဖုန်းနံပတ်": u['Phone'],
            "ရွေးချယ်ထားသော အသင်းများ": ", ".join(u['Teams']),
            "အရေအတွက်": count
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"စုစုပေါင်း အသုံးပြုသူ {len(final_list)} ဦး တွေ့ရှိပါသည်။")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန်", csv, "all_users.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
