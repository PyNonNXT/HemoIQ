import streamlit as st
import pdfplumber as pp
import pandas as pd
import re
import io
from typing import Optional, Dict, List, Tuple
st.set_page_config(
  page_title = "HemoIQ - Blood test scanner",
  page_icon="⚕️")

st.title("HemoIQ:- Blood Test Scanner")
st.sidebar.title("""
HemoIQ - Blood Test Analyser""")
st.sidebar.success("""
Upload your blood test in PDF format
Values will be parsed and full report of 
patient's health will be given
""")
uploaded_file = st.file_uploader("Upload your blood test PDF", type=["pdf"], help="Upload a PDF laboratory/blood test report." )
if uploaded_file is not None: 
  st.success(f"Uploaded: {uploaded_file.name}")
  try:
    with pp.open(uploaded_file) as pdf:
      st.write(f"**Number of pages:** {len(pdf.pages)}")
      all_text = [] 
      all_tables = []
      for page_number, page in enumerate(pdf.pages, start=1):
        st.markdown(f"### Page {page_number}")
        text = page.extract_text() 
        if text:
          all_text.append( f"\n--- PAGE {page_number} ---\n{text}" )
        tables = page.extract_tables() 
        if tables:
          for table_number, table in enumerate( 
            tables, 
            start=1 ): 
           if not table: 
            continue
            cleaned_table = [
              row 
              for row in table
              if row and any( 
                cell is not None and str(cell).strip() 
                for cell in row ) 
            ]
            if cleaned_table:
              all_tables.append( 
                { "page": page_number,
                  "table_number": table_number, 
                  "data": cleaned_table })
        st.divider() 
        st.header("📄 Extracted Text")
        if all_text: 
          combined_text = "\n".join(all_text) 
          with st.expander(
            "Show extracted text", 
            expanded=True ):
              st.text_area( 
                "PDF Text",
                combined_text, 
                height=400 ) 
        else:
          st.warning("No text could be extracted from this PDF.")
        st.header("📊 Extracted Tables") 
        if all_tables: 
          st.write( f"Found **{len(all_tables)} table(s)**." ) 
          for table_info in all_tables: 
            page_number = table_info["page"] 
            table_number = table_info["table_number"] 
            table_data = table_info["data"]
            st.subheader(f"Page {page_number} — Table {table_number}")
            try:
              header = table_data[0]
              rows = table_data[1:]
              cleaned_headers = [] 
              for index, column in enumerate(header):
                if column is None or not str(column).strip(): 
                  column = f"Column {index + 1}" 
                  cleaned_headers.append(str(column).strip())
              cleaned_rows = []
              for row in rows: 
                row = list(row) 
                if len(row) < len(cleaned_headers): 
                  row += [None] * (len(cleaned_headers) - len(row)) 
                elif len(row) > len(cleaned_headers):
                  row = row[:len(cleaned_headers)] 
                cleaned_rows.append(row)
              df = pd.DataFrame(cleaned_rows, 
                                columns=cleaned_headers) 
              st.dataframe(df,
                           use_container_width=True,
                           hide_index=True)
            except Exception as e: 
              st.warning(f"Could not display table as DataFrame: {e}") 
              st.write(table_data) 
            else: 
              st.warning("No tables were detected in this PDF.") 
  except Exception as e: 
    st.error("There was a problem reading the PDF.")
    st.exception(e)
 
  st.divider()

  st.header("🩸 Blood Test Analysis")

  parsed_results = []

  for table_info in all_tables:

    table_data = table_info["data"]

    if len(table_data) < 2:
        continue

    headers = [
        str(cell).strip() if cell else f"Column {i + 1}"
        for i, cell in enumerate(table_data[0])
    ]

    normalized_headers = [
        header.lower()
        for header in headers
    ]

    test_index = None
    result_index = None
    unit_index = None
    reference_index = None
    flag_index = None

    for i, header in enumerate(normalized_headers):

        if any(
            x in header
            for x in [
                "test",
                "investigation",
                "parameter",
                "analyte",
                "description"
            ]
        ):
            if test_index is None:
                test_index = i

        if any(
            x in header
            for x in [
                "result",
                "value",
                "reading",
                "observed"
            ]
        ):
            if result_index is None:
                result_index = i

        if "unit" in header:
            unit_index = i

        if any(
            x in header
            for x in [
                "reference",
                "ref range",
                "normal range",
                "range"
            ]
        ):
            reference_index = i

        if any(
            x in header
            for x in [
                "flag",
                "status"
            ]
        ):
            flag_index = i

    for row in table_data[1:]:

        row = list(row)

        if len(row) < len(headers):
            row += [None] * (
                len(headers) - len(row)
            )

        if len(row) > len(headers):
            row = row[:len(headers)]

        row = [
            str(cell).strip()
            if cell is not None
            else ""
            for cell in row
        ]

        if test_index is None:
            continue

        test_name = row[test_index]

        if not test_name:
            continue

        result = (
            row[result_index]
            if result_index is not None
            else ""
        )

        unit = (
            row[unit_index]
            if unit_index is not None
            else ""
        )

        reference = (
            row[reference_index]
            if reference_index is not None
            else ""
        )

        flag = (
            row[flag_index]
            if flag_index is not None
            else ""
        )

        parsed_results.append(
            {
                "Test": test_name,
                "Result": result,
                "Unit": unit,
                "Reference Range": reference,
                "Flag": flag,
                "Page": table_info["page"]
            }
        )


if parsed_results:

    results_df = pd.DataFrame(
        parsed_results
    )

    results_df = results_df.drop_duplicates(
        subset=[
            "Test",
            "Result",
            "Unit"
        ]
    )

    st.success(
        f"Detected {len(results_df)} laboratory results."
    )

    st.subheader("📋 Parsed Results")

    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("🔎 Filter Results")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:

        test_search = st.text_input(
            "Search for a test",
            placeholder="e.g. Hemoglobin"
        )

    with filter_col2:

        flag_filter = st.selectbox(
            "Filter by flag",
            [
                "All",
                "High",
                "Low",
                "Normal",
                "Unknown"
            ]
        )

    filtered_df = results_df.copy()

    if test_search:

        filtered_df = filtered_df[
            filtered_df["Test"].str.contains(
                test_search,
                case=False,
                na=False
            )
        ]

    if flag_filter != "All":

        filtered_df = filtered_df[
            filtered_df["Flag"].str.contains(
                flag_filter,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("📊 Quick Summary")

    total = len(results_df)

    high_count = len(
        results_df[
            results_df["Flag"].str.contains(
                "high|H|HH",
                case=False,
                na=False,
                regex=True
            )
        ]
    )

    low_count = len(
        results_df[
            results_df["Flag"].str.contains(
                "low|L|LL",
                case=False,
                na=False,
                regex=True
            )
        ]
    )

    normal_count = len(
        results_df[
            results_df["Flag"].str.contains(
                "normal|N",
                case=False,
                na=False,
                regex=True
            )
        ]
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Tests",
            total
        )

    with col2:
        st.metric(
            "🔴 High",
            high_count
        )

    with col3:
        st.metric(
            "🔵 Low",
            low_count
        )

    with col4:
        st.metric(
            "🟢 Normal",
            normal_count
        )

    st.divider()

    st.subheader("⚠️ Results Requiring Attention")

    abnormal_df = results_df[
        results_df["Flag"].str.contains(
            "high|low|H|L",
            case=False,
            na=False,
            regex=True
        )
    ]

    if abnormal_df.empty:

        st.success(
            "No explicitly flagged abnormal results were found."
        )

    else:

        for _, row in abnormal_df.iterrows():

            flag = row["Flag"].upper()

            message = (
                f"**{row['Test']}**: "
                f"{row['Result']} {row['Unit']} "
                f"({flag})"
            )

            if "H" in flag:

                st.error(message)

            elif "L" in flag:

                st.info(message)

            else:

                st.warning(message)

    st.divider()

    st.subheader("📈 Test Details")

    selected_test = st.selectbox(
        "Select a test",
        results_df["Test"].tolist()
    )

    selected_row = results_df[
        results_df["Test"]
        == selected_test
    ].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Result",
            selected_row["Result"]
        )

    with col2:

        st.metric(
            "Unit",
            selected_row["Unit"]
            or "Not available"
        )

    with col3:

        st.metric(
            "Flag",
            selected_row["Flag"]
            or "Not flagged"
        )

    st.write(
        f"**Reference range:** "
        f"{selected_row['Reference Range'] or 'Not provided'}"
    )

    st.write(
        f"**Source page:** "
        f"{selected_row['Page']}"
    )

    st.divider()

    st.subheader("⬇️ Export")

    csv = results_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Results as CSV",
        data=csv,
        file_name="blood_test_results.csv",
        mime="text/csv"
    )

else:

    st.warning(
        "No structured laboratory results "
        "could be identified from the extracted tables."
    )


st.write("BKB, 2026, all rights reserved")
