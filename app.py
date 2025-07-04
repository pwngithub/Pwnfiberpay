
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Splice Count Dashboard", layout="wide")

st.title("Splice Count Dashboard")

uploaded_file = st.file_uploader("Upload Fiber Pay Excel File", type=["xlsx"])

if uploaded_file:
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
        return pd.Series({
            "Splice Count": int(splice_count_match.group(1)) if splice_count_match else 0,
            "Closure Type": closure_type_match.group(1).strip() if closure_type_match else "Unknown",
            "Splice Type": splice_type_match.group(1).strip() if splice_type_match else "Unknown"
        })

    raw_df[["Splice Count", "Closure Type", "Splice Type"]] = raw_df.apply(extract_closure_details, axis=1)

    split_df = raw_df.copy()
    split_df["Technician Role"] = "Primary"
    split_df["Adjusted Splice Count"] = split_df["Splice Count"]
    split_df.loc[split_df["Other Employee"].notna(), "Adjusted Splice Count"] /= 2

    other_emp_df = raw_df[raw_df["Other Employee"].notna()].copy()
    other_emp_df["Technician Name"] = other_emp_df["Other Employee"]
    other_emp_df["Technician Role"] = "Other"
    other_emp_df["Adjusted Splice Count"] = other_emp_df["Splice Count"] / 2

    combined_df = pd.concat([split_df, other_emp_df], ignore_index=True)

    # Sidebar filters - defined once
    techs = combined_df["Technician Name"].unique().tolist()
    projects = combined_df["Project"].dropna().unique().tolist()
    min_date = combined_df["Date"].min()
    max_date = combined_df["Date"].max()

    selected_techs = st.sidebar.multiselect("Select Technicians", techs, default=techs)
    selected_projects = st.sidebar.multiselect("Select Projects", projects, default=projects)
    start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])
    granularity = st.sidebar.radio("Time Granularity", ["Day", "Week", "Month"])

    combined_df = combined_df[
        combined_df["Technician Name"].isin(selected_techs) &
        combined_df["Project"].isin(selected_projects) &
        (combined_df["Date"] >= pd.to_datetime(start_date)) &
        (combined_df["Date"] <= pd.to_datetime(end_date))
    ]

    st.subheader("Total Splice Count by Technician")
    total_df = combined_df.groupby(["Technician Name", "Technician Role"])["Adjusted Splice Count"].sum().reset_index()
    st.dataframe(total_df)

    st.subheader("Splice Counts by Closure Type")
    closure_type_df = combined_df.groupby("Closure Type")["Adjusted Splice Count"].sum().reset_index()
    st.dataframe(closure_type_df)
    st.bar_chart(closure_type_df.set_index("Closure Type"))

    st.subheader("Splice Counts by Splice Type")
    splice_type_df = combined_df.groupby("Splice Type")["Adjusted Splice Count"].sum().reset_index()
    st.dataframe(splice_type_df)
    st.bar_chart(splice_type_df.set_index("Splice Type"))

    st.subheader(f"{granularity}ly Splice Counts")
    if granularity == "Day":
        time_df = combined_df.groupby(["Date", "Technician Name"])["Adjusted Splice Count"].sum().reset_index()
    elif granularity == "Week":
        time_df = combined_df.groupby([pd.Grouper(key="Date", freq="W"), "Technician Name"])["Adjusted Splice Count"].sum().reset_index()
    else:
        time_df = combined_df.groupby([pd.Grouper(key="Date", freq="M"), "Technician Name"])["Adjusted Splice Count"].sum().reset_index()

    pivot = time_df.pivot(index="Date", columns="Technician Name", values="Adjusted Splice Count")
    st.line_chart(pivot)
