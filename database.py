import sqlalchemy
import pandas as pd
import streamlit as st

def get_engine():
    url = (
        f"mysql+pymysql://{st.secrets['db']['user']}:{st.secrets['db']['password']}"
        f"@{st.secrets['db']['host']}:{st.secrets['db']['port']}/{st.secrets['db']['database']}"
    )
    return sqlalchemy.create_engine(url)

def query(sql):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)