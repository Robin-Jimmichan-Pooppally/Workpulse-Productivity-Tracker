import streamlit as st
import time
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="WorkPulse", layout="wide")

# ===== SIDEBAR =====
mode = st.sidebar.radio("Select Mode", ["Employee", "Manager Dashboard"])

file = "task_log.csv"

# =========================
# 👨‍💻 EMPLOYEE MODE
# =========================
if mode == "Employee":

    st.title("👨‍💻 WorkPulse – Employee Tracker")

    user = st.text_input("Enter Your Name")

    tasks = [
        "List Bill Audit",
        "Retro Bill Audit",
        "CPS Creation"
    ]

    task = st.selectbox("Select Task", tasks)

    # SESSION STATE
    if "running" not in st.session_state:
        st.session_state.running = False
        st.session_state.start_time = None
        st.session_state.elapsed = 0
        st.session_state.idle_time = 0

    col1, col2, col3 = st.columns(3)

    # START
    if col1.button("▶️ Start"):
        st.session_state.running = True
        st.session_state.start_time = time.time()
        st.session_state.elapsed = 0
        st.session_state.idle_time = 0

    # PAUSE
    if col2.button("⏸ Pause"):
        st.session_state.running = False

    # STOP
    if col3.button("⏹ Stop"):
        total_time = st.session_state.elapsed
        active_time = total_time - st.session_state.idle_time

        data = {
            "User": user,
            "Task": task,
            "Start Time": datetime.fromtimestamp(st.session_state.start_time),
            "End Time": datetime.now(),
            "Total Time (sec)": total_time,
            "Idle Time (sec)": st.session_state.idle_time,
            "Active Time (sec)": active_time
        }

        df = pd.DataFrame([data])

        if os.path.exists(file):
            existing = pd.read_csv(file)
            df = pd.concat([existing, df], ignore_index=True)

        df.to_csv(file, index=False)

        st.success("✅ Task Logged Successfully!")
        st.session_state.running = False

    # TIMER
    if st.session_state.running:
        st.session_state.elapsed += 1
        time.sleep(1)
        st.rerun()

    st.write(f"⏳ Total Time: {st.session_state.elapsed} sec")
    st.write(f"🔥 Active Time: {st.session_state.elapsed - st.session_state.idle_time} sec")


# =========================
# 👨‍💼 MANAGER DASHBOARD
# =========================
elif mode == "Manager Dashboard":

    st.title("📊 WorkPulse – Manager Dashboard")

    if not os.path.exists(file):
        st.warning("No data available yet.")
    else:
        df = pd.read_csv(file)

        # Convert datetime
        df["Start Time"] = pd.to_datetime(df["Start Time"])
        df["End Time"] = pd.to_datetime(df["End Time"])

        # ===== FILTERS =====
        st.subheader("🔍 Filters")

        col1, col2, col3 = st.columns(3)

        users = ["All"] + list(df["User"].dropna().unique())
        selected_user = col1.selectbox("Select Employee", users)

        tasks = ["All"] + list(df["Task"].unique())
        selected_task = col2.selectbox("Select Task", tasks)

        selected_date = col3.date_input("Select Date")

        # APPLY FILTERS
        filtered_df = df.copy()

        if selected_user != "All":
            filtered_df = filtered_df[filtered_df["User"] == selected_user]

        if selected_task != "All":
            filtered_df = filtered_df[filtered_df["Task"] == selected_task]

        if selected_date:
            filtered_df = filtered_df[
                filtered_df["Start Time"].dt.date == selected_date
            ]

        # DISPLAY
        st.subheader("📋 Filtered Data")
        st.dataframe(filtered_df, use_container_width=True)

        # METRICS
        st.subheader("📈 Summary")

        total_time = filtered_df["Total Time (sec)"].sum()
        idle_time = filtered_df["Idle Time (sec)"].sum()
        active_time = filtered_df["Active Time (sec)"].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Time (hrs)", round(total_time / 3600, 2))
        col2.metric("Idle Time (hrs)", round(idle_time / 3600, 2))
        col3.metric("Active Time (hrs)", round(active_time / 3600, 2))

        # DOWNLOAD
        st.subheader("⬇️ Export Report")

        csv = filtered_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Filtered Report",
            data=csv,
            file_name="workpulse_report.csv",
            mime="text/csv"
        )
