"""streamlit server"""

import json
import time
import os

import pandas as pd
import requests
import streamlit as st
import nvidia_smi
import altair as alt


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


def df_append_record(type, df, cnt, value):
    """append new data row per request to dataframe"""
    if type == "gpu":
        row = {"%": value, "Requests": cnt}
    elif type == "cpu":
        row = {"%": value, "Requests": cnt}
    elif type == "latency":
        row = {"latency": value, "Requests": cnt}
    df = df.append(row, ignore_index=True)
    df["Requests"] = df["Requests"].astype("int")
    return df


def latency_average(df, skip=5):
    """calculate the average latency"""
    if len(df) > 5:
        avg = df["latency"].mean()
        return round(avg, 5)
    else:
        return 0


def send2api(api, json_data):
    """Sends JSON request & recieve a JSON response"""
    
    response = requests.post(api, json=json_data)
    json_response = response.content.decode('utf-8')
    json_response = json.loads(json_response)
    return json_response


def altair_chart_plot(df, color, latency_avg="None", X_label="Requests", Y_label="%", height=200):
    """configure altair chart"""
    if Y_label == "%":
        c = alt.Chart(df, height=height
                ).mark_line(
                ).encode(
                    alt.Y(Y_label, scale=alt.Scale(domain=(0, 100))),
                    alt.X(X_label, axis=alt.Axis(tickMinStep=1)),
                    tooltip=[Y_label, X_label]
                ).configure_line(
                    color=color)
    else:
        c = alt.Chart(df, height=height, title="Avg: " + str(latency_avg)
                ).mark_line(
                ).encode(
                    alt.Y(Y_label),
                    alt.X(X_label, axis=alt.Axis(tickMinStep=1)),
                    tooltip=[Y_label, X_label]
                ).configure_line(
                    color=color)
    return c


def main():
    """design streamlit fronend"""
    st.title("Memory Leak & Latency Test")

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

        st.subheader("Latency")
        latency_chart_row = st.empty()

        # read json request
        json_data = json.loads(json_data.read())
        cpu = gpu = pd.DataFrame(columns=["%", "Requests"])
        latency = pd.DataFrame(columns=["latency", "Requests"])

        # send request, reload chart
        for cnt, i in enumerate(range(int(no_requests))):
            gpu = df_append_record("gpu", gpu, cnt, gpu_memory_tracker())
            chart = altair_chart_plot(gpu, "red")
            gpu_chart_row.altair_chart(chart, use_container_width=True)

            cpu = df_append_record("cpu", cpu, cnt, cpu_memory_tracker())
            chart = altair_chart_plot(cpu, "blue")
            cpu_chart_row.altair_chart(chart, use_container_width=True)
            
            start = time.time()
            send2api(api, json_data)

            duration = time.time()-start
            latency = df_append_record("latency", latency, cnt, duration)
            latency_avg = latency_average(latency) 
            chart = altair_chart_plot(latency, "green", latency_avg=latency_avg, Y_label="latency")
            latency_chart_row.altair_chart(chart, use_container_width=True)
            st.write()


if __name__ == "__main__":
    main()