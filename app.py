import streamlit as st


def parse_txt(content: str):
    users = []
    roll = 1

    lines = [l.strip() for l in content.splitlines() if l.strip()]

    name = None
    teams = []
    phone = ""

    for line in lines:
        lower = line.lower()

        # phone / okbet line
        if lower.startswith("ok") or any(ch.isdigit() for ch in line):
            phone = line
            users.append({
                "roll": roll,
                "user": name,
                "teams": teams,
                "phone": phone
            })
            roll += 1
            name = None
            teams = []
            phone = ""
        elif name is None:
            name = line
        else:
            teams.append(line)

    return users


st.set_page_config(page_title="User Table", layout="wide")

st.title("📊 User Table (TXT Upload)")

uploaded_file = st.file_uploader(
    "⬆️ users.txt ဖိုင်ကို upload လုပ်ပါ",
    type=["txt"]
)

if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    data = parse_txt(content)

    st.markdown("""
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead tr {
            border-bottom: 2px solid #ddd;
        }
        th {
            text-align: left;
            padding: 10px 8px;
            font-weight: 600;
        }
        td {
            padding: 12px 8px;
            vertical-align: top;
            border-bottom: 1px solid #eee;
        }
    </style>
    """, unsafe_allow_html=True)

    html = """
    <table>
        <thead>
            <tr>
                <th style="width:80px;">Roll No</th>
                <th style="width:160px;">User</th>
                <th style="width:50%;">Teams</th>
                <th style="width:220px;">Phone</th>
            </tr>
        </thead>
        <tbody>
    """

    for row in data:
        teams_html = ",<br>".join(row["teams"])
        html += f"""
        <tr>
            <td>{row['roll']}</td>
            <td>{row['user']}</td>
            <td>{teams_html}</td>
            <td>{row['phone']}</td>
        </tr>
        """

    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)

else:
    st.info("⬆️ users.txt ဖိုင်ကို upload လုပ်ပါ")
