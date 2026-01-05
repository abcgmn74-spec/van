import re
import pandas as pd

# -----------------------------
# 1. REGEX PATTERNS
# -----------------------------

USER_PATTERN = re.compile(
    r"^(.*?),\s*\[\d{1,2}/\d{1,2}/\d{4}"
)

ACCOUNT_PATTERN = re.compile(
    r"((?:ok\s?bet|okbet|okbest|ok\s?bet\.?|okbet_|okbet-?|ok\s?bet-|ok\s?bet/|OKBET|OK\s?BET|\.959|09|၀၉)?"
    r"[0-9၀-၉]{6,})",
    re.IGNORECASE
)

# -----------------------------
# 2. TEAM ALIAS DICTIONARY
# -----------------------------

TEAM_ALIASES = {
    "Aston Villa": [
        "ဗီလာ", "အက်စတွန်ဗီလာ", "အက်စတန်ဗီလာ", "အက်တွန်ဗီလာ",
        "အေဗီလာ", "aဗီလာ", "aston villa", "astonvilla", "astin villa",
        "villa"
    ],
    "Arsenal": [
        "အာဆင်နယ်", "အာဇင်နယ်", "arsenal", "aresnal", "arsen"
    ],
    "Barcelona": [
        "ဘာစီလိုနာ", "ဘာစီ", "ဘာစိ", "ဘာကာ",
        "barcelona", "bercelona", "bercelona", "barca"
    ],
    "Real Madrid": [
        "ရီးရဲလ်မက်ဒရစ်", "ရီရဲလ်မက်ဒရစ်", "ရီးရဲ", "ရီရဲ", "မက်ဒရစ်",
        "real madrid", "realmadrid", "real mardid", "real madird"
    ],
    "Liverpool": [
        "လီဗာပူး", "လီဗာပူးလ်", "လီပါပူး", "လီဗားပူး",
        "liverpool", "liverpol", "liver"
    ],
    "Manchester City": [
        "မန်စီးတီး", "မန်စီတီး", "မန်းစီးတီး", "စီးတီး",
        "man city", "mancity", "manchester city"
    ],
    "Manchester United": [
        "မန်ယူ", "မန်ယူနိုက်တက်",
        "man united", "man utd", "manunited"
    ],
    "Tottenham Hotspur": [
        "စပါး", "spur", "hotspur", "tottenham"
    ],
    "Brighton": [
        "ဘရိုက်တန်", "ဘရုိက်တန်",
        "brighton"
    ],
    "Newcastle": [
        "နယူးကာဆယ်", "နယူး", "နယူကာဆယ်",
        "newcastle", "nwecastle"
    ],
    "Sevilla": [
        "ဆီဗီလာ", "ဆီးဗီးလား", "ဆီးဗီလာ",
        "sevilla"
    ],
    "Villarreal": [
        "ဗီလာရီရဲလ်", "ဗီလာရီးရဲ", "ဗယ်လာရီးရဲ",
        "villareal", "villareal", "villarreal"
    ],
    "Everton": [
        "အဲဗာတန်", "အယ်ဗာတန်",
        "everton"
    ],
    "West Ham": [
        "ဝက်ဟမ်း", "ဝက်စ်ဟမ်း",
        "west ham", "westham"
    ],
    "Athletic Club": [
        "ဘီဘာအို", "ဗီဘာအို",
        "athletic club", "bilbao"
    ],
}

# -----------------------------
# 3. NORMALIZE FUNCTION
# -----------------------------

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\wက-အ]", "", text)
    return text

# -----------------------------
# 4. TEAM RESOLVER
# -----------------------------

def resolve_team(text: str):
    norm = normalize(text)
    for standard, aliases in TEAM_ALIASES.items():
        for alias in aliases:
            if normalize(alias) in norm or norm in normalize(alias):
                return standard
    return None

# -----------------------------
# 5. MAIN PARSER
# -----------------------------

def parse_chat(text: str):
    rows = []
    current_user = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # USER
        user_match = USER_PATTERN.search(line)
        if user_match:
            current_user = user_match.group(1)
            continue

        # ACCOUNT
        acc_match = ACCOUNT_PATTERN.search(line)
        if acc_match:
            rows.append({
                "User": current_user,
                "Team": None,
                "Account": acc_match.group(1)
            })
            continue

        # TEAM
        team = resolve_team(line)
        if team:
            rows.append({
                "User": current_user,
                "Team": team,
                "Account": None
            })

    return rows

# -----------------------------
# 6. RUN WITH TXT FILE
# -----------------------------

if __name__ == "__main__":
    with open("input.txt", "r", encoding="utf-8") as f:
        text = f.read()

    data = parse_chat(text)

    df = pd.DataFrame(data)
    df.to_excel("output.xlsx", index=False)

    print("✅ Done! output.xlsx generated")
