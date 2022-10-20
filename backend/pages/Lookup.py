#! /usr/bin/env python3

import pandas as pd
import numpy as np
import streamlit as st
from dune import *

# st.sidebar.image("logo.png", width=100)

st.write("⚠️Your privacy might be at risk⚠️")
st.write("Potential Link caused by matching total cross-pool amounts")


query_id = 1279259
execution_id = execute_query(query_id)
wait_for_execution(execution_id)
raw = download_response(execution_id)
parsed = parse(raw)

df = pd.DataFrame(parsed)
formated_df = df[
    ["depositor_list", "recipient_list", "0.1 ETH", "1 ETH", "10 ETH", "100 ETH"]
]
formated_df = formated_df.rename(
    columns={"depositor_list": "Depositor", "recipient_list": "Recipient"}
)


st.text_input("Search address", key="search")

if st.session_state.search == "":
    filtered_df = formated_df
else:
    mask = np.column_stack(
        [
            formated_df[col].str.contains(st.session_state.search, na=False)
            for col in ["Depositor", "Recipient"]
        ]
    )
    filtered_df = formated_df.loc[mask.any(axis=1)]

st.dataframe(filtered_df)
