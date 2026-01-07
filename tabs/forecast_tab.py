import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
from utils.forecast_tracker import get_forecast_history, delete_forecasts
from utils.security import sanitize_ticker

def show_forecast_tracker_tab():

    """Show the Forecast Tracker Dashboard (Tab 5)"""

    st.header("🎯 Forecast Tracker")

    st.markdown("Track the performance of your saved forecasts against live market prices.")


    # 1. Load History

    history = get_forecast_history()


    if not history:

        st.info("ℹ️ No saved forecasts yet. Use the **'Save Forecast'** button in the Analysis tabs to track predictions.")

        return

        

    st.caption(f"Found {len(history)} saved forecasts.")


    # 2. Get Unique Tickers for Bulk Fetch

    tickers = list(set([h['ticker'] for h in history]))


    # 3. Fetch Live Prices (with progress bar)

    live_prices = {}

    progress_bar = st.progress(0)


    for i, ticker in enumerate(tickers):

        try:

            # Use basic yfinance for speed, sanitizing first
            # Remove $ manually as sanitize_ticker is strict
            candidate = ticker.replace("$", "").strip().upper()
            if not candidate.startswith("^") and not candidate.endswith(('.NS', '.BO')):
                 candidate += ".NS"
            
            sanitized_ticker = sanitize_ticker(candidate)
            if not sanitized_ticker: continue
            
            t = yf.Ticker(sanitized_ticker)

            # Use 'regularMarketPrice' or fast history

            todays_data = t.history(period="1d")

            if not todays_data.empty:

                live_prices[ticker] = todays_data['Close'].iloc[-1]

            else:

                live_prices[ticker] = None

        except Exception as e:

            time.sleep(0.1)

            live_prices[ticker] = None

        

        progress_bar.progress((i + 1) / len(tickers))

        

    progress_bar.empty()

    

    # 4. Build Table Data

    table_data = []

    for h in history:

        ticker = h['ticker']

        saved_price = h['current_price']

        curr_price = live_prices.get(ticker, 0)

        

        # Calculate performance

        if curr_price:

            change_pct = ((curr_price - saved_price) / saved_price) * 100

        else:

            change_pct = 0.0

            curr_price = 0.0 # N/A

            

        saved_date = datetime.fromisoformat(h['timestamp']).strftime("%Y-%m-%d")

        

        table_data.append({

            "Delete": False,  # Selection col

            "Date Saved": saved_date,

            "Ticker": ticker,

            "Entry Price": saved_price,

            "Current Price": curr_price,

            "Change %": change_pct,

            "Target (2026)": h['target_price'],

            "Strategy": h['strategy'],

            "Confidence": h['confidence'],

            "ID": h['timestamp'] # Hidden ID

        })

        

    # 5. Display Interactive Data Editor

    df = pd.DataFrame(table_data)

    

    # Configure columns

    # We want 'Delete' to be editable, others read-only ideally

    edited_df = st.data_editor(

        df,

        column_config={

            "Delete": st.column_config.CheckboxColumn(

                "Delete?",

                help="Select to delete",

                default=False,

            ),

            "Entry Price": st.column_config.NumberColumn(format="₹%.2f"),

            "Current Price": st.column_config.NumberColumn(format="₹%.2f"),

            "Change %": st.column_config.NumberColumn(format="%.2f%%"),

            "Target (2026)": st.column_config.NumberColumn(format="₹%.2f"),

            "ID": None # Hide ID column

        },

        disabled=["Date Saved", "Ticker", "Entry Price", "Current Price", "Change %", "Target (2026)", "Strategy", "Confidence"],

        hide_index=True,

        width='stretch',

        key="forecast_editor"

    )

    

    # 6. Deletion Logic

    if not edited_df.empty:

        to_delete = edited_df[edited_df["Delete"] == True]

        

        if not to_delete.empty:

            st.warning(f"⚠️ You have selected {len(to_delete)} forecasts for deletion.")

            if st.button("🗑️ Delete Selected Forecasts", type="primary"):

                # Get IDs (timestamps)

                ids_to_del = to_delete["ID"].tolist()

                if delete_forecasts(ids_to_del):

                    st.success("✅ Forecasts deleted!")

                    st.rerun()

                else:

                    st.error("❌ Error deleting forecasts.")



    # 7. Summary Metrics

    st.markdown("---")



    avg_perf = df["Change %"].mean()

    col1, col2, col3 = st.columns([1, 1, 1])

    col1.metric("Avg Portfolio Performance", f"{avg_perf:+.2f}%")

    col2.metric("Active Forecasts", len(df))

    

    with col3:

        # CSV Export

        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(

            "📥 Download CSV",

            csv,

            "forecast_history.csv",

            "text/csv",

            key='download-forecasts'

        )
