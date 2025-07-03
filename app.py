
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Splice Count Dashboard", layout="wide")

st.title("Splice Count Dashboard")

uploaded_file = st.file_uploader("Upload Fiber Pay Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    
    total_df = df["Total by Technician"]
    daily_df = df["Daily"]
    weekly_df = df["Weekly"]
    monthly_df = df["Monthly"]
    
    techs = total_df["Technician Name"].unique().tolist()
    selected_techs = st.sidebar.multiselect("Select Technicians", techs, default=techs)
    
    st.subheader("Total Splice Count by Technician")
    filtered_total = total_df[total_df["Technician Name"].isin(selected_techs)]
    st.dataframe(filtered_total)
    st.bar_chart(filtered_total.set_index("Technician Name"))
    
    st.subheader("Daily Splice Counts")
    filtered_daily = daily_df[daily_df["Technician Name"].isin(selected_techs)]
    st.line_chart(filtered_daily.pivot(index="Date", columns="Technician Name", values="Daily Splice Count"))
    
    st.subheader("Weekly Splice Counts")
    filtered_weekly = weekly_df[weekly_df["Technician Name"].isin(selected_techs)]
    st.line_chart(filtered_weekly.pivot(index="Date", columns="Technician Name", values="Weekly Splice Count"))
    
    st.subheader("Monthly Splice Counts")
    filtered_monthly = monthly_df[monthly_df["Technician Name"].isin(selected_techs)]
    st.line_chart(filtered_monthly.pivot(index="Date", columns="Technician Name", values="Monthly Splice Count"))
    
    st.subheader("Download Summary Report")
    st.download_button(
        "Download Report as Excel",
        uploaded_file.read(),
        file_name="splice_summary_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Please upload the generated splice_summary_report.xlsx file to view the dashboard.")
