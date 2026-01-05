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
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United",
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City", "Mancity": "Manchester City",
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "ရီရဲ": "Real Madrid", "Real madrid": "Real Madrid",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "Aston villa": "Aston Villa",
    "ဘရိုက်တန်": "Brighton", "နယူး": "Newcastle United", "Newcastle": "Newcastle United",
    "စပါး": "Tottenham Hotspur", "ဆီးဗီလာ": "Sevilla", "ဆီဗီလာ": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "Villareal": "Villarreal"
}

def clean_team_name(text):
    text = text.strip()
    if not text: return None
    # ၁။ Map စစ်ဆေးခြင်း
    for key, val in TEAM_MAP.items():
        if key.lower() in text.lower(): return val
    # ၂။ Fuzzy Match (English)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    return text 

st.title("⚽ Football Data Extractor (Smart Phone Detection)")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    all_extracted_items = set() 
    
    # Telegram timestamp pattern
    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = user_pattern.match(line)
        if match:
            if current_user:
                parsed_data.append(current_user)
            
            current_user = {
                "Name": match.group(1),
                "Phone": "မသိပါ",
                "Teams": []
            }
            continue
        
        if current_user:
            # ဖုန်းနံပတ် စစ်ထုတ်ခြင်း - 09 သို့မဟုတ် 959 နဲ့စတာအပြင် ဂဏန်း ၆ လုံးအထက်ပါရင် ယူမယ်
            # (Regex: 09 သို့မဟုတ် 959 ပါသော နံပါတ်များ သို့မဟုတ် ဂဏန်းသက်သက် ၆ လုံးနှင့်အထက်)
            phone_match = re.search(r'(09\d{7,11}|959\d{7,11}|\d{6,15})', line.replace(" ", "").replace("-", ""))
            
            if phone_match:
                # လက်ရှိ User မှာ ဖုန်းနံပတ် မရှိသေးရင် သို့မဟုတ် ပိုရှည်တဲ့ နံပါတ်တွေ့ရင် Update လုပ်မယ်
                current_user["Phone"] = phone_match.group(1)
            else:
                # အသင်း (သို့မဟုတ်) စာသား
                cleaned = re.sub(r'^\d+[\s\.\)]+', '', line) # နံပါတ်စဉ်ဖယ်ထုတ်ခြင်း
                if cleaned and cleaned != current_user["Name"]:
                    std_name = clean_team_name(cleaned)
                    if std_name:
                        current_user["Teams"].append(std_name)
                        all_extracted_items.add(std_name)

    if current_user:
        parsed_data.append(current_user)

    # --- Sidebar Filter ---
    st.sidebar.header("စစ်ထုတ်ရန် Settings")
    filter_options = sorted(list(all_extracted_items))
    selected_items = st.sidebar.multiselect(
        "မန့်ထားသော စာသားများအလိုက် စစ်ထုတ်ရန်:", 
        options=filter_options
    )

    final_list = []
    for u in parsed_data:
        if selected_items:
            # User ရွေးထားတဲ့ item ထဲမှာ filter လုပ်ထားတဲ့ item တစ်ခုခု ပါ/မပါ စစ်ခြင်း
            if not any(item in u['Teams'] for item in selected_items):
                continue

        final_list.append({
            "နာမည်": u['Name'],
            "ဖုန်းနံပတ်": u['Phone'],
            "မန့်ထားသောစာသားများ": ", ".join(u['Teams']),
            "အရေအတွက်": len(u['Teams'])
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"စုစုပေါင်း {len(final_list)} ဦး တွေ့ရှိပါသည်။")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_report.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
