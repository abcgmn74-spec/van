import streamlit as st
import pandas as pd
import re
from thefuzz import process

# စာမျက်နှာ အပြင်အဆင်
st.set_page_config(page_title="Football Filter", layout="wide")

# Standard English Team Names
STANDARD_TEAMS = [
    "Liverpool", "Arsenal", "Manchester United", "Manchester City", 
    "Chelsea", "Tottenham Hotspur", "Aston Villa", "Newcastle United", 
    "Brighton", "Real Madrid", "Barcelona", "Sevilla", "Villarreal"
]

# မြန်မာလို စာလုံးပေါင်းမှားတာတွေကို English ပြောင်းပေးဖို့ Dictionary
TEAM_MAP = {
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal",
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "Man United": "Manchester United",
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City", "Man City": "Manchester City", "Mancity": "Manchester City",
    "ဘာစီလိုနာ": "Barcelona", "ဘာစီ": "Barcelona", "Barcelona": "Barcelona",
    "ရီးရဲလ်": "Real Madrid", "ရီးရဲ": "Real Madrid", "Real Madrid": "Real Madrid", "ရီရဲ": "Real Madrid",
    "ဗီလာ": "Aston Villa", "အက်စတွန်ဗီလာ": "Aston Villa", "Aston Villa": "Aston Villa",
    "ဘရိုက်တန်": "Brighton", "Brighton": "Brighton",
    "နယူး": "Newcastle United", "နယူးကာဆယ်": "Newcastle United", "Newcastle": "Newcastle United", "နယူကာဆယ်": "Newcastle United",
    "စပါး": "Tottenham Hotspur", "Spur": "Tottenham Hotspur", "Tottenham": "Tottenham Hotspur",
    "ဆီးဗီလာ": "Sevilla", "Sevilla": "Sevilla", "ဆီဗီလာ": "Sevilla",
    "ဗယ်လာရီးရဲလ်": "Villarreal", "Villareal": "Villarreal"
}

def get_standard_name(text):
    text = text.strip()
    if not text: return None
    # ၁။ Map ထဲမှာ တိုက်ရိုက်ရှာမယ်
    if text in TEAM_MAP:
        return TEAM_MAP[text]
    # ၂။ Fuzzy Match နဲ့ အနီးစပ်ဆုံးရှာမယ်
    match, score = process.extractOne(text, STANDARD_TEAMS)
    return match if score > 60 else text

st.title("⚽ Football Team Filter App")
st.info("Telegram မှ ကူးလာသော စာသားဖိုင်များကို Upload လုပ်ပြီး အသင်းအလိုက် စစ်ထုတ်နိုင်ပါသည်။")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    raw_content = uploaded_file.getvalue().decode("utf-8")
    
    # User တစ်ယောက်ချင်းစီရဲ့ block ကို ခွဲထုတ်ခြင်း (နံမည်နဲ့ အချိန်ပါတဲ့ line ကို အခြေခံသည်)
    user_blocks = re.split(r'\n\s*\n', raw_content)
    
    parsed_data = []
    
    for block in user_blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 2: continue
        
        user_name = lines[0].split(',')[0] # ပထမဆုံးစာကြောင်းက နာမည်
        phone = "Unknown"
        user_teams = []
        
        for line in lines:
            # ဖုန်းနံပတ်ရှာခြင်း (959... သို့မဟုတ် 09...)
            phone_match = re.search(r'(959\d{8,10}|09\d{7,9})', line)
            if phone_match:
                phone = phone_match.group(1)
            
            # အသင်းအမည်များကို ရှာခြင်း (ရှေ့က နံပါတ်စဉ်များ ဖယ်ထုတ်ပြီး)
            elif not any(x in line for x in ["[", "]", "/"]): # အချိန်ပါတဲ့ line မဟုတ်ရင်
                clean_name = re.sub(r'^\d+[\s\.\)]+', '', line)
                if clean_name and clean_name != user_name:
                    std_name = get_standard_name(clean_name)
                    if std_name in STANDARD_TEAMS:
                        user_teams.append(std_name)

        if len(user_teams) > 0:
            parsed_data.append({
                "Name": user_name,
                "Phone": phone,
                "Teams": list(dict.fromkeys(user_teams)) # Duplicate ဖယ်ခြင်း
            })

    # Sidebar Filter
    st.sidebar.header("Filter Settings")
    selected_team = st.sidebar.selectbox("Select Team to Search:", ["All Teams"] + STANDARD_TEAMS)

    # Filtering Logic
    filtered_list = []
    for u in parsed_data:
        if selected_team == "All Teams" or selected_team in u['Teams']:
            filtered_list.append({
                "User Name": u['Name'],
                "Phone Number": u['Phone'],
                "Selected Teams": ", ".join(u['Teams'])
            })

    if filtered_list:
        df = pd.DataFrame(filtered_list)
        st.success(f"Found {len(df)} users for {selected_team}")
        st.dataframe(df, use_container_width=True)
        
        # CSV ထုတ်ရန်
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download Results as CSV", csv, "football_filter.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
