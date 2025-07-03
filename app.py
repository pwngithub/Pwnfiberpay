
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Splice Count Dashboard", layout="wide")

st.title("Splice Count Dashboard")

uploaded_file = st.file_uploader("Upload Fiber Pay Excel File", type=["xlsx"])

if uploaded_file:
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    st.write("Detected sheets:", sheet_names)

    if set(["Total by Technician", "Daily", "Weekly", "Monthly"]).issubset(sheet_names):
        # It's a report file
        st.success("Report file detected.")

        df = pd.read_excel(uploaded_file, sheet_name=None)
        
        total_df = df["Total by Technician"]
        daily_df = df["Daily"]
        weekly_df = df["Weekly"]
        monthly_df = df["Monthly"]
    else:
        # Assume it's raw fiber pay data and process
        st.info("Raw fiber pay data detected. Processing...")
        raw_df = pd.read_excel(uploaded_file, sheet_name=0)
        raw_df.columns = raw_df.columns.str.strip()
        raw_df["Date"] = pd.to_datetime(raw_df["Date"], errors='coerce')
        raw_df["Technician Name"] = raw_df["Technician Name"].str.strip().str.title()
        raw_df["Other Employee"] = raw_df["Other Employee"].fillna("").str.strip().str.title()

        def extract_closure_details(row):
            text = row.get("Closures/Panels", "")
            splice_count_match = re.search(r'Splice Count:\s*(\d+)', text)
            closure_type_match = re.search(r'Closure Type:\s*([^,]+)', text)
            splice_type_match = re.search(r'Splice Type:\s*([^,]+)', text)
            row["Splice Count"] = int(splice_count_match.group(1)) if splice_count_match else 0
            row["Closure Type"] = closure_type_match.group(1).strip() if closure_type_match else "Unknown"
            row["Splice Type"] = splice_type_match.group(1).strip() if splice_type_match else "Unknown"
            return row

        raw_df = raw_df.apply(extract_closure_details, axis=1)

        total_df = raw_df.groupby("Technician Name")["Splice Count"].sum().reset_index().rename(columns={"Splice Count": "Total Splice Count"})
        daily_df = raw_df.groupby(["Date", "Technician Name"])["Splice Count"].sum().reset_index().rename(columns={"Splice Count": "Daily Splice Count"})
        weekly_df = raw_df.groupby([pd.Grouper(key="Date", freq="W"), "Technician Name"])["Splice Count"].sum().reset_index().rename(columns={"Splice Count": "Weekly Splice Count"})
        monthly_df = raw_df.groupby([pd.Grouper(key="Date", freq="M"), "Technician Name"])["Splice Count"].sum().reset_index().rename(columns={"Splice Count": "Monthly Splice Count"})


    techs_primary = raw_df["Technician Name"].unique().tolist()
    techs_other = raw_df["Other Employee"].unique().tolist()
    techs = list(set(techs_primary + [t for t in techs_other if t]))
    selected_techs = st.sidebar.multiselect("Select Technicians", techs, default=techs)

    st.subheader("Total Splice Count by Technician")
    filtered_total = total_df[total_df["Technician Name"].isin(selected_techs)]
    st.dataframe(filtered_total)
    st.bar_chart(filtered_total.set_index("Technician Name"))

    st.subheader("Daily Splice Counts")
    filtered_daily = daily_df[daily_df["Technician Name"].isin(selected_techs)]
    st.line_chart(filtered_daily.pivot(index="Date", columns="Technician Name", values=filtered_daily.columns[-1]))

    st.subheader("Weekly Splice Counts")
    filtered_weekly = weekly_df[weekly_df["Technician Name"].isin(selected_techs)]
    st.line_chart(filtered_weekly.pivot(index="Date", columns="Technician Name", values=filtered_weekly.columns[-1]))

    st.subheader("Splice Counts by Closure Type")
    closure_type_df = combined_df.groupby(["Closure Type"])["Adjusted Splice Count"].sum().reset_index()
    st.dataframe(closure_type_df)
    st.bar_chart(closure_type_df.set_index("Closure Type"))

    st.subheader("Splice Counts by Splice Type")
    splice_type_df = combined_df.groupby(["Splice Type"])["Adjusted Splice Count"].sum().reset_index()
    st.dataframe(splice_type_df)
    st.bar_chart(splice_type_df.set_index("Splice Type"))

    st.subheader("Monthly Splice Counts")
    filtered_monthly = monthly_df[monthly_df["Technician Name"].isin(selected_techs)]
    st.line_chart(filtered_monthly.pivot(index="Date", columns="Technician Name", values=filtered_monthly.columns[-1]))
else:
    st.info("Please upload a raw fiber pay Excel file or a generated splice_summary_report.xlsx.")
