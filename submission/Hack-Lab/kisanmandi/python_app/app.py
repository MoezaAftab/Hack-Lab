import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    
    page_title="KisanMandi",
    page_icon="🌾",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# ---------------- API HELPERS ----------------
@st.cache_data(ttl=30)
def get_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return []



def post_data(endpoint, payload):
    try:
        response = requests.post(
            f"{API_URL}/{endpoint}",
            json=payload,
            timeout=5
        )

        if not response.ok:
            return False, (
                f"API Error {response.status_code}: "
                f"{response.text}"
            )

        get_data.clear()
        return True, "Saved successfully!"

    except requests.RequestException as error:
        return False, f"Connection error: {error}"


def delete_data(endpoint, record_id):
    try:
        response = requests.delete(
            f"{API_URL}/{endpoint}/{record_id}",
            timeout=5
        )
        response.raise_for_status()
        get_data.clear()
        return True, "Deleted successfully!"
    except requests.RequestException as error:
        return False, f"Could not delete: {error}"


# ---------------- LOAD DATA ----------------
st.title("🌾 KisanMandi")
st.caption("Crop prices, market comparison and direct produce marketplace for Sindh")

crops = get_data("crops")
markets = get_data("markets")
prices = get_data("prices")
listings = get_data("listings")
alerts = get_data("alerts")
users = get_data("users")

if not crops or not markets:
    st.error(
        "The app cannot load crop or market data. "
        "Keep the FastAPI server running at http://127.0.0.1:8000."
    )
    st.info("Check the API at http://127.0.0.1:8000/docs and refresh this page.")
    st.stop()

crop_df = pd.DataFrame(crops)
market_df = pd.DataFrame(markets)

crop_names = dict(zip(crop_df["id"], crop_df["name"]))
market_names = dict(
    zip(
        market_df["id"],
        market_df.get("name", market_df.get("district", market_df["id"]))
    )
)

if prices:
    price_df = pd.DataFrame(prices)
    price_df["crop_name"] = price_df["crop_id"].map(crop_names).fillna("Unknown crop")
    price_df["market_name"] = price_df["market_id"].map(market_names).fillna("Unknown market")
    price_df["date"] = pd.to_datetime(price_df["date"], errors="coerce")
    price_df["price"] = pd.to_numeric(price_df["price"], errors="coerce")
    price_df = price_df.dropna(subset=["date", "price"])
else:
    price_df = pd.DataFrame()

if listings:
    listing_df = pd.DataFrame(listings)
    listing_df["crop_name"] = listing_df["crop_id"].map(crop_names).fillna("Unknown crop")
else:
    listing_df = pd.DataFrame()

# ---------------- SIDEBAR ----------------
st.sidebar.header("👤 Your Profile")
user_name = st.sidebar.text_input("Your name", value="KisanMandi User")
user_role = st.sidebar.selectbox("I am a", ["Farmer", "Buyer"])
district = st.sidebar.selectbox(
    "Your district",
    ["Hyderabad", "Sukkur", "Mirpur Khas", "Nawabshah", "Other"]
)
st.sidebar.caption("Demo profile — no login required.")

if st.sidebar.button("🔄 Refresh data", use_container_width=True):
    get_data.clear()
    st.rerun()

# ---------------- DASHBOARD METRICS ----------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("🌱 Crops", len(crops))
col2.metric("📍 Markets", len(markets))
col3.metric("📊 Price records", len(price_df))
col4.metric(
    "🛒 Active listings",
    int((listing_df["status"] == "Active").sum())
    if not listing_df.empty and "status" in listing_df.columns
    else 0
)

st.divider()

# ---------------- NAVIGATION ----------------
tab_prices, tab_trends, tab_market, tab_alerts, tab_profit = st.tabs(
    ["📈 Crop Prices", "📊 Price Trends", "🛒 Marketplace", "🔔 Price Alerts", "🧮 Profit Calculator"]
)

# ================= CROP PRICES =================
with tab_prices:
    st.subheader("Today's Crop Prices")
    st.write("Compare crop prices across available markets.")

    if price_df.empty:
        st.warning("No price records are available.")
    else:
        filter1, filter2, filter3 = st.columns(3)

        crop_options = ["All crops"] + sorted(price_df["crop_name"].unique().tolist())
        selected_crop = filter1.selectbox("Select crop", crop_options)

        market_options = ["All markets"] + sorted(price_df["market_name"].unique().tolist())
        selected_market = filter2.selectbox("Select market", market_options)

        search_text = filter3.text_input("Search crop")

        filtered = price_df.copy()

        latest_date = filtered["date"].max()
        today_prices = filtered[filtered["date"] == latest_date].copy()

        if selected_crop != "All crops":
            today_prices = today_prices[today_prices["crop_name"] == selected_crop]

        if selected_market != "All markets":
            today_prices = today_prices[today_prices["market_name"] == selected_market]

        if search_text:
            today_prices = today_prices[
                today_prices["crop_name"].str.contains(search_text, case=False, na=False)
            ]

        if today_prices.empty:
            st.info("No prices match your filters.")
        else:
            st.caption(f"Showing latest available prices: {latest_date.strftime('%d %b %Y')}")

            display = today_prices[
                ["crop_name", "market_name", "price", "date"]
            ].rename(
                columns={
                    "crop_name": "Crop",
                    "market_name": "Market",
                    "price": "Price (PKR)",
                    "date": "Date"
                }
            ).sort_values("Price (PKR)", ascending=False)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

            best = today_prices.loc[today_prices["price"].idxmax()]
            st.success(
                f"Highest listed price: {best['crop_name']} at "
                f"{best['market_name']} — PKR {best['price']:,.0f}"
            )

            chart = px.bar(
                today_prices,
                x="crop_name",
                y="price",
                color="market_name",
                barmode="group",
                title="Latest crop prices by market",
                labels={
                    "crop_name": "Crop",
                    "price": "Price (PKR)",
                    "market_name": "Market"
                }
            )
            st.plotly_chart(chart, use_container_width=True)

# ================= PRICE TRENDS =================
with tab_trends:
    st.subheader("14-Day Price Trends")

    if price_df.empty:
        st.warning("No historical price data is available.")
    else:
        trend_crop = st.selectbox(
            "Choose crop for trend",
            sorted(price_df["crop_name"].unique()),
            key="trend_crop"
        )

        trend_data = price_df[price_df["crop_name"] == trend_crop].copy()

        if not trend_data.empty:
            trend = trend_data.groupby(
                ["date", "market_name"], as_index=False
            )["price"].mean()

            line_chart = px.line(
                trend,
                x="date",
                y="price",
                color="market_name",
                markers=True,
                title=f"{trend_crop}: price history by market",
                labels={
                    "date": "Date",
                    "price": "Price (PKR)",
                    "market_name": "Market"
                }
            )
            st.plotly_chart(line_chart, use_container_width=True)

            a, b, c = st.columns(3)
            a.metric("Minimum price", f"PKR {trend_data['price'].min():,.0f}")
            b.metric("Maximum price", f"PKR {trend_data['price'].max():,.0f}")
            c.metric("Average price", f"PKR {trend_data['price'].mean():,.0f}")

            st.subheader("Market comparison")
            comparison = trend_data.groupby("market_name", as_index=False)["price"].mean()
            comparison = comparison.sort_values("price", ascending=False)
            st.dataframe(
                comparison.rename(
                    columns={"market_name": "Market", "price": "Average price (PKR)"}
                ),
                use_container_width=True,
                hide_index=True
            )

# ================= MARKETPLACE =================
with tab_market:
    st.subheader("🛒 Produce Marketplace")
    st.write("Explore produce offered by farmers.")

    if listing_df.empty:
        st.info("No produce listings found.")
    else:
        active = listing_df.copy()
        if "status" in active.columns:
            active = active[active["status"] == "Active"]

        m1, m2 = st.columns(2)
        listing_crops = ["All crops"] + sorted(active["crop_name"].unique().tolist())
        chosen_listing_crop = m1.selectbox("Filter by crop", listing_crops)

        district_options = ["All districts"]
        if "district" in active.columns:
            district_options += sorted(active["district"].dropna().unique().tolist())

        chosen_district = m2.selectbox("Filter by district", district_options)

        if chosen_listing_crop != "All crops":
            active = active[active["crop_name"] == chosen_listing_crop]

        if chosen_district != "All districts" and "district" in active.columns:
            active = active[active["district"] == chosen_district]

        if active.empty:
            st.info("No listings match those filters.")
        else:
            for _, item in active.iterrows():
                with st.container(border=True):
                    left, right = st.columns([3, 1])

                    left.subheader(f"🌱 {item['crop_name']}")
                    left.write(f"📍 District: {item.get('district', 'Not provided')}")
                    left.write(f"📦 Quantity: {item.get('quantity', 'N/A')}")
                    left.write(f"⭐ Grade: {item.get('grade', 'Not specified')}")
                    left.write(f"📅 Available from: {item.get('available_from', 'N/A')}")

                    right.metric(
                        "Asking price",
                        f"PKR {float(item.get('asking_price', 0)):,.0f}"
                    )
                    right.caption(f"Listing ID: {item['id']}")

            st.caption("Contact details and direct calling can be added when seller phone numbers are connected.")

# ================= PRICE ALERTS =================
with tab_alerts:
    st.subheader("🔔 Create a Price Alert")
    st.write("Set a target price to monitor a crop.")

    with st.form("alert_form"):
        alert_crop_name = st.selectbox("Crop", sorted(crop_names.values()))
        alert_market_name = st.selectbox("Market", sorted(market_names.values()))
        direction = st.radio(
            "Alert me when price is",
            ["Above target", "Below target"],
            horizontal=True
        )
        target_price = st.number_input(
            "Target price (PKR)",
            min_value=1.0,
            value=3000.0,
            step=100.0
        )
        create_alert = st.form_submit_button("Create alert")

    if create_alert:
        crop_id = next(k for k, v in crop_names.items() if v == alert_crop_name)
        market_id = next(k for k, v in market_names.items() if v == alert_market_name)

       
payload = {
    "user_id": 1,
    "crop_id": crop_id,
    "market_id": market_id,
    "target_price": target_price,
    "condition": direction,
    "is_active": True
}

success, message = post_data("alerts", payload)

if success:
    st.success(message)
    st.rerun()
else:
    st.error(message)

st.subheader("Saved alerts")
current_alerts = get_data("alerts")


if not current_alerts:
        st.info("No alerts saved yet.")
else:
     for alert in current_alerts:
            with st.container(border=True):
                crop_label = crop_names.get(
                    alert.get("crop_id"), "Unknown crop"
                )
                market_label = market_names.get(
                    alert.get("market_id"), "Unknown market"
                )

                st.write(
                    f"**{crop_label}** at **{market_label}** — "
                    f"target PKR {alert.get('target_price', 'N/A')} "
                    f"({alert.get('condition', 'N/A')})"
                )

                st.caption(f"Alert ID: {alert.get('id')}")


# ================= PROFIT CALCULATOR =================
with tab_profit:
    st.subheader("🧮 Farmer Profit Calculator")
    st.write("Estimate potential revenue and profit before selling.")

    p1, p2 = st.columns(2)
    quantity = p1.number_input(
        "Quantity (kg)",
        min_value=1.0,
        value=100.0,
        step=10.0
    )
    selling_price = p2.number_input(
        "Selling price per kg (PKR)",
        min_value=0.0,
        value=3000.0,
        step=100.0
    )

    p3, p4 = st.columns(2)
    total_cost = p3.number_input(
        "Total production and transport cost (PKR)",
        min_value=0.0,
        value=100000.0,
        step=5000.0
    )
    price_change = p4.slider(
        "Possible price change (%)",
        min_value=-20,
        max_value=20,
        value=0,
        step=5
    )

    adjusted_price = selling_price * (1 + price_change / 100)
    revenue = quantity * adjusted_price
    profit = revenue - total_cost

    r1, r2, r3 = st.columns(3)
    r1.metric("Estimated revenue", f"PKR {revenue:,.0f}")
    r2.metric("Estimated profit/loss", f"PKR {profit:,.0f}")
    r3.metric("Price after change", f"PKR {adjusted_price:,.0f} per kg")

    if profit >= 0:
        st.success("Your estimated revenue covers the entered costs.")
    else:
        st.warning("Your estimated costs are higher than the revenue.")

# ---------------- FOOTER ----------------
st.divider()
st.caption(
    "KisanMandi Hackathon Demo | Sample data for demonstration only. "
    "Prices are not verified live market quotations."
)