import streamlit as st
import pdfplumber as pp
import json
import pandas as pd
import openai
import re
import os
import io
from typing import Optional, Dict, List, Tuple
def calculate_flag(result, reference_range):
    try:
        value = float(str(result).replace(",", "").strip())

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:[-–]|to)\s*(\d+(?:\.\d+)?)",
            str(reference_range)
        )

        if match:
            low = float(match.group(1))
            high = float(match.group(2))
            low, high = min(low, high), max(low, high)

            if value < low:
                return "Low"
            elif value > high:
                return "High"
            else:
                return "Normal"

        if "≤" in reference_range:
            limit = float(reference_range.replace("≤", "").strip())
            return "High" if value > limit else "Normal"
        elif "≥" in reference_range:
            limit = float(reference_range.replace("≥", "").strip())
            return "Low" if value < limit else "Normal"

        return "Unknown"

    except (ValueError, TypeError):
        return "Unknown"
client = openai.OpenAI(
   base_url="https://openrouter.ai/api/v1",
   api_key=os.getenv("KEY")
)
all_text = []
all_tables = []
parsed_results = []
st.set_page_config(
  page_title = "HemoIQ - Blood test scanner",
  page_icon="⚕️")

st.title("HemoIQ:- Blood Test Scanner")
st.sidebar.title("""
HemoIQ - Blood Test Analyser""")
st.sidebar.success(
"Upload your blood test in PDF format"
"Values will be parsed and full report of"
"patient's health will be given"
)
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
        str(cell).strip()
        if cell is not None and str(cell).strip()
        else f"Column {i + 1}"
        for i, cell in enumerate(table_data[0])
    ]

    normalized_headers = [
        header.lower().strip()
        for header in headers
    ]

    test_index = None
    result_index = None
    unit_index = None
    reference_index = None
    flag_index = None

    for i, header in enumerate(normalized_headers):

        if test_index is None and any(
            x in header
            for x in [
                "test",
                "test name",
                "investigation",
                "parameter",
                "analyte",
                "description"
            ]
        ):
            test_index = i

        if result_index is None and any(
            x in header
            for x in [
                "result",
                "value",
                "reading",
                "observed",
                "result value"
            ]
        ):
            result_index = i

        if unit_index is None and (
            "unit" in header
        ):
            unit_index = i

        if reference_index is None and any(
            x in header
            for x in [
                "reference",
                "ref range",
                "reference range",
                "normal range",
                "biological reference",
                "range"
            ]
        ):
            reference_index = i

        if flag_index is None and any(
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

        elif len(row) > len(headers):
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
        calculated_flag = calculate_flag(
             result,
             reference_range
        )

        parsed_results.append({
            "Test": test_name,
            "Result": result,
            "Unit": unit,
            "Reference Range": reference,
            "Flag": calculated_flag,
            "Page": table_info["page"],
            "Source": "Table"
        })


for text_block in all_text:

    lines = text_block.splitlines()

    current_page = None

    for line in lines:

        line = line.strip()

        if not line:
            continue

        page_match = re.search(
            r"PAGE\s+(\d+)",
            line,
            re.IGNORECASE
        )

        if page_match:
            current_page = int(
                page_match.group(1)
            )
            continue

        if not re.search(
            r"\d",
            line
        ):
            continue

        normalized_line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        reference = ""

        reference_match = re.search(
            r"(-?\d+(?:\.\d+)?\s*"
            r"(?:-|–|—)\s*"
            r"-?\d+(?:\.\d+)?)",
            normalized_line
        )

        if reference_match:

            reference = (
                reference_match.group(1)
            )

        comparison_match = re.search(
            r"(<=|>=|<|>)\s*"
            r"-?\d+(?:\.\d+)?",
            normalized_line
        )

        if not reference and comparison_match:
            reference = comparison_match.group(0)

        numbers = list(
            re.finditer(
                r"(?<![A-Za-z])"
                r"-?\d+(?:\.\d+)?",
                normalized_line
            )
        )

        if not numbers:
            continue

        result_match = numbers[0]

        result = result_match.group()

        test_name = normalized_line[
            :result_match.start()
        ].strip()

        if not test_name:
            continue

        test_name = re.sub(
            r"^[\d\W]+",
            "",
            test_name
        )

        test_name = re.sub(
            r"[:|]+$",
            "",
            test_name
        ).strip()

        ignored_lines = [
            "page",
            "patient",
            "patient name",
            "name",
            "age",
            "sex",
            "gender",
            "date",
            "address",
            "phone",
            "email",
            "laboratory",
            "laboratory report",
            "blood test report",
            "reference range",
            "normal range",
            "result",
            "results",
            "test",
            "investigation",
            "parameter"
        ]

        if test_name.lower() in ignored_lines:
            continue

        if len(test_name) < 2:
            continue

        after_result = normalized_line[
            result_match.end():
        ].strip()

        unit = ""

        unit_patterns = [
            r"mg/dL",
            r"g/dL",
            r"g/L",
            r"mg/L",
            r"mmol/L",
            r"mEq/L",
            r"µmol/L",
            r"umol/L",
            r"nmol/L",
            r"pmol/L",
            r"IU/L",
            r"U/L",
            r"IU/mL",
            r"U/mL",
            r"ng/mL",
            r"pg/mL",
            r"ng/dL",
            r"pg/dL",
            r"fL",
            r"pg",
            r"/µL",
            r"/uL",
            r"/mm3",
            r"/mm³",
            r"%",
        ]

        for pattern in unit_patterns:

            unit_match = re.search(
                pattern,
                after_result,
                re.IGNORECASE
            )

            if unit_match:

                unit = unit_match.group()

                break

        flag = ""

        flag_match = re.search(
            r"\b(HH|LL|H|L|N|High|Low|Normal)\b",
            after_result,
            re.IGNORECASE
        )

        if flag_match:
            flag = flag_match.group()

        parsed_results.append({
            "Test": test_name,
            "Result": result,
            "Unit": unit,
            "Reference Range": reference,
            "Flag": flag,
            "Page": current_page,
            "Source": "Text"
        })


if parsed_results:

    results_df = pd.DataFrame(
        parsed_results
    )

    results_df["Test"] = (
        results_df["Test"]
        .astype(str)
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    results_df = results_df[
        results_df["Test"].str.len() >= 2
    ]

    results_df = results_df.drop_duplicates(
        subset=[
            "Test",
            "Result",
            "Unit"
        ],
        keep="first"
    ).reset_index(drop=True)

    st.divider()

    st.header("🩸 Blood Test Analysis")

    st.success(
        f"Detected {len(results_df)} laboratory results."
    )

    total_tests = len(results_df)

    flagged_high = results_df[
        results_df["Flag"].str.contains(
            r"high|^H$|^HH$",
            case=False,
            na=False,
            regex=True
        )
    ]

    flagged_low = results_df[
        results_df["Flag"].str.contains(
            r"low|^L$|^LL$",
            case=False,
            na=False,
            regex=True
        )
    ]

    flagged_normal = results_df[
        results_df["Flag"].str.contains(
            r"normal|^N$",
            case=False,
            na=False,
            regex=True
        )
    ]

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    with summary_col1:
        st.metric(
            "Total Tests",
            total_tests
        )

    with summary_col2:
        st.metric(
            "🔴 High",
            len(flagged_high)
        )

    with summary_col3:
        st.metric(
            "🔵 Low",
            len(flagged_low)
        )

    with summary_col4:
        st.metric(
            "🟢 Normal",
            len(flagged_normal)
        )

    st.divider()

    st.subheader("📋 Parsed Results")

    search_col, filter_col = st.columns(2)

    with search_col:

        search_test = st.text_input(
            "Search test",
            placeholder="e.g. Hemoglobin"
        )

    with filter_col:

        status_filter = st.selectbox(
            "Filter results",
            [
                "All",
                "High",
                "Low",
                "Normal",
                "Unknown"
            ]
        )

    filtered_df = results_df.copy()

    if search_test:

        filtered_df = filtered_df[
            filtered_df["Test"].str.contains(
                search_test,
                case=False,
                na=False
            )
        ]

    if status_filter == "High":

        filtered_df = filtered_df[
            filtered_df["Flag"].str.contains(
                r"high|^H$|^HH$",
                case=False,
                na=False,
                regex=True
            )
        ]

    elif status_filter == "Low":

        filtered_df = filtered_df[
            filtered_df["Flag"].str.contains(
                r"low|^L$|^LL$",
                case=False,
                na=False,
                regex=True
            )
        ]

    elif status_filter == "Normal":

        filtered_df = filtered_df[
            filtered_df["Flag"].str.contains(
                r"normal|^N$",
                case=False,
                na=False,
                regex=True
            )
        ]

    elif status_filter == "Unknown":

        filtered_df = filtered_df[
            ~filtered_df["Flag"].str.contains(
                r"high|low|normal|^H$|^HH$|^L$|^LL$|^N$",
                case=False,
                na=False,
                regex=True
            )
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("⚠️ Results Requiring Attention")

    abnormal_df = results_df[
        results_df["Flag"].str.contains(
            r"high|low|^H$|^HH$|^L$|^LL$",
            case=False,
            na=False,
            regex=True
        )
    ]

    if abnormal_df.empty:

        st.success(
            "No explicitly flagged abnormal results "
            "were detected."
        )

    else:

        for _, row in abnormal_df.iterrows():

            result_text = (
                f"**{row['Test']}** — "
                f"{row['Result']} "
                f"{row['Unit']} "
                f"({row['Flag']})"
            )

            if re.search(
                r"high|^H$|^HH$",
                row["Flag"],
                re.IGNORECASE
            ):

                st.error(
                    result_text
                )

            else:

                st.info(
                    result_text
                )

    st.divider()

    st.subheader("🔬 Individual Test")

    test_names = results_df[
        "Test"
    ].tolist()

    selected_test = st.selectbox(
        "Select a test",
        test_names
    )

    selected_rows = results_df[
        results_df["Test"]
        == selected_test
    ]

    if not selected_rows.empty:

        selected = selected_rows.iloc[0]

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:

            st.metric(
                "Result",
                f"{selected['Result']} "
                f"{selected['Unit']}".strip()
            )

        with detail_col2:

            st.metric(
                "Flag",
                selected["Flag"]
                if selected["Flag"]
                else "Not flagged"
            )

        with detail_col3:

            st.metric(
                "Page",
                selected["Page"]
                if selected["Page"]
                else "Unknown"
            )

        st.write(
            f"**Reference Range:** "
            f"{selected['Reference Range']}"
            if selected["Reference Range"]
            else "**Reference Range:** Not provided"
        )

        st.write(
            f"**Source:** {selected['Source']}"
        )

    st.divider()

    st.subheader("⬇️ Export Results")

    export_data = results_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=export_data,
        file_name="blood_test_results.csv",
        mime="text/csv"
    )
    st.subheader("🧠 AI Conclusion")

if st.button("Generate Conclusion"):

    with st.spinner("Analysing blood-test results..."):

        results_json = results_df.to_dict(
            orient="records"
        )

        results_text = json.dumps(
            results_json,
            indent=2
        )

        prompt = f"""
You are a laboratory-report explanation assistant.

Analyse the complete blood-test dataset below.

Requirements:
- Consider the results together, not only individually.
- Use the reference ranges supplied in the report.
- Explain abnormal findings in simple language.
- Mention important normal findings when relevant.
- Do not diagnose diseases.
- Do not prescribe medication.
- Do not invent missing information.
- Clearly state when information is insufficient.
- End with a concise overall conclusion.
- Recommend sensible dietary changes as well as appropriate medication while mentioning to consider the information as suggestive.
- Recommend discussing concerning findings with a qualified healthcare professional.

Blood-test data:

{results_text}

If the data seems to not be from a blood test, respond in no more than two lines.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
               {"role": "user", "content": prompt}
            ]
)
        conclusion = response.choices[0].message.content
        st.info(conclusion)
else:

    st.warning(
        "No laboratory results could be identified "
        "from the extracted PDF text or tables."
    )


st.divider()
st.write("This application is only intended for educational purposes. Do not substitute professional medical advice with the information \n provided by this application")
st.write("BKB, 2026, all rights reserved")
