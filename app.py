import streamlit as st
import pandas as pd
import re
from thefuzz import process

# စာမျက်နှာ အပြင်အဆင်
st.set_page_config(page_title="Football 5-Team Filter", layout="wide")

# Standard English Team Names
STANDARD_TEAMS = [
    "Liverpool", "Arsenal", "Manchester United", "Manchester City", 
    "Chelsea", "Tottenham Hotspur", "Aston Villa", "Newcastle United", 
    "Brighton", "Real Madrid", "Barcelona", "Sevilla", "Villarreal"
]

# စာလုံးပေါင်းသတ်မှတ်ချက်များ
TEAM_MAP = {
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal", "Arsenal": "Arsenal",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "Man United": "Manchester United", "Man Utd": "Manchester United",
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City", "Man City": "Manchester City", "Mancity": "Manchester City",
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "Barcelona": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "Real Madrid": "Real Madrid", "ရီရဲ": "Real Madrid", "Real madrid": "Real Madrid",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "Aston Villa": "Aston Villa", "Astin Villa": "Aston Villa", "ဗယ်လာ": "Aston Villa",
    "ဘရိုက်တန်": "Brighton", "Brighton": "Brighton",
    "နယူး": "Newcastle United", "နယူးကာဆယ်": "Newcastle United", "Newcastle": "Newcastle United", "နယူကာဆယ်": "Newcastle United",
    "စပါး": "Tottenham Hotspur", "Spur": "Tottenham Hotspur", "Tottenham": "Tottenham Hotspur",
    "ဆီးဗီလာ": "Sevilla", "Sevilla": "Sevilla", "ဆီဗီလာ": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "Villareal": "Villarreal", "Villarreal": "Villarreal"
}

def get_standard_name(text):
    text = text.strip()
    if not text: return None
    # ၁။ တိုက်ရိုက်စစ်ခြင်း
    for key, val in TEAM_MAP.items():
        if key.lower() == text.lower():
            return val
    # ၂။ Fuzzy Match (၈၅% ကျော်မှ ယူမည်)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    return match if score > 85 else None

st.title("⚽ Football Filter (၅ သင်းပြည့်စစ်ထုတ်စနစ်)")

uploaded_file = st.file_uploader("Telegram စာသားဖိုင် (.txt) ကို Upload လုပ်ပါ", type=["txt"])

if uploaded_file:
    raw_content = uploaded_file.getvalue().decode("utf-8")
    user_blocks = re.split(r'\n\s*\n', raw_content)
    
    parsed_data = []
    
    for block in user_blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 2: continue
        
        user_name = lines[0].split(',')[0]
        phone = "မသိပါ"
        temp_teams = []
        
        for line in lines:
            # Phone number parsing (959 သို့မဟုတ် 09)
            phone_match = re.search(r'(959\d{8,10}|09\d{7,9})', line)
            if phone_match:
                phone = phone_match.group(1)
            
            # Team name parsing
            elif "[" not in line and line != user_name:
                # နံပါတ်စဉ်များ ဖယ်ထုတ်ခြင်း (ဥပမာ 1. 2.)
                clean_name = re.sub(r'^\d+[\s\.\)]+', '', line)
                std_name = get_standard_name(clean_name)
                if std_name:
                    temp_teams.append(std_name)

        # Duplicate ဖယ်ထုတ်ပြီး ၅ သင်းအတိအကျ ရှိ/မရှိ စစ်ဆေးခြင်း
        unique_teams = list(dict.fromkeys(temp_teams))
        
        parsed_data.append({
            "User Name": user_name,
            "Phone": phone,
            "Teams": unique_teams,
            "Count": len(unique_teams)
        })

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Settings")
    
    # ၅ သင်းပြည့်သူများကိုသာ ပြရန် Option
    only_five = st.sidebar.checkbox("၅ သင်းအတိအကျ ရွေးထားသူများကိုသာ ပြရန်", value=True)
    
    # အသင်းအများကြီး ရွေးနိုင်သော Filter
    selected_teams = st.sidebar.multiselect(
        "အသင်းများကို ရွေးချယ်ပါ (Optional):", 
        options=STANDARD_TEAMS
    )

    # Filtering Logic
    filtered_list = []
    for u in parsed_data:
        # အခြေအနေ ၁: ၅ သင်းပြည့်ရမယ် (Checkbox ရွေးထားရင်)
        if only_five and u['Count'] != 5:
            continue
            
        # အခြေအနေ ၂: ကိုယ်ရွေးလိုက်တဲ့ အသင်းတွေ ပါရမယ်
        if selected_teams:
            matches = [t for t in u['Teams'] if t in selected_teams]
            if not matches:
                continue
            match_str = ", ".join(matches)
        else:
            match_str = "All Selected"

        filtered_list.append({
            "နာမည်": u['User Name'],
            "ဖုန်းနံပတ်": u['Phone'],
            "ရွေးချယ်ထားသော အသင်းများ": ", ".join(u['Teams']),
            "အသင်းအရေအတွက်": u['Count'],
            "ကိုက်ညီမှု": match_str
        })

    # Result Display
    if filtered_list:
        df = pd.DataFrame(filtered_list)
        st.subheader(f"📊 စုစုပေါင်း: {len(df)} ဦး တွေ့ရှိသည်")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result ကို CSV ဖိုင်ဖြင့် သိမ်းရန်", csv, "football_5teams.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။ (မှတ်ချက် - ၅ သင်းမပြည့်သူများကို ဖယ်ထုတ်ထားခြင်း ဖြစ်နိုင်သည်)")
