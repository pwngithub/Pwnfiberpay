
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fiber Splicing Dashboard", layout="wide")

st.title("Fiber Splicing Dashboard")

uploaded_file = st.file_uploader("Upload Fiber Pay Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=0)
    df.columns = df.columns.str.strip()
    st.write("Detected columns:", df.columns.tolist())

    # Validate required columns
    required_columns = ['Project', 'Technician Name', 'Closure/Panel Count', 'Closures/Panels', 'Hours Worked']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"Missing required column(s): {', '.join(missing)}")
        st.stop()

    # Extract metrics
    import re
    def extract_metrics(row):
        fat_match = re.search(r'Number of FATs:\s*(\d+)', row.get('Closure/Panel Count', ''))
        splice_match = re.search(r'Splicing Hours:\s*(\d+)', row.get('Hours Worked', ''))
        test_match = re.search(r'Testing Hours:\s*(\d+)', row.get('Hours Worked', ''))
        labor_match = re.search(r'Labor Hours:\s*(\d+)', row.get('Hours Worked', ''))

        closure_text = row.get("Closures/Panels", "")
        splice_type_match = re.search(r'Splice Type:\s*([^,]+)', closure_text)
        splice_count_match = re.search(r'Splice Count:\s*(\d+)', closure_text)
        fiber_type_match = re.search(r'Fiber Type:\s*([^,]+)', closure_text)
        max_cable_match = re.search(r'Max Cable Size:\s*(\d+)', closure_text)

        return pd.Series({
            'FATs': int(fat_match.group(1)) if fat_match else 0,
            'Splicing Hours': int(splice_match.group(1)) if splice_match else 0,
            'Testing Hours': int(test_match.group(1)) if test_match else 0,
            'Labor Hours': int(labor_match.group(1)) if labor_match else 0,
            'Splice Type': splice_type_match.group(1).strip() if splice_type_match else None,
            'Splice Count': int(splice_count_match.group(1)) if splice_count_match else 0,
            'Fiber Type': fiber_type_match.group(1).strip() if fiber_type_match else None,
            'Max Cable Size': max_cable_match.group(1).strip() if max_cable_match else None
        })

    df = df.copy()
    metrics = df.apply(extract_metrics, axis=1)
    df = pd.concat([df, metrics], axis=1)
    df['Date'] = pd.to_datetime(df.get('Date'), errors='coerce')
    df['Splicing Bonus Pay'] = df['Splicing Hours'] * 25.00

    # Filters
    techs = df['Technician Name'].dropna().unique().tolist()
    projects = df['Project'].dropna().unique().tolist()
    splice_types = df['Splice Type'].dropna().unique().tolist()
    fiber_types = df['Fiber Type'].dropna().unique().tolist()

    st.sidebar.header("Filters")
    selected_tech = st.sidebar.multiselect("Technician", techs, default=techs)
    selected_proj = st.sidebar.multiselect("Project", projects, default=projects)
    selected_splice = st.sidebar.multiselect("Splice Type", splice_types, default=splice_types)
    selected_fiber = st.sidebar.multiselect("Fiber Type", fiber_types, default=fiber_types)

    filtered_df = df[
        df['Technician Name'].isin(selected_tech) &
        df['Project'].isin(selected_proj) &
        df['Splice Type'].isin(selected_splice) &
        df['Fiber Type'].isin(selected_fiber)
    ]

    st.subheader("Summary Table")
    st.dataframe(filtered_df[[
        'Date', 'Technician Name', 'Project', 'FATs', 'Splicing Hours',
        'Splicing Bonus Pay', 'Splice Type', 'Splice Count', 'Fiber Type', 'Max Cable Size'
    ]])

    st.subheader("Total Splicing Bonus Pay per Technician")
    bonus_chart = filtered_df.groupby("Technician Name")["Splicing Bonus Pay"].sum().reset_index()
    st.bar_chart(bonus_chart.set_index("Technician Name"))

    st.subheader("Total FATs per Technician")
    fat_chart = filtered_df.groupby("Technician Name")["FATs"].sum().reset_index()
    st.bar_chart(fat_chart.set_index("Technician Name"))

    st.subheader("Total Splicing Hours per Project")
    splicing_chart = filtered_df.groupby("Project")["Splicing Hours"].sum().reset_index()
    st.bar_chart(splicing_chart.set_index("Project"))


    st.subheader("Download Filtered Data")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "fiber_summary.csv", "text/csv")

    st.subheader("Weekly Summary (Splicing Bonus Pay)")
    weekly_summary = filtered_df.groupby(pd.Grouper(key='Date', freq='W'))["Splicing Bonus Pay"].sum().reset_index()
    st.line_chart(weekly_summary.set_index("Date"))

    st.subheader("Monthly Summary (Splicing Bonus Pay)")
    monthly_summary = filtered_df.groupby(pd.Grouper(key='Date', freq='M'))["Splicing Bonus Pay"].sum().reset_index()
    st.line_chart(monthly_summary.set_index("Date"))
