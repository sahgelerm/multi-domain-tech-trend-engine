import streamlit as st
import pandas as pd
import numpy as np
import io
import os
from fpdf import FPDF

# ========== НАСТРОЙКИ СТРАНИЦЫ ==========
st.set_page_config(page_title="TechTrends Dashboard", layout="wide")
st.title("📊 TechTrends Dashboard")

# ========== ЗАГРУЗКА ДАННЫХ ==========
# Путь к файлу Trend Score (от Натальи)
TREND_SCORE_PATH = "/home/ubuntu/indlab-techtrends-ds/src/data/processed/trend_score.csv"

@st.cache_data
def load_trend_score():
    if os.path.exists(TREND_SCORE_PATH):
        df = pd.read_csv(TREND_SCORE_PATH)
        st.success(f"✅ Загружен файл Trend Score: {df.shape[0]} строк, {df.shape[1]} колонок")
        return df
    else:
        st.error(f"❌ Файл не найден: {TREND_SCORE_PATH}")
        # Демо-данные для примеров
        return pd.DataFrame({
            "Тренд": ["ИИ", "Блокчейн", "Квантовые вычисления", "Edge AI", "Web3"],
            "Trend Score": [95, 78, 82, 88, 70],
            "Категория": ["AI", "FinTech", "Computing", "AI", "Web3"],
            "Рост": [12, 5, 8, 15, 3]   # для примера
        })

df_trend = load_trend_score()

# Для демонстрации остальных вкладок создадим ещё один датафрейм
@st.cache_data
def load_subtechnologies():
    return pd.DataFrame({
        "Технология": ["Трансформеры", "Смарт-контракты", "Квантовые алгоритмы"],
        "Подтехнология": ["Attention", "EVM", "Shor"],
        "Популярность": [92, 65, 78]
    })

df_sub = load_subtechnologies()

# ========== ФУНКЦИИ ДЛЯ ОТЧЕТОВ ==========
def generate_report_data(report_type):
    """Формирует DataFrame для отчёта в зависимости от типа."""
    if report_type == "ТЗ":
        if "Trend Score" in df_trend.columns:
            df_report = df_trend.nlargest(10, "Trend Score")
        else:
            df_report = df_trend.head(10)
        title = "Техническое задание: Топ-10 трендов по Trend Score"
    else:  # CVC
        if "Рост" in df_trend.columns:
            df_report = df_trend[df_trend["Рост"] > 0].nlargest(10, "Trend Score")
        else:
            df_report = df_trend.sample(min(10, len(df_trend)))
        title = "CVC отчет: Перспективные направления для инвестиций"
    return df_report, title

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Отчет')
    return output.getvalue()

def to_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)

    # Заголовки таблицы
    col_width = pdf.w / (len(df.columns) + 1)
    pdf.set_font("Arial", 'B', 10)
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()

    # Данные
    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        for col in df.columns:
            pdf.cell(col_width, 10, str(row[col]), border=1)
        pdf.ln()
        if pdf.get_y() > 250:
            pdf.add_page()
            pdf.set_font("Arial", size=9)
    return pdf.output(dest='S').encode('latin1')

# ========== ВКЛАДКИ ==========
tab1, tab2, tab3, tab4 = st.tabs(["📈 Тренды", "🔬 Подтехнологии", "🔍 Data Explorer", "📄 Отчеты"])

# ----- Вкладка 1: Тренды -----
with tab1:
    st.subheader("Анализ технологических трендов")
    st.dataframe(df_trend, use_container_width=True)
    if "Trend Score" in df_trend.columns:
        st.bar_chart(df_trend.set_index(df_trend.columns[0])["Trend Score"])

# ----- Вкладка 2: Подтехнологии -----
with tab2:
    st.subheader("Детализация подтехнологий")
    st.dataframe(df_sub, use_container_width=True)
    st.write("Пример: распределение популярности")
    st.bar_chart(df_sub.set_index("Технология")["Популярность"])

# ----- Вкладка 3: Data Explorer -----
with tab3:
    st.subheader("Интерактивный просмотр данных")
    dataset_choice = st.radio("Выберите набор данных:", ["Trend Score", "Подтехнологии"])
    if dataset_choice == "Trend Score":
        st.dataframe(df_trend)
        st.download_button("Скачать Trend Score (CSV)", data=df_trend.to_csv(index=False), file_name="trend_score.csv", mime="text/csv")
    else:
        st.dataframe(df_sub)
        st.download_button("Скачать Подтехнологии (CSV)", data=df_sub.to_csv(index=False), file_name="subtech.csv", mime="text/csv")

# ----- Вкладка 4: Отчеты (ТЗ, CVC, Excel, PDF) -----
with tab4:
    st.subheader("📄 Генерация отчетов с Trend Score")

    # Выбор типа отчета
    report_type = st.radio("Выберите тип отчета:", ["ТЗ", "CVC"], horizontal=True)

    # Предпросмотр
    df_preview, title_preview = generate_report_data(report_type)
    st.write(f"**Предпросмотр ({report_type}):** {title_preview}")
    st.dataframe(df_preview, use_container_width=True)

    # Кнопки выгрузки
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"📎 Скачать {report_type} отчет в Excel"):
            excel_data = to_excel(df_preview)
            st.download_button(
                label="✅ Скачать Excel",
                data=excel_data,
                file_name=f"{report_type}_отчет.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col2:
        if st.button(f"📄 Скачать {report_type} отчет в PDF"):
            pdf_data = to_pdf(df_preview, title_preview)
            st.download_button(
                label="✅ Скачать PDF",
                data=pdf_data,
                file_name=f"{report_type}_отчет.pdf",
                mime="application/pdf"
            )

    # Дополнительно: исходный Trend Score
    with st.expander("📊 Исходные данные Trend Score (от Натальи)"):
        st.dataframe(df_trend, use_container_width=True)
        csv = df_trend.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Скачать Trend Score как CSV", data=csv, file_name="trend_score.csv", mime="text/csv")