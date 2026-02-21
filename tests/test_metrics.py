import pandas as pd
import sys
sys.path.append('.')

from etl.metrics import calc_cagr, calc_yoy, calc_acceleration, calc_domain_summary

def test_calc_cagr():
    # Известный результат: 100 → 200 за 10 лет = ~7.2% / год
    result = calc_cagr(100, 200, 10)
    assert round(result, 1) == 7.2, f"Ожидалось 7.2, получили {result}"
    print("calc_cagr — OK")

def test_calc_cagr_zero():
    # Нулевое начальное значение должно вернуть None
    result = calc_cagr(0, 200, 10)
    assert result is None
    print("calc_cagr с нулём — OK")

def test_calc_yoy():
    df = pd.DataFrame({"year": [2022, 2023, 2024], "count": [1000, 1200, 1100]})
    result = calc_yoy(df, 2023)
    assert round(result, 1) == 20.0, f"Ожидалось 20.0, получили {result}"
    print("calc_yoy — OK")

def test_calc_acceleration():
    # 10 лет данных для проверки acceleration
    df = pd.DataFrame({
        "year":  list(range(2010, 2025)),
        "count": [100, 110, 120, 130, 140, 150, 145, 140, 135, 130, 125, 120, 115, 110, 105]
    })
    result = calc_acceleration(df)
    assert result is not None
    assert "acceleration" in result
    print("calc_acceleration — OK")

if __name__ == "__main__":
    test_calc_cagr()
    test_calc_cagr_zero()
    test_calc_yoy()
    test_calc_acceleration()
    print("Все тесты прошли!")