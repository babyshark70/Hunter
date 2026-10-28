
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
from zoneinfo import ZoneInfo

# ------------------ تنظیمات صفحه ------------------
st.set_page_config(
    page_title="Semiconductor Day Trader",
    page_icon="⚡",
    layout="wide"
)

# ------------------ ورود با رمز ------------------
def check_password():
    if st.session_state.get("authenticated", False):
        return True

    st.title("🔐 ورود به داشبورد")
    password = st.text_input("رمز عبور", type="password")

    if st.button("ورود"):
        if password == "Arash1234":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("رمز عبور اشتباه است.")

    return False


if not check_password():
    st.stop()

# تم واقعی روشن/تاریک؛ انتخاب در session حفظ می‌شود و کل رابط هماهنگ تغییر می‌کند.
if "dashboard_theme" not in st.session_state:
    st.session_state["dashboard_theme"] = "تاریک"
st.sidebar.header("🎨 ظاهر برنامه")
st.sidebar.radio("حالت نمایش", ["تاریک", "روشن"], key="dashboard_theme", horizontal=True)
IS_DARK = st.session_state["dashboard_theme"] == "تاریک"
THEME = {
    "bg": "#0b1220" if IS_DARK else "#f4f7fb",
    "panel": "#111c2e" if IS_DARK else "#ffffff",
    "panel2": "#172338" if IS_DARK else "#edf2f8",
    "text": "#e8eef7" if IS_DARK else "#172033",
    "muted": "#a9b7ca" if IS_DARK else "#596579",
    "border": "#2b3b52" if IS_DARK else "#d7dfeb",
    "input": "#152238" if IS_DARK else "#ffffff",
    "tv": "dark" if IS_DARK else "light",
}
st.markdown(f"""<style>
:root {{
  color-scheme: {'dark' if IS_DARK else 'light'};
  --text-color: {THEME['text']};
  --background-color: {THEME['bg']};
  --secondary-background-color: {THEME['panel']};
  --primary-color: {'#66bbff' if IS_DARK else '#1457b8'};
}}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background: {THEME['bg']} !important;
  color: {THEME['text']} !important;
}}
[data-testid="stHeader"] {{ background: {THEME['bg']} !important; }}
[data-testid="stSidebar"] {{ background: {THEME['panel']} !important; }}
[data-testid="stSidebar"] * {{ color: {THEME['text']}; }}
/* Force readable theme-aware text across Streamlit's native components. */
.stApp p, .stApp li, .stApp label, .stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stText"], .stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricDelta"] {{ color: {THEME['text']}; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
  color: {THEME['text']} !important;
}}
.stApp [data-testid="stCaptionContainer"], .stApp small {{ color: {THEME['muted']} !important; }}
[data-testid="stMetric"] {{ background: {THEME['panel']} !important; border: 1px solid {THEME['border']}; border-radius: 10px; padding: 10px; }}
[data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] div {{ color: {THEME['text']} !important; }}
[data-testid="stMetricDelta"] svg {{ fill: currentColor; }}
[data-testid="stExpander"] {{ background: {THEME['panel']} !important; border: 1px solid {THEME['border']}; border-radius: 9px; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary span {{ color: {THEME['text']} !important; }}
[data-testid="stDataFrame"], [data-testid="stTable"] {{ background: {THEME['panel']} !important; color: {THEME['text']} !important; }}
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"],
.stTextArea textarea {{ background: {THEME['input']} !important; color: {THEME['text']} !important; }}
[data-baseweb="select"] *, [data-baseweb="input"] *, [data-baseweb="checkbox"] + label {{ color: {THEME['text']} !important; }}
hr {{ border-color: {THEME['border']} !important; }}
</style>""", unsafe_allow_html=True)

st_autorefresh(interval=15000, key="market_refresh")

st.title("⚡ داشبورد معاملات روزانه نیمه‌هادی‌ها")
st.caption("سیگنال ۵ دقیقه‌ای با تأیید ۱۵ دقیقه‌ای؛ تصمیم ورود از مدیریت موقعیت جداست. داده Yahoo Finance ممکن است تأخیری باشد؛ این داشبورد سفارش واقعی ثبت نمی‌کند.")

# مدیریت موقعیت اختیاری؛ برای خروج/نگهداری باید قیمت ورود واقعی وارد شود.
st.sidebar.header("مدیریت موقعیت فعلی")
st.sidebar.caption("اگر SOXL یا SOXS داری، اطلاعات ورود را وارد کن تا پیشنهاد نگهداری/خروج محاسبه شود.")
position_inputs = {}
for _sym in ("SOXL", "SOXS"):
    with st.sidebar.expander(f"موقعیت {_sym}", expanded=False):
        _held = st.checkbox(f"در حال حاضر {_sym} دارم", key=f"held_{_sym}")
        _entry = st.number_input(f"قیمت ورود {_sym} ($)", min_value=0.0, value=0.0, step=0.05, key=f"entry_{_sym}")
        _shares = st.number_input(f"تعداد سهم {_sym}", min_value=0, value=0, step=1, key=f"shares_{_sym}")
        position_inputs[_sym] = {"held": _held, "entry": float(_entry), "shares": int(_shares)}

SYMBOLS = [
    "SOXL", "SOXS", "SOXX", "QQQ", "SPY",
    "NVDA", "AVGO", "AMD", "QCOM", "AMAT",
    "MU", "LRCX", "KLAC", "MRVL", "INTC"
]

SEMIS = [
    "NVDA", "AVGO", "AMD", "QCOM", "AMAT",
    "MU", "LRCX", "KLAC", "MRVL", "INTC"
]

# ------------------ دریافت داده ------------------
@st.cache_data(ttl=15, show_spinner=False)
def download_data():
    raw = yf.download(
        tickers=" ".join(SYMBOLS),
        period="5d",
        interval="5m",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True
    )

    result = {}

    if raw is None or raw.empty:
        return result

    for symbol in SYMBOLS:
        try:
            if not isinstance(raw.columns, pd.MultiIndex):
                continue

            if symbol in raw.columns.get_level_values(0):
                df = raw[symbol].copy()
            elif symbol in raw.columns.get_level_values(1):
                df = raw.xs(symbol, axis=1, level=1).copy()
            else:
                continue
            # برخی نسخه‌های yfinance ترتیب سطوح ستون‌ها را متفاوت برمی‌گردانند.
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[-1] if str(c[-1]).title() in {"Open", "High", "Low", "Close", "Volume"} else c[0] for c in df.columns]

            df.columns = [str(c).title() for c in df.columns]
            required = ["Open", "High", "Low", "Close", "Volume"]

            if not all(c in df.columns for c in required):
                continue

            df = df[required].apply(pd.to_numeric, errors="coerce")
            df = df.dropna(subset=["Open", "High", "Low", "Close"])
            df = df[~df.index.duplicated(keep="last")].sort_index()

            if len(df) >= 60:
                result[symbol] = df

        except Exception:
            continue

    return result


# ------------------ اندیکاتورها ------------------
def add_indicators(df):
    x = df.copy()

    x["EMA9"] = x["Close"].ewm(span=9, adjust=False).mean()
    x["EMA21"] = x["Close"].ewm(span=21, adjust=False).mean()

    delta = x["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / 14, min_periods=14, adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / 14, min_periods=14, adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    x["RSI"] = 100 - 100 / (1 + rs)

    # MACD استاندارد: خط MACD، خط سیگنال و هیستوگرام جداگانه نگهداری می‌شوند.
    macd_line = (
        x["Close"].ewm(span=12, adjust=False).mean()
        - x["Close"].ewm(span=26, adjust=False).mean()
    )
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    x["MACDLine"] = macd_line
    x["MACDSignal"] = macd_signal
    x["MACDHist"] = macd_line - macd_signal

    typical = (x["High"] + x["Low"] + x["Close"]) / 3
    volume = x["Volume"].fillna(0)
    session = pd.Series(x.index.date, index=x.index)

    pv = (typical * volume).groupby(session).cumsum()
    cv = volume.groupby(session).cumsum()
    x["VWAP"] = pv / cv.replace(0, np.nan)

    x["RVOL"] = (
        volume
        / volume.shift(1).rolling(20).mean().replace(0, np.nan)
    )

    previous_close = x["Close"].shift(1)

    true_range = pd.concat([
        x["High"] - x["Low"],
        (x["High"] - previous_close).abs(),
        (x["Low"] - previous_close).abs()
    ], axis=1).max(axis=1)

    x["ATR"] = true_range.ewm(
        alpha=1 / 14, min_periods=14, adjust=False
    ).mean()

    x["Tenkan"] = (
        x["High"].rolling(9).max()
        + x["Low"].rolling(9).min()
    ) / 2

    x["Kijun"] = (
        x["High"].rolling(26).max()
        + x["Low"].rolling(26).min()
    ) / 2

    x["SpanA"] = (x["Tenkan"] + x["Kijun"]) / 2

    x["SpanB"] = (
        x["High"].rolling(52).max()
        + x["Low"].rolling(52).min()
    ) / 2

    return x


def analyze(raw):
    if raw is None or len(raw) < 60:
        return None

    # کندل آخر کنار گذاشته می‌شود چون ممکن است هنوز باز باشد.
    x = add_indicators(raw.iloc[:-1].copy())
    x = x.dropna(subset=["EMA9", "EMA21", "RSI", "MACDHist", "ATR"])

    if len(x) < 30:
        return None

    last = x.iloc[-1]
    previous = x.iloc[-2]
    price = float(last["Close"])

    # درصد تغییر روزانه: آخرین کندل بسته‌شده در برابر قیمت بسته‌شدن جلسه قبل.
    # این مقدار با تغییر آخرین کندل ۵ دقیقه‌ای فرق دارد.
    current_session_date = x.index[-1].date()
    prior_session_rows = x[[stamp.date() < current_session_date for stamp in x.index]]
    if not prior_session_rows.empty and float(prior_session_rows["Close"].iloc[-1]) != 0:
        previous_session_close = float(prior_session_rows["Close"].iloc[-1])
        daily_change = (price / previous_session_close - 1) * 100
    else:
        daily_change = np.nan
    change_5m = (
        (price / float(previous["Close"]) - 1) * 100
        if float(previous["Close"]) != 0 else np.nan
    )

    bars15 = raw.iloc[:-1].resample("15min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    }).dropna()
    # فقط کندل‌های کامل ۱۵ دقیقه‌ای را برای تأیید روند استفاده کن.
    if len(x.index):
        last_closed_time = x.index[-1] + pd.Timedelta(minutes=5)
        bars15 = bars15[bars15.index + pd.Timedelta(minutes=15) <= last_closed_time]

    trend15 = None

    if len(bars15) >= 25:
        ema9_15 = bars15["Close"].ewm(span=9, adjust=False).mean()
        ema21_15 = bars15["Close"].ewm(span=21, adjust=False).mean()
        trend15 = bool(ema9_15.iloc[-1] > ema21_15.iloc[-1])

    vwap = float(last["VWAP"]) if pd.notna(last["VWAP"]) else np.nan

    cloud = None
    if pd.notna(last["SpanA"]) and pd.notna(last["SpanB"]):
        cloud = price > max(float(last["SpanA"]), float(last["SpanB"]))

    return {
        "price": price,
        "change": daily_change,
        "change_5m": change_5m,
        "rsi": float(last["RSI"]),
        "ema9": float(last["EMA9"]),
        "ema21": float(last["EMA21"]),
        "macd": float(last["MACDHist"]),
        "macd_prev": float(previous["MACDHist"]) if pd.notna(previous["MACDHist"]) else np.nan,
        "macd_line": float(last["MACDLine"]),
        "macd_signal": float(last["MACDSignal"]),
        "macd_line_prev": float(previous["MACDLine"]) if pd.notna(previous["MACDLine"]) else np.nan,
        "macd_signal_prev": float(previous["MACDSignal"]) if pd.notna(previous["MACDSignal"]) else np.nan,
        "previous_high": float(previous["High"]),
        "previous_low": float(previous["Low"]),
        "vwap": vwap,
        "rvol": float(last["RVOL"]) if pd.notna(last["RVOL"]) else np.nan,
        "atr": float(last["ATR"]),
        "trend15": trend15,
        "cloud": cloud,
        "time": str(x.index[-1])
    }


# ------------------ پهنای گروه ------------------
def get_breadth(analysis):
    valid = [
        analysis.get(s) for s in SEMIS
        if analysis.get(s) is not None
    ]

    if not valid:
        return None

    bullish = sum(
        a["ema9"] > a["ema21"]
        and pd.notna(a["vwap"])
        and a["price"] > a["vwap"]
        for a in valid
    )

    return bullish / len(valid), bullish, len(valid)


# ------------------ ارزیابی SOXL و SOXS ------------------
def evaluate(symbol, a, soxx, qqq, spy, breadth):
    if a is None:
        return {
            "symbol": symbol,
            "score": 0,
            "decision": "داده ناکافی",
            "reasons": [],
            "warnings": ["داده کافی دریافت نشد."],
            "stop": np.nan,
            "target": np.nan,
            "data": None
        }

    score = 0
    reasons = []
    warnings = []

    is_long = symbol == "SOXL"
    ema_up = a["ema9"] > a["ema21"]
    ema_down = a["ema9"] < a["ema21"]
    vwap_valid = pd.notna(a["vwap"])
    vwap_aligned = vwap_valid and (a["price"] > a["vwap"] if is_long else a["price"] < a["vwap"])
    # MACD استاندارد: خط/سیگنال و تغییر هیستوگرام جداگانه؛ برای SOXS جهت نزولی لازم است.
    macd_up = a.get("macd_line", -np.inf) > a.get("macd_signal", np.inf)
    macd_down = a.get("macd_line", np.inf) < a.get("macd_signal", -np.inf)
    macd_aligned = macd_up if is_long else macd_down
    macd_improving = pd.notna(a.get("macd_prev", np.nan)) and (
        a["macd"] > a["macd_prev"] if is_long else a["macd"] < a["macd_prev"]
    )
    macd_cross = (
        pd.notna(a.get("macd_line_prev", np.nan))
        and pd.notna(a.get("macd_signal_prev", np.nan))
        and ((a["macd_line_prev"] <= a["macd_signal_prev"] and a["macd_line"] > a["macd_signal"])
             if is_long else
             (a["macd_line_prev"] >= a["macd_signal_prev"] and a["macd_line"] < a["macd_signal"]))
    )
    breakout = (a["price"] > a.get("previous_high", np.inf)) if is_long else (a["price"] < a.get("previous_low", -np.inf))
    trend15_aligned = a["trend15"] is (True if is_long else False)
    rsi = a["rsi"]

    if (ema_up if is_long else ema_down):
        score += 15
        reasons.append("EMA9 بالاتر از EMA21 است." if is_long else "EMA9 پایین‌تر از EMA21 است؛ جهت نزولی تأیید می‌شود.")
    else:
        warnings.append("چیدمان EMA با جهت معامله هم‌خوان نیست.")

    if vwap_aligned:
        score += 15
        reasons.append("قیمت بالاتر از VWAP است." if is_long else "قیمت پایین‌تر از VWAP است.")
    else:
        warnings.append("قیمت نسبت به VWAP با جهت معامله هم‌خوان نیست.")

    if macd_aligned:
        score += 12
        reasons.append("خط MACD بالاتر از سیگنال است." if is_long else "خط MACD پایین‌تر از سیگنال است.")
    else:
        warnings.append("خط MACD هنوز جهت معامله را تأیید نمی‌کند.")

    if macd_improving:
        score += 5
        reasons.append("هیستوگرام MACD در جهت معامله تقویت شده است.")
    else:
        warnings.append("هیستوگرام MACD هنوز در جهت معامله تقویت نشده است.")

    if macd_cross:
        score += 3
        reasons.append("کراس تازه MACD در جهت معامله تأیید شده است.")

    if breakout:
        score += 5
        reasons.append("شکست سقف کندل قبلی تأیید شده است." if is_long else "شکست کف کندل قبلی به سمت پایین تأیید شده است.")
    else:
        warnings.append("شکست سطح کندل قبلی در جهت معامله هنوز تأیید نشده است.")

    if is_long:
        if 50 <= rsi <= 67:
            score += 10; reasons.append("RSI در محدوده مناسب مومنتوم صعودی است.")
        elif 45 <= rsi < 50:
            score += 5; reasons.append("RSI نزدیک محدوده مثبت است.")
        elif rsi > 72:
            warnings.append("RSI بالاست؛ خطر تعقیب قیمت وجود دارد.")
        elif rsi < 40:
            warnings.append("RSI پایین است؛ به‌تنهایی سیگنال خرید نیست.")
    else:
        if 33 <= rsi <= 50:
            score += 10; reasons.append("RSI با مومنتوم نزولی سازگار است.")
        elif 50 < rsi <= 55:
            score += 5; reasons.append("RSI نزدیک محدوده نزولی است.")
        elif rsi < 28:
            warnings.append("RSI بسیار پایین است؛ خطر جهش برگشتی SOXS وجود دارد.")
        elif rsi > 60:
            warnings.append("RSI بالا است و با مومنتوم نزولی هم‌خوانی ندارد.")

    if pd.notna(a["rvol"]) and a["rvol"] >= 1.2:
        score += 10
        reasons.append("حجم نسبی از ۱٫۲ بیشتر است.")
    elif pd.notna(a["rvol"]) and a["rvol"] < 0.7:
        warnings.append("حجم نسبی پایین است.")
    else:
        warnings.append("حجم هنوز تأیید قوی نمی‌دهد.")

    if trend15_aligned:
        score += 10
        reasons.append("روند ۱۵ دقیقه‌ای صعودی است." if is_long else "روند ۱۵ دقیقه‌ای نزولی است.")
    elif a["trend15"] is not None:
        warnings.append("روند ۱۵ دقیقه‌ای با جهت معامله هم‌خوان نیست.")

    if a["cloud"] is (True if is_long else False):
        score += 5
        reasons.append("قیمت بالاتر از ابر ایچیموکو است." if is_long else "قیمت زیر ابر ایچیموکو است.")
    elif a["cloud"] is not None:
        warnings.append("موقعیت قیمت نسبت به ابر ایچیموکو تأیید کامل نمی‌دهد.")

    if soxx is not None:
        soxx_up = (
            soxx["ema9"] > soxx["ema21"]
            and pd.notna(soxx["vwap"])
            and soxx["price"] > soxx["vwap"]
        )
        soxx_down = (
            soxx["ema9"] < soxx["ema21"]
            and pd.notna(soxx["vwap"])
            and soxx["price"] < soxx["vwap"]
        )

        if symbol == "SOXL" and soxx_up:
            score += 15
            reasons.append("SOXX صعودی است و از جهت SOXL حمایت می‌کند.")
        elif symbol == "SOXS" and soxx_down:
            score += 15
            reasons.append("SOXX ضعیف است و جهت صنعت به نفع SOXS است.")
        elif symbol == "SOXL" and soxx_down:
            warnings.append("SOXX نزولی است؛ خرید SOXL ریسک بیشتری دارد.")
        elif symbol == "SOXS" and soxx_up:
            warnings.append("SOXX صعودی است؛ خرید SOXS ریسک بیشتری دارد.")

    if breadth is not None:
        ratio, bullish, total = breadth

        if symbol == "SOXL" and ratio >= 0.7:
            score += 10
            reasons.append(f"{bullish} از {total} سهم گروه صعودی‌اند.")
        elif symbol == "SOXL" and ratio <= 0.3:
            warnings.append("پهنای گروه ضعیف است.")
        elif symbol == "SOXS" and ratio <= 0.3:
            score += 10
            reasons.append("ضعف سهام گروه گسترده است.")
        elif symbol == "SOXS" and ratio >= 0.7:
            warnings.append("اکثر سهام گروه صعودی‌اند؛ SOXS پرریسک‌تر است.")

    market = [m for m in (qqq, spy) if m is not None]

    if market:
        up_count = sum(m["ema9"] > m["ema21"] for m in market)

        if symbol == "SOXL" and up_count == len(market):
            score += 5
            reasons.append("روند کوتاه‌مدت QQQ و SPY صعودی است.")
        elif symbol == "SOXS" and up_count == 0:
            score += 5
            reasons.append("روند کوتاه‌مدت QQQ و SPY نزولی است.")
        elif symbol == "SOXL" and up_count == 0:
            warnings.append("QQQ و SPY ضعیف‌اند.")
        elif symbol == "SOXS" and up_count == len(market):
            warnings.append("QQQ و SPY صعودی‌اند.")

    score = min(score, 100)

    # امتیاز به‌تنهایی اجازه ورود نیست: شرایط پایه باید هم‌زمان برقرار باشد.
    rsi_ok = (50 <= rsi < 72) if is_long else (28 < rsi <= 50)
    core_ok = (
        (ema_up if is_long else ema_down)
        and vwap_aligned and macd_aligned and macd_improving
        and breakout and trend15_aligned and rsi_ok
        and pd.notna(a["rvol"]) and a["rvol"] >= 0.8
    )

    if symbol == "SOXL":
        core_ok = core_ok and soxx is not None
    if symbol == "SOXL" and soxx is not None:
        core_ok = core_ok and (
            soxx["ema9"] > soxx["ema21"]
            and pd.notna(soxx["vwap"])
            and soxx["price"] > soxx["vwap"]
        )
        if breadth is not None:
            core_ok = core_ok and breadth[0] >= 0.5

    if symbol == "SOXS":
        core_ok = core_ok and soxx is not None
    if symbol == "SOXS" and soxx is not None:
        core_ok = core_ok and (
            soxx["ema9"] < soxx["ema21"]
            and pd.notna(soxx["vwap"])
            and soxx["price"] < soxx["vwap"]
        )
        if breadth is not None:
            core_ok = core_ok and breadth[0] <= 0.5

    if score >= 75 and core_ok:
        decision = "خرید مشروط"
    elif score >= 45:
        decision = "انتظار برای تأیید"
    else:
        decision = "عدم معامله"

    if decision != "خرید مشروط":
        warnings.append("شرایط ورود کامل نیست؛ معامله را اجباری نکن.")

    return {
        "symbol": symbol,
        "score": score,
        "decision": decision,
        "reasons": reasons,
        "warnings": warnings,
        "stop": (
            a["price"] - 1.25 * a["atr"] if is_long and a["atr"] > 0
            else a["price"] + 1.25 * a["atr"] if (not is_long and a["atr"] > 0)
            else np.nan
        ),
        "target": (
            a["price"] + 1.875 * a["atr"] if is_long and a["atr"] > 0
            else a["price"] - 1.875 * a["atr"] if (not is_long and a["atr"] > 0)
            else np.nan
        ),
        "data": a
    }


# ------------------ تحلیل داده‌های دریافتی ------------------
with st.spinner("در حال دریافت داده‌های بازار..."):
    raw_data = download_data()

analysis = {}

for symbol, frame in raw_data.items():
    try:
        analysis[symbol] = analyze(frame)
    except Exception:
        analysis[symbol] = None

if not raw_data:
    st.error(
        "داده بازار از Yahoo Finance دریافت نشد؛ بنابراین سیگنال زنده نمایش داده نمی‌شود. "
        "اینترنت، دسترسی Yahoo Finance و نصب/به‌روز بودن yfinance را بررسی کن. "
        "بخش نمودارهای TradingView و جدول نمادها همچنان نمایش داده می‌شود."
    )
    st.info("اگر این پیام تکرار شد، در ترمینال اجرای Streamlit خطای yfinance را بررسی کن؛ داده ساختگی جایگزین نمی‌شود.")

breadth = get_breadth(analysis)
soxx = analysis.get("SOXX")
qqq = analysis.get("QQQ")
spy = analysis.get("SPY")

# ------------------ خلاصه شاخص‌ها ------------------
st.subheader("🌐 وضعیت کلی بازار")
if not raw_data:
    st.caption("حالت نمایش در دسترس است، اما داده تحلیلی Yahoo Finance فعلاً بارگیری نشده است.")
c1, c2, c3, c4 = st.columns(4)

for col, symbol, label in [
    (c1, "SOXX", "SOXX — صنعت تراشه"),
    (c2, "QQQ", "QQQ — فناوری"),
    (c3, "SPY", "SPY — بازار عمومی")
]:
    a = analysis.get(symbol)

    if a is None:
        col.metric(label, "داده موجود نیست")
    else:
        col.metric(label, f"${a['price']:.2f}", f"{a['change']:+.2f}%")
        col.caption(
            f"RSI: {a['rsi']:.2f} | "
            f"روند ۱۵ دقیقه: "
            f"{'صعودی' if a['trend15'] is True else 'نزولی' if a['trend15'] is False else 'نامشخص'}"
        )

if breadth is not None:
    c4.metric(
        "پهنای گروه نیمه‌هادی",
        f"{breadth[1]}/{breadth[2]}",
        f"{breadth[0] * 100:.0f}%"
    )
else:
    c4.metric("پهنای گروه نیمه‌هادی", "نامشخص")

# ------------------ تصمیم فشرده + نمودارهای اصلی ------------------
st.markdown("---")
st.subheader("⚖️ تصمیم ورود و نمودارهای اصلی")

results = [
    evaluate("SOXL", analysis.get("SOXL"), soxx, qqq, spy, breadth),
    evaluate("SOXS", analysis.get("SOXS"), soxx, qqq, spy, breadth)
]

# نمودار اصلی را کنار تصمیم‌ها نگه می‌داریم تا برای دیدن آن‌ها نیاز به اسکرول زیاد نباشد.
def render_tv(symbol, height=340):
    widget_id = "tv_" + symbol.replace(":", "_")
    html = f"""
    <div id="{widget_id}"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
      "width":"100%",
      "height":{height},
      "symbol":"{symbol}",
      "interval":"5",
      "timezone":"America/New_York",
      "theme":"{THEME['tv']}",
      "style":"1",
      "locale":"en",
      "enable_publishing":false,
      "allow_symbol_change":true,
      "container_id":"{widget_id}",
      "studies":["RSI@tv-basicstudies", "MACD@tv-basicstudies", "IchimokuCloud@tv-basicstudies"]
    }});
    </script>
    """
    components.html(html, height=height + 20, scrolling=False)


def fmt_price(value):
    return f"${value:.2f}" if pd.notna(value) and np.isfinite(value) else "—"

for col, result in zip(st.columns(2), results):
    with col:
        color = (
            "#00c853" if result["decision"] == "خرید مشروط"
            else "#ffb300" if result["decision"] == "انتظار برای تأیید"
            else "#ff5252"
        )
        a = result["data"]
        st.markdown(
            f"""<div style="padding:10px 12px;border-radius:9px;border:2px solid {color};
            background:{THEME['panel']};color:{THEME['text']};margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
              <h3 style="margin:0;color:{color}">{result['symbol']} — {result['decision']}</h3>
              <b>امتیاز {result['score']}/100</b>
            </div></div>""",
            unsafe_allow_html=True
        )
        if a:
            m1, m2, m3 = st.columns(3)
            m1.metric("قیمت آخرین کندل بسته", fmt_price(a["price"]), f"{a['change']:+.2f}% روزانه")
            m2.metric("حد ضرر تخمینی", fmt_price(result["stop"]))
            m3.metric("هدف تخمینی", fmt_price(result["target"]))
            # پیشنهاد مدیریت موقعیت فقط وقتی قیمت ورود واقعی وارد شده باشد.
            _pos = position_inputs.get(result["symbol"], {})
            if _pos.get("held") and _pos.get("entry", 0) > 0 and _pos.get("shares", 0) > 0:
                _entry = _pos["entry"]
                _shares = _pos["shares"]
                _pnl_pct = (a["price"] / _entry - 1) * 100
                _pnl_dollars = (a["price"] - _entry) * _shares
                _is_long_position = result["symbol"] == "SOXL"
                _stop_pos = _entry - 1.25 * a["atr"] if _is_long_position else _entry + 1.25 * a["atr"]
                _target_pos = _entry + 1.875 * a["atr"] if _is_long_position else _entry - 1.875 * a["atr"]
                _now_et = datetime.now(ZoneInfo("America/New_York")).time()
                _weak = (a["ema9"] < a["ema21"] and pd.notna(a["vwap"]) and a["price"] < a["vwap"] and a["macd"] < 0)
                if a["price"] <= _stop_pos:
                    _hold_advice = "خروج طبق حد ضرر راهنما"
                elif a["price"] >= _target_pos:
                    _hold_advice = "رسیدن به هدف؛ برداشت سود/خروج را بررسی کن"
                elif _weak:
                    _hold_advice = "هشدار ضعف؛ خروج یا کاهش حجم را بررسی کن"
                elif _now_et >= time(15, 45):
                    _hold_advice = "پایان روز نزدیک است؛ طبق قانون بدون نگهداری شبانه خارج شو"
                else:
                    _hold_advice = "نگهداری مشروط؛ حد ضرر و هدف را زیر نظر بگیر"
                st.warning(f"**وضعیت موقعیت:** {_hold_advice}\n\nورود ${_entry:.2f} | تعداد {_shares} | بازده باز { _pnl_pct:+.2f}% | سود/زیان تقریبی ${_pnl_dollars:+.2f} | حد ضرر راهنما ${_stop_pos:.2f} | هدف راهنما ${_target_pos:.2f}")
            elif _pos.get("held"):
                st.info("برای پیشنهاد نگهداری/خروج، قیمت ورود و تعداد سهم را وارد کن.")
            st.caption(f"آخرین کندل بسته‌شده: {a['time']} | RSI {a['rsi']:.1f} | RVOL {a['rvol']:.2f}x" if pd.notna(a['rvol']) else f"آخرین کندل بسته‌شده: {a['time']} | RSI {a['rsi']:.1f} | RVOL نامشخص")
        positives = result["reasons"][:3]
        blockers = result["warnings"][:3]
        with st.expander(f"دلایل و موانع {result['symbol']}", expanded=False):
            st.markdown("**دلایل مثبت**")
            st.write("\n".join("✅ " + x for x in positives) if positives else "تأیید مثبت کافی وجود ندارد.")
            st.markdown("**موانع و ریسک‌ها**")
            st.write("\n".join("⚠️ " + x for x in blockers) if blockers else "مانع مهمی در فیلترهای فعلی شناسایی نشد.")

st.caption("MACD با خط MACD، خط سیگنال و هیستوگرام جداگانه سنجیده می‌شود؛ ورود به کندل بسته‌شده، شکست سقف قبلی، روند ۱۵ دقیقه‌ای و فیلتر SOXX وابسته است. حد ضرر/هدف برآوردی بر پایه ATR کندل‌های ۵ دقیقه‌ای هستند و سفارش حفاظتی واقعی نیستند. داده Yahoo ممکن است تأخیری باشد و سود تضمین‌شده نیست.")

# چهار نمودار اصلی در یک ردیف، به ترتیب درخواستی: SOXS، SOXL، SOXX، NVDA.
main_chart_cols = st.columns(4)
main_charts = [
    ("AMEX:SOXS", "SOXS"),
    ("AMEX:SOXL", "SOXL"),
    ("NASDAQ:SOXX", "SOXX"),
    ("NASDAQ:NVDA", "NVDA"),
]
for chart_col, (tv_symbol, display_name) in zip(main_chart_cols, main_charts):
    with chart_col:
        st.markdown(f"**{display_name} — نمودار ۵ دقیقه**")
        render_tv(tv_symbol, 430)

# ------------------ جدول و تحلیل کنار آن ------------------
st.markdown("---")
st.subheader("📊 جدول بازار و تحلیل کلی")

rows = []

for symbol in SYMBOLS:
    a = analysis.get(symbol)

    if a is None:
        rows.append({
            "نماد": symbol,
            "قیمت ($)": np.nan,
            "تغییر روزانه (%)": np.nan,
            "RSI": np.nan,
            "EMA9": np.nan,
            "EMA21": np.nan,
            "VWAP": np.nan,
            "RVOL": np.nan,
            "روند ۱۵ دقیقه": "نامشخص"
        })
    else:
        rows.append({
            "نماد": symbol,
            "قیمت ($)": a["price"],
            "تغییر روزانه (%)": a["change"],
            "RSI": a["rsi"],
            "EMA9": a["ema9"],
            "EMA21": a["ema21"],
            "VWAP": a["vwap"],
            "RVOL": a["rvol"],
            "روند ۱۵ دقیقه": (
                "صعودی" if a["trend15"] is True
                else "نزولی" if a["trend15"] is False
                else "نامشخص"
            )
        })

table = pd.DataFrame(rows)


def color_change(value):
    if pd.isna(value):
        return ""
    if value > 0:
        return "color:#00d26a;font-weight:bold"
    if value < 0:
        return "color:#ff5252;font-weight:bold"
    return f"color:{THEME['text']}"


styled = (
    table.style
    .format({
        "قیمت ($)": "${:.2f}",
        "تغییر روزانه (%)": "{:+.2f}%",
        "RSI": "{:.2f}",
        "EMA9": "${:.2f}",
        "EMA21": "${:.2f}",
        "VWAP": "${:.2f}",
        "RVOL": "{:.2f}x"
    }, na_rep="—")
    .map(color_change, subset=["تغییر روزانه (%)"])
    .set_properties(**{
        "font-size": "14px",
        "padding": "5px 6px",
        "white-space": "nowrap"
    })
    .set_table_styles([
        {"selector": "table", "props": [
            ("color", THEME["text"]),
            ("background-color", THEME["panel"]),
        ]},
        {"selector": "td", "props": [
            ("color", THEME["text"]),
            ("background-color", THEME["panel"]),
        ]},
        {"selector": "th", "props": [
            ("color", THEME["text"]),
            ("background-color", THEME["panel2"]),
            ("font-size", "13px"),
            ("font-weight", "bold"),
            ("white-space", "normal"),
            ("padding", "5px")
        ]}
    ])
)

left, right = st.columns([1.65, 1])

with left:
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=540
    )

with right:
    st.markdown("### 🧭 تحلیل کلی بازار")

    summary = []

    if soxx is not None:
        summary.append(
            f"**SOXX:** تغییر روزانه {soxx['change']:+.2f}%؛ "
            f"RSI برابر {soxx['rsi']:.2f}."
        )

    if qqq is not None:
        summary.append(
            f"**QQQ:** تغییر روزانه {qqq['change']:+.2f}%؛ "
            f"RSI برابر {qqq['rsi']:.2f}."
        )

    if spy is not None:
        summary.append(
            f"**SPY:** تغییر روزانه {spy['change']:+.2f}%؛ "
            f"RSI برابر {spy['rsi']:.2f}."
        )

    if breadth is not None:
        ratio, bullish, total = breadth

        if ratio >= 0.7:
            group_status = "قدرت گروه نسبتاً خوب است."
        elif ratio <= 0.3:
            group_status = "ضعف گروه گسترده است؛ احتیاط لازم است."
        else:
            group_status = "وضعیت گروه ترکیبی است."

        summary.append(
            f"**گروه نیمه‌هادی:** {bullish} از {total} سهم صعودی‌اند. "
            f"{group_status}"
        )

    if soxx is not None and qqq is not None and spy is not None:
        if soxx["change"] < 0 and qqq["change"] < 0 and spy["change"] < 0:
            conclusion = (
                "هر سه شاخص در آخرین کندل منفی‌اند؛ برای SOXL "
                "منتظر تثبیت و برگشت معتبر باش."
            )
        elif soxx["ema9"] > soxx["ema21"] and soxx["change"] > 0:
            conclusion = (
                "SOXX نشانه‌های کوتاه‌مدت مثبت دارد؛ "
                "حجم، VWAP و تأیید ۱۵ دقیقه را هم بررسی کن."
            )
        else:
            conclusion = (
                "بازار هنوز یک‌دست نیست؛ از ورود عجولانه پرهیز کن "
                "و تأیید هم‌زمان قیمت و روند را بخواه."
            )

        summary.append("**جمع‌بندی:** " + conclusion)

    st.info("\n\n".join(summary) if summary else "داده کافی موجود نیست.")

    st.markdown("### 📖 معنی ستون آخر")
    st.write("**صعودی:** EMA9 بالاتر از EMA21 در تایم‌فریم ۱۵ دقیقه است.")
    st.write("**نزولی:** EMA9 پایین‌تر از EMA21 است.")
    st.write("این ستون سود یا احتمال سود را نشان نمی‌دهد.")

    st.markdown("### ⚠️ یادآوری")
    st.write(
        "درصد تغییر جدول و کارت‌ها از قیمت بسته‌شدن جلسه قبل تا آخرین کندل بسته‌شده امروز محاسبه می‌شود؛ "
        "تغییر آخرین کندل ۵ دقیقه‌ای جداگانه محاسبه می‌شود. حد ضرر و هدف پیشنهادی تضمین‌شده نیستند."
    )

# ------------------ نمودارهای تکمیلی TradingView ------------------
with st.expander("📈 نمودارهای تکمیلی TradingView — سایر نمادها", expanded=False):
    tv_symbols = [
        ("NASDAQ:QQQ", "QQQ"), ("AMEX:SPY", "SPY"),
        ("NASDAQ:AVGO", "AVGO"), ("NASDAQ:AMD", "AMD"),
        ("NASDAQ:QCOM", "QCOM"), ("NASDAQ:AMAT", "AMAT"), ("NASDAQ:MU", "MU"),
        ("NASDAQ:LRCX", "LRCX"), ("NASDAQ:KLAC", "KLAC"), ("NASDAQ:MRVL", "MRVL"),
        ("NASDAQ:INTC", "INTC")
    ]
    for start_idx in range(0, len(tv_symbols), 3):
        chart_cols = st.columns(3)
        for col, (symbol, name) in zip(chart_cols, tv_symbols[start_idx:start_idx + 3]):
            with col:
                st.markdown(f"**{name}**")
                render_tv(symbol, 340)

st.caption(
    "این داشبورد فقط ابزار تحلیل است و سفارش خرید یا فروش ثبت نمی‌کند. "
    "قیمت Yahoo Finance ممکن است تأخیری باشد."
)
