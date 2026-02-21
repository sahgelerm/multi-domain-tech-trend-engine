import pandas as pd
import numpy as np


def calc_cagr(start_value, end_value, n_years):
    """
    Compound Annual Growth Rate — среднегодовой темп роста.

    Args:
        start_value: значение в начальном году
        end_value: значение в конечном году
        n_years: количество лет между ними

    Returns:
        CAGR в процентах, например -3.1 означает -3.1% / год
    """
    if start_value <= 0 or n_years <= 0:
        return None
    return ((end_value / start_value) ** (1 / n_years) - 1) * 100


def calc_yoy(yearly_df, year):
    """
    Year-over-Year — рост текущего года относительно предыдущего.

    Args:
        yearly_df: DataFrame с колонками [year, count]
        year: год для которого считаем YoY

    Returns:
        YoY в процентах или None если нет данных
    """
    current = yearly_df.loc[yearly_df["year"] == year, "count"]
    previous = yearly_df.loc[yearly_df["year"] == year - 1, "count"]

    if current.empty or previous.empty or previous.values[0] == 0:
        return None

    return (current.values[0] / previous.values[0] - 1) * 100


def calc_mom(monthly_df, year, month):
    """
    Month-over-Month — рост текущего месяца относительно предыдущего.

    Args:
        monthly_df: DataFrame с колонками [period_dt, count]
        year: год текущего месяца
        month: номер текущего месяца (1-12)

    Returns:
        MoM в процентах или None если нет данных
    """
    current_date = pd.Timestamp(year=year, month=month, day=1)
    prev_date = current_date - pd.DateOffset(months=1)

    current = monthly_df.loc[monthly_df["period_dt"] == current_date, "count"]
    previous = monthly_df.loc[monthly_df["period_dt"] == prev_date, "count"]

    if current.empty or previous.empty or previous.values[0] == 0:
        return None

    return (current.values[0] / previous.values[0] - 1) * 100


def calc_acceleration(yearly_df, window=5):
    """
    Acceleration — разница между ростом в последнем окне и предыдущем.
    Показывает ускоряется ли рост или замедляется.

    Args:
        yearly_df: DataFrame с колонками [year, count]
        window: размер окна в годах (default 5)

    Returns:
        dict с ключами: recent_growth, previous_growth, acceleration
    """
    years = sorted(yearly_df["year"].tolist())
    if len(years) < window * 2:
        return None

    recent_years   = years[-window:]
    previous_years = years[-window * 2:-window]

    recent_mean   = yearly_df[yearly_df["year"].isin(recent_years)]["count"].mean()
    previous_mean = yearly_df[yearly_df["year"].isin(previous_years)]["count"].mean()

    if previous_mean == 0:
        return None

    recent_growth   = (recent_mean / previous_mean - 1) * 100
    previous_growth = (previous_mean / yearly_df[yearly_df["year"].isin(
        years[-window * 3:-window * 2]
    )]["count"].mean() - 1) * 100 if len(years) >= window * 3 else None

    return {
        "recent_growth":   round(recent_growth, 1),
        "previous_growth": round(previous_growth, 1) if previous_growth else None,
        "acceleration":    round(recent_growth - previous_growth, 1) if previous_growth else None
    }


def calc_domain_summary(domain_key, label, yearly_df, monthly_df):
    """
    Сводная таблица всех метрик для одного домена.
    Используется для Topic Card и финального отчёта.

    Args:
        domain_key: ключ домена
        label: отображаемое название
        yearly_df: DataFrame с колонками [year, count]
        monthly_df: DataFrame с колонками [period_dt, count]

    Returns:
        dict со всеми метриками
    """
    yd = yearly_df.copy()

    first_year = yd["year"].min()
    last_year  = yd["year"].max()
    first_count = yd.loc[yd["year"] == first_year, "count"].values[0]
    last_count  = yd.loc[yd["year"] == last_year,  "count"].values[0]

    peak_idx   = yd["count"].idxmax()
    peak_year  = yd.loc[peak_idx, "year"]
    peak_count = yd.loc[peak_idx, "count"]

    cagr         = calc_cagr(first_count, last_count, last_year - first_year)
    yoy_last     = calc_yoy(yd, last_year)
    acceleration = calc_acceleration(yd)

    return {
        "domain":        domain_key,
        "label":         label,
        "total":         int(yd["count"].sum()),
        "first_year":    int(first_year),
        "last_year":     int(last_year),
        "first_count":   int(first_count),
        "last_count":    int(last_count),
        "peak_year":     int(peak_year),
        "peak_count":    int(peak_count),
        "cagr":          round(cagr, 1) if cagr is not None else None,
        "yoy_last":      round(yoy_last, 1) if yoy_last is not None else None,
        "acceleration":  acceleration
    }


def print_domain_summary(summary):
    """Выводит сводку метрик в читаемом виде."""
    acc = summary["acceleration"] or {}
    print("." * 30)
    print("Domain:        " + summary["label"])
    print("Period:        " + str(summary["first_year"]) + " – " + str(summary["last_year"]))
    print("Total papers:  " + f"{summary['total']:,}")
    print("Peak year:     " + str(summary["peak_year"]) + " (" + f"{summary['peak_count']:,}" + ")")
    print(str(summary["first_year"]) + ":           " + f"{summary['first_count']:,}")
    print(str(summary["last_year"]) + ":           " + f"{summary['last_count']:,}")
    print("CAGR:          " + (f"{summary['cagr']:+.1f}% / year" if summary["cagr"] else "—"))
    print("YoY (last):    " + (f"{summary['yoy_last']:+.1f}%" if summary["yoy_last"] else "—"))
    if acc:
        print("Acceleration:  " + (f"{acc['acceleration']:+.1f}%" if acc.get("acceleration") else "—"))
    print("." * 30)


def calc_pmi(summaries):
    """
    Patent Momentum Indicator — сравнительный индекс импульса по доменам.
    PMI = Z(Activity) + Z(CAGR)

    Высокий PMI = домен с мощным импульсом роста.

    Args:
        summaries: список dict от calc_domain_summary()
                   каждый должен содержать 'total' и 'cagr'

    Returns:
        список dict с добавленными полями z_activity, z_cagr, pmi
    """
    if len(summaries) < 2:
        print("PMI требует минимум 2 домена для сравнения.")
        return summaries

    activities = np.array([s["total"] for s in summaries], dtype=float)
    cagrs      = np.array([s["cagr"] if s["cagr"] is not None else 0.0
                           for s in summaries], dtype=float)

    def zscore(arr):
        std = arr.std()
        if std == 0:
            return np.zeros_like(arr)
        return (arr - arr.mean()) / std

    z_activities = zscore(activities)
    z_cagrs      = zscore(cagrs)
    pmis         = z_activities + z_cagrs

    result = []
    for i, s in enumerate(summaries):
        s = s.copy()
        s["z_activity"] = round(float(z_activities[i]), 3)
        s["z_cagr"]     = round(float(z_cagrs[i]), 3)
        s["pmi"]        = round(float(pmis[i]), 3)
        result.append(s)

    return sorted(result, key=lambda x: x["pmi"], reverse=True)


def print_pmi_report(summaries_with_pmi):
    """Выводит сравнительную таблицу PMI по доменам."""    
    print("PMI REPORT (Patent Momentum Indicator)")
    print("." * 35)
    print(f"{'Domain':<25} {'Activity':>10} {'CAGR':>8} {'PMI':>8}")
    print("." * 35)
    for s in summaries_with_pmi:
        print(
            f"{s['label']:<25} "
            f"{s['z_activity']:>+10.3f} "
            f"{s['z_cagr']:>+8.3f} "
            f"{s['pmi']:>+8.3f}"
        )
    print("." * 35)
    winner = summaries_with_pmi[0]
    print("Highest momentum: " + winner["label"] + " (PMI " + f"{winner['pmi']:+.3f})")