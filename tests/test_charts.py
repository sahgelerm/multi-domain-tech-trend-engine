"""
Запуск: python tests/test_charts.py
"""
import sys
import pandas as pd

sys.path.append('.')
from visualization.charts import plot_publications_dynamics


def make_monthly_df():
    dates = pd.date_range("2019-01-01", periods=60, freq="MS")
    return pd.DataFrame({"period_dt": dates, "count": range(100, 160)})


def make_yearly_df():
    return pd.DataFrame({
        "year":  [2019, 2020, 2021, 2022, 2023],
        "count": [1200, 1350, 1500, 1420, 1600]
    })


def test_returns_figure():
    """Функция должна возвращать объект Figure."""
    import plotly.graph_objects as go
    fig = plot_publications_dynamics(
        domain_key="test",
        label="Test Domain",
        color="#1f77b4",
        monthly_df=make_monthly_df(),
        yearly_df=make_yearly_df()
    )
    assert isinstance(fig, go.Figure), "Возвращается не Figure"
    print("Возвращает Figure — OK")


def test_has_two_traces():
    """График должен содержать два трейса: monthly и yearly."""
    fig = plot_publications_dynamics(
        domain_key="test",
        label="Test Domain",
        color="#1f77b4",
        monthly_df=make_monthly_df(),
        yearly_df=make_yearly_df()
    )
    assert len(fig.data) == 2, "Ожидалось 2 трейса, получили " + str(len(fig.data))
    print("Два трейса (monthly + yearly) — OK")


def test_yearly_trace_has_correct_points():
    """Годовой трейс должен содержать столько точек сколько лет."""
    fig = plot_publications_dynamics(
        domain_key="test",
        label="Test Domain",
        color="#1f77b4",
        monthly_df=make_monthly_df(),
        yearly_df=make_yearly_df()
    )
    yearly_trace = fig.data[1]
    assert len(yearly_trace.x) == 5, "Ожидалось 5 точек (2019–2023)"
    print("Количество точек на годовом графике — OK")


def test_title_contains_label():
    """Заголовок графика должен содержать название домена."""
    label = "Batteries"
    fig = plot_publications_dynamics(
        domain_key="test",
        label=label,
        color="#ff7f0e",
        monthly_df=make_monthly_df(),
        yearly_df=make_yearly_df()
    )
    assert label in fig.layout.title.text, "Название домена не в заголовке"
    print("Заголовок содержит название домена — OK")


def test_color_applied():
    """Цвет должен применяться к обоим трейсам."""
    color = "#ff0000"
    fig = plot_publications_dynamics(
        domain_key="test",
        label="Test",
        color=color,
        monthly_df=make_monthly_df(),
        yearly_df=make_yearly_df()
    )
    assert fig.data[0].line.color == color, "Цвет не применён к monthly трейсу"
    assert fig.data[1].line.color == color, "Цвет не применён к yearly трейсу"
    print("Цвет применяется корректно — OK")


if __name__ == "__main__":
    print("Тесты charts.py\n")
    test_returns_figure()
    test_has_two_traces()
    test_yearly_trace_has_correct_points()
    test_title_contains_label()
    test_color_applied()
    print("Все тесты прошли!")



def visual_check():
    """
    Визуальная проверка графиков — запускается вручную.
    Не является автоматическим тестом.
    """
    print("\n[ Визуальная проверка ]")
    fig = plot_publications_dynamics(
        domain_key="test",
        label="Batteries (visual check)",
        color="#ff7f0e",
        monthly_df=make_monthly_df(),
        yearly_df=make_yearly_df()
    )
    fig.show()
    print("График открыт в браузере.")


if __name__ == "__main__":
    print("Тесты charts.py\n")
    test_returns_figure()
    test_has_two_traces()
    test_yearly_trace_has_correct_points()
    test_title_contains_label()
    test_color_applied()
    print("Все тесты прошли!")

    # Визуальная проверка — только при явном запросе
    import sys
    if "--visual" in sys.argv:
        visual_check()