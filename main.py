import streamlit as st
import pdfplumber as pdf
import pandas as pd
reference_ranges = {
  "male_adult" : {
    "Haemoglobin": (13.0, 17.0),
    "WBC": (4000, 11000), 
    "Platelets": (150000,400000),
    "RBC": (4.5,5.5),
    "MCV": (80,100),
    "Fasting_Glucose": (70,100),
    "HbA1C": (0,5.7),
    "TSH": (0.4,4.0),
    "T3": (0.8,1.8),
    "T4": (2.3,4.2),
    "MCH": (27,33),
    "MCHC": (32,36),
    "Creatinine": (0.7,1.3),
    "BUN": (7,20),
    "Blood Urea": (15,40),
    "Uric Acid": (3.4,7.0),
    "LDL": (0,100),
    "HDL": (40,100),
    "Cholesterol": (0,200),
    "Triglycerides": (0,150),
    "Vitamin D": (30,100),
    "Vitamin B12": (200,900),
    "Total Bilirubin": (0.1,1.2)
  },
    "female_adult" : {
    "Haemoglobin": (12.0, 15.5),
    "WBC": (4000, 11000), 
    "Platelets": (150000,400000),
    "RBC": (4.0,5.0),
    "MCV": (80,100),
    "Fasting_Glucose": (70,100),
    "HbA1C": (0,5.7),
    "TSH": (0.4,4.0),
    "T3": (0.8,1.8),
    "T4": (2.3,4.2),
    "MCH": (27,33),
    "MCHC": (32,36),
    "Creatinine": (0.6,1.1),
    "BUN": (7,20),
    "Blood Urea": (15,40),
    "Uric Acid": (2.4,6.0),
    "LDL": (0,100),
    "HDL": (50,100),
    "Cholesterol": (0,200),
    "Triglycerides": (0,150),
    "Vitamin D": (30,100),
    "Vitamin B12": (200,900),
    "Total Bilirubin": (0.1,1.2)
  }
}
st.title("HemoIQ:- Blood Test Scanner")
st.sidebar("""
HemoIQ - Blood Test Analyser
Upload your blood test in PDF format
Values will be parsed and full report of 
patient's health will be given
""")
st.write("BKB, 2026, all rights reserved")
