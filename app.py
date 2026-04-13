import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import calendar
import os

# --- 1. CONFIG ---
st.set_page_config(page_title="Smart Finance Pro", layout="wide", page_icon="💎")

TRANS_FILE = "transactions_db.csv"
GOALS_FILE = "goals_db.csv"

def load_db(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)

def save_db(df, file_path):
    df.to_csv(file_path, index=False)

# --- CUSTOM CSS (Для красоты) ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .st-emotion-cache-1r6slb0 { border-radius: 15px; border: 1px solid #e0e0e0; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #1f77b4; }
    div.stButton > button { width: 100%; border-radius: 10px; height: 3em; background-color: #1f77b4; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# --- LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>💎 Smart Finance</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            name = st.text_input("Name")
            surname = st.text_input("Surname")
            if st.button("Enter"):
                if name and surname:
                    st.session_state.user_name = f"{name} {surname}".strip()
                    st.session_state.logged_in = True
                    st.rerun()
else:
    # DATA LOADING
    all_trans = load_db(TRANS_FILE, ["User", "Date", "Type", "Category", "Amount", "Description"])
    all_goals = load_db(GOALS_FILE, ["User", "Name", "Target"])
    
    user_name = st.session_state.user_name
    df = all_trans[all_trans["User"] == user_name].copy()
    user_goals = all_goals[all_goals["User"] == user_name].copy()

    # SIDEBAR
    with st.sidebar:
        st.title("💼 Wallet")
        st.write(f"User: **{user_name}**")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        # Добавим кнопку скачивания отчета
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Excel (CSV)", csv, "report.csv", "text/csv")

    st.title(f"Hello, {user_name.split()[0]}! ✨")

    tab_dash, tab_add, tab_goals = st.tabs(["📊 Stats", "💸 New Operation", "🎯 My Goals"])

    # --- TAB: DASHBOARD ---
    with tab_dash:
        if not df.empty:
            df["Amount"] = pd.to_numeric(df["Amount"])
            # Считаем итоги
            inc = df[df["Type"] == "Income"]["Amount"].sum()
            exp = df[df["Type"] == "Expense"]["Amount"].sum()
            balance = inc - exp
            
            # Статистика за сегодня
            today_str = str(date.today())
            today_exp = df[(df["Type"] == "Expense") & (df["Date"] == today_str)]["Amount"].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("Balance", f"{balance:,.2f} €")
            m2.metric("Today's Spent", f"{today_exp:,.2f} €")
            m3.metric("Total Income", f"{inc:,.2f} €")

            st.divider()
            
            c1, c2 = st.columns([1.2, 1])
            with c1:
                # График
                view = st.radio("Show:", ["Expenses", "Income"], horizontal=True)
                t_filter = "Expense" if view == "Expenses" else "Income"
                chart_df = df[df["Type"] == t_filter]
                if not chart_df.empty:
                    fig = px.pie(chart_df, values='Amount', names='Category', hole=0.6, 
                                 color_discrete_sequence=px.colors.sequential.RdBu if t_filter == "Expense" else px.colors.sequential.Mint)
                    st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("History")
                for i, row in df.sort_index(ascending=False).head(10).iterrows():
                    with st.container(border=True):
                        col_a, col_b, col_c = st.columns([3, 2, 1])
                        sign = "🔴" if row["Type"] == "Expense" else "🟢"
                        col_a.write(f"{sign} {row['Category']}")
                        col_a.caption(f"{row['Description']}")
                        col_b.write(f"**{row['Amount']} €**")
                        if col_c.button("🗑️", key=f"del_{i}"):
                            all_trans = all_trans.drop(i)
                            save_db(all_trans, TRANS_FILE)
                            st.rerun()
        else:
            st.info("Add your first transaction to see stats!")

    # --- TAB: ADD ---
    with tab_add:
        st.subheader("Quick Add")
        t_type = st.segmented_control("Type", ["Expense", "Income"], default="Expense")
        
        # Улучшенные категории с эмодзи
        if t_type == "Income":
            cats = ["💰 Salary", "🎁 Gift", "📈 Investment", "✨ Other"]
        else:
            cats = ["🍕 Food", "🚌 Transport", "🏠 Housing", "🎬 Fun", "🛍️ Shop", "💊 Health", "✨ Other"]

        with st.container(border=True):
            col1, col2 = st.columns(2)
            d = col1.date_input("Date", date.today())
            c = col1.selectbox("Category", cats)
            a = col2.number_input("Amount (€)", min_value=0.0, step=1.0)
            desc = col2.text_input("Note (optional)")
            
            if st.button("Save Transaction", type="primary"):
                if a > 0:
                    new = pd.DataFrame([{"User": user_name, "Date": d, "Type": t_type, "Category": c, "Amount": a, "Description": desc}])
                    all_trans = pd.concat([all_trans, new], ignore_index=True)
                    save_db(all_trans, TRANS_FILE)
                    st.toast("Success!", icon="✅")
                    st.rerun()
                else:
                    st.error("Enter amount!")

    # --- TAB: GOALS ---
    with tab_goals:
        # (Оставляем твой код для целей, он и так хорош, добавим только дизайн)
        st.subheader("My Goals")
        balance = (df[df["Type"]=="Income"]["Amount"].sum() - df[df["Type"]=="Expense"]["Amount"].sum()) if not df.empty else 0
        
        with st.expander("➕ New Goal"):
            g_n = st.text_input("Goal name")
            g_s = st.number_input("Sum (€)", min_value=1.0)
            if st.button("Create"):
                new_g = pd.DataFrame([{"User": user_name, "Name": g_n, "Target": g_s}])
                all_goals = pd.concat([all_goals, new_g], ignore_index=True)
                save_db(all_goals, GOALS_FILE)
                st.rerun()

        for i, g in user_goals.iterrows():
            p = min(balance / g['Target'], 1.0) if balance > 0 else 0
            with st.container(border=True):
                ca, cb = st.columns([4, 1])
                ca.write(f"**{g['Name']}** ({g['Target']} €)")
                ca.progress(p)
                cb.write(f"{p*100:.0f}%")
                if st.button("Delete Goal", key=f"g_{i}"):
                    all_goals = all_goals.drop(i)
                    save_db(all_goals, GOALS_FILE)
                    st.rerun()
