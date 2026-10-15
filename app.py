import streamlit as st
import plotly.graph_objects as go

from trading_strategy import (
    calculate_moving_averages,
    get_stock_data,
    identify_golden_cross,
    implement_strategy,
)


@st.cache_data
def load_dashboard_data():
    data = get_stock_data("MSFT")
    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions


def summarize_trades(positions):
    if positions.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "average_profit_pct": 0.0,
            "average_holding_days": 0.0,
            "target_reached": 0,
            "max_holding_period": 0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
        }

    total_trades = len(positions)
    winning_trades = len(positions[positions["ProfitPct"] > 0])
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades else 0

    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(float(win_rate), 2),
        "average_profit_pct": round(float(positions["ProfitPct"].mean()), 2),
        "average_holding_days": round(float(positions["HoldingDays"].mean()), 2),
        "target_reached": int((positions["SellReason"] == "Target reached").sum()),
        "max_holding_period": int((positions["SellReason"] == "Max holding period").sum()),
        "best_trade_pct": round(float(positions["ProfitPct"].max()), 2),
        "worst_trade_pct": round(float(positions["ProfitPct"].min()), 2),
    }


def build_price_chart(data, positions):
    chart_df = data.reset_index().rename(columns={"index": "Date"})
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["Date"],
            y=chart_df["Close"],
            mode="lines",
            name="Price",
            line={"color": "#0f172a", "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["Date"],
            y=chart_df["MA50"],
            mode="lines",
            name="MA50",
            line={"color": "#3b82f6", "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["Date"],
            y=chart_df["MA200"],
            mode="lines",
            name="MA200",
            line={"color": "#f97316", "width": 2},
        )
    )

    if not positions.empty:
        buy_points = positions[["BuyDate", "BuyPrice"]].rename(columns={"BuyDate": "Date", "BuyPrice": "Price"})
        sell_points = positions[["SellDate", "SellPrice"]].rename(columns={"SellDate": "Date", "SellPrice": "Price"})

        fig.add_trace(
            go.Scatter(
                x=buy_points["Date"],
                y=buy_points["Price"],
                mode="markers",
                name="Buy Points",
                marker={"size": 10, "color": "#22c55e", "line": {"color": "white", "width": 1}},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=sell_points["Date"],
                y=sell_points["Price"],
                mode="markers",
                name="Sell Points",
                marker={"size": 10, "color": "#ef4444", "line": {"color": "white", "width": 1}},
            )
        )

    fig.update_layout(
        title="MSFT Price and Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return fig


def main():
    st.set_page_config(page_title="Trading Strategy Dashboard", layout="wide")
    st.title("Trading Strategy Dashboard")

    data, positions = load_dashboard_data()
    stats = summarize_trades(positions)

    tabs = st.tabs(["Price Chart", "Trade Statistics", "Detailed Trades"])

    with tabs[0]:
        st.subheader("MSFT Price and Moving Averages")
        st.plotly_chart(build_price_chart(data, positions), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Trades", stats["total_trades"])
        col2.metric("Win Rate", f"{stats['win_rate']}%")
        col3.metric("Average Profit", f"{stats['average_profit_pct']}%")

    with tabs[1]:
        st.subheader("Overall Trade Statistics")

        stat_cols = st.columns(5)
        stat_cols[0].metric("Total Trades", stats["total_trades"])
        stat_cols[1].metric("Winning Trades", stats["winning_trades"])
        stat_cols[2].metric("Losing Trades", stats["losing_trades"])
        stat_cols[3].metric("Win Rate", f"{stats['win_rate']}%")
        stat_cols[4].metric("Average Profit", f"{stats['average_profit_pct']}%")

        stat_cols2 = st.columns(5)
        stat_cols2[0].metric("Average Holding Days", f"{stats['average_holding_days']}")
        stat_cols2[1].metric("Target Reached", stats["target_reached"])
        stat_cols2[2].metric("Max Holding Period", stats["max_holding_period"])
        stat_cols2[3].metric("Best Trade", f"{stats['best_trade_pct']}%")
        stat_cols2[4].metric("Worst Trade", f"{stats['worst_trade_pct']}%")

    with tabs[2]:
        st.subheader("Detailed Trade Records")
        if positions.empty:
            st.info("No trades were generated for the selected strategy.")
        else:
            display_df = positions[["BuyDate", "SellDate", "BuyPrice", "SellPrice", "HoldingDays", "ProfitPct", "SellReason"]].copy()
            display_df = display_df.rename(
                columns={
                    "BuyDate": "Buy Date",
                    "SellDate": "Sell Date",
                    "BuyPrice": "Buy Price",
                    "SellPrice": "Sell Price",
                    "HoldingDays": "Holding Days",
                    "ProfitPct": "Profit %",
                    "SellReason": "Sell Reason",
                }
            )
            display_df["Buy Price"] = display_df["Buy Price"].map(lambda x: f"${x:,.2f}")
            display_df["Sell Price"] = display_df["Sell Price"].map(lambda x: f"${x:,.2f}")
            display_df["Profit %"] = display_df["Profit %"].map(lambda x: f"{x:.2f}%")
            st.dataframe(display_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
