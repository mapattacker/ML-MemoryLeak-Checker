"""streamlit server for demo site"""

import json
import time
import os

import pandas as pd
import requests
import streamlit as st
import nvidia_smi



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


def memory_df_record(type, cnt=0):
  df = pd.DataFrame(columns=["%"])
  if type == "gpu":
    row = {"%": gpu_memory_tracker()}
  elif type == "cpu":
    row = {"%": cpu_memory_tracker()}
  df = df.append(row, ignore_index=True)
  return df


def send2api(api, json_data):
    """Sends JSON request & recieve a JSON response"""
    
    response = requests.post(api, json=json_data)
    json_response = response.content.decode('utf-8')
    json_response = json.loads(json_response)
    return json_response


def main():
    """design streamlit fronend"""
    st.title("Memory Leak Test")

    st.subheader("Requirements")
    st.info("""   1. Your flask app & this streamlit app are in the same machine
    2. Your machine has Nvidia GPU & CUDA installed
    3. Do not work on other stuff while this test is running""")

    st.sidebar.title("Define Test Parameters")
    api = st.sidebar.text_input("API Endpoint", value="http://localhost:5000")
    no_requests = st.sidebar.slider("No. Requests to Run", min_value=20, max_value=1000, value=500, step=10)
    json_data = st.sidebar.file_uploader("Upload a Sample Request JSON file")
    
    if api != "" and json_data is not None:
      
      # plot charts
      st.subheader("GPU Utilisation")
      gpu = memory_df_record("gpu")
      gpu_chart = st.line_chart(gpu, height=250)

      st.subheader("RAM Utilisation")
      cpu = memory_df_record("cpu")
      cpu_chart = st.line_chart(cpu, height=250)

      # read json request
      json_data = json.loads(json_data.read())

      # send request, reload chart
      for cnt, i in enumerate(range(int(no_requests))):
        gpu = memory_df_record("gpu")
        gpu_chart.add_rows(gpu)
        cpu = memory_df_record("cpu")
        cpu_chart.add_rows(cpu)
        
        send2api(api, json_data)
        time.sleep(0.25)


if __name__ == "__main__":
    main()