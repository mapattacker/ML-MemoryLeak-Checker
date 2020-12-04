"""streamlit server"""

import json
import os
import time

import altair as alt
import nvidia_smi
import pandas as pd
import requests
import streamlit as st


def gpu_memory_tracker():
    """returns nvidia gpu memory consumed"""
    nvidia_smi.nvmlInit()
    handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
    info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
    used = info.used
    total = info.total
    percent = used / total * 100
    return percent


def cpu_memory_tracker():
    """returns cpu memory from system"""
    total = os.popen("""free -m | grep "Mem" | awk '{ print $2 }'""").read().strip()
    used = os.popen("""free -m | grep "Mem" | awk '{ print $3 }'""").read().strip()
    free = os.popen("""free -m | grep "Mem" | awk '{ print $4 }'""").read().strip()
    used_percent = int(used) / int(total) * 100
    return used_percent


def memory_df_record(type, df, cnt):
    """append new memory data row per request to dataframe"""
    if type == "gpu":
        row = {"%": gpu_memory_tracker(), "Requests": cnt}
    elif type == "cpu":
        row = {"%": cpu_memory_tracker(), "Requests": cnt}
    df = df.append(row, ignore_index=True)
    df["Requests"] = df["Requests"].astype("int")
    return df


def altair_mem_chart(df, color):
    """configure altair chart"""
    c = alt.Chart(df, height=250
            ).mark_line(
            ).encode(
                alt.Y("%", scale=alt.Scale(domain=(0, 100))),
                alt.X("Requests", axis=alt.Axis(tickMinStep=1)),
                tooltip=["%", "Requests"]
            ).configure_line(
                color=color)
    return c


def main():
    """design streamlit fronend"""
    st.title("Memory Leak Test")

    st.subheader("Requirements")
    st.info("""   1. Your flask app & this streamlit app are in the same machine
    2. Your machine has Nvidia GPU & CUDA installed
    3. Do not work on other stuff while this test is running""")

    st.sidebar.title("Define Test Parameters")
    api = st.sidebar.text_input("API Endpoint", value="http://localhost:5000")
    no_requests = st.sidebar.slider("Requests to Run", min_value=20, max_value=1000, value=500, step=10)
    json_data = st.sidebar.file_uploader("Upload a Sample Request JSON file")
    
    if api != "" and json_data is not None:
      
        # set charts frames
        st.subheader("GPU Utilisation")
        gpu_chart_row = st.empty()

        st.subheader("RAM Utilisation")
        cpu_chart_row = st.empty()

        # read json request
        json_data = json.loads(json_data.read())
        cpu = gpu = pd.DataFrame(columns=["%", "Requests"])

        # send request, reload chart
        for cnt, i in enumerate(range(int(no_requests))):
            gpu = memory_df_record("gpu", gpu, cnt)
            chart = altair_mem_chart(gpu, "red")
            gpu_chart_row.altair_chart(chart, use_container_width=True)

            cpu = memory_df_record("cpu", cpu, cnt)
            chart = altair_mem_chart(cpu, "blue")
            cpu_chart_row.altair_chart(chart, use_container_width=True)
            
            requests.post(api, json=json_data)
            time.sleep(0.2)


if __name__ == "__main__":
    main()