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
st.write("BKB, 2026, all rights reserved")
