import streamlit as st
import pandas as pd
import re

# App Title
st.set_page_config(page_title="Football Team Filter", layout="wide")
st.title("⚽ ဘောလုံးအသင်း ရွေးချယ်သူများ စစ်ထုတ်ခြင်း")

# 1. File Upload လုပ်ရန်
uploaded_file = st.file_uploader("ဘောလုံးအသင်းစာရင်း (.txt) ဖိုင်ကို Upload လုပ်ပါ", type=["txt"])

if uploaded_file is not None:
    # ဖိုင်ကို ဖတ်ခြင်း
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    data = []
    all_teams = set()

    # Data တွေကို format ချပြီး ဖတ်ခြင်း (ဥပမာ- ဖုန်းနံပတ်၊ အသင်းများ)
    for line in lines:
        if line.strip():
            # ဖုန်းနံပတ်ကို ရှာခြင်း (Regex သုံးပြီး)
            phone_match = re.search(r'(09\d{7,9})', line)
            if phone_match:
                phone = phone_match.group(1)
                # အသင်းအမည်များကို ခွဲထုတ်ခြင်း (comma သို့မဟုတ် space သုံးထားသည်ဟု ယူဆသည်)
                # ဖုန်းနံပတ် မဟုတ်တဲ့ ကျန်တဲ့ စာသားတွေကို အသင်းအမည်အဖြစ် ယူဆမယ်
                teams_part = line.replace(phone, "").strip()
                # ကော်မာ (,) သို့မဟုတ် space ဖြင့် ခွဲထားသော အသင်းများကို ရယူခြင်း
                teams = [t.strip() for t in re.split(r'[,|၊]', teams_part) if t.strip()]
                
                data.append({"Phone": phone, "Teams": teams})
                for t in teams:
                    all_teams.add(t)

    # 2. Sidebar မှာ အသင်းများကို Select လုပ်ရန်
    st.sidebar.header("ရှာဖွေလိုသောအသင်းများ")
    selected_teams = st.sidebar.multiselect("အသင်းများကို ရွေးပါ:", sorted(list(all_teams)))

    if selected_teams:
        st.subheader(f"📍 {', '.join(selected_teams)} အသင်းကို ရွေးထားသော User များ")
        
        results = []
        for entry in data:
            # User ရွေးထားတဲ့ အသင်းတွေထဲမှာ ကိုယ်ရွေးလိုက်တဲ့အသင်း ပါ/မပါ စစ်ခြင်း
            matched_teams = [t for t in entry['Teams'] if t in selected_teams]
            if matched_teams:
                results.append({
                    "ဖုန်းနံပတ်": entry['Phone'],
                    "ရွေးချယ်ထားသော အသင်းများ": ", ".join(entry['Teams']),
                    "ကိုက်ညီမှု": ", ".join(matched_teams)
                })

        if results:
            df = pd.DataFrame(results)
            st.table(df) # ဇယားဖြင့် ပြသခြင်း
            
            # Excel/CSV အနေနဲ့ ပြန်ထုတ်ချင်ရင်
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("Download Result as CSV", csv, "filtered_users.csv", "text/csv")
        else:
            st.warning("ကိုက်ညီသော User မရှိပါ။")
    else:
        st.info("ဘယ်ဘက် Sidebar မှ အသင်းများကို ရွေးချယ်ပေးပါ။")

else:
    st.info("ကျေးဇူးပြု၍ .txt ဖိုင်ကို Upload အရင်လုပ်ပေးပါ။")
