import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from thefuzz import process

st.set_page_config(page_title="Football Data AI Extractor", layout="wide")

# --- Gemini API Configuration ---
st.sidebar.header("🤖 AI Settings")
api_key = st.sidebar.text_input("Gemini API Key ကိုထည့်ပါ:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Flash model သည် မြန်ဆန်ပြီး parsing အတွက် အဆင်ပြေဆုံးဖြစ်သည်
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.sidebar.warning("API Key မရှိသေးပါ။ Dictionary စနစ်ဖြင့်သာ အလုပ်လုပ်ပါမည်။")

# ၁။ Standard Teams စာရင်း
STANDARD_TEAMS = [
    "Arsenal", "Aston Villa", "Barcelona", "Brighton", "Chelsea", 
    "Everton", "Liverpool", "Manchester City", "Manchester United", 
    "Newcastle United", "Real Madrid", "Sevilla", "Tottenham Hotspur", 
    "Villarreal", "Atletico Madrid", "Inter Milan", "AC Milan", "Juventus", "Napoli"
]

# ၂။ Mapping Dictionary
TEAM_MAP = {
    "မန်စီး": "Manchester City", "မန်ယူ": "Manchester United", "လီဗာပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal", "ဘာစီလိုနာ": "Barcelona", "ရီးရဲလ်": "Real Madrid",
    "နယူး": "Newcastle United", "ဘရိုက်တန်": "Brighton", "ဗီလာ": "Aston Villa",
    "စပါး": "Tottenham Hotspur", "ဝက်ဟမ်း": "West Ham"
}

def get_team_with_ai(text):
    # (က) အရင်ဆုံး ပေးထားတဲ့ Mapping Dictionary နဲ့ စစ်မယ်
    for key, val in TEAM_MAP.items():
        if key in text:
            return val
            
    # (ခ) Dictionary မှာ မတွေ့ရင် Gemini AI ကို ခိုင်းမယ်
    if api_key:
        try:
            # Prompt ကို တိတိကျကျပေးထားသည်
            prompt = f"Extract the professional football team name from this text: '{text}'. Return ONLY the English team name (e.g., 'Manchester City'). If no football team is found, return 'None'."
            response = model.generate_content(prompt)
            result = response.text.strip()
            if result != "None" and len(result) < 30: # အရှည်ကြီးပြန်လာလျှင် မယူပါ
                return result
        except:
            pass
            
    # (ဂ) API မရှိရင် သို့မဟုတ် error တက်ရင် Fuzzy Match နဲ့ နောက်ဆုံးစစ်မယ်
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    
    return None

st.title("⚽ Football Data Pro AI Extractor")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    # ဖိုင်ဖတ်နေစဉ် Loading ပြရန်
    with st.spinner('AI က အချက်အလက်များကို ခွဲခြားနေပါသည်...'):
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
                    # AI စနစ်ဖြင့် အသင်းအမည် ခွဲထုတ်ခြင်း
                    cleaned_text = re.sub(r'^\d+[\s\.\)]+', '', line) 
                    if cleaned_text and cleaned_text != current_user["Name"]:
                        std_name = get_team_with_ai(cleaned_text)
                        if std_name:
                            if std_name not in current_user["Teams"]:
                                current_user["Teams"].append(std_name)
                        else:
                            current_user["Other_Comments"].append(cleaned_text)

    if current_user: parsed_data.append(current_user)

    # --- Sidebar Filter ---
    st.sidebar.header("စစ်ထုတ်ရန် Settings")
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန်:", sorted(STANDARD_TEAMS))

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
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_ai_data.csv", "text/csv")
