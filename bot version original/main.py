"""
╔══════════════════════════════════════════════════════════╗
║         JACKPOT VALUE BOT — On-Demand Edition           ║
║   Run instantly. Filter specific games. No waiting.     ║
╚══════════════════════════════════════════════════════════╝
"""

import logging, time, sys
from datetime import datetime
from math import exp, factorial
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  ✏️  STEP 1: PASTE YOUR KEYS HERE
# ═══════════════════════════════════════════════════════════════════

CONFIG = {
    "ODDS_API_KEY":       "your ODDS API KEY HERE",
    "TELEGRAM_BOT_TOKEN": "YOUR TELEGRAM BOT KEY HERE",
    "TELEGRAM_CHAT_ID":   "TELEGRAM CHAT ID HERE",
    "API_FOOTBALL_KEY":   "YOUR API FOOTBALL KEY HERE",  # RapidAPI key — for Africa/Romania/Scotland or for any league not easily found

    "ODDS_API_BASE":      "https://api.the-odds-api.com/v4",
    "APIFOOTBALL_BASE":   "https://api-football-v1.p.rapidapi.com/v3",

    "EV_THRESHOLD":   0.05,   # 5% minimum edge to alert
    "MIN_ODDS":       1.30,
    "MAX_ODDS":       10.0,
    "KELLY_FRACTION": 0.25,
    "BANKROLL":       1000,
    "CURRENCY":       "USD EUR GBP YEN DIR",

    "LEAGUE_AVG_GOALS": {
        "soccer_epl":                 1.35,
        "soccer_spain_la_liga":       1.30,
        "soccer_italy_serie_a":       1.25,
        "soccer_germany_bundesliga":  1.45,
        "soccer_france_ligue_one":    1.30,
        "soccer_uefa_champs_league":  1.40,
        "default":                    1.30,
    },
}


# ═══════════════════════════════════════════════════════════════════
#  ✏️  STEP 2: TYPE YOUR JACKPOT GAMES HERE (update every jackpot)
#
#  HOW: Look at your jackpot ticket. Type each game exactly as:
#       "Home Team vs Away Team"
#  TIP: Run "python main.py listgames" first to see exact team names
# ═══════════════════════════════════════════════════════════════════

MY_JACKPOT_GAMES = [
    # ✏️ DELETE these examples and type YOUR games here each week
    # Format: "Home Team vs Away Team"  ← exact names from API
    # Run "python main.py listgames" to get exact team names
    "Elche vs Espanyol",
    "Brighton and Hove Albion vs Nottingham Forest",
    "Paris FC vs Nice",
    "Valencia vs Osasuna",
    "FC Utrecht vs AZ Alkmaar",
    "Eintracht Frankfurt vs SC Freiburg",
    "Torino vs Lazio",
    "Excelsior vs Go Ahead Eagles",
    "AS Roma vs Juventus",
    "Girona vs Celta Vigo",
]

# ═══════════════════════════════════════════════════════════════════
#  ✏️  STEP 2B: TURN ON ONLY THE LEAGUES YOUR GAMES ARE IN
#
#  HOW TO USE:
#  - Lines WITHOUT # at the start = ON  (bot will fetch this)
#  - Lines WITH    # at the start = OFF (bot skips this, saves requests)
#
#  RULE: Only turn on leagues that have your jackpot games.
#  Each ON league costs 1 API request per scan.
#
#  ⚠️  LEAGUES MARKED "→ API-FOOTBALL" are NOT in The Odds API.
#      Add those games to MY_MISSING_LEAGUE_GAMES below instead.
# ═══════════════════════════════════════════════════════════════════

MY_JACKPOT_LEAGUES = [
    # Edit as necessary 
    # ── ENGLAND ───────────────────────────────────────────────────
    "soccer_epl",                        # Premier League (1st)
    # "soccer_efl_champ",                # Championship (2nd)
    # "soccer_england_league1",          # League One (3rd)
    # "soccer_england_league2",          # League Two (4th)

    # ── SPAIN ─────────────────────────────────────────────────────
     "soccer_spain_la_liga",            # La Liga (1st)
    # "soccer_spain_segunda_division",   # La Liga 2 (2nd)
    # ❌ 3rd tier (Segunda B) → API-FOOTBALL only

    # ── GERMANY ───────────────────────────────────────────────────
     "soccer_germany_bundesliga",       # Bundesliga (1st)
    # "soccer_germany_bundesliga2",      # 2. Bundesliga (2nd)
    # "soccer_germany_liga3",            # 3. Liga (3rd)

    # ── FRANCE ────────────────────────────────────────────────────
     "soccer_france_ligue_one",         # Ligue 1 (1st)
    # "soccer_france_ligue_two",         # Ligue 2 (2nd)
    # ❌ 3rd tier (National) → API-FOOTBALL only

    # ── ITALY ─────────────────────────────────────────────────────
     "soccer_italy_serie_a",            # Serie A (1st)
    # "soccer_italy_serie_b",            # Serie B (2nd)
    # ❌ 3rd tier (Serie C) → API-FOOTBALL only

    # ── PORTUGAL ──────────────────────────────────────────────────
    # "soccer_portugal_primeira_liga",   # Primeira Liga (1st)
    # ❌ 2nd tier (Liga Portugal 2) → API-FOOTBALL only
    # ❌ 3rd tier → API-FOOTBALL only

    # ── AUSTRIA ───────────────────────────────────────────────────
    # "soccer_austria_bundesliga",       # Austrian Bundesliga (1st)
    # ❌ 2nd tier (2. Liga) → API-FOOTBALL only
    # ❌ 3rd tier → API-FOOTBALL only

    # ── DENMARK ───────────────────────────────────────────────────
    # "soccer_denmark_superliga",        # Superliga (1st)
    # ❌ 2nd tier (1st Division) → API-FOOTBALL only
    # ❌ 3rd tier → API-FOOTBALL only

    # ── NETHERLANDS ───────────────────────────────────────────────
     "soccer_netherlands_eredivisie",   # Eredivisie (1st)
    # ❌ 2nd tier (Eerste Divisie) → API-FOOTBALL only
    # ❌ 3rd tier → API-FOOTBALL only

    # ── SCOTLAND ──────────────────────────────────────────────────
    # "soccer_spl",                      # Scottish Premiership (1st)
    # ❌ Championship (2nd) → API-FOOTBALL only
    # ❌ League One (3rd) → API-FOOTBALL only

    # ── BRAZIL ────────────────────────────────────────────────────
    # "soccer_brazil_campeonato",        # Série A (1st)
    # "soccer_brazil_serie_b",           # Série B (2nd)
    # ❌ Série C (3rd) → API-FOOTBALL only

    # ── ARGENTINA ─────────────────────────────────────────────────
    # "soccer_argentina_primera_division", # Primera División (1st)
    # ❌ 2nd tier (Primera Nacional) → API-FOOTBALL only

    # ── REST OF SOUTH AMERICA ─────────────────────────────────────
    # "soccer_chile_campeonato",         # Chile Primera División (1st)
    # ❌ 2nd tier → API-FOOTBALL only
    # "soccer_conmebol_copa_libertadores", # Copa Libertadores
    # "soccer_conmebol_copa_sudamericana", # Copa Sudamericana
    # "soccer_conmebol_copa_america",    # Copa América (tournament)
    # ❌ Bolivia, Paraguay, Uruguay, Peru, Ecuador, Colombia, Venezuela → API-FOOTBALL only

    # ── USA / NORTH AMERICA ───────────────────────────────────────
    # "soccer_usa_mls",                  # MLS (1st)
    # ❌ USL Championship (2nd) → API-FOOTBALL only
    # ❌ USL League One (3rd) → API-FOOTBALL only
    # "soccer_concacaf_leagues_cup",     # Concacaf Leagues Cup
    # ❌ Mexico 2nd tier → API-FOOTBALL only
    # "soccer_mexico_ligamx",            # Liga MX Mexico (1st)

    # ── AUSTRALIA ─────────────────────────────────────────────────
    # "soccer_australia_aleague",        # A-League (1st)
    # ❌ 2nd tier (A-League Women / NPL) → API-FOOTBALL only

    # ── ASIA ──────────────────────────────────────────────────────
    # "soccer_japan_j_league",           # J-League Japan (1st)
    # ❌ J2 League (2nd) → API-FOOTBALL only
    # "soccer_korea_kleague1",           # K League 1 South Korea (1st)
    # ❌ K League 2 (2nd) → API-FOOTBALL only
    # "soccer_china_superleague",        # Super League China (1st)
    # ❌ China 2nd tier → API-FOOTBALL only
    # ❌ Saudi Pro League → API-FOOTBALL only
    # ❌ UAE Pro League → API-FOOTBALL only
    # ❌ Indian Super League → API-FOOTBALL only

    # ── AFRICA ────────────────────────────────────────────────────
    # "soccer_africa_cup_of_nations",    # AFCON (tournament only)
    # ❌ ALL domestic African leagues → API-FOOTBALL only
    # (Kenya, Nigeria, Egypt, South Africa, Morocco, Ghana,
    #  Tanzania, Uganda, Ethiopia, Zambia, Zimbabwe etc.)

    # ── OTHER EUROPE (bonus) ──────────────────────────────────────
    # "soccer_belgium_first_div",        # Belgium Pro League (1st)
    # "soccer_turkey_super_league",      # Turkey Süper Lig (1st)
    # "soccer_greece_super_league",      # Greece Super League (1st)
    # "soccer_poland_ekstraklasa",       # Poland Ekstraklasa (1st)
    # "soccer_russia_premier_league",    # Russia Premier League (1st)
    # "soccer_sweden_allsvenskan",       # Sweden Allsvenskan (1st)
    # "soccer_sweden_superettan",        # Sweden Superettan (2nd)
    # "soccer_norway_eliteserien",       # Norway Eliteserien (1st)
    # "soccer_finland_veikkausliiga",    # Finland Veikkausliiga (1st)
    # "soccer_switzerland_superleague",  # Switzerland Super League (1st)
    # "soccer_league_of_ireland",        # League of Ireland (1st)

    # ── UEFA COMPETITIONS ─────────────────────────────────────────
    # "soccer_uefa_champs_league",       # Champions League
    # "soccer_uefa_europa_league",       # Europa League
    # "soccer_uefa_europa_conference_league", # Conference League
]

# ═══════════════════════════════════════════════════════════════════
#  ✏️  STEP 2C: GAMES FROM LEAGUES NOT IN THE ODDS API
#
#  For ANY league marked "→ API-FOOTBALL only" above,
#  add the games here in this format:
#  "Home Team vs Away Team|Exact League Name"
#
#  The league name must match one in the LEAGUE_IDS dict
#  inside the APIFootball class further down in the code.
# ═══════════════════════════════════════════════════════════════════

MY_MISSING_LEAGUE_GAMES = [
    # ── ROMANIA ───────────────────────────────────────────────────
    # "CFR Cluj vs FCSB|Romania Liga 1",
    # "Rapid Bucharest vs Universitatea Craiova|Romania Liga 1",

    # ── PORTUGAL 2nd tier ─────────────────────────────────────────
    # "Sporting B vs Porto B|Portugal Liga 2",

    # ── SCOTLAND lower tiers ──────────────────────────────────────
    # "Dundee vs Partick Thistle|Scottish Championship",
    # "Airdrieonians vs Dunfermline|Scottish League One",

    # ── AFRICA ────────────────────────────────────────────────────
    # "Gor Mahia vs AFC Leopards|Kenya Premier League",
    # "Zamalek vs Al Ahly|Egypt Premier League",
    # "Kaizer Chiefs vs Orlando Pirates|South Africa PSL",
    # "Enyimba vs Rangers FC|Nigeria Premier League",

    # ── SOUTH AMERICA lower tiers ─────────────────────────────────
    # "Club Nacional vs Penarol|Uruguay Primera Division",
    # "Olimpia vs Cerro Porteno|Paraguay Division Profesional",

    # ── ASIA ──────────────────────────────────────────────────────
    # "Al Hilal vs Al Nassr|Saudi Pro League",
    # "Mumbai City vs Mohun Bagan|Indian Super League",
    "US Catanzaro vs Frosinone Calcio|Italy Serie B",
    "CD Mirandes vs AD Ceuta|Spain Segunda B",
    "FC Fredericia vs Silkeborg IF|Denmark 1st Division",
    "Wolfsberger AC vs Sturm Graz|Austria 2. Liga",
    "Casa Pia vs Moreirense|Portugal Liga 2",
]


# ═══════════════════════════════════════════════════════════════════
#  TEAM STRENGTH DATABASE (attack/defense relative to league avg)
#  attack  > 1.0 = scores more than average
#  defense < 1.0 = concedes LESS (good defense)
# ═══════════════════════════════════════════════════════════════════

TEAM_STRENGTHS = {
    "Manchester City":    {"attack": 1.85, "defense": 0.65},
    "Arsenal":            {"attack": 1.60, "defense": 0.70},
    "Liverpool":          {"attack": 1.75, "defense": 0.72},
    "Chelsea":            {"attack": 1.45, "defense": 0.88},
    "Tottenham Hotspur":  {"attack": 1.40, "defense": 0.95},
    "Manchester United":  {"attack": 1.30, "defense": 1.05},
    "Newcastle United":   {"attack": 1.35, "defense": 0.85},
    "Aston Villa":        {"attack": 1.40, "defense": 0.90},
    "Real Madrid":        {"attack": 1.90, "defense": 0.60},
    "Barcelona":          {"attack": 1.80, "defense": 0.75},
    "Atletico Madrid":    {"attack": 1.35, "defense": 0.65},
    "Napoli":             {"attack": 1.60, "defense": 0.75},
    "Inter Milan":        {"attack": 1.55, "defense": 0.70},
    "AC Milan":           {"attack": 1.45, "defense": 0.85},
    "Juventus":           {"attack": 1.35, "defense": 0.80},
    "Bayern Munich":      {"attack": 2.10, "defense": 0.65},
    "Borussia Dortmund":  {"attack": 1.65, "defense": 0.90},
    "Paris Saint-Germain":{"attack": 1.95, "defense": 0.70},
    "Marseille":          {"attack": 1.40, "defense": 0.90},
    "Gor Mahia":          {"attack": 1.20, "defense": 1.10},
    "AFC Leopards":       {"attack": 1.10, "defense": 1.15},
    "Celtic":             {"attack": 1.70, "defense": 0.75},
    "Rangers":            {"attack": 1.60, "defense": 0.80},
    "CFR Cluj":           {"attack": 1.25, "defense": 0.90},
}

def get_strength(name):
    if name in TEAM_STRENGTHS:
        return TEAM_STRENGTHS[name]
    for k, v in TEAM_STRENGTHS.items():
        if k.lower() in name.lower() or name.lower() in k.lower():
            return v
    log.warning(f"Unknown team '{name}' — using default")
    return {"attack": 1.0, "defense": 1.0}

def games_match(api_name_home, api_name_away, my_game_string):
    """
    Fuzzy match: 'Arsenal vs Liverpool' matches even if
    API says 'Arsenal FC' or 'Liverpool FC'
    """
    h = api_name_home.lower().replace(" fc","").replace(" cf","").strip()
    a = api_name_away.lower().replace(" fc","").replace(" cf","").strip()
    mine = my_game_string.lower().replace(" fc","").replace(" cf","").strip()
    return (f"{h} vs {a}" in mine) or (mine in f"{h} vs {a}") or \
           (h in mine and a in mine)


# ═══════════════════════════════════════════════════════════════════
#  POISSON ENGINE
# ═══════════════════════════════════════════════════════════════════

def poisson_prob(lam, x):
    if lam <= 0: return 1.0 if x == 0 else 0.0
    return (exp(-lam) * (lam ** x)) / factorial(x)

def match_probs(home, away, league="default"):
    avg  = CONFIG["LEAGUE_AVG_GOALS"].get(league, 1.30)
    hs   = get_strength(home)
    as_  = get_strength(away)
    lh   = hs["attack"] * as_["defense"] * avg
    la   = as_["attack"] * hs["defense"] * avg * 0.90
    hw = dr = aw = 0.0
    for h in range(8):
        for a in range(8):
            p = poisson_prob(lh, h) * poisson_prob(la, a)
            if h > a:    hw += p
            elif h == a: dr += p
            else:        aw += p
    t = hw + dr + aw
    return {"home_win": round(hw/t,4), "draw": round(dr/t,4),
            "away_win": round(aw/t,4), "lh": round(lh,3), "la": round(la,3)}

def ev(prob, odds): return (prob * odds) - 1.0
def impl(odds):     return 1.0 / odds if odds else 0
def kelly(prob, odds):
    b = odds - 1; q = 1 - prob
    pct = max(0, (prob*b - q)/b * CONFIG["KELLY_FRACTION"])
    return {"pct": round(pct*100,2), "amt": round(pct*CONFIG["BANKROLL"],2)}


# ═══════════════════════════════════════════════════════════════════
#  TELEGRAM
# ═══════════════════════════════════════════════════════════════════

class Telegram:
    def __init__(self):
        self.token = CONFIG["TELEGRAM_BOT_TOKEN"]
        self.chat  = CONFIG["TELEGRAM_CHAT_ID"]
        self.demo  = (self.token == "YOUR_BOT_TOKEN_HERE")

    def send(self, text):
        if self.demo:
            print("\n" + "─"*55)
            print(text.replace("<b>","").replace("</b>","")
                      .replace("<code>","").replace("</code>",""))
            print("─"*55)
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat, "text": text, "parse_mode": "HTML"},
                timeout=10)
        except Exception as e:
            log.error(f"Telegram: {e}")

    def game_summary(self, home, away, league, probs, all_bets):
        """
        ONE message per game, always — whether value found or not.

        Layout:
        - Model probabilities for all 3 outcomes
        - One-line odds summary: best Home / Draw / Away across ALL bookies
        - How many bookmakers were checked
        - Recommended bet (highest EV) or SKIP verdict
        - Kelly stake
        """
        n_bookies = len(set(b["bookmaker"] for b in all_bets)) if all_bets else 0

        # ── Gather best odds per outcome across all bookmakers ─────
        best = {}   # mkt_key → {odds, bookmaker, ev_pct, edge_pct, model_pct, kelly}
        for mkt_key in ["home_win", "draw", "away_win"]:
            candidates = [b for b in all_bets if b["market"] == mkt_key]
            if candidates:
                top = max(candidates, key=lambda x: x["odds"])
                best[mkt_key] = top

        # Best single odds for the one-liner display
        h_odds = best["home_win"]["odds"] if "home_win" in best else "—"
        d_odds = best["draw"]["odds"]     if "draw"     in best else "—"
        a_odds = best["away_win"]["odds"] if "away_win" in best else "—"

        # ── Find value bets (above EV threshold) ──────────────────
        value_outcomes = {
            k: v for k, v in best.items()
            if v["ev_pct"] >= CONFIG["EV_THRESHOLD"] * 100
        }

        # ── Decide fire level and recommended bet ─────────────────
        if value_outcomes:
            rec  = max(value_outcomes.values(), key=lambda x: x["ev_pct"])
            fire = "🔥🔥🔥" if rec["ev_pct"] >= 15 else "🔥🔥" if rec["ev_pct"] >= 10 else "🔥"
            rec_label = {
                "home_win": f"🏠 {home} Win",
                "draw":     "🤝 Draw",
                "away_win": f"✈️  {away} Win",
            }[rec["market"]]
            verdict = (
                f"✅ <b>RECOMMENDED BET</b>\n"
                f"  {rec_label}\n"
                f"  Best odds: <b>{rec['odds']}</b> @ {rec['bookmaker']}\n"
                f"  My model: {rec['model_pct']:.1f}%  "
                f"Market: {100/rec['odds']:.1f}%\n"
                f"  Edge: <b>+{rec['edge_pct']:.1f}%</b>  "
                f"EV: <b>+{rec['ev_pct']:.1f}%</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 Stake: {rec['kelly']['pct']:.1f}% = "
                f"<code>{CONFIG['CURRENCY']}{rec['kelly']['amt']}</code>"
            )
        else:
            fire    = "⚪"
            verdict = (
                f"⏭️ <b>VERDICT: SKIP</b>\n"
                f"  No outcome clears the {CONFIG['EV_THRESHOLD']*100:.0f}% EV threshold.\n"
                f"  Market is fairly priced — no edge detected."
            )

        msg = (
            f"{fire} <b>{home} vs {away}</b>\n"
            f"🏆 {league}  |  📋 {n_bookies} bookmakers checked\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📐 <b>Model vs Market</b>\n"
            f"  🏠 {home}\n"
            f"     Model: {probs['home_win']*100:.1f}%  "
            f"Best odds: <b>{h_odds}</b>\n"
            f"  🤝 Draw\n"
            f"     Model: {probs['draw']*100:.1f}%  "
            f"Best odds: <b>{d_odds}</b>\n"
            f"  ✈️  {away}\n"
            f"     Model: {probs['away_win']*100:.1f}%  "
            f"Best odds: <b>{a_odds}</b>\n"
            f"  λ home={probs['lh']}  λ away={probs['la']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            + verdict
        )
        self.send(msg)

    def final_summary(self, game_results, total_games):
        """
        One final summary message listing every game and its verdict.
        Sent after all individual game messages.
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not game_results:
            self.send(
                f"📋 <b>JACKPOT SCORECARD — {now}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏭️ All {total_games} games: SKIP\n"
                f"No value bets above {CONFIG['EV_THRESHOLD']*100:.0f}% EV threshold.\n"
                f"Markets fairly priced — no edge detected right now.\n"
                f"Try scanning again closer to kickoff."
            )
            return

        lines = [
            f"📋 <b>JACKPOT SCORECARD — {now}</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"✅ {len(game_results)} bets  ⏭️ {total_games - len(game_results)} skips"
            f"  |  {total_games} games total",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for i, g in enumerate(game_results, 1):
            icon = "🔥" if g["ev_pct"] >= 10 else "✅"
            lines.append(
                f"{icon} {i}. <b>{g['home']} vs {g['away']}</b>\n"
                f"   BET: {g['rec_label']}  @  <b>{g['best_odds']}</b>\n"
                f"   EV: +{g['ev_pct']:.1f}%  |  "
                f"Stake: <code>{CONFIG['CURRENCY']}{g['kelly_amt']}</code>"
            )
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🔥 EV ≥10%  ✅ EV 5–10%  ⏭️ No edge — skip",
        ]
        self.send("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════
#  ODDS API (big leagues)
# ═══════════════════════════════════════════════════════════════════

class OddsAPI:
    def __init__(self):
        self.key  = CONFIG["ODDS_API_KEY"]
        self.base = CONFIG["ODDS_API_BASE"]
        self.used = self.remaining = 0

    def get(self, league):
        if self.key == "YOUR_ODDS_API_KEY_HERE":
            log.warning("No Odds API key — skipping live fetch, using demo data")
            return []
        try:
            r = requests.get(
                f"{self.base}/sports/{league}/odds",
                params={"apiKey": self.key, "regions": "uk,eu,us,au",
                        "markets": "h2h", "oddsFormat": "decimal"},
                timeout=15)
            if "x-requests-used" in r.headers:
                self.used      = int(r.headers["x-requests-used"])
                self.remaining = int(r.headers.get("x-requests-remaining", 0))
                log.info(f"API usage: {self.used} used, {self.remaining} remaining")
            if r.status_code != 200:
                log.error(f"Odds API {r.status_code}: {r.text[:100]}")
                return []
            return r.json()
        except Exception as e:
            log.error(f"Odds API error: {e}")
            return []

    def list_leagues(self):
        """Print all available league IDs — useful for setup"""
        if self.key == "YOUR_ODDS_API_KEY_HERE":
            print("Add your API key first to list leagues.")
            return
        try:
            r = requests.get(
                f"{self.base}/sports",
                params={"apiKey": self.key, "all": "true"}, timeout=15)
            for s in r.json():
                if "soccer" in s.get("key",""):
                    print(f"  {s['key']:45} | {s['title']}")
        except Exception as e:
            log.error(f"List leagues error: {e}")


# ═══════════════════════════════════════════════════════════════════
#  API-FOOTBALL (Africa, Romania, Scotland, 1000+ leagues)
# ═══════════════════════════════════════════════════════════════════

class APIFootball:
    """
    Backup source for leagues the Odds API doesn't cover.
    Sign up free at: https://rapidapi.com/api-sports/api/api-football
    Free tier = 100 requests/day
    """
    LEAGUE_IDS = {
        # ── EUROPE: 2nd & 3rd tiers not in Odds API ───────────────
        "Portugal Liga 2":           94,
        "Portugal Liga 3":          955,
        "Austria 2. Liga":          119,
        "Austria Regionalliga":     120,
        "Denmark 1st Division":      90,
        "Denmark 2nd Division":      91,
        "Netherlands Eerste Divisie": 131,
        "Netherlands Tweede Divisie": 132,
        "Scotland Championship":    180,
        "Scotland League One":      181,
        "Scotland League Two":      182,
        "Spain Segunda B":          142,
        "France National":           61,
        "Italy Serie C":            135,
        "Romania Liga 1":           283,
        "Romania Liga 2":           284,
        "Belgium First B":          145,
        "Turkey First League":      203,
        "Greece Super League 2":    197,
        "Poland Division 1":        106,
        "Sweden Division 1":         68,
        "Norway First Division":    162,
        "Switzerland Challenge":    329,
        "Russia First League":      235,
        # ── SOUTH AMERICA ─────────────────────────────────────────
        "Argentina Primera Nacional": 132,
        "Brazil Serie C":            74,
        "Brazil Serie D":            75,
        "Uruguay Primera Division":  268,
        "Uruguay Segunda Division":  269,
        "Colombia Primera A":        239,
        "Colombia Primera B":        240,
        "Ecuador Serie A":           253,
        "Ecuador Serie B":           254,
        "Paraguay Division Pro":     244,
        "Bolivia Division Pro":      242,
        "Peru Liga 1":               265,
        "Venezuela Primera":         271,
        # ── NORTH & CENTRAL AMERICA ───────────────────────────────
        "USL Championship":          254,
        "USL League One":            255,
        "Mexico Ascenso":            263,
        "Costa Rica Primera":        322,
        "Guatemala Liga Nacional":   323,
        "Honduras Liga Nacional":    324,
        # ── AFRICA ────────────────────────────────────────────────
        "Kenya Premier League":      681,
        "Nigeria Premier League":    332,
        "South Africa PSL":          288,
        "Egypt Premier League":      233,
        "Morocco Botola Pro":        200,
        "Tunisia Ligue 1":           202,
        "Algeria Ligue Pro":         199,
        "Ghana Premier League":      475,
        "Tanzania Premier League":   374,
        "Uganda Premier League":     394,
        "Zambia Super League":       396,
        "Zimbabwe Premier":          398,
        "Ivory Coast Ligue 1":       499,
        "Senegal Ligue 1":           500,
        "Cameroon Elite One":        498,
        "Ethiopia Premier":          735,
        "Rwanda Premier":            736,
        # ── ASIA ──────────────────────────────────────────────────
        "Japan J2 League":            99,
        "Japan J3 League":           100,
        "South Korea K League 2":    293,
        "China Super League 2":      169,
        "Saudi Pro League":          307,
        "UAE Pro League":            435,
        "India Super League":        323,
        "Iran Pro League":           290,
        "Qatar Stars League":        513,
        "Australia NPL":             193,
        "Australia A-League Women":  191,
    }

    def __init__(self):
        self.key  = CONFIG["API_FOOTBALL_KEY"]
        self.base = CONFIG["APIFOOTBALL_BASE"]

    def get_fixtures_with_odds(self, league_name, days_ahead=3):
        """Fetch upcoming fixtures + odds for a specific league."""
        if self.key == "YOUR_API_FOOTBALL_KEY_HERE":
            log.warning(f"No API-Football key — skipping {league_name}")
            return []

        league_id = self.LEAGUE_IDS.get(league_name)
        if not league_id:
            log.warning(f"League '{league_name}' not in LEAGUE_IDS dict. Add its ID first.")
            return []

        headers = {
            "X-RapidAPI-Key":  self.key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        try:
            # Step 1: Get fixtures
            r = requests.get(
                f"{self.base}/fixtures",
                headers=headers,
                params={"league": league_id, "next": days_ahead * 3,
                        "season": datetime.now().year},
                timeout=15)
            fixtures = r.json().get("response", [])

            # Step 2: Get odds for each fixture
            games = []
            for fix in fixtures[:10]:  # Max 10 to save requests
                fid = fix["fixture"]["id"]
                home = fix["teams"]["home"]["name"]
                away = fix["teams"]["away"]["name"]

                odds_r = requests.get(
                    f"{self.base}/odds",
                    headers=headers,
                    params={"fixture": fid, "bet": 1},  # bet=1 = 1X2 (win/draw/lose)
                    timeout=15)
                bookmakers = []
                for bk in odds_r.json().get("response", [{}])[0].get("bookmakers", []):
                    for mkt in bk.get("bets", []):
                        if mkt["name"] == "Match Winner":
                            odds_vals = {v["value"]: float(v["odd"]) for v in mkt["values"]}
                            bookmakers.append({
                                "name": bk["name"],
                                "home": odds_vals.get("Home"),
                                "draw": odds_vals.get("Draw"),
                                "away": odds_vals.get("Away"),
                            })
                games.append({
                    "home_team": home, "away_team": away,
                    "fixture_id": fid, "bookmakers": bookmakers,
                    "source": "api_football", "league": league_name,
                })
                time.sleep(0.3)
            return games
        except Exception as e:
            log.error(f"API-Football error: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════
#  MAIN BOT
# ═══════════════════════════════════════════════════════════════════

class JackpotBot:
    def __init__(self):
        self.odds_api   = OddsAPI()
        self.apifb      = APIFootball()
        self.telegram   = Telegram()

    def analyse_game(self, home, away, bookmakers_data, league="default"):
        """
        Runs Poisson + EV across ALL bookmakers for one game.
        Returns (probs, all_value_bets).
        """
        probs    = match_probs(home, away, league)
        all_bets = []

        for bk in bookmakers_data:
            bk_name = bk.get("title") or bk.get("name") or "Unknown"

            if "markets" in bk:
                odds_map = {}
                for mkt in bk["markets"]:
                    if mkt.get("key") != "h2h": continue
                    for outcome in mkt["outcomes"]:
                        if outcome["name"] == home:   odds_map["home_win"] = outcome["price"]
                        elif outcome["name"] == away: odds_map["away_win"] = outcome["price"]
                        else:                         odds_map["draw"]     = outcome["price"]
            else:
                odds_map = {
                    "home_win": bk.get("home"),
                    "draw":     bk.get("draw"),
                    "away_win": bk.get("away"),
                }

            for mkt_key in ["home_win", "draw", "away_win"]:
                odds = odds_map.get(mkt_key)
                if not odds or not (CONFIG["MIN_ODDS"] <= odds <= CONFIG["MAX_ODDS"]):
                    continue
                model_p = probs[mkt_key]
                edge    = model_p - impl(odds)
                ev_val  = ev(model_p, odds)
                all_bets.append({
                    "home": home, "away": away, "league": league,
                    "market":     mkt_key,
                    "bookmaker":  bk_name,
                    "odds":       odds,
                    "model_pct":  round(model_p * 100, 1),
                    "market_pct": round(impl(odds) * 100, 1),
                    "edge_pct":   round(edge * 100, 1),
                    "ev_pct":     round(ev_val * 100, 1),
                    "kelly":      kelly(model_p, odds),
                    "lh": probs["lh"], "la": probs["la"],
                })

        value_bets = [b for b in all_bets if b["ev_pct"] >= CONFIG["EV_THRESHOLD"] * 100]
        return probs, value_bets

    def on_demand_scan(self):
        """
        ONE message per game + ONE final summary.
        Total messages = number of games + 1.
        """
        print(f"\n{'='*55}")
        print(f"  JACKPOT SCAN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"  Looking for {len(MY_JACKPOT_GAMES)} specific games")
        print(f"{'='*55}\n")

        games_checked = 0
        games_found   = []
        game_results  = []

        for league in MY_JACKPOT_LEAGUES:
            print(f"  Fetching {league}...")
            all_games = self.odds_api.get(league)
            time.sleep(0.5)

            for game in all_games:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                if not any(games_match(home, away, t) for t in MY_JACKPOT_GAMES):
                    continue

                games_found.append(f"{home} vs {away}")
                games_checked += 1
                print(f"  ✓ FOUND: {home} vs {away}")

                probs, value_bets = self.analyse_game(
                    home, away, game.get("bookmakers", []), league)
                self.telegram.game_summary(home, away, league, probs, value_bets)
                time.sleep(1)

                if value_bets:
                    rec = max(value_bets, key=lambda x: x["ev_pct"])
                    game_results.append({
                        "home":      home, "away": away,
                        "rec_label": {"home_win": f"{home} Win",
                                      "draw": "Draw",
                                      "away_win": f"{away} Win"}.get(rec["market"]),
                        "best_odds": rec["odds"],
                        "ev_pct":    rec["ev_pct"],
                        "kelly_amt": rec["kelly"]["amt"],
                    })

        if MY_MISSING_LEAGUE_GAMES:
            print(f"\n  Checking {len(MY_MISSING_LEAGUE_GAMES)} games via API-Football...")
            missing_by_league = {}
            for game_str in MY_MISSING_LEAGUE_GAMES:
                if "|" in game_str:
                    g, lg = game_str.split("|")
                    missing_by_league.setdefault(lg.strip(), []).append(g.strip())
                else:
                    missing_by_league.setdefault("Unknown", []).append(game_str)

            for league_name, game_list in missing_by_league.items():
                for game in self.apifb.get_fixtures_with_odds(league_name):
                    home = game["home_team"]
                    away = game["away_team"]
                    if not any(games_match(home, away, t) for t in game_list): continue
                    games_found.append(f"{home} vs {away}")
                    games_checked += 1
                    print(f"  ✓ FOUND (API-Football): {home} vs {away}")
                    probs, value_bets = self.analyse_game(
                        home, away, game["bookmakers"], league_name)
                    self.telegram.game_summary(home, away, league_name, probs, value_bets)
                    time.sleep(1)
                    if value_bets:
                        rec = max(value_bets, key=lambda x: x["ev_pct"])
                        game_results.append({
                            "home": home, "away": away,
                            "rec_label": {"home_win": f"{home} Win",
                                          "draw": "Draw",
                                          "away_win": f"{away} Win"}.get(rec["market"]),
                            "best_odds": rec["odds"],
                            "ev_pct":    rec["ev_pct"],
                            "kelly_amt": rec["kelly"]["amt"],
                        })

        print(f"\n{chr(45)*55}")
        not_found = [g for g in MY_JACKPOT_GAMES
                     if not any(games_match(gf.split(' vs ')[0],
                         gf.split(' vs ')[-1], g) for gf in games_found)]
        if not_found:
            print("\n  ⚠️  NOT FOUND (run listgames to check names):")
            for g in not_found: print(f"     - {g}")
        print(f"\n  Games found:       {games_checked}")
        print(f"  Games with value:  {len(game_results)}")
        if self.odds_api.remaining:
            print(f"  API requests left: {self.odds_api.remaining}")
        print(f"{chr(45)*55}\n")

        self.telegram.final_summary(game_results, games_checked)
        return game_results

    def list_available_games(self):
        """
        Run with: python main.py listgames
        Prints every game the API has right now so you can copy exact team names.
        """
        print(f"\n  Games available right now in your leagues:\n")
        for league in MY_JACKPOT_LEAGUES:
            print(f"\n  ── {league} ──")
            games = self.odds_api.get(league)
            if not games:
                print("    (no games found / check API key)")
                continue
            for g in games:
                ko = g.get("commence_time","")[:16].replace("T"," ")
                print(f"    {g['home_team']} vs {g['away_team']}  [{ko}]")
            time.sleep(0.5)
        print()

    def list_all_leagues(self):
        """
        Run with: python main.py listleagues
        Prints every league ID available in the Odds API.
        """
        print("\n  All soccer leagues available in the Odds API:\n")
        self.odds_api.list_leagues()
        print()


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINTS — how to run the bot
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    bot = JackpotBot()
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"

    if mode == "scan":
        # ★ NORMAL USE: python main.py
        bot.on_demand_scan()

    elif mode == "test":
        print("\n  OFFLINE TEST\n")
        p = match_probs("Arsenal", "Liverpool", "soccer_epl")
        print(f"  Arsenal vs Liverpool:")
        print(f"    Home win: {p['home_win']*100:.1f}%  Draw: {p['draw']*100:.1f}%  Away: {p['away_win']*100:.1f}%")
        print(f"    λ home={p['lh']}  λ away={p['la']}")
        print(f"\n  Telegram game summary preview (1 message per game):")

        # Simulate 3 bookmakers offering different odds
        fake_bets = [
            {"market":"home_win","bookmaker":"Pinnacle","odds":2.20,
             "model_pct":52.3,"market_pct":45.5,"edge_pct":6.8,"ev_pct":14.9,
             "kelly":{"pct":3.8,"amt":38.0},"lh":1.61,"la":1.27},
            {"market":"home_win","bookmaker":"Bet365","odds":2.15,
             "model_pct":52.3,"market_pct":46.5,"edge_pct":5.8,"ev_pct":12.1,
             "kelly":{"pct":3.1,"amt":31.0},"lh":1.61,"la":1.27},
            {"market":"draw","bookmaker":"Betfair","odds":3.50,
             "model_pct":24.1,"market_pct":28.6,"edge_pct":-4.5,"ev_pct":-15.7,
             "kelly":{"pct":0,"amt":0},"lh":1.61,"la":1.27},
            {"market":"away_win","bookmaker":"Pinnacle","odds":3.40,
             "model_pct":36.5,"market_pct":29.4,"edge_pct":7.1,"ev_pct":24.1,
             "kelly":{"pct":4.9,"amt":49.0},"lh":1.61,"la":1.27},
        ]
        bot.telegram.game_summary("Arsenal", "Liverpool", "soccer_epl", p, fake_bets)

        print(f"\n  Telegram final summary preview:")
        bot.telegram.final_summary([
            {"home":"Arsenal","away":"Liverpool","rec_label":"Liverpool Win",
             "best_odds":3.40,"ev_pct":24.1,"kelly_amt":49.0},
            {"home":"Chelsea","away":"Tottenham","rec_label":"Draw",
             "best_odds":3.20,"ev_pct":8.3,"kelly_amt":22.0},
        ], 5)
        print("\n  ✅ Test passed.\n")

    elif mode == "listgames":
        # See exact team names before typing them in: python main.py listgames
        bot.list_available_games()

    elif mode == "listleagues":
        # Find league IDs: python main.py listleagues
        bot.list_all_leagues()

    else:
        print(f"  Unknown mode '{mode}'. Options: scan | test | listgames | listleagues")