import streamlit as st
import pandas as pd
import re
from thefuzz import process

# စာမျက်နှာ အပြင်အဆင်
st.set_page_config(page_title="Football Team Filter", layout="wide")

# Standard English Team Names
STANDARD_TEAMS = [
    "Liverpool", "Arsenal", "Manchester United", "Manchester City", 
    "Chelsea", "Tottenham Hotspur", "Aston Villa", "Newcastle United", 
    "Brighton", "Real Madrid", "Barcelona", "Sevilla", "Villarreal"
]

# မြန်မာလို/အင်္ဂလိပ်လို စာလုံးပေါင်းအမျိုးမျိုးကို Standard အမည်သို့ ပြောင်းရန်
TEAM_MAP = {
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal", "Arsenal": "Arsenal",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "Man United": "Manchester United", "Man Utd": "Manchester United",
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City", "Man City": "Manchester City", "Mancity": "Manchester City",
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "Barcelona": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "Real Madrid": "Real Madrid", "ရီရဲ": "Real Madrid", "Real madrid": "Real Madrid",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "Aston Villa": "Aston Villa", "Astin Villa": "Aston Villa",
    "ဘရိုက်တန်": "Brighton", "Brighton": "Brighton",
    "နယူး": "Newcastle United", "နယူးကာဆယ်": "Newcastle United", "Newcastle": "Newcastle United", "နယူကာဆယ်": "Newcastle United",
    "စပါး": "Tottenham Hotspur", "Spur": "Tottenham Hotspur", "Tottenham": "Tottenham Hotspur",
    "ဆီးဗီလာ": "Sevilla", "Sevilla": "Sevilla", "ဆီဗီလာ": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "Villareal": "Villarreal", "Villarreal": "Villarreal"
}

def get_standard_name(text):
    text = text.strip()
    if not text: return None
    # ၁။ Map ထဲမှာ အရင်စစ်မယ် (Case insensitive)
    for key, val in TEAM_MAP.items():
        if key.lower() == text.lower():
            return val
    # ၂။ Fuzzy Match (၈၀% ကျော်မှ ယူမယ် - စာလုံးပေါင်းမှားတာတွေအတွက်)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    return match if score > 80 else text

st.title("⚽ Football Filter (Multi-Select Mode)")

uploaded_file = st.file_uploader("Telegram စာသားဖိုင် (.txt) ကို Upload လုပ်ပါ", type=["txt"])

if uploaded_file:
    raw_content = uploaded_file.getvalue().decode("utf-8")
    # User တစ်ယောက်ချင်းစီကို ခွဲထုတ်ခြင်း
    user_blocks = re.split(r'\n\s*\n', raw_content)
    
    parsed_data = []
    
    for block in user_blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 2: continue
        
        user_name = lines[0].split(',')[0]
        phone = "Unknown"
        user_teams = []
        
        for line in lines:
            # Phone number parsing
            phone_match = re.search(r'(959\d{8,10}|09\d{7,9})', line)
            if phone_match:
                phone = phone_match.group(1)
            
            # Team name parsing (Ignore name line and timestamp line)
            elif "[" not in line and line != user_name:
                clean_name = re.sub(r'^\d+[\s\.\)]+', '', line) # နံပါတ်စဉ်ဖယ်ခြင်း
                std_name = get_standard_name(clean_name)
                if std_name in STANDARD_TEAMS:
                    user_teams.append(std_name)

        if user_teams:
            parsed_data.append({
                "User Name": user_name,
                "Phone": phone,
                "Teams": list(dict.fromkeys(user_teams))
            })

    # --- Multiple Select Sidebar ---
    st.sidebar.header("Filter Settings")
    st.sidebar.write("ကြည့်ချင်သော အသင်းများကို ရွေးပါ (အများကြီး ရွေးနိုင်သည်)")
    selected_teams = st.sidebar.multiselect(
        "Select Teams:", 
        options=STANDARD_TEAMS,
        default=[]
    )

    # Filter Logic (Any match)
    filtered_list = []
    if selected_teams:
        for u in parsed_data:
            # User ရွေးထားတဲ့ အသင်းတွေထဲမှာ ကိုယ်ရွေးလိုက်တဲ့ အသင်း တစ်သင်းသင်း ပါ/မပါ စစ်ခြင်း
            matches = [t for t in u['Teams'] if t in selected_teams]
            if matches:
                filtered_list.append({
                    "နာမည်": u['User Name'],
                    "ဖုန်းနံပတ်": u['Phone'],
                    "ရွေးချယ်ထားသော အသင်းများ": ", ".join(u['Teams']),
                    "ကိုက်ညီသည့်အသင်း": ", ".join(matches)
                })
    else:
        # ဘာမှမရွေးထားရင် အကုန်ပြမယ်
        for u in parsed_data:
            filtered_list.append({
                "နာမည်": u['User Name'],
                "ဖုန်းနံပတ်": u['Phone'],
                "ရွေးချယ်ထားသော အသင်းများ": ", ".join(u['Teams']),
                "ကိုက်ညီသည့်အသင်း": "-"
            })

    # Result Display
    if filtered_list:
        df = pd.DataFrame(filtered_list)
        st.subheader(f"📊 ရလဒ်ပေါင်း: {len(df)} ခု")
        st.dataframe(df, use_container_width=True)
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download Results (Excel/CSV)", csv, "filtered_football.csv", "text/csv")
    else:
        st.warning("ရွေးချယ်ထားသော အသင်းများနှင့် ကိုက်ညီသူ မရှိပါ။")
