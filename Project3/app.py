from datetime import datetime
import streamlit as st

from main import CommodityValuationEngine

st.set_page_config(page_title="Commodity Valuation Engine", layout="wide")


@st.cache_resource
def load_engine():
    return CommodityValuationEngine()


engine = load_engine()

st.title("🌾 Commodity Price & Valuation System")

user_query = st.text_input("Enter Commodity Name:", value="onion")
fetch_btn = st.button("Fetch Live Price", type="primary")

if fetch_btn or user_query:
    result = engine.fetch_live_prices(user_query)

    st.write(f"**Data Source:** `{result['source']}`")

    if result["status"] == "fallback":
        st.warning(
            "⚠️ Live scrape did not return data — showing the historical "
            "model benchmark instead, not today's actual market price."
        )
        if result.get("scrape_error"):
            with st.expander("Show scrape error details"):
                st.code(result["scrape_error"])
    elif result["status"] == "success" and result.get("is_stale_price"):
        st.info(
            "ℹ️ No price was published for today — showing the most "
            f"recently available price, from **{result.get('date_used')}**."
        )
    elif result["status"] == "success":
        st.success("✅ Live price successfully scraped from AMIS (today's price).")

    if result.get("data"):
        for item in result["data"]:
            var_name = item["variation_name"]
            unit_price = item["price_per_unit"]
            bulk_price = item["price_per_100kg"]

            st.metric(
                label=f"📌 {var_name} (per kg)",
                value=f"Rs. {unit_price:.2f}",
                delta=f"100 kg Bulk: Rs. {bulk_price:,.2f}",
            )

            eval_res = engine.evaluate_variation(user_query, unit_price)
            st.info(
                f"Market Valuation Verdict: **{eval_res['verdict']}** (Real Price: Rs. {eval_res['real_price']}/kg)"
            )

            if eval_res.get("categories"):
                st.subheader("📊 Historical Valuation Breakdown & Seasonality")
                cols = st.columns(3)

                for idx, (cat_name, cat_info) in enumerate(
                    eval_res["categories"].items()
                ):
                    with cols[idx]:
                        is_current = cat_name == eval_res["verdict"]
                        badge = " 👈 (Current)" if is_current else ""

                        st.markdown(f"### {cat_name}{badge}")
                        st.markdown(
                            f"**Price Range:** Rs. {cat_info['min_nominal']} – Rs. {cat_info['max_nominal']} /kg"
                        )

                        months = cat_info["dominant_months"]
                        if months:
                            st.write(
                                "**Dominant Months:**", ", ".join(months)
                            )
                        else:
                            st.caption("No dominant seasonal months detected.")