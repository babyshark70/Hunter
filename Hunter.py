import streamlit as st
import os
from streamlit.errors import StreamlitSecretNotFoundError
import pandas as pd
import yfinance as yf
import numpy as np
import streamlit.components.v1 as components
import requests
import time
from datetime import datetime

# Must be the first Streamlit command.
st.set_page_config(layout="wide", page_title="Alpha Market Scanner & Multi-TF Monitor")

# Support both Streamlit secrets.toml and environments without a secrets file.
try:
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", os.environ.get("APP_PASSWORD", "Arash1234"))
except StreamlitSecretNotFoundError:
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "Arash1234")

def check_password():
    def password_entered():
        st.session_state["password_correct"] = (
            st.session_state.get("password", "") == APP_PASSWORD
        )
        st.session_state.pop("password", None)

    if st.session_state.get("password_correct") is True:
        return True
    st.text_input("لطفاً رمز عبور را وارد کنید:", type="password",
                  on_change=password_entered, key="password")
    if st.session_state.get("password_correct") is False:
        st.error("😕 رمز عبور اشتباه است")
    return False

if not check_password():
    st.stop()

st.markdown("""
<style>
.stApp,[data-testid="stHeader"],[data-testid="stSidebar"]{background:#131722!important;color:#d1d4dc!important}
.block-container{padding:.2rem .5rem 0!important}
h1{font-size:32px!important;font-weight:bold!important;color:#f8fafc!important;margin-bottom:0!important}
h2,h3{font-size:22px!important;font-weight:bold!important;color:#e2e8f0!important;margin:5px 0!important}
div[data-testid="stTextInput"]>label,div[data-testid="stWidgetLabel"] p{font-size:16px!important;font-weight:bold!important;color:#f8fafc!important}
hr{margin:5px 0!important;border-color:#2a2e39!important}
</style>
""", unsafe_allow_html=True)
st.title("🎯 Alpha Market Scanner & Multi-TF Q-Line Monitor")

FALLBACK_TICKERS = """
AAPL MSFT NVDA AMZN GOOGL GOOG META BRK-B AVGO LLY JPM WMT XOM V MA ORCL COST NFLX JNJ HD PG ABBV BAC KO PLTR CVX CRM AMD TMUS MRK CSCO ACN GE IBM WFC PM LIN ABT MCD TMO NOW ISRG CAT GS RTX AXP DIS QCOM INTU AMAT TXN PEP VZ MS UNH UBER BKNG LOW SPGI BLK SCHW C T DHR ADI SYK ANET MU LRCX KLAC PANW ADP BSX TJX CHTR PGR COP DE CB MMC CME ICE SO AMGN ETN MO REGN WM NEE HON MDT UPS CI CVS BMY ELV PNC USB AON EQIX APH SNPS CDNS CRWD MAR PLD SHW MCK CL CMG ORLY EOG FDX ITW GD EMR NOC NSC FCX NUE CMI PH MSI ROP TT CARR JCI FISV FICO RSG AEP DUK SRE EXC XEL OKE SLB ECL APD CTVA AIG MET PRU ALL AFL TRV KKR BX APO TROW COIN SHOP ARM SNOW DDOG ZS MDB NET TEAM VRTX GILD BIIB ZTS IDXX DXCM EW HCA HUM CEG VST PWR URI FAST ODFL LULU NKE SBUX YUM ROST DELL HPQ HPE STX WDC GLW TEL FLEX AME IR PHM LEN DHI NVR CCL RCL DAL UAL LUV ABNB DASH MELI TTD RBLX EA TTWO WDAY PAYX PAYC RMD CPRT CSGP VRSK ACGL AJG BRO ERIE WRB WTW FDS MCO MSCI NDAQ CBOE CINF FNF RJF KEY RF HBAN CFG MTB FITB TFC COF SYF DFS ARES OWL KNSL FANG MPC PSX VLO OXY DVN HAL BKR CTRA WMB KMI FTV CNP ETR PPL DTE ED AES GIS K DPZ KDP MDLZ HSY CLX KMB KR WBA TGT DG DLTR BBY TSCO GPC AZO AN BWA GM TM HMC NEM GOLD AEM WPM KGC RGLD SCCO AA CENX CCK BALL PKG IP AVY IFF LYB DOW DD NTR MOS CF FMC ADM BG TSN HRL CPB MKC SJM CHD ELF ULTA TPR RL PVH DECK CROX GPS ANF AEO URBN BBWI SIG COTY HIMS DOCS TEM CNC MOH INSP UHS THC HLT H HST VICI WYNN LVS MGM CZR PENN DKNG CHDN FLUT EXPE RKT RDFN ZG OPEN COMP INVH AMH EQR AVB ESS MAA CPT UDR FRT REG KIM BXP VNO SLG ARE PSA CUBE EXR IRM O SPG WPC NNN ELS SUI EQT SWN AR APA PR RRC CNX PAA ET MPLX EPD ENPH FSLR NRG DLR AMT CCI SBAC BEN IVZ AMP STT BK NTRS FIS GPN FI FOUR BILL SQ HOOD SOFI AFRM UPST TOST TWLO DOCU ZM OKTA ESTC AKAM FFIV JNPR CDW CIEN LITE COHR KEYS JBL SANM QRVO SWKS MCHP NXPI ON STM MPWR MRVL INTC TSM ENTG TER ACLS AMKR WOLF ALGM LSCC SYNA OLED MTSI CRUS RMBS IPGP RUN PLUG QS CHPT EVGO LCID RIVN NIO XPEV LI RACE CVNA KMX PAG LAD LKQ WAB CNI CP UNP CSX XPO SAIA JBHT CHRW EXPD LSTR WCN CWST GFL VRT FIX GEV LMT HII LHX TDG HEI TXT JOBY ACHR SOUN IONQ RGTI QBTS OKLO SMR CCJ PCG EIX ED ES WEC CMS NI EVRG IDA POR AWK XYL WAT A O WELL CCI TOWER TROW FNF FITB KEY CFG RF MTB HBAN CMA ZION WAL EWBC FHN SNV UMBF ONB WTFC PB CACC MORN RYAN CACI LDOS SAIC J BAH PSN KBR ACM FLR PCTY PAYC WEX BR
""".split()

def get_dynamic_universe():
    """Fetch a large US stock universe from Yahoo Screener, market-cap filtered."""
    screen_error = "unknown error"
    metadata = {}
    try:
        from yfinance import EquityQuery
        query = EquityQuery("and", [
            EquityQuery("eq", ["region", "us"]),
            # EquityQuery is-in expects each allowed value as a separate operand.
            EquityQuery("is-in", ["exchange", "NMS", "NYQ", "ASE"]),
            EquityQuery("gte", ["intradaymarketcap", 15_000_000_000]),
            EquityQuery("lte", ["intradaymarketcap", 6_000_000_000_000]),
            EquityQuery("gte", ["intradayprice", 5]),
        ])
        quotes = []
        # Yahoo Screener returns at most 250 per page. Request another page for 300+.
        for offset, size in ((0, 250), (250, 100), (350, 100)):
            result = yf.screen(query, offset=offset, size=size,
                               sortField="intradaymarketcap", sortAsc=False)
            if isinstance(result, dict):
                quotes.extend(result.get("quotes", []))
        symbols = []
        for item in quotes:
            if not isinstance(item, dict):
                continue
            symbol = str(item.get("symbol", "")).strip().upper()
            if not symbol:
                continue
            cap = item.get("intradaymarketcap", item.get("marketCap", np.nan))
            try:
                cap = float(cap)
            except (TypeError, ValueError):
                cap = np.nan
            # Keep only entries with a valid market cap in the requested range.
            if not np.isfinite(cap) or not (15_000_000_000 <= cap <= 6_000_000_000_000):
                continue
            if symbol not in metadata:
                symbols.append(symbol)
                metadata[symbol] = {
                    "MarketCap": cap,
                    "Company": item.get("longName") or item.get("shortName") or symbol,
                    "Industry": item.get("industry") or item.get("industryName") or "",
                }
        if len(symbols) >= 250:
            selected_symbols = symbols[:300]
            selected_metadata = {symbol: metadata[symbol] for symbol in selected_symbols}
            return selected_symbols, selected_metadata, "Yahoo Screener ($15B–$6T; market-cap verified)"
        screen_error = f"Screener returned only {len(symbols)} verified symbols"
    except Exception as exc:
        screen_error = f"{type(exc).__name__}: {exc}"
    # This fallback is intentionally marked as unverified: never claim its market caps are live-verified.
    symbols = list(dict.fromkeys(FALLBACK_TICKERS))[:300]
    metadata = {symbol: {"MarketCap": np.nan, "Company": symbol, "Industry": ""} for symbol in symbols}
    return symbols, metadata, f"Fallback list ({len(symbols)} symbols; $15B cap not verified): {screen_error}"

TICKERS, UNIVERSE_META, UNIVERSE_SOURCE = get_dynamic_universe()
OHLCV = ["Open","High","Low","Close","Volume"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

def normalize_history(frame):
    """Normalize yfinance MultiIndex and ordinary OHLCV data."""
    if frame is None or frame.empty:
        return pd.DataFrame()
    frame = frame.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        flat = []
        for column in frame.columns:
            parts = [str(x) for x in column]
            found = next((x for x in parts if x in OHLCV + ["Adj Close"]), None)
            flat.append(found or parts[0])
        frame.columns = flat
    frame.columns = [str(x) for x in frame.columns]
    frame = frame.loc[:, ~frame.columns.duplicated()]
    if not all(c in frame.columns for c in OHLCV):
        return pd.DataFrame()
    frame = frame[OHLCV]
    for c in OHLCV:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    frame = frame.dropna(subset=["Open","High","Low","Close"])
    return frame.loc[~frame.index.duplicated(keep="last")].sort_index()

def fetch_direct_yahoo(ticker):
    errors = []
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{ticker}"
        try:
            response = requests.get(
                url, params={"range":"1y","interval":"1d","events":"div,splits"},
                headers=HEADERS, timeout=(5, 12)
            )
            if response.status_code != 200:
                errors.append(f"{host}: HTTP {response.status_code}: {response.text[:100]!r}")
                continue
            payload = response.json()
            chart = payload.get("chart", {})
            if chart.get("error"):
                errors.append(f"{host}: Yahoo error {chart['error']}")
                continue
            result = (chart.get("result") or [None])[0]
            if not result:
                errors.append(f"{host}: empty result")
                continue
            timestamps = result.get("timestamp") or []
            quotes = result.get("indicators", {}).get("quote") or []
            if not timestamps or not quotes:
                errors.append(f"{host}: no OHLCV data")
                continue
            quote = quotes[0]
            dates = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None)
            raw = pd.DataFrame({c: quote.get(c.lower()) for c in OHLCV}, index=dates)
            raw.index.name = "Date"
            clean = normalize_history(raw)
            if not clean.empty:
                return clean, f"Yahoo chart API ({host})", None
            errors.append(f"{host}: OHLCV data unusable")
        except requests.exceptions.SSLError as exc:
            errors.append(f"{host}: SSL error: {exc}")
        except requests.exceptions.Timeout:
            errors.append(f"{host}: timeout")
        except requests.exceptions.RequestException as exc:
            errors.append(f"{host}: network error {type(exc).__name__}: {exc}")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"{host}: invalid response {type(exc).__name__}: {exc}")
        time.sleep(0.25)
    return pd.DataFrame(), None, " | ".join(errors)

def fetch_history(ticker):
    direct, source, direct_error = fetch_direct_yahoo(ticker)
    if not direct.empty:
        return direct, source, None
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False,
                           threads=False, auto_adjust=False, timeout=15)
        data = normalize_history(data)
        if not data.empty:
            return data, "yfinance fallback", None
        yf_error = "yfinance returned empty data"
    except Exception as exc:
        yf_error = f"{type(exc).__name__}: {exc}"
    return pd.DataFrame(), None, f"Direct API: {direct_error} | yfinance: {yf_error}"

def q_cloud_analysis(frame):
    """Analyze the *visually aligned* Q-Line and Ichimoku cloud from the user's Pine script.

    Quality Line = Kijun-26 plotted with offset +26, so the value visible at the
    latest chart bar is BaseLine[26] (iloc[-27]). The cloud is plotted with
    offset displacement-1 = +25, so its value visible at the latest bar is
    SpanA[25]/SpanB[25] (iloc[-26]). This alignment avoids a 25/26-bar mismatch.
    Returns a dict of position, Q-Line value, cloud bounds, cloud color/direction,
    distance, and a concise event/alert.
    """
    empty = {"status":"N/A", "value":np.nan, "cloud_low":np.nan,
             "cloud_high":np.nan, "cloud_color":"N/A", "cloud_move":"N/A",
             "distance_pct":np.nan, "event":"Insufficient data"}
    if frame is None or frame.empty or len(frame) < 78:
        return empty.copy()
    try:
        high = pd.to_numeric(frame["High"], errors="coerce")
        low = pd.to_numeric(frame["Low"], errors="coerce")
        close = pd.to_numeric(frame["Close"], errors="coerce")
        def donchian(length):
            return (high.rolling(length, min_periods=length).max() +
                    low.rolling(length, min_periods=length).min()) / 2
        conversion = donchian(9)
        baseline = donchian(26)
        span_a = (conversion + baseline) / 2
        span_b = donchian(52)

        # Pine offsets are display shifts, not shifts to the underlying series.
        q_value = float(baseline.iloc[-27])       # plot(baseLine, offset=+26)
        span_a_now = float(span_a.iloc[-26])      # cloud offset=+25
        span_b_now = float(span_b.iloc[-26])
        span_a_prev = float(span_a.iloc[-27])
        span_b_prev = float(span_b.iloc[-27])
        last_close = float(close.iloc[-1])
        values = [q_value, span_a_now, span_b_now, span_a_prev, span_b_prev, last_close]
        if not all(np.isfinite(v) for v in values):
            return empty.copy()

        cloud_low, cloud_high = min(span_a_now, span_b_now), max(span_a_now, span_b_now)
        if q_value < cloud_low:
            status = "Below Cloud"
        elif q_value > cloud_high:
            status = "Above Cloud"
        else:
            status = "Inside Cloud"
        cloud_color = "Green" if span_a_now > span_b_now else "Red"
        mid_now = (span_a_now + span_b_now) / 2
        mid_prev = (span_a_prev + span_b_prev) / 2
        cloud_delta_pct = (mid_now - mid_prev) / abs(mid_prev) * 100 if mid_prev else 0.0
        cloud_move = "Up" if cloud_delta_pct > 0.05 else "Down" if cloud_delta_pct < -0.05 else "Flat"
        gap = (cloud_low - q_value) if q_value < cloud_low else (q_value - cloud_high) if q_value > cloud_high else 0.0
        distance_pct = gap / abs(q_value) * 100 if q_value else np.nan

        # Events use the prior aligned bar, to distinguish first contact/entry from a static state.
        q_prev = float(baseline.iloc[-28]) if len(baseline) >= 78 and pd.notna(baseline.iloc[-28]) else np.nan
        lo_prev = min(float(span_a.iloc[-27]), float(span_b.iloc[-27]))
        hi_prev = max(float(span_a.iloc[-27]), float(span_b.iloc[-27]))
        if q_value < cloud_low:
            # Primary condition requested by the user: Q-Line outside and below the cloud.
            if np.isfinite(q_prev) and q_prev >= lo_prev:
                event = "OUTSIDE BELOW — Q-Line exited cloud"
            elif distance_pct <= 0.5:
                event = "OUTSIDE BELOW — near cloud"
            else:
                event = "OUTSIDE BELOW — Q-Line alert"
        elif q_value > cloud_high:
            # Track this as a separate position, not a bearish alert by itself.
            if np.isfinite(q_prev) and q_prev <= hi_prev:
                event = "OUTSIDE ABOVE — Q-Line exited cloud (separate status)"
            elif distance_pct <= 0.5:
                event = "OUTSIDE ABOVE — near cloud"
            else:
                event = "OUTSIDE ABOVE — separate status; not bearish by itself"
        else:
            if np.isfinite(q_prev) and (q_prev < lo_prev or q_prev > hi_prev):
                event = "Q-Line re-entered cloud — outside alert cleared"
            else:
                # User said the inside-cloud state is not important; keep it neutral.
                event = "Inside cloud — no outside alert"
        if cloud_color == "Red" and cloud_move == "Up":
            event += " | Red cloud rising"
        return {"status":status, "value":q_value, "cloud_low":cloud_low,
                "cloud_high":cloud_high, "cloud_color":cloud_color,
                "cloud_move":cloud_move, "distance_pct":distance_pct, "event":event}
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return empty.copy()


def calc_q_line(frame):
    """Backward-compatible (Q-Line position vs aligned cloud, Q-Line value)."""
    result = q_cloud_analysis(frame)
    return result["status"], result["value"]

def calc_q_status(frame):
    # Backward-compatible status-only helper.
    return calc_q_line(frame)[0]


def fmt_q(value):
    return f"${float(value):.2f}" if pd.notna(value) and np.isfinite(float(value)) else "N/A"


def extract_ticker_frame(batch, ticker):
    """Extract a single ticker from yfinance batch MultiIndex data."""
    if batch is None or batch.empty:
        return pd.DataFrame()
    if isinstance(batch.columns, pd.MultiIndex):
        for level in range(batch.columns.nlevels):
            if ticker in batch.columns.get_level_values(level):
                try:
                    return normalize_history(batch.xs(ticker, axis=1, level=level, drop_level=True))
                except Exception:
                    continue
    return normalize_history(batch)


def download_batch(symbols, period, interval):
    """Batch downloads in moderate chunks instead of one HTTP request per symbol."""
    output = {}
    for pos in range(0, len(symbols), 40):
        chunk = symbols[pos:pos + 40]
        try:
            raw = yf.download(chunk, period=period, interval=interval, group_by="ticker",
                              auto_adjust=False, progress=False, threads=True, timeout=25)
        except Exception:
            raw = pd.DataFrame()
        for ticker in chunk:
            output[ticker] = extract_ticker_frame(raw, ticker)
    return output


def resample_4h(frame):
    """Aggregate real hourly OHLCV bars into 4-hour bars."""
    if frame is None or frame.empty:
        return pd.DataFrame()
    try:
        out = frame.sort_index().resample("4h", origin="start_day", offset="30min", label="left", closed="left").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
        })
        return out.dropna(subset=["Open", "High", "Low", "Close"])
    except Exception:
        return pd.DataFrame()

def early_recovery_metrics(frame, hourly, benchmark=None):
    """Rank potential early bottoms using observable price/volume evidence only.

    This is a discovery/ranking score, not a BUY signal. Missing evidence earns
    no bonus; the existing Q-Line display and other app behavior remain separate.
    """
    result = {
        "EarlyRecoveryScore": 0, "FallingKnifeRisk": 50,
        "SellingPressure": "نامشخص", "Stabilization": "نامشخص",
        "HigherLow": "نامشخص", "BearishStructureBreak": "نامشخص",
        "RelativeStrength": "نامشخص", "ReboundFromLowPct": np.nan,
        "RecoveryStage": "شواهد ناکافی"
    }
    try:
        close = frame["Close"].astype(float).dropna()
        high = frame["High"].astype(float).reindex(close.index)
        low = frame["Low"].astype(float).reindex(close.index)
        volume = frame["Volume"].fillna(0).astype(float).reindex(close.index)
        if len(close) < 30 or close.iloc[-1] <= 0:
            return result
        price = float(close.iloc[-1])
        score = 0.0
        knife = 0.0

        # 1) Meaningful prior decline: discovery context, not a reason by itself to buy.
        peak60 = float(high.iloc[-60:].max())
        drop60 = max(0.0, (peak60-price)/peak60*100) if peak60 > 0 else 0.0
        score += min(20.0, drop60 * 0.65) if drop60 >= 8 else 0.0

        # 2) Selling pressure: are recent down-day volumes fading vs earlier down days?
        change = close.diff()
        down_mask = change < 0
        recent_down_vol = volume.iloc[-5:][down_mask.iloc[-5:]]
        prior_down_vol = volume.iloc[-25:-5][down_mask.iloc[-25:-5]]
        pressure_fading = False
        if len(recent_down_vol) >= 2 and len(prior_down_vol) >= 3 and float(prior_down_vol.mean()) > 0:
            ratio = float(recent_down_vol.mean()) / float(prior_down_vol.mean())
            pressure_fading = ratio < 0.85
            if pressure_fading:
                score += 18.0 if ratio < 0.65 else 12.0
                result["SellingPressure"] = f"فشار فروش ضعیف‌تر ({ratio:.2f}x)"
            else:
                result["SellingPressure"] = f"هنوز قوی ({ratio:.2f}x)"
        elif len(recent_down_vol) < 2:
            # Fewer recent red days is mildly constructive, but not proof of absorption.
            if int(down_mask.iloc[-5:].sum()) <= 2:
                score += 5.0
                result["SellingPressure"] = "روزهای نزولی کمتر"

        # Absorption clue: unusually active session that closes in the upper half of its range.
        last_range = max(float(high.iloc[-1]-low.iloc[-1]), price*0.001)
        close_location = (price-float(low.iloc[-1]))/last_range
        base_vol = float(volume.iloc[-21:-1].median()) if len(volume) >= 21 else 0.0
        if base_vol > 0 and float(volume.iloc[-1]) >= 1.25*base_vol and close_location >= 0.65:
            score += 8.0

        # 3) Stabilization and higher low: compare two completed 5-session windows.
        recent_low = float(low.iloc[-5:].min())
        prior_low = float(low.iloc[-10:-5].min())
        stabilizing = recent_low >= prior_low * 0.985
        if stabilizing:
            score += 10.0
            result["Stabilization"] = "تثبیت نسبی"
        else:
            result["Stabilization"] = "کف پایین‌تر"
            knife += 18.0
        higher_low = recent_low > prior_low * 1.005
        if higher_low:
            score += 12.0
            result["HigherLow"] = "بله"
        else:
            result["HigherLow"] = "خیر/تأییدنشده"

        # A break is only counted when the latest close clears a short-term prior swing high.
        prior_swing_high = float(high.iloc[-6:-1].max())
        daily_break = price > prior_swing_high
        hourly_break = False
        if hourly is not None and not hourly.empty and len(hourly) >= 25:
            hc = hourly["Close"].astype(float).dropna()
            hh = hourly["High"].astype(float).reindex(hc.index)
            hourly_break = float(hc.iloc[-1]) > float(hh.iloc[-13:-1].max())
        if daily_break or hourly_break:
            score += 10.0 if daily_break else 7.0
            result["BearishStructureBreak"] = "تأیید در Daily" if daily_break else "شکست کوتاه‌مدت در 1H"
        else:
            result["BearishStructureBreak"] = "هنوز تأیید نشده"
            # Do not call it a knife only because structure has not broken yet.

        # Relative strength: 5-session return vs SPY, with a second comparison to 20 sessions.
        rs5 = rs20 = None
        if benchmark is not None and not benchmark.empty:
            bc = benchmark["Close"].astype(float).dropna()
            joined = pd.concat([close.rename("stock"), bc.rename("benchmark")], axis=1).dropna()
            if len(joined) >= 21:
                sr5 = (joined["stock"].iloc[-1]/joined["stock"].iloc[-6]-1)*100
                br5 = (joined["benchmark"].iloc[-1]/joined["benchmark"].iloc[-6]-1)*100
                sr20 = (joined["stock"].iloc[-1]/joined["stock"].iloc[-21]-1)*100
                br20 = (joined["benchmark"].iloc[-1]/joined["benchmark"].iloc[-21]-1)*100
                rs5, rs20 = float(sr5-br5), float(sr20-br20)
        if rs5 is not None:
            if rs5 > 1.0 or (rs5 > -0.5 and rs5 > rs20):
                score += 10.0
                result["RelativeStrength"] = f"بهبود (5D نسبت به SPY: {rs5:+.1f}٪)"
            else:
                result["RelativeStrength"] = f"ضعیف (5D نسبت به SPY: {rs5:+.1f}٪)"
                if rs5 < -4:
                    knife += 10.0

        # Earlyness: favor price near its recent low; penalize entries after a large rebound.
        low10 = float(low.iloc[-10:].min())
        rebound = (price/low10-1)*100 if low10 > 0 else 0.0
        result["ReboundFromLowPct"] = round(rebound, 2)
        if rebound <= 3:
            score += 10.0
        elif rebound <= 6:
            score += 7.0
        elif rebound <= 10:
            score += 3.0
        else:
            score -= min(18.0, (rebound-10)*1.5)

        # Strong recent lower lows plus accelerating downside are a warning, not a buy veto.
        ret5 = (price/float(close.iloc[-6])-1)*100 if float(close.iloc[-6]) > 0 else 0.0
        ret_prev5 = (float(close.iloc[-6])/float(close.iloc[-11])-1)*100 if float(close.iloc[-11]) > 0 else 0.0
        if recent_low < prior_low*0.97:
            knife += 18.0
        if ret5 < -5 and ret5 < ret_prev5:
            knife += 15.0
        if not stabilizing and not pressure_fading:
            knife += 12.0

        result["EarlyRecoveryScore"] = int(round(max(0, min(100, score))))
        result["FallingKnifeRisk"] = int(round(max(0, min(100, knife))))
        if result["FallingKnifeRisk"] >= 45:
            result["RecoveryStage"] = "ریسک سقوط؛ نیازمند تثبیت"
        elif result["EarlyRecoveryScore"] >= 55 and (higher_low or daily_break or hourly_break):
            result["RecoveryStage"] = "بازیابی زودهنگام با شواهد ساختاری"
        elif stabilizing and (pressure_fading or higher_low):
            result["RecoveryStage"] = "کف احتمالی در حال شکل‌گیری"
        else:
            result["RecoveryStage"] = "فقط زیرنظر؛ تأیید ناکافی"
        return result
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError, OverflowError):
        return result

@st.cache_data(ttl=900, show_spinner=False)
def run_fast_market_scan():
    rows, diagnostic_rows = [], []
    daily_map = download_batch(list(dict.fromkeys(list(TICKERS) + ["SPY"])), "1y", "1d")
    hourly_map = download_batch(TICKERS, "60d", "1h")
    for ticker in TICKERS:
        frame = daily_map.get(ticker, pd.DataFrame())
        hourly = hourly_map.get(ticker, pd.DataFrame())
        if frame.empty or len(frame) < 52:
            diagnostic_rows.append({"Ticker":ticker,"Status":"FAILED","Source":"Yahoo batch download",
                                    "Details":f"Daily data unavailable/insufficient ({len(frame)} rows)"})
            continue
        try:
            close, high, low = frame["Close"].astype(float), frame["High"].astype(float), frame["Low"].astype(float)
            volume = frame["Volume"].fillna(0).astype(float)
            price, previous = float(close.iloc[-1]), float(close.iloc[-2])
            if not np.isfinite(price) or price <= 0:
                raise ValueError("Invalid latest close")
            change = (price-previous)/previous*100 if previous > 0 else 0.0
            max52 = float(high.max()); drop52 = (max52-price)/max52*100 if max52 > 0 else 0.0
            max20 = float(high.iloc[-20:].max()); drop20 = (max20-price)/max20*100 if max20 > 0 else 0.0
            prior_vol = volume.iloc[-21:-1] if len(volume) >= 21 else volume.iloc[:-1]
            avg_vol = float(prior_vol.mean()) if len(prior_vol) else 0.0
            vol_ratio = float(volume.iloc[-1])/avg_vol if avg_vol > 0 else 0.0
            delta = close.diff(); gains = delta.clip(lower=0).rolling(14).mean()
            losses = (-delta.clip(upper=0)).rolling(14).mean(); rs = gains / losses.replace(0, np.nan)
            rsi_line = 100 - (100/(1+rs)); rsi = float(rsi_line.iloc[-1]) if pd.notna(rsi_line.iloc[-1]) else 50.0
            sma50 = float(close.rolling(50).mean().iloc[-1])
            sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else sma50
            sma50_diff = (price-sma50)/sma50*100 if sma50 > 0 else 0.0
            sma200_diff = (price-sma200)/sma200*100 if sma200 > 0 else 0.0
            support = float(low.iloc[-60:].min()) if len(low) >= 60 else float(low.min())
            tr = pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
            atr = float(tr.rolling(14).mean().iloc[-1])
            if not np.isfinite(atr) or atr <= 0: atr = price*0.02
            h4 = resample_4h(hourly)
            qd_info = q_cloud_analysis(frame)
            q4_info = q_cloud_analysis(h4)
            q1_info = q_cloud_analysis(hourly)
            recovery = early_recovery_metrics(frame, hourly, daily_map.get("SPY", pd.DataFrame()))
            qd, qdv = qd_info["status"], qd_info["value"]
            q4, q4v = q4_info["status"], q4_info["value"]
            q1, q1v = q1_info["status"], q1_info["value"]
            meta = UNIVERSE_META.get(ticker, {})
            rows.append({"Ticker":ticker,"Company":meta.get("Company",ticker),"Industry":meta.get("Industry", "") or "N/A",
                "MarketCap":meta.get("MarketCap",np.nan),
                "Price":round(price,2),"Change":round(change,2),"Drop52W":round(drop52,2),"RSI":round(rsi,2),
                "NearSupport":"Valid" if price <= support*1.10 else "Normal",
                "Q_Daily":qd,"Q_Daily_Value":qdv,"Q_4H":q4,"Q_4H_Value":q4v,"Q_1H":q1,"Q_1H_Value":q1v,
                "Q_Daily_Event":qd_info["event"],"Q_4H_Event":q4_info["event"],"Q_1H_Event":q1_info["event"],
                "Q_Daily_Cloud":f"{qd_info['cloud_color']} {qd_info['cloud_move']}",
                "Q_4H_Cloud":f"{q4_info['cloud_color']} {q4_info['cloud_move']}",
                "Q_1H_Cloud":f"{q1_info['cloud_color']} {q1_info['cloud_move']}",
                "VolRatio":round(vol_ratio,2),"SMA50_Diff":round(sma50_diff,2),"SMA200_Diff":round(sma200_diff,2),
                "StopLoss":round(price-1.5*atr,2),"Volume":int(volume.iloc[-1]) if np.isfinite(volume.iloc[-1]) else 0,
                **recovery,
                "Score":round(float(recovery["EarlyRecoveryScore"])-0.30*float(recovery["FallingKnifeRisk"]),2)})
            diagnostic_rows.append({"Ticker":ticker,"Status":"OK" if not hourly.empty else "PARTIAL",
                "Source":"Yahoo Finance batch download",
                "Details":f"{len(frame)} daily bars; {len(hourly)} hourly bars; {len(h4)} derived 4H bars"})
        except Exception as exc:
            diagnostic_rows.append({"Ticker":ticker,"Status":"FAILED","Source":"Yahoo batch download",
                                    "Details":f"Calculation error: {type(exc).__name__}: {exc}"})
    return rows, diagnostic_rows

btn_col, _ = st.columns([1,4])
with btn_col:
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("در حال دریافت داده از Yahoo Finance..."):
    scan_data, diagnostics = run_fast_market_scan()

df_res = pd.DataFrame(scan_data)
if len(df_res):
    st.success(f"دریافت داده موفق برای {len(df_res)} از {len(TICKERS)} نماد. منبع Universe: {UNIVERSE_SOURCE}")
else:
    st.error("هیچ نمادی داده دریافت نکرد. بخش تشخیص اتصال را باز کن تا خطای واقعی مشخص شود.")
with st.expander("🔎 Yahoo connection diagnostics", expanded=df_res.empty):
    st.caption(f"زمان اسکن: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.dataframe(pd.DataFrame(diagnostics), use_container_width=True, hide_index=True)

if not df_res.empty:
    # Discovery ranking favors early recovery evidence and subtracts falling-knife risk.
    df_res = df_res.sort_values(["Score", "EarlyRecoveryScore"], ascending=[False, False]).head(10)
    if "Industry" not in df_res.columns:
        df_res["Industry"] = "N/A"
    for _idx, _row in df_res.iterrows():
        if not str(_row.get("Industry", "N/A")).strip() or str(_row.get("Industry", "N/A")).strip().upper() == "N/A":
            df_res.at[_idx, "Industry"] = lookup_industry(_row["Ticker"])
fallback = ["NVDA","AMD","INTC","TSLA","AAPL","MSFT"]
top_tickers = df_res["Ticker"].tolist() if not df_res.empty else fallback.copy()
while len(top_tickers) < 6:
    top_tickers.append(fallback[len(top_tickers) % len(fallback)])
top_tickers = top_tickers[:6]

def fmt_cap(value):
    if pd.isna(value): return "N/A"
    value = float(value)
    if value >= 1e12: return f"${value/1e12:.2f}T"
    if value >= 1e9: return f"${value/1e9:.2f}B"
    if value >= 1e6: return f"${value/1e6:.2f}M"
    return f"${value:,.0f}"

def fmt_volume(value):
    value = float(value)
    if value >= 1e9: return f"{value/1e9:.2f}B"
    if value >= 1e6: return f"{value/1e6:.2f}M"
    if value >= 1e3: return f"{value/1e3:.1f}K"
    return f"{value:,.0f}"

@st.cache_data(ttl=86400, show_spinner=False)
def lookup_industry(ticker):
    """Fetch industry label from Yahoo metadata; return N/A rather than inventing one."""
    try:
        info = yf.Ticker(str(ticker)).get_info()
        industry = info.get("industry") if isinstance(info, dict) else None
        return str(industry).strip() if industry else "N/A"
    except Exception:
        return "N/A"

st.caption(f"Universe: {len(TICKERS)} نماد | منبع: {UNIVERSE_SOURCE}")
st.caption("رتبه‌بندی فرصت کف: افت قبلی + تضعیف فشار فروش/جذب عرضه + تثبیت و Higher Low + شکست ساختار نزولی + قدرت نسبی بهتر؛ امتیاز Falling-Knife Risk از رتبه کم می‌کند. این امتیاز فقط برای کشف و رتبه‌بندی است و سیگنال BUY نیست.")
st.caption("Q-Line مطابق Pine Script شما محاسبه می‌شود: Base Line دورهٔ ۲۶ با offset=+26 و ابر با offset=+25. تمرکز هشدار روی Q-Line خارج از ابر و به‌ویژه زیر ابر است؛ داخل ابر هشدار مهمی ندارد. بالای ابر فقط وضعیت جداگانه است و به‌تنهایی سیگنال منفی نیست. بازگشت به ابر هشدار خروج را پاک می‌کند. 4H از کندل‌های 1H تجمیع می‌شود.")
st.subheader("📊 Top Alpha Stocks — Early Recovery Ranking")
rows_html = ""
if not df_res.empty:
    for rank, row in enumerate(df_res.reset_index(drop=True).to_dict("records"), start=1):
        chg = row["Change"]
        chg_color = "#f87171" if chg < 0 else "#4ade80"
        s50, s200 = row["SMA50_Diff"], row["SMA200_Diff"]
        cells = [
            f"<td style='color:#94a3b8'>{rank}</td>",
            f"<td><b style='color:#38bdf8'>{row['Ticker']}</b></td>",
            f"<td style='text-align:left;color:#f1f5f9'>{row['Company']}</td>",
            f"<td style='text-align:left;color:#c4b5fd'>{row.get('Industry', 'N/A')}</td>",
            f"<td style='color:#38bdf8'>{fmt_cap(row['MarketCap'])}</td>",
            f"<td style='color:#fff'>${row['Price']:.2f}</td>",
            f"<td style='color:{chg_color}'>{chg:+.2f}%</td>",
            f"<td style='color:#fbbf24'>-{row['Drop52W']:.2f}%</td>",
            f"<td style='color:#38bdf8'>{row['RSI']:.2f}</td>",
            f"<td style='color:#22c55e'>{row.get('EarlyRecoveryScore', 0)}</td>",
            f"<td style='color:{'#ef4444' if row.get('FallingKnifeRisk', 50) >= 45 else '#fbbf24'}'>{row.get('FallingKnifeRisk', 50)}</td>",
            f"<td>{row.get('RecoveryStage', 'N/A')}</td>",
            f"<td style='color:#4ade80'>{row['NearSupport']}</td>",
            f"<td style='color:#cbd5e1'>{fmt_volume(row['Volume'])}</td>",
            f"<td style='color:{'#38bdf8' if row['VolRatio'] >= 1.2 else '#cbd5e1'}'>{row['VolRatio']:.2f}x</td>",
            f"<td style='color:{'#f87171' if s50 < 0 else '#4ade80'}'>{s50:+.2f}%</td>",
            f"<td style='color:{'#f87171' if s200 < 0 else '#4ade80'}'>{s200:+.2f}%</td>",
            f"<td style='color:#f87171'>${row['StopLoss']:.2f}</td>",
        ]
        rows_html += "<tr>" + "".join(cells) + "</tr>"

table_html = """
<!DOCTYPE html><html><head><style>
body{margin:0;padding:0;background:#131722;font-family:Arial,sans-serif}
table{width:100%;border-collapse:collapse;background:#131722;color:#d1d4dc;table-layout:fixed}
th{background:#1e222d;color:#f8fafc;font-size:12px;font-weight:bold;padding:8px 2px;text-align:center;border-bottom:2px solid #2a2e39;white-space:nowrap}
td{padding:8px 2px;text-align:center;border-bottom:1px solid #2a2e39;font-size:14px;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
tr:hover{background:#1e222d}
</style></head><body><table><thead><tr>
<th style='width:2.5%'>No</th><th style='width:5.5%'>Ticker</th><th style='width:10%;text-align:left'>Company</th><th style='width:11%;text-align:left'>Industry</th>
<th style='width:6.5%'>Cap</th><th style='width:5.5%'>Price</th><th style='width:5.5%'>Chg %</th>
<th style='width:6.5%'>52W Drop</th><th style='width:4.5%'>RSI</th><th style='width:6%'>Early Score</th><th style='width:6%'>Knife Risk</th><th style='width:6%'>Recovery Stage</th><th style='width:6%'>Support</th>
<th style='width:6%'>Volume</th><th style='width:5%'>RVol</th><th style='width:6%'>SMA50</th>
<th style='width:6%'>SMA200</th><th style='width:6.5%'>StopLoss</th>
</tr></thead><tbody>
""" + rows_html + "</tbody></table></body></html>"
components.html(table_html, height=520, scrolling=True)

with st.expander("🚨 Q-Line / Cloud Alerts — جزئیات هشدار", expanded=True):
    if not df_res.empty:
        alert_cols = ["Ticker", "Price", "Q_Daily", "Q_Daily_Value", "Q_Daily_Cloud", "Q_Daily_Event",
                      "Q_4H", "Q_4H_Value", "Q_4H_Cloud", "Q_4H_Event",
                      "Q_1H", "Q_1H_Value", "Q_1H_Cloud", "Q_1H_Event"]
        alert_view = df_res[[c for c in alert_cols if c in df_res.columns]].copy()
        st.dataframe(alert_view, use_container_width=True, hide_index=True)
    else:
        st.info("برای هشدار Q-Line دادهٔ معتبر در دسترس نیست.")

st.markdown("---")
st.subheader("🖥️ 6-Chart Live TradingView Grid (Auto-Synced with Top Table)")
timeframe = st.radio("Global Timeframe:", ["5","60","240","D"], index=3, horizontal=True,
                     format_func=lambda x: {"5":"5m","60":"1H","240":"4H","D":"1D"}[x])

def render_chart(symbol, interval, height=750):
    symbol = "".join(ch for ch in str(symbol).upper().strip() if ch.isalnum() or ch in ".-_")
    if not symbol:
        st.warning("لطفاً نماد معتبر وارد کن.")
        return
    widget = f"""
    <html style="margin:0;padding:0;height:100%"><body style="margin:0;padding:0;height:100%;background:#131722">
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {{
        "autosize":true,"symbol":"{symbol}","interval":"{interval}",
        "timezone":"Etc/UTC","theme":"dark","style":"1","locale":"en",
        "allow_symbol_change":true,
        "studies":["IchimokuCloud@tv-basicstudies","RSI@tv-basicstudies","MACD@tv-basicstudies","Moving Average Weighted@tv-basicstudies"],
        "support_host":"https://www.tradingview.com"
      }}
      </script>
    </div></body></html>
    """
    components.html(widget, height=height)

for row_idx in range(2):
    chart_cols = st.columns(3)
    for col_idx, col in enumerate(chart_cols):
        idx = row_idx*3 + col_idx
        with col:
            symbol = st.text_input(f"Chart {idx+1} (Rank {idx+1})",
                                   value=top_tickers[idx], key=f"chart_symbol_{idx+1}")
            render_chart(symbol, timeframe, height=750)
