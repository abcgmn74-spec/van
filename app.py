import streamlit as st
import pandas as pd
import re

# Web Page Settings
st.set_page_config(page_title="Football Comment Filter", page_icon="⚽", layout="wide")

st.title("⚽ Football Comment Filter Tool (Updated)")
st.write("Telegram မှ ကူးလာသော မှတ်ချက်များကို ပိုမိုတိကျစွာ စစ်ထုတ်ပေးပါသည်။ Space အပိုများနှင့် စာလုံးပေါင်းကွဲလွဲမှုများကို ပြင်ဆင်ထားပါသည်။")

# Sidebar
st.sidebar.header("⚙️ သတ်မှတ်ချက်များ")

# အသုံးများသော အသင်းနာမည်များနှင့် စာလုံးပေါင်းပုံစံများ
default_teams = (
    "Aston Villa, Brighton, Wolves, Arsenal, Brentford, Newcastle, Villarreal, "
    "Barcelona, Levante, Real Madrid, ဗီလာ, ဘရိုက်တန်, ဘာစီလိုနာ, နယူးကာဆယ်, အာဆင်နယ်, "
    "ရီးရဲလ်, ရီရဲလ်, ရီးရဲ, ရီရဲ, မက်ဒရစ်"
)

teams_input = st.sidebar.text_area("စစ်ထုတ်မည့် အသင်းနာမည်များ (ကော်မာ ခြားပေးပါ)", default_teams, height=150)
min_match = st.sidebar.slider("အနည်းဆုံး ပါဝင်ရမည့် အသင်းအရေအတွက်", 1, 10, 5)

# Process target teams
target_teams = [t.strip() for t in teams_input.split(',') if t.strip()]

uploaded_file = st.file_uploader("မှတ်ချက်များပါသော .txt file ကို တင်ပါ", type="txt")

if uploaded_file is not None:
    try:
        content = uploaded_file.read().decode("utf-8")
        
        # Telegram block split logic: split by double newlines to separate comments
        blocks = re.split(r'\n\s*\n', content)
        
        final_results = []

        for block in blocks:
            if not block.strip():
                continue
            
            # စာသားထဲက Tab တွေ Space အပိုတွေကို ရှင်းထုတ်ခြင်း
            # ဒါက "ရီရဲလ်" ရှေ့မှာ Space တွေ ဘယ်လောက်ပါပါ ရှာတွေ့စေပါတယ်
            clean_block = " ".join(block.split())
            
            found_teams = []
            for team in target_teams:
                # Case insensitive search
                if team.lower() in clean_block.lower():
                    found_teams.append(team)
            
            # တစ်သင်းတည်းကို စာလုံးပေါင်းနှစ်မျိုးနဲ့ ရေးထားရင် တစ်ခုပဲ ရေတွက်ရန်
            unique_found = []
            seen_normalized = set()
            
            # ပိုမိုတိကျသော ရေတွက်မှုအတွက် Normalized logic (ရီးရဲလ် နှင့် ရီရဲလ် ကို တစ်ခုတည်းဟု သတ်မှတ်ခြင်း)
            for f in found_teams:
                norm = f.lower().replace("ရီ", "ရီး").replace("ရဲ", "ရဲလ်")
                if "real" in norm or "madrid" in norm or "ရီးရဲလ်" in norm:
                    norm = "real_madrid_group"
                if norm not in seen_normalized:
                    seen_normalized.add(norm)
                    unique_found.append(f)

            if len(unique_found) >= min_match:
                # ဖုန်းနံပါတ် သို့မဟုတ် OKBET ID ရှာဖွေခြင်း
                # Regex ကို ပိုမိုကျယ်ပြန့်စွာ ရှာနိုင်ရန် ပြင်ဆင်ထားသည်
                contact_match = re.search(r'(?:Ok\s?bet[-|\s]?)?(?:09|959)\d{7,11}', clean_block, re.IGNORECASE)
                contact = contact_match.group(0) if contact_match else "မတွေ့ရှိပါ"
                
                # အမည်ထုတ်ယူခြင်း (ပထမဆုံးစာကြောင်း)
                lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
                name = "Unknown"
                if lines:
                    # Telegram style "Name, [Date]" format ကို ရှင်းထုတ်ခြင်း
                    name = re.split(r', \[', lines[0])[0]
                
                final_results.append({
                    "အမည်": name,
                    "ဖုန်း/ID": contact,
                    "တွေ့ရှိသည့်အသင်းများ": ", ".join(unique_found),
                    "အရေအတွက်": len(unique_found)
                })

        if final_results:
            st.success(f"ကိုက်ညီသူ {len(final_results)} ဦး တွေ့ရှိပါသည်!")
            df = pd.DataFrame(final_results)
            
            # Display result table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download button for CSV
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ရလဒ်များကို Excel (CSV) ဖြင့် သိမ်းရန်",
                data=csv,
                file_name="filtered_results.csv",
                mime="text/csv"
            )
        else:
            st.warning("ကိုက်ညီသူ မရှိပါ။ စာလုံးပေါင်းများ သို့မဟုတ် အရေအတွက် သတ်မှတ်ချက်ကို ပြန်စစ်ပေးပါ။")

    except Exception as e:
        st.error(f"ဖိုင်ကို ဖတ်ရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်- {e}")

st.divider()
st.caption("Football Comment Filter Tool v2.1 | အချက်အလက်များကို ပိုမိုတိကျစွာ စစ်ထုတ်နိုင်ရန် အဆင့်မြှင့်ထားပါသည်။")
