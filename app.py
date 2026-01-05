import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Pro Extractor", layout="wide")

# Standard Teams
STANDARD_TEAMS = [
    "Arsenal", "Aston Villa", "Barcelona", "Brighton", "Chelsea", 
    "Everton", "Liverpool", "Manchester City", "Manchester United", 
    "Newcastle United", "Real Madrid", "Sevilla", "Tottenham Hotspur", 
    "Villarreal", "Atletico Madrid", "West Ham"
]

# Mapping (မြန်မာအခေါ်အဝေါ်များ)
TEAM_MAP = {
    "မန်စီး": "Manchester City", "မန်စီးတီး": "Manchester City", "mancity": "Manchester City",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "man u": "Manchester United",
    "လီပါပူး": "Liverpool", "လီဗာပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "ဘာကာ": "Barcelona", "ဘာဂါ": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "ရီးရယ်": "Real Madrid", "ရီရဲ": "Real Madrid",
    "နယူကာဆယ်": "Newcastle United", "နယူး": "Newcastle United", "ဘရိုက်တန်": "Brighton",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "အဲဗာတန်": "Everton", "ဝက်ဟမ်း": "West Ham"
}

def get_std_team(text):
    text_lower = text.strip().lower()
    for key, val in TEAM_MAP.items():
        if key.lower() == text_lower or key.lower() in text_lower:
            return val
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    return None

st.title("⚽ Football Data Pro (Dual Filter System)")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    all_other_comments = set() # Other filter အတွက် list ထုတ်ရန်
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
            clean_num = re.sub(r'[^0-9]', '', line)
            is_phone = (len(clean_num) >= 6 and (line.startswith('09') or line.startswith('959') or 
                        any(x in line.lower() for x in ['ok', 'bet', 'best', 'ph']))) or (len(clean_num) >= 9)

            if is_phone:
                current_user["Phone"] = clean_num
            else:
                cleaned_text = re.sub(r'^\d+[\s\.\)]+', '', line)
                if cleaned_text and cleaned_text != current_user["Name"]:
                    std_name = get_std_team(cleaned_text)
                    if std_name:
                        if std_name not in current_user["Teams"]:
                            current_user["Teams"].append(std_name)
                    else:
                        current_user["Other_Comments"].append(cleaned_text)
                        all_other_comments.add(cleaned_text)

    if current_user: parsed_data.append(current_user)

    # --- Sidebar Filters ---
    st.sidebar.header("🔍 Filters")
    
    # ၁။ ဘောလုံးအသင်း Filter
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန်:", sorted(STANDARD_TEAMS))
    
    # ၂။ တခြားမှတ်ချက် Filter
    selected_others = st.sidebar.multiselect("တခြားမှတ်ချက် (Other) များဖြင့် စစ်ထုတ်ရန်:", sorted(list(all_other_comments)))
    
    # ၃။ ၅ ခုပြည့်သူများကိုသာ ပြရန်
    show_only_five = st.sidebar.checkbox("၅ သင်းအတိအကျ ရွေးထားသူများကိုသာ ပြရန်", value=False)

    final_list = []
    for u in parsed_data:
        # Team Filter Logic
        if selected_teams:
            if not any(t in u['Teams'] for t in selected_teams): continue
            
        # Other Comment Filter Logic
        if selected_others:
            if not any(o in u['Other_Comments'] for o in selected_others): continue
            
        # 5-Team Count Logic
        team_count = len(u['Teams'])
        if show_only_five and team_count != 5:
            continue

        final_list.append({
            "User Name": u['Name'],
            "Phone Number": u['Phone'],
            "Football Teams": ", ".join(u['Teams']),
            "Other Comments": ", ".join(u['Other_Comments']),
            "Count": team_count
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"တွေ့ရှိသူစုစုပေါင်း: {len(final_list)} ဦး")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_dual_filter.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။ Filter များကို ပြန်စစ်ပေးပါ။")
