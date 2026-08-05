import streamlit as st
import pdfplumber as pdf
import pandas as pd
reference_ranges = {
  "male_adult" : {
    "Haemoglobin": (13.5, 17.5),
    "WBC": (4000, 11000), 
    "Platelets": (150000,400000),
    "RBC": (4.5,5.5),
    "MCV": (80,100),
    "Fasting_Glucose": (70,100),
    "HbA1C": (0,5.7),
    "TSH": (0.4,4.0),
    "T3": (0.8,1.8),
    "T4": (2.3,4.2)
  }
}
st.title("HemoIQ:- Blood Test Scanner")
st.write("BKB, 2026, all rights reserved")
