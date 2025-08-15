import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os


st.title("\U0001F4B0 Финансовый планировщик")
st.markdown("""Добро пожаловать, Сармат.""")

# input данных
col1, col2 = st.columns(2)
with col1:
    current_age = st.number_input("Мой текущий возраст", min_value=18, max_value=100, value=24)
    retirement_age = st.number_input("Возраст выхода на пассивный доход", min_value=current_age+1, max_value=100, value=45)
    starting_capital = st.number_input("Начальный капитал (₽)", min_value=0, value=0, format="%d")
    monthly_contribution_start = st.number_input("Начальный ежемесячный взнос (₽)", min_value=0, value=100_000, format="%d")
    accumulation_interest = st.slider("Доходность инвестиций в период накопления (%)", 0.0, 30.0, 15.0) / 100
with col2:
    monthly_target_income_today = st.number_input("Желаемый ежемесячный доход (в сегодняшних ₽)", value=600_000, format="%d")
    inflation_rate = st.slider("Годовая инфляция (%)", 0.0, 20.0, 9.4) / 100
    retirement_interest = st.slider("Ставка депозита в пассивный период (%)", 0.0, 30.0, 15.0) / 100
    contribution_growth_rate = st.slider("Рост ежемесячных взносов (% в год)", 0.0, 30.0, 6.7) / 100

# произвести расчёты
if st.button("Рассчитать план"):
    years = retirement_age - current_age
    months = years * 12

    monthly_target_income_future = monthly_target_income_today * ((1 + inflation_rate) ** years)
    required_capital = monthly_target_income_future * 12 / retirement_interest

    capital = starting_capital
    contributions = []
    capitals = []

    for year in range(years):
        for month in range(12):
            contribution = monthly_contribution_start * ((1 + contribution_growth_rate) ** year)
            capital *= (1 + accumulation_interest / 12)
            capital += contribution
            contributions.append(contribution)
            capitals.append(capital)

    final_nominal = capital
    final_real = final_nominal / ((1 + inflation_rate) ** years)
    goal_achieved = final_nominal >= required_capital
    plan_completion_pct = final_nominal / required_capital * 100

    df = pd.DataFrame({
        "Месяц": np.arange(1, months + 1),
        "Взнос (₽)": contributions,
        "Капитал (₽)": capitals,
        "Выполнение цели (%)": [c / required_capital * 100 for c in capitals]
    })

    # Вывод результатов
    st.subheader("Результаты")
    st.metric("Необходимый капитал (₽)", f"{required_capital:,.0f}".replace(",", " "))
    st.metric("Итоговый капитал (₽)", f"{final_nominal:,.0f}".replace(",", " "), delta=f"{'Достигнута' if goal_achieved else 'Недостаточно'}")
    st.metric("Процент выполнения плана", f"{plan_completion_pct:.2f}%")

    # Информативные графики
    st.subheader("Визуализация накоплений")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Месяц"], df["Капитал (₽)"], label="Капитал", color="green")
    ax.plot(df["Месяц"], df["Взнос (₽)"].cumsum(), label="Накопленные взносы", linestyle="--", color="blue")
    ax.axhline(required_capital, color="red", linestyle=":", label="Целевой капитал")
    ax.set_title("Рост капитала и накопленных взносов")
    ax.set_xlabel("Месяц")
    ax.set_ylabel("₽")
    ax.legend()
    st.pyplot(fig)

    # Таблица платежей
    st.subheader("График платежей")
    st.dataframe(df.style.format({"Взнос (₽)": "{:,.0f}", "Капитал (₽)": "{:,.0f}", "Выполнение цели (%)": "{:.2f}"}))

    # Скачивание CSV
    st.subheader("Скачать результаты")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Скачать таблицу в CSV", csv, "financial_model.csv", "text/csv")

    # PDF экспорт
    st.subheader("Скачать PDF отчет")

    font_path = os.path.join("fonts", "DejaVuSans.ttf")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        class PDF(FPDF):
            def header(self):
                self.set_font("DejaVu", '', 14)
                self.cell(0, 10, "Финансовый отчет", 0, 1, 'C')

        pdf = PDF()
        pdf.add_font('DejaVu', '', font_path, uni=True)
        pdf.set_font("DejaVu", '', 12)
        pdf.add_page()

        lines = [
            f"Возраст: {current_age} - {retirement_age}",
            f"Ежемесячный доход (сегодня): {monthly_target_income_today:,.0f} ₽".replace(",", " "),
            f"Инфляция: {inflation_rate*100:.2f}%",
            f"Доходность до {retirement_age}: {accumulation_interest*100:.2f}%",
            f"Ставка депозита после {retirement_age}: {retirement_interest*100:.2f}%",
            f"Рост взносов: {contribution_growth_rate*100:.2f}% в год",
            f"Целевой капитал: {required_capital:,.0f} ₽".replace(",", " "),
            f"Итоговый капитал: {final_nominal:,.0f} ₽".replace(",", " "),
            f"Процент выполнения: {plan_completion_pct:.2f}%",
            f"Цель {'достигнута ✅' if goal_achieved else 'не достигнута ❌'}"
        ]
        for line in lines:
            pdf.cell(0, 10, line, ln=True)

        # Таблица платежей в PDF
        pdf.add_page()
        pdf.set_font("DejaVu", '', 10)
        pdf.cell(0, 10, "График платежей", ln=True)

        pdf.set_font("DejaVu", '', 8)
        col_width = pdf.w / 4 - 5
        pdf.cell(col_width, 6, "Месяц", border=1)
        pdf.cell(col_width, 6, "Взнос (₽)", border=1)
        pdf.cell(col_width, 6, "Капитал (₽)", border=1)
        pdf.cell(col_width, 6, "Выполнение (%)", border=1)
        pdf.ln()

        for i in range(months):
            pdf.cell(col_width, 6, str(i + 1), border=1)
            pdf.cell(col_width, 6, f"{contributions[i]:,.0f}".replace(",", " "), border=1)
            pdf.cell(col_width, 6, f"{capitals[i]:,.0f}".replace(",", " "), border=1)
            pdf.cell(col_width, 6, f"{capitals[i]/required_capital*100:.2f}%", border=1)
            pdf.ln()
            if (i + 1) % 40 == 0:
                pdf.add_page()
                pdf.set_font("DejaVu", '', 8)

        pdf.output(tmp_pdf.name)
        with open(tmp_pdf.name, "rb") as file:
            st.download_button("📄 Скачать PDF отчет", file.read(), "financial_report.pdf", "application/pdf")
