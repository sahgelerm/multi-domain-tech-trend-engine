import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_publications_dynamics(domain_key, label, color, monthly_df, yearly_df):
    """
    Строит график динамики публикаций для одного домена.
    Универсальная функция — работает и для публикаций, и для патентов.

    Args:
        domain_key: ключ домена ('semiconductors' / 'gene_engineering')
        label: отображаемое название ('Semiconductors')
        color: цвет линий (hex)
        monthly_df: DataFrame с колонками [period_dt, count]
        yearly_df: DataFrame с колонками [year, count]

    Returns:
        plotly Figure
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            label + " — Monthly",
            label + " — Yearly"
        ),
        horizontal_spacing=0.12
    )

    fig.add_trace(go.Scatter(
        x=monthly_df["period_dt"],
        y=monthly_df["count"],
        mode="lines",
        name=label + " (monthly)",
        line=dict(color=color, width=1.2)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=yearly_df["year"],
        y=yearly_df["count"],
        mode="lines+markers+text",
        name=label + " (yearly)",
        line=dict(color=color, width=2),
        marker=dict(size=7),
        text=yearly_df["count"].apply(lambda x: f"{x:,}"),
        textposition="top center",
        textfont=dict(size=9)
    ), row=1, col=2)

    fig.update_layout(
        title="Scientific Publications Dynamics: " + label + " (2010–2025)",
        height=400,
        showlegend=False
    )
    fig.update_yaxes(title_text="Publications / month", col=1)
    fig.update_yaxes(title_text="Publications / year", col=2)
    fig.update_xaxes(tickmode="linear", dtick=2, col=2)

    return fig