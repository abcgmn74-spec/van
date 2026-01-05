import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Final", layout="wide")

# Standard Teams
STANDARD_TEAMS = [
    "Arsenal", "Aston Villa", "Barcelona", "Brighton", "Chelsea", "Everton", "Liverpool", 
    "Manchester City", "Manchester United", "Newcastle United", "Real Madrid", "Sevilla", 
    "Tottenham Hotspur", "Villarreal", "Atletico Madrid", "West Ham", "AC Milan", "Inter Milan", "Juventus"
]

# Mapping Variations to Standard Name
TEAM_MAP = {
    "မန်စီး": "Manchester City", "မန်စီးတီး": "Manchester City", "mancity": "Manchester City", "man city": "Manchester City",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "man u": "Manchester United", "manu": "Manchester United",
    "လီပါပူး": "Liverpool", "လီဗာပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool", "liverpool": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "arsenal": "Arsenal",
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "ဘာကာ": "Barcelona", "ဘာဂါ": "Barcelona", "barca": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "ရီးရယ်": "Real Madrid", "ရီရဲ": "Real Madrid", "real": "Real Madrid", "madrid": "Real Madrid",
    "နယူကာဆယ်": "Newcastle United", "နယူး": "Newcastle United", "newcastle": "Newcastle United",
    "ဘရိုက်တန်": "Brighton", "brighton": "Brighton",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "aston villa": "Aston Villa",
    "အဲဗာတန်": "Everton", "everton": "Everton", "ဝက်ဟမ်း": "West Ham", "westham": "West Ham",
    "စပါး": "Tottenham Hotspur", "spurs": "Tottenham Hotspur", "tottenham": "Tottenham Hotspur",
    "ဆီးဗီလာ": "Sevilla", "ဆီဗီလာ": "Sevilla", "sevilla": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "villareal": "Villarreal": "လီဗာပူလ်း"
}

def get_std_team(text):
    # ရှေ့က နံပါတ်စဉ်တွေ ဖယ်ထုတ်ခြင်း (ဥပမာ - "1. ဗီလာ" -> "ဗီလာ")
    text = re.sub(r'^\d+[\s\.\)-]+', '', text).strip()
    text_lower = text.lower()
    
    # ၁။ Map ထဲမှာ တိုက်ရိုက်ပါလား အရင်စစ်မယ်
    for key, val in TEAM_MAP.items():
        if key.lower() == text_lower or key.lower() in text_lower:
            return val
            
    # ၂။ Fuzzy Match (၈၀% အထိ လျှော့စစ်မယ်)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 80: return match
    return None

st.title("⚽ Football Data Pro (Final Fixed Version)")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    all_other_comments = set()
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
            # ဖုန်းနံပတ် စစ်ခြင်း
            clean_num = re.sub(r'[^0-9]', '', line)
            is_phone = (len(clean_num) >= 6 and (line.startswith('09') or line.startswith('959') or 
                        any(x in line.lower() for x in ['ok', 'bet', 'best', 'ph', 'tel']))) or (len(clean_num) >= 9)

            if is_phone:
                current_user["Phone"] = clean_num
            else:
                # အသင်းဟုတ်၊ မဟုတ် အရင်စစ်မယ်
                std_name = get_std_team(line)
                
                if std_name:
                    if std_name not in current_user["Teams"]:
                        current_user["Teams"].append(std_name)
                else:
                    # အသင်းလည်းမဟုတ်၊ ဖုန်းလည်းမဟုတ်၊ User Name လည်းမဟုတ်မှ Other ထဲထည့်မယ်
                    if line.strip() != current_user["Name"]:
                        current_user["Other_Comments"].append(line.strip())
                        all_other_comments.add(line.strip())

    if current_user: parsed_data.append(current_user)

    # --- Filters ---
    st.sidebar.header("🔍 Filters")
    selected_teams = st.sidebar.multiselect("အသင်းများဖြင့် စစ်ထုတ်ရန်:", sorted(STANDARD_TEAMS))
    selected_others = st.sidebar.multiselect("Other Comments ဖြင့် စစ်ထုတ်ရန်:", sorted(list(all_other_comments)))
    show_only_five = st.sidebar.checkbox("နှစ်ခုပေါင်း ၅ ခု အတိအကျရှိသူများကိုသာ ပြရန်", value=True)

    final_list = []
    for u in parsed_data:
        # Filter logic
        matches_team = any(t in u['Teams'] for t in selected_teams) if selected_teams else True
        matches_other = any(o in u['Other_Comments'] for o in selected_others) if selected_others else True
        
        if not (matches_team and matches_other): continue
            
        total_count = len(u['Teams']) + len(u['Other_Comments'])
        if show_only_five and total_count != 5: continue

        final_list.append({
            "User Name": u['Name'],
            "Phone Number": u['Phone'],
            "Football Teams": ", ".join(u['Teams']),
            "Other Comments": ", ".join(u['Other_Comments']),
            "Total Items": total_count
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"တွေ့ရှိသူစုစုပေါင်း: {len(final_list)} ဦး")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_fixed.csv", "text/csv")

