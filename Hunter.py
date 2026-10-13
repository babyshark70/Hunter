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
            EquityQuery("gte", ["intradaymarketcap", 25_000_000_000]),
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
            if not np.isfinite(cap) or not (25_000_000_000 <= cap <= 6_000_000_000_000):
                continue
            if symbol not in metadata:
                symbols.append(symbol)
                metadata[symbol] = {
                    "MarketCap": cap,
                    "Company": item.get("longName") or item.get("shortName") or symbol,
                }
        if len(symbols) >= 250:
            selected_symbols = symbols[:300]
            selected_metadata = {symbol: metadata[symbol] for symbol in selected_symbols}
            return selected_symbols, selected_metadata, "Yahoo Screener ($25B–$6T; market-cap verified)"
        screen_error = f"Screener returned only {len(symbols)} verified symbols"
    except Exception as exc:
        screen_error = f"{type(exc).__name__}: {exc}"
    # This fallback is intentionally marked as unverified: never claim its market caps are live-verified.
    symbols = list(dict.fromkeys(FALLBACK_TICKERS))[:300]
    metadata = {symbol: {"MarketCap": np.nan, "Company": symbol} for symbol in symbols}
    return symbols, metadata, f"Fallback list ({len(symbols)} symbols; $25B cap not verified): {screen_error}"

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

def calc_q_line(frame):
    """Return (status, value) for Q-Line, defined here as Ichimoku Kijun-26.

    The line is the midpoint of the highest high and lowest low over the last
    26 completed bars of the same timeframe. Status compares the latest close
    with that numeric line. Insufficient/malformed data returns N/A and NaN.
    """
    if frame is None or frame.empty or len(frame) < 26:
        return "N/A", np.nan
    try:
        high = pd.to_numeric(frame["High"], errors="coerce")
        low = pd.to_numeric(frame["Low"], errors="coerce")
        close = pd.to_numeric(frame["Close"], errors="coerce")
        q_line = (high.rolling(26, min_periods=26).max() +
                  low.rolling(26, min_periods=26).min()) / 2
        q_value = float(q_line.iloc[-1])
        last_close = float(close.iloc[-1])
        if not np.isfinite(q_value) or not np.isfinite(last_close):
            return "N/A", np.nan
        tolerance = max(abs(q_value) * 0.0005, 0.01)
        if last_close > q_value + tolerance:
            status = "Above"
        elif last_close < q_value - tolerance:
            status = "Below"
        else:
            status = "On Q"
        return status, q_value
    except (KeyError, TypeError, ValueError, IndexError):
        return "N/A", np.nan


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

@st.cache_data(ttl=900, show_spinner=False)
def run_fast_market_scan():
    rows, diagnostic_rows = [], []
    daily_map = download_batch(TICKERS, "1y", "1d")
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
            qd, qdv = calc_q_line(frame)
            q4, q4v = calc_q_line(h4)
            q1, q1v = calc_q_line(hourly)
            meta = UNIVERSE_META.get(ticker, {})
            rows.append({"Ticker":ticker,"Company":meta.get("Company",ticker),"Sector":"N/A",
                "MarketCap":meta.get("MarketCap",np.nan),
                "Price":round(price,2),"Change":round(change,2),"Drop52W":round(drop52,2),"RSI":round(rsi,2),
                "NearSupport":"Valid" if price <= support*1.10 else "Normal",
                "Q_Daily":qd,"Q_Daily_Value":qdv,"Q_4H":q4,"Q_4H_Value":q4v,"Q_1H":q1,"Q_1H_Value":q1v,
                "VolRatio":round(vol_ratio,2),"SMA50_Diff":round(sma50_diff,2),"SMA200_Diff":round(sma200_diff,2),
                "StopLoss":round(price-1.5*atr,2),"Volume":int(volume.iloc[-1]) if np.isfinite(volume.iloc[-1]) else 0,
                "Score":round(drop20+(50-rsi)+(vol_ratio*3),2)})
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
    df_res = df_res.sort_values("Score", ascending=False).head(10)
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

st.caption(f"Universe: {len(TICKERS)} نماد | منبع: {UNIVERSE_SOURCE}")
st.caption("Q-Line = Kijun-26 (میانه بیشترین High و کمترین Low در ۲۶ کندل همان تایم‌فریم). هر ستون هم مقدار خط و هم وضعیت Close نسبت به خط را نشان می‌دهد؛ 4H از کندل‌های 1H تجمیع می‌شود.")
st.subheader("📊 Top Alpha Stocks (Multi-TF Q-Line Status: Daily, 4H, 1H)")
rows_html = ""
if not df_res.empty:
    for rank, row in enumerate(df_res.reset_index(drop=True).to_dict("records"), start=1):
        chg = row["Change"]
        chg_color = "#f87171" if chg < 0 else "#4ade80"
        def q_color(value):
            return "#4ade80" if value == "Above" else "#f87171" if value == "Below" else "#fbbf24"
        s50, s200 = row["SMA50_Diff"], row["SMA200_Diff"]
        cells = [
            f"<td style='color:#94a3b8'>{rank}</td>",
            f"<td><b style='color:#38bdf8'>{row['Ticker']}</b></td>",
            f"<td style='text-align:left;color:#f1f5f9'>{row['Company']}</td>",
            f"<td style='color:#38bdf8'>{fmt_cap(row['MarketCap'])}</td>",
            f"<td style='color:#fff'>${row['Price']:.2f}</td>",
            f"<td style='color:{chg_color}'>{chg:+.2f}%</td>",
            f"<td style='color:#fbbf24'>-{row['Drop52W']:.2f}%</td>",
            f"<td style='color:#38bdf8'>{row['RSI']:.2f}</td>",
            f"<td style='color:#4ade80'>{row['NearSupport']}</td>",
            f"<td title='Q={fmt_q(row['Q_Daily_Value'])}' style='color:{q_color(row['Q_Daily'])}'>{fmt_q(row['Q_Daily_Value'])} · {row['Q_Daily']}</td>",
            f"<td title='Q={fmt_q(row['Q_4H_Value'])}' style='color:{q_color(row['Q_4H'])}'>{fmt_q(row['Q_4H_Value'])} · {row['Q_4H']}</td>",
            f"<td title='Q={fmt_q(row['Q_1H_Value'])}' style='color:{q_color(row['Q_1H'])}'>{fmt_q(row['Q_1H_Value'])} · {row['Q_1H']}</td>",
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
<th style='width:2.5%'>No</th><th style='width:5.5%'>Ticker</th><th style='width:11.5%;text-align:left'>Company</th>
<th style='width:6.5%'>Cap</th><th style='width:5.5%'>Price</th><th style='width:5.5%'>Chg %</th>
<th style='width:6.5%'>52W Drop</th><th style='width:4.5%'>RSI</th><th style='width:6%'>Support</th>
<th style='width:7.5%'>Q-Line D</th><th style='width:7.5%'>Q-Line 4H</th><th style='width:7.5%'>Q-Line 1H</th>
<th style='width:6%'>Volume</th><th style='width:5%'>RVol</th><th style='width:6%'>SMA50</th>
<th style='width:6%'>SMA200</th><th style='width:6.5%'>StopLoss</th>
</tr></thead><tbody>
""" + rows_html + "</tbody></table></body></html>"
components.html(table_html, height=520, scrolling=True)

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
