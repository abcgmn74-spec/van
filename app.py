import streamlit as st
import re

# Web Page ခေါင်းစဉ်နှင့် Layout သတ်မှတ်ချက်
st.set_page_config(page_title="Football Comment Filter", layout="wide")

st.title("⚽ Football Comment Filter Tool")
st.write("Text File ကို တင်ပြီး ကိုယ်လိုချင်တဲ့ အသင်းပါတဲ့သူတွေကို စစ်ထုတ်ပါ")

# ဘေးဘောင် (Sidebar) တွင် အသင်းနာမည်များ ထည့်သွင်းရန်
st.sidebar.header("သတ်မှတ်ချက်များ")
default_teams = "Aston Villa, Brighton, Wolves, Arsenal, Brentford, Newcastle, Villarreal, Barcelona, Levante, Real Madrid, ဗီလာ, ဘရိုက်တန်, ဘာစီလိုနာ, နယူးကာဆယ်, အာဆင်နယ်"
teams_input = st.sidebar.text_area("စစ်ထုတ်မည့် အသင်းနာမည်များ (ကော်မာ ခြားပေးပါ)", default_teams)
min_match = st.sidebar.slider("အနည်းဆုံး ပါဝင်ရမည့် အသင်းအရေအတွက်", 1, 10, 5)

target_teams = [t.strip() for t in teams_input.split(',')]

# File Upload လုပ်ရန် နေရာ
uploaded_file = st.file_uploader("မှတ်ချက်များပါသော .txt file ကို ရွေးပါ", type="txt")

if uploaded_file is not None:
    # File ကို ဖတ်ခြင်း
    content = uploaded_file.read().decode("utf-8")
    
    # မှတ်ချက်တစ်ခုချင်းစီကို ခွဲထုတ်ခြင်း
    blocks = content.split('\n\n')
    
    final_results = []

    for block in blocks:
        if not block.strip():
            continue
        
        found_teams = [team for team in target_teams if team.lower() in block.lower()]
        
        if len(found_teams) >= min_match:
            # ဖုန်းနံပါတ် သို့မဟုတ် OKBET ID ကို ရှာခြင်း
            phone_match = re.search(r'(09\d{7,11}|959\d{7,11}|Ok\s?bet\s?\d+)', block, re.IGNORECASE)
            phone = phone_match.group(0) if phone_match else "ဖုန်းနံပါတ် မတွေ့ပါ"
            
            # အမည်ကို ရှာခြင်း (ပထမဆုံးစာကြောင်းကို အမည်ဟု ယူဆသည်)
            lines = block.strip().split('\n')
            name = lines[0].split(',')[0] # Telegram format အတွက်
            
            final_results.append({
                "အမည်": name,
                "ဖုန်း/ID": phone,
                "ပါဝင်သော အသင်းများ": ", ".join(found_teams)
            })

    # ရလဒ်များကို ပြသခြင်း
    if final_results:
        st.success(f"သတ်မှတ်ချက်နှင့် ကိုက်ညီသူ {len(final_results)} ဦး တွေ့ရှိပါသည်!")
        st.table(final_results)
        
        # CSV အနေနဲ့ Download ဆွဲဖို့ ခလုတ်
        import pandas as pd
        df = pd.DataFrame(final_results)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("ရလဒ်ကို Excel (CSV) အနေဖြင့် သိမ်းရန်", csv, "filtered_results.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသူ မရှိပါ။")