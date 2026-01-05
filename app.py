import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Extractor", layout="wide")

# Standardized Team Names for Filter
STANDARD_TEAMS = [
    "Liverpool", "Arsenal", "Manchester United", "Manchester City", 
    "Chelsea", "Tottenham Hotspur", "Aston Villa", "Newcastle United", 
    "Brighton", "Real Madrid", "Barcelona", "Sevilla", "Villarreal"
]

# Mapping all variations to a single Standard Name
TEAM_MAP = {
    # Manchester United
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "man u": "Manchester United", 
    "manutd": "Manchester United", "manchester united": "Manchester United", "manu": "Manchester United",
    # Liverpool
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "liverpool": "Liverpool",
    # Arsenal
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal", "arsenal": "Arsenal",
    # Man City
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City", "mancity": "Manchester City", "manchester city": "Manchester City",
    # Barcelona
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "barcelona": "Barcelona", "barca": "Barcelona",
    # Real Madrid
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "ရီရဲ": "Real Madrid", "real madrid": "Real Madrid",
    # Others
    "ဗီလာ": "Aston Villa", "aston villa": "Aston Villa", "astin villa": "Aston Villa",
    "ဘရိုက်တန်": "Brighton", "brighton": "Brighton",
    "နယူး": "Newcastle United", "newcastle": "Newcastle United", "နယူကာဆယ်": "Newcastle United",
    "စပါး": "Tottenham Hotspur", "spur": "Tottenham Hotspur", "tottenham": "Tottenham Hotspur",
    "ဆီးဗီလာ": "Sevilla", "sevilla": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "villareal": "Villarreal"
}

def get_std_team(text):
    text_lower = text.strip().lower()
    # ၁။ Map ထဲမှာ တိုက်ရိုက်စစ်ခြင်း
    for key, val in TEAM_MAP.items():
        if key.lower() in text_lower or text_lower in key.lower():
            return val
    # ၂။ Fuzzy Match (English)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    return None

st.title("⚽ Football Data Pro Extractor")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
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
            # ၁။ ဖုန်းနံပတ် စစ်ခြင်း (ဂဏန်း ၆ လုံးနှင့်အထက်)
            clean_num = re.sub(r'[^0-9]', '', line)
            if len(clean_num) >= 6 and (line.startswith('09') or line.startswith('959') or any(x in line.lower() for x in ['ok', 'bet', 'ph'])):
                current_user["Phone"] = clean_num
            elif len(clean_num) >= 9: # စာသားမပါဘဲ ဂဏန်းချည်းပဲ ၉ လုံးကျော်ရင်လည်း ဖုန်းလို့ယူမယ်
                current_user["Phone"] = clean_num
            else:
                # ၂။ အသင်းအမည် ဟုတ်/မဟုတ် စစ်ခြင်း
                cleaned_text = re.sub(r'^\d+[\s\.\)]+', '', line) # နံပါတ်စဉ်ဖယ်
                if cleaned_text and cleaned_text != current_user["Name"]:
                    std_name = get_std_team(cleaned_text)
                    if std_name:
                        if std_name not in current_user["Teams"]:
                            current_user["Teams"].append(std_name)
                    else:
                        # ၃။ အသင်းမဟုတ်လျှင် Other Comments ထဲထည့်
                        current_user["Other_Comments"].append(cleaned_text)

    if current_user: parsed_data.append(current_user)

    # --- Sidebar Filter ---
    st.sidebar.header("Filter Settings")
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန် (Standard Name):", STANDARD_TEAMS)

    final_list = []
    for u in parsed_data:
        if selected_teams:
            if not any(t in u['Teams'] for t in selected_teams): continue

        final_list.append({
            "User Name": u['Name'],
            "Phone Number": u['Phone'],
            "Football Teams": ", ".join(u['Teams']),
            "Other Comments": ", ".join(u['Other_Comments'])
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"တွေ့ရှိသူစုစုပေါင်း: {len(final_list)} ဦး")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_data.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
