import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Scanner", layout="wide")

# Standard Teams for Matching
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

def clean_team_name(text):
    text = text.strip()
    if not text: return None
    # ၁။ Map ထဲမှာရှိလားအရင်စစ်
    for key, val in TEAM_MAP.items():
        if key in text: return val
    # ၂။ English Standard ထဲမှာရှိလားစစ်
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    return text # အသင်းမဟုတ်ရင် မူရင်းစာသားအတိုင်းပြန်ပေးမယ်

st.title("⚽ Football Data Extractor (Full Scan)")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    
    # Telegram timestamp pattern: Name, [1/1/2026 9:30 AM]
    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # User အသစ် စတင်ကြောင်းစစ်ဆေး
        match = user_pattern.match(line)
        if match:
            if current_user:
                parsed_data.append(current_user)
            
            current_user = {
                "Name": match.group(1),
                "Phone": "Unknown",
                "Teams": []
            }
            continue
        
        if current_user:
            # Phone number detection
            phone_match = re.search(r'(959\d{8,10}|09\d{7,9})', line)
            if phone_match:
                current_user["Phone"] = phone_match.group(1)
            else:
                # အသင်း (သို့မဟုတ်) ရေးထားတဲ့စာသားကို သန့်စင်ပြီးသိမ်းဆည်း
                cleaned = re.sub(r'^\d+[\s\.\)]+', '', line) # နံပါတ်စဉ်ဖယ်
                if cleaned and cleaned != current_user["Name"]:
                    std_name = clean_team_name(cleaned)
                    if std_name:
                        current_user["Teams"].append(std_name)

    if current_user:
        parsed_data.append(current_user)

    # --- Filter Options ---
    st.sidebar.header("Filter Settings")
    only_5 = st.sidebar.checkbox("၅ ခု အတိအကျမန့်သူများကိုသာ ပြရန်", value=False)
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန် (Standard အမည်များ)", STANDARD_TEAMS)

    final_list = []
    for u in parsed_data:
        # အရေအတွက်စစ်ခြင်း
        count = len(u['Teams'])
        if only_5 and count != 5:
            continue
            
        # အသင်းစစ်ထုတ်ခြင်း
        if selected_teams:
            # User ရဲ့ list ထဲမှာ ရွေးထားတဲ့ standard အသင်းပါမှပြမယ်
            if not any(t in u['Teams'] for t in selected_teams):
                continue

        final_list.append({
            "User Name": u['Name'],
            "Phone": u['Phone'],
            "Selected Items": ", ".join(u['Teams']),
            "Count": count
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"စုစုပေါင်း အသုံးပြုသူ {len(final_list)} ဦးကို ရှာဖွေတွေ့ရှိပါသည်။")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result ကို CSV အနေနဲ့ သိမ်းရန်", csv, "football_results.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
