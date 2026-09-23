import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Clean, professional BI dark-compatible theme tokens
PLOTLY_TEMPLATE = "plotly_white"
COLOR_LINE = "#2563eb"
COLOR_BAR_SCALE = "Blues"
COLOR_TEAL_SCALE = "Teal"

# Hoverlabel configured with dark background, crisp white font, and subtle border
# to ensure readability across dark mode and light mode dashboards
_LAYOUT_DEFAULTS = dict(
    margin=dict(l=15, r=15, t=35, b=15),
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12),
    hoverlabel=dict(
        bgcolor="#1e293b",
        font_color="#f8fafc",
        font_family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        font_size=12,
        bordercolor="#334155"
    ),
    autosize=True
)


def _x_col(df: pd.DataFrame, *candidates: str) -> str:
    """Return the first candidate column that exists in the dataframe."""
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"None of {candidates} found in dataframe columns: {list(df.columns)}")


def plot_revenue_trend(monthly_df: pd.DataFrame, title: str = "Monthly Revenue (£)") -> go.Figure:
    """Line chart for monthly revenue. Accepts Date, InvoiceDate, or year_month as x-axis."""
    x = _x_col(monthly_df, "Date", "InvoiceDate", "year_month")
    y = _x_col(monthly_df, "Revenue", "monthly_revenue")
    label_map = {y: "Revenue (£)", x: "Month"}
    fig = px.line(
        monthly_df, x=x, y=y,
        markers=True,
        labels=label_map,
        title=title,
    )
    fig.update_traces(
        line_color=COLOR_LINE,
        line_width=2.5,
        marker=dict(size=6, color=COLOR_LINE),
        hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.2f}<extra></extra>"
    )
    fig.update_layout(template=PLOTLY_TEMPLATE, hovermode="x unified", **_LAYOUT_DEFAULTS)
    return fig


def plot_country_revenue(country_df: pd.DataFrame, title: str = "Revenue by Country (£)") -> go.Figure:
    """Horizontal bar chart for top-10 countries by revenue."""
    top_10 = country_df.sort_values("total_revenue", ascending=False).head(10).copy()
    x = _x_col(top_10, "total_revenue", "total_line_amount")
    y = _x_col(top_10, "country", "Country")
    fig = px.bar(
        top_10, x=x, y=y,
        orientation='h',
        color=x,
        color_continuous_scale=COLOR_BAR_SCALE,
        title=title,
        text_auto='.2s',
        labels={x: "Revenue (£)", y: "Country"},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Revenue: £%{x:,.2f}<extra></extra>"
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
        **_LAYOUT_DEFAULTS,
    )
    return fig


def plot_rfm_segments(rfm_summary: pd.DataFrame, title: str = "Customer Segments (RFM)") -> go.Figure:
    """Treemap of customer RFM segments by count and revenue."""
    fig = px.treemap(
        rfm_summary,
        path=["Segment"],
        values="CustomerCount",
        color="TotalRevenue",
        color_continuous_scale="Blues",
        title=title,
        hover_data=["AvgRevenuePerCustomer", "RevenueSharePct"],
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<br>Revenue: £%{color:,.2f}<extra></extra>"
    )
    fig.update_layout(template=PLOTLY_TEMPLATE, **_LAYOUT_DEFAULTS)
    return fig


def plot_top_products(prod_df: pd.DataFrame, title: str = "Top Products by Revenue (£)") -> go.Figure:
    """Horizontal bar chart for top 15 products by revenue."""
    top15 = prod_df.head(15).copy()
    x = _x_col(top15, "total_revenue", "TotalLineAmount")
    y = _x_col(top15, "description", "Description")
    fig = px.bar(
        top15, x=x, y=y,
        orientation='h',
        color=x,
        color_continuous_scale=COLOR_TEAL_SCALE,
        title=title,
        text_auto='.2s',
        labels={x: "Revenue (£)", y: "Product"},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Revenue: £%{x:,.2f}<extra></extra>"
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
        **_LAYOUT_DEFAULTS,
    )
    return fig


def plot_forecast_chart(forecast_data: dict, title: str = "Revenue Forecast with Confidence Intervals") -> go.Figure:
    """Combined historical + forecast line chart with confidence bands."""
    hist = forecast_data["historical_monthly"]
    fut = forecast_data["future_forecast"]

    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=hist["Date"], y=hist["Revenue"],
        mode="lines+markers", name="Historical Revenue",
        line=dict(color="#334155", width=2.5),
        marker=dict(size=5),
        hovertemplate="<b>%{x|%Y-%m}</b><br>Historical: £%{y:,.2f}<extra></extra>"
    ))

    # 95% CI band
    fig.add_trace(go.Scatter(
        x=pd.concat([fut["Date"], fut["Date"][::-1]]),
        y=pd.concat([fut["Upper95"], fut["Lower95"][::-1]]),
        fill="toself",
        fillcolor="rgba(59, 130, 246, 0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        name="95% Confidence Interval",
    ))

    # 80% CI band
    fig.add_trace(go.Scatter(
        x=pd.concat([fut["Date"], fut["Date"][::-1]]),
        y=pd.concat([fut["Upper80"], fut["Lower80"][::-1]]),
        fill="toself",
        fillcolor="rgba(59, 130, 246, 0.22)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        name="80% Confidence Interval",
    ))

    # Forecast line
    model_name = forecast_data.get("best_model_name", "Model")
    fig.add_trace(go.Scatter(
        x=fut["Date"], y=fut["ForecastRevenue"],
        mode="lines+markers", name=f"Forecast ({model_name})",
        line=dict(color=COLOR_LINE, width=2.5, dash="dash"),
        marker=dict(size=5),
        hovertemplate="<b>%{x|%Y-%m}</b><br>Forecast: £%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=title,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **_LAYOUT_DEFAULTS,
    )
    return fig


def plot_churn_risk(churn_df: pd.DataFrame, title: str = "Churn Risk Score Distribution") -> go.Figure:
    """Histogram of predicted churn risk scores by observed inactivity status."""
    fig = px.histogram(
        churn_df,
        x="ChurnRiskScore",
        nbins=20,
        color="IsChurned",
        color_discrete_map={0: "#10b981", 1: "#ef4444"},
        title=title,
        labels={
            "ChurnRiskScore": "Predicted Churn Risk (%)",
            "IsChurned": "Observed Inactive",
        },
        barmode="overlay",
        opacity=0.75,
    )
    fig.update_traces(
        hovertemplate="Risk Range: %{x}%<br>Count: %{y}<extra></extra>"
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **_LAYOUT_DEFAULTS
    )
    return fig


def plot_macro_trend(macro_df: pd.DataFrame, title: str = "UK Macro-Economic Indicators") -> go.Figure:
    """Grouped bar chart for annual UK macro indicators."""
    fig = px.bar(
        macro_df,
        x="year",
        y="value",
        color="indicator_name",
        barmode="group",
        title=title,
        labels={"year": "Year", "value": "Value (%)", "indicator_name": "Indicator"},
    )
    fig.update_traces(
        hovertemplate="<b>%{data.name}</b><br>Year: %{x}<br>Value: %{y:.2f}%<extra></extra>"
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **_LAYOUT_DEFAULTS,
    )
    return fig
