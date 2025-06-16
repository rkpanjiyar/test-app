import streamlit as st
import pandas as pd

st.title("My First Streamlit App")
st.write("Hello *world!*")

data = {'col1': [1, 2], 'col2': [3, 4]}
df = pd.DataFrame(data)
st.write(df)
