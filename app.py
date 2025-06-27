
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fiber Splicing Dashboard", layout="wide")

st.title("Fiber Splicing Dashboard")

uploaded_file = st.file_uploader("Upload Fiber Pay Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=0)
    df.columns = df.columns.str.strip()
    st.write("Detected columns:", df.columns.tolist())

    # Extract metrics
    import re
    def extract_metrics(row):
        fat_match = re.search(r'Number of FATs:\s*(\d+)', row.get('Closure/Panel Count', ''))
        splice_match = re.search(r'Splicing Hours:\s*(\d+)', row.get('Hours Worked', ''))
        test_match = re.search(r'Testing Hours:\s*(\d+)', row.get('Hours Worked', ''))
        labor_match = re.search(r'Labor Hours:\s*(\d+)', row.get('Hours Worked', ''))

        return pd.Series({
            'FATs': int(fat_match.group(1)) if fat_match else 0,
            'Splicing Hours': int(splice_match.group(1)) if splice_match else 0,
            'Testing Hours': int(test_match.group(1)) if test_match else 0,
            'Labor Hours': int(labor_match.group(1)) if labor_match else 0
        })

    df = df.copy()
    metrics = df.apply(extract_metrics, axis=1)
    df = pd.concat([df, metrics], axis=1)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Splicing Bonus Pay'] = df['Splicing Hours'] * 25.00

    # Filters
    techs = df['Technician Name'].dropna().unique().tolist()
    projects = df['Project'].dropna().unique().tolist()

    selected_tech = st.multiselect("Filter by Technician", techs, default=techs)
    selected_proj = st.multiselect("Filter by Project", projects, default=projects)

    filtered_df = df[df['Technician Name'].isin(selected_tech) & df['Project'].isin(selected_proj)]

    st.subheader("Summary Table")
    st.dataframe(filtered_df[['Date', 'Technician Name', 'Project', 'FATs', 'Splicing Hours', 'Splicing Bonus Pay']])

    st.subheader("Total Splicing Bonus Pay per Technician")
    bonus_chart = filtered_df.groupby("Technician Name")["Splicing Bonus Pay"].sum().reset_index()
    st.bar_chart(bonus_chart.set_index("Technician Name"))

    st.subheader("Total FATs per Technician")
    fat_chart = filtered_df.groupby("Technician Name")["FATs"].sum().reset_index()
    st.bar_chart(fat_chart.set_index("Technician Name"))

    st.subheader("Total Splicing Hours per Project")
    splicing_chart = filtered_df.groupby("Project")["Splicing Hours"].sum().reset_index()
    st.bar_chart(splicing_chart.set_index("Project"))
