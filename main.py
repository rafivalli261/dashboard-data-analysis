import streamlit as st
import pandas as pd
import numpy as np

st.write("This is a social media impact on life data")
df = pd.read_csv("./dataset/social_media_impact_on_life.csv")
st.scatter_chart(df, x='Academic_Performance_GPA', y='Perceived_Stress_Score')