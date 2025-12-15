# ghadiyalu_gui.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from pytz import timezone

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Ghadiyalu Calculator",
    layout="centered"
)

# -------------------------------------------------
# Custom CSS
# -------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }

    .section-header {
        background-color: #4a90e2;
        color: white;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 20px;
        margin-top: 20px;
    }

    .sun-box {
        background: linear-gradient(90deg, #f6d365, #fda085);
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 10px;
        font-size: 18px;
    }

    .date-box {
        background-color: #1e3a8a;
        color: white;
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-size: 16px;
        margin-bottom: 10px;
    }

    [data-testid="stSidebar"] {
        background-color: #e3eefc;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Title
# -------------------------------------------------
st.markdown("<h1 style='text-align:center;'>⏱️ Ghadiyalu Calculator</h1>", unsafe_allow_html=True)

# -------------------------------------------------
# Sidebar Inputs
# -------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    calc_date = st.date_input(
        "Select Date",
        value=date.today(),
        min_value=date(1981, 1, 1),
        max_value=date(2082, 12, 31)
    )

    sunrise_str = st.text_input("Sunrise Time (HH:MM)", "06:00")
    sunset_str = st.text_input("Sunset Time (HH:MM)", "18:00")

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def parse_hhmm(t):
    return datetime.strptime(t, "%H:%M").time()

def seconds_per_ghadi(total_minutes):
    return int((total_minutes * 60) / 30)

def build_ghadi(start_dt, sec, batch):
    rows = []
    cur = start_dt
    for i in range(1, 31):
        nxt = cur + timedelta(seconds=sec)
        rows.append({
            "Date": cur.strftime("%d/%m/%Y"),
            "Week": cur.strftime("%A"),
            "Batch": batch,
            "Ghadi No": i,
            "Start Time": cur.strftime("%H:%M:%S"),
            "End Time": nxt.strftime("%H:%M:%S"),
        })
        cur = nxt
    return rows

def highlight_current(df, now):
    def row_style(row):
        start = datetime.combine(
            now.date(),
            datetime.strptime(row["Start Time"], "%H:%M:%S").time()
        )
        end = datetime.combine(
            now.date(),
            datetime.strptime(row["End Time"], "%H:%M:%S").time()
        )

        if end < start:
            end += timedelta(days=1)

        ist = timezone("Asia/Kolkata")
        start = ist.localize(start)
        end = ist.localize(end)

        if start <= now <= end:
            return ["background-color:#14532d;color:white;font-weight:bold"] * len(row)
        return [""] * len(row)

    return df.style.apply(row_style, axis=1)

# -------------------------------------------------
# Main Button
# -------------------------------------------------
if st.button("🔍 Calculate Ghadiyalu"):

    try:
        ist = timezone("Asia/Kolkata")
        now = datetime.now(ist)

        sunrise_dt = ist.localize(datetime.combine(calc_date, parse_hhmm(sunrise_str)))
        sunset_dt = ist.localize(datetime.combine(calc_date, parse_hhmm(sunset_str)))

        if sunset_dt <= sunrise_dt:
            sunset_dt += timedelta(days=1)

        next_sunrise = sunrise_dt + timedelta(days=1)

        # Date & Week Header
        st.markdown(
            f"<div class='date-box'>📅 {calc_date.strftime('%d/%m/%Y')} | 🗓 {calc_date.strftime('%A')}</div>",
            unsafe_allow_html=True
        )

        # Sunrise / Sunset
        st.markdown(
            f"<div class='sun-box'>🌅 Sunrise: {sunrise_str} &nbsp;&nbsp; | &nbsp;&nbsp; 🌇 Sunset: {sunset_str}</div>",
            unsafe_allow_html=True
        )

        # Morning
        day_minutes = (sunset_dt - sunrise_dt).total_seconds() / 60
        morning_df = pd.DataFrame(
            build_ghadi(sunrise_dt, seconds_per_ghadi(day_minutes), "Morning Ghadiyas")
        )

        # Evening
        night_minutes = (next_sunrise - sunset_dt).total_seconds() / 60
        evening_df = pd.DataFrame(
            build_ghadi(sunset_dt, seconds_per_ghadi(night_minutes), "Evening Ghadiyas")
        )

        # Display
        st.markdown("<div class='section-header'>🌅 Morning Ghadiyas</div>", unsafe_allow_html=True)
        st.dataframe(highlight_current(morning_df, now), use_container_width=True)

        st.markdown("<div class='section-header'>🌙 Evening Ghadiyas</div>", unsafe_allow_html=True)
        st.dataframe(highlight_current(evening_df, now), use_container_width=True)

        # -------------------------------------------------
        # ✅ CSV DOWNLOAD (ANDROID SAFE)
        # -------------------------------------------------
        combined_df = pd.concat([morning_df, evening_df], ignore_index=True)
        csv_data = combined_df.to_csv(index=False)

        st.download_button(
            label="⬇ Download CSV",
            data=csv_data,
            file_name="ghadiyalu.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
