import streamlit as st
import time
import pandas as pd
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="WorkPulse", layout="wide")

# ===== TIMEZONE =====
IST = pytz.timezone("Asia/Kolkata")

# ===== FILE =====
file = "task_log.csv"

# ===== LOAD USERS FROM SECRETS =====
users = st.secrets["users"]

# =========================
# 🔐 LOGIN SYSTEM
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

if not st.session_state.logged_in:

    st.title("🔐 WorkPulse Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid Credentials ❌")

    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.write(f"👤 {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

mode = "Employee"
if st.session_state.role == "manager":
    mode = st.sidebar.radio("Mode", ["Employee", "Manager Dashboard"])

# =========================
# 👨‍💻 EMPLOYEE MODE
# =========================
if mode == "Employee":

    st.title("👨‍💻 WorkPulse – Employee Tracker")

    user = st.session_state.username
    st.write(f"👤 User: {user}")

    tasks = [
        "Meeting", "List bill audit", "Retro bill audit", "CPS creation",
        "Backup creations", "Assessments", "Training video",
        "Coordination", "QA check", "Break"
    ]

    task = st.selectbox("Select Activity", tasks)
    client_name = st.text_input("Client Name")
    status = st.selectbox("Status", ["In Progress", "Completed"])
    comments = st.text_area("Comments (Optional)")
    selected_date = st.date_input("Date", datetime.now(IST))

    if "running" not in st.session_state:
        st.session_state.running = False
        st.session_state.start_time = None
        st.session_state.pause_time = None
        st.session_state.total_paused = 0

    col1, col2, col3 = st.columns(3)

    if col1.button("▶️ Start"):
        if client_name.strip() == "":
            st.warning("Enter client name")
        else:
            st.session_state.running = True
            if st.session_state.pause_time:
                st.session_state.total_paused += time.time() - st.session_state.pause_time
                st.session_state.pause_time = None
            else:
                st.session_state.start_time = time.time()

    if col2.button("⏸ Pause"):
        if st.session_state.running:
            st.session_state.running = False
            st.session_state.pause_time = time.time()

    if col3.button("⏹ Stop"):
        if st.session_state.start_time:
            end_time = time.time()
            total_time = int(end_time - st.session_state.start_time - st.session_state.total_paused)

            start_dt = datetime.fromtimestamp(st.session_state.start_time, IST)
            end_dt = datetime.now(IST)

            new_data = pd.DataFrame([{
                "User": user,
                "Task": task,
                "Client Name": client_name,
                "Status": status,
                "Comments": comments,
                "Date": selected_date.strftime("%Y-%m-%d"),
                "Start Time": start_dt.strftime("%I:%M:%S %p"),
                "End Time": end_dt.strftime("%I:%M:%S %p"),
                "Total Time (sec)": total_time,
                "Active Time (sec)": total_time
            }])

            if os.path.exists(file):
                df = pd.read_csv(file)
                df = pd.concat([df, new_data], ignore_index=True)
            else:
                df = new_data

            df.to_csv(file, index=False)

            st.success("Task Saved ✅")

            st.session_state.running = False
            st.session_state.start_time = None
            st.session_state.pause_time = None
            st.session_state.total_paused = 0

            st.rerun()

    # TIMER
    if st.session_state.start_time:
        now = time.time() if st.session_state.running else st.session_state.pause_time
        elapsed = int(now - st.session_state.start_time - st.session_state.total_paused)

        h, r = divmod(elapsed, 3600)
        m, s = divmod(r, 60)

        st.markdown(f"## ⏳ {h:02d}:{m:02d}:{s:02d}")

        if st.session_state.running:
            time.sleep(1)
            st.rerun()

# =========================
# 👨‍💼 MANAGER DASHBOARD
# =========================
elif mode == "Manager Dashboard":

    st.title("📊 WorkPulse – Dashboard")

    if not os.path.exists(file):
        st.warning("No data yet")
    else:
        df = pd.read_csv(file)

        # 🔍 SEARCH BAR
        search = st.text_input("🔍 Search (User / Task / Client / Comments)")

        if search:
            df = df[
                df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
            ]

        st.dataframe(df, use_container_width=True)

        # =========================
        # ✏️ EDIT / DELETE
        # =========================
        st.subheader("✏️ Edit / Delete")

        if not df.empty:

            selected_index = st.selectbox(
                "Select Row",
                df.index,
                format_func=lambda i: f"{df.loc[i, 'User']} | {df.loc[i, 'Task']}"
            )

            row = df.loc[selected_index]

            # 🔐 ACCESS CONTROL
            can_edit = (
                st.session_state.role == "manager" or
                row["User"] == st.session_state.username
            )

            can_delete = st.session_state.role == "manager"

            new_task = st.text_input("Task", row["Task"], disabled=not can_edit)
            new_client = st.text_input("Client", row["Client Name"], disabled=not can_edit)
            new_status = st.selectbox(
                "Status",
                ["In Progress", "Completed"],
                index=0 if row["Status"] == "In Progress" else 1,
                disabled=not can_edit
            )
            new_comments = st.text_area("Comments", row.get("Comments", ""), disabled=not can_edit)

            col1, col2 = st.columns(2)

            if col1.button("💾 Update"):
                if can_edit:
                    df.at[selected_index, "Task"] = new_task
                    df.at[selected_index, "Client Name"] = new_client
                    df.at[selected_index, "Status"] = new_status
                    df.at[selected_index, "Comments"] = new_comments

                    df.to_csv(file, index=False)
                    st.success("Updated ✅")
                    st.rerun()
                else:
                    st.error("❌ Not allowed")

            confirm = st.checkbox("Confirm Delete")

            if col2.button("🗑 Delete"):
                if can_delete and confirm:
                    df = df.drop(selected_index)
                    df.to_csv(file, index=False)
                    st.success("Deleted ✅")
                    st.rerun()
                elif not can_delete:
                    st.error("❌ Only manager can delete")

        # METRICS
        total = df["Total Time (sec)"].sum()
        active = df["Active Time (sec)"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Hours", round(total / 3600, 2))
        col2.metric("Active Hours", round(active / 3600, 2))

        if not df.empty:
            st.bar_chart(df.groupby("Task")["Active Time (sec)"].sum())

        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "report.csv"
        )
