import streamlit as st
import time
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="WorkPulse", layout="wide")

# ===== FILE =====
file = "task_log.csv"

# ===== SIDEBAR =====
mode = st.sidebar.radio("Select Mode", ["Employee", "Manager Dashboard"])


# =========================
# 👨‍💻 EMPLOYEE MODE
# =========================
if mode == "Employee":

    st.title("👨‍💻 WorkPulse – Employee Tracker")

    # ===== TEAM MEMBERS =====
    team_members = sorted([
        "Robin",
        "Shiksha",
        "Hemanth",
        "Allan",
        "Manisha",
        "Dinesh",
        "Rithapreetha",
        "Suhas",
        "Prajwal"
    ])

    user = st.selectbox("Select Your Name", ["-- Select --"] + team_members)

    # ===== TASKS =====
    tasks = [
        "List Bill Audit",
        "Retro Bill Audit",
        "CPS Creation"
    ]

    task = st.selectbox("Select Task", tasks)

    # ===== NEW FIELDS =====
    client_name = st.text_input("Enter Client Name")

    status_options = ["Completed", "Pending", "In Progress"]
    status = st.selectbox("Select Status", status_options)

    # ===== SESSION STATE =====
    if "running" not in st.session_state:
        st.session_state.running = False
        st.session_state.start_time = None
        st.session_state.pause_time = None
        st.session_state.total_paused = 0

    col1, col2, col3 = st.columns(3)

    # ▶️ START / RESUME
    if col1.button("▶️ Start / Resume"):
        if user == "-- Select --":
            st.warning("⚠️ Please select your name")
        elif client_name.strip() == "":
            st.warning("⚠️ Please enter client name")
        else:
            if not st.session_state.running:
                st.session_state.running = True

                if st.session_state.pause_time:
                    st.session_state.total_paused += time.time() - st.session_state.pause_time
                    st.session_state.pause_time = None
                else:
                    st.session_state.start_time = time.time()

    # ⏸ PAUSE
    if col2.button("⏸ Pause"):
        if st.session_state.running:
            st.session_state.running = False
            st.session_state.pause_time = time.time()

    # ⏹ STOP
    if col3.button("⏹ Stop"):
        if st.session_state.start_time is None:
            st.warning("⚠️ Start a task first")
        else:
            end_time = time.time()

            total_time = int(end_time - st.session_state.start_time - st.session_state.total_paused)

            data = {
                "User": user,
                "Task": task,
                "Client Name": client_name,
                "Status": status,
                "Start Time": datetime.fromtimestamp(st.session_state.start_time).strftime("%Y-%m-%d %I:%M:%S %p"),
                "End Time": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "Total Time (sec)": total_time,
                "Idle Time (sec)": 0,
                "Active Time (sec)": total_time
            }

            df = pd.DataFrame([data])

            if os.path.exists(file):
                existing = pd.read_csv(file)
                df = pd.concat([existing, df], ignore_index=True)

            df.to_csv(file, index=False)

            st.success("✅ Task Logged Successfully!")

            # Reset
            st.session_state.running = False
            st.session_state.start_time = None
            st.session_state.pause_time = None
            st.session_state.total_paused = 0

    # ===== LIVE TIMER =====
    if st.session_state.start_time:

        if st.session_state.running:
            current_time = time.time()
        else:
            current_time = st.session_state.pause_time or time.time()

        elapsed = int(current_time - st.session_state.start_time - st.session_state.total_paused)

        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)

        st.markdown(f"## ⏳ Timer: {hours:02d}:{minutes:02d}:{seconds:02d}")

        if st.session_state.running:
            time.sleep(1)
            st.rerun()


# =========================
# 👨‍💼 MANAGER DASHBOARD
# =========================
elif mode == "Manager Dashboard":

    st.title("📊 WorkPulse – Manager Dashboard")

    if not os.path.exists(file):
        st.warning("No data available yet.")
    else:
        df = pd.read_csv(file)

        # SAFE CONVERSION
        df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
        df["End Time"] = pd.to_datetime(df["End Time"], errors="coerce")

        df = df.dropna(subset=["Start Time", "End Time"])

        # ===== FILTERS =====
        st.subheader("🔍 Filters")

        col1, col2, col3, col4 = st.columns(4)

        users = ["All"] + list(df["User"].dropna().unique())
        selected_user = col1.selectbox("Employee", users)

        tasks = ["All"] + list(df["Task"].unique())
        selected_task = col2.selectbox("Task", tasks)

        statuses = ["All"] + list(df["Status"].dropna().unique())
        selected_status = col3.selectbox("Status", statuses)

        selected_date = col4.date_input("Date")

        filtered_df = df.copy()

        if selected_user != "All":
            filtered_df = filtered_df[filtered_df["User"] == selected_user]

        if selected_task != "All":
            filtered_df = filtered_df[filtered_df["Task"] == selected_task]

        if selected_status != "All":
            filtered_df = filtered_df[filtered_df["Status"] == selected_status]

        if selected_date:
            filtered_df = filtered_df[
                filtered_df["Start Time"].dt.date == selected_date
            ]

        # ===== TABLE =====
        st.subheader("📋 Data")
        st.dataframe(filtered_df, use_container_width=True)

        # ===== METRICS =====
        st.subheader("📈 Summary")

        total_time = filtered_df["Total Time (sec)"].sum()
        active_time = filtered_df["Active Time (sec)"].sum()

        col1, col2 = st.columns(2)

        col1.metric("Total Hours", round(total_time / 3600, 2))
        col2.metric("Active Hours", round(active_time / 3600, 2))

        # ===== CHART =====
        st.subheader("📊 Task Distribution")

        if not filtered_df.empty:
            st.bar_chart(filtered_df.groupby("Task")["Active Time (sec)"].sum())
        else:
            st.warning("No data available")

        # ===== DOWNLOAD =====
        st.subheader("⬇️ Export")

        csv = filtered_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Report",
            csv,
            "workpulse_report.csv",
            "text/csv"
        )
