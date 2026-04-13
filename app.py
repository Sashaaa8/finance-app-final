import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import calendar
import os  # Для работы с файлами базы данных
 
# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Smart Finance", layout="wide", page_icon="💎")
 
# Названия файлов нашей "базы данных"
TRANS_FILE = "transactions_db.csv"
GOALS_FILE = "goals_db.csv"
 
# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (CSV) ---
def load_db(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)
 
def save_db(df, file_path):
    df.to_csv(file_path, index=False)
 
# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
    div.stButton > button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)
 
# --- 2. SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
 
# --- 3. LOGIC FUNCTIONS ---
def login():
    st.markdown("<h1 style='text-align: center;'>💎 Smart Finance Manager</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Welcome back!")
            name = st.text_input("First Name", placeholder="John")
            surname = st.text_input("Last Name", placeholder="Doe")
            if st.button("Get Started", use_container_width=True, type="primary"):
                if name and surname:
                    st.session_state.user_name = f"{name} {surname}".strip()
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Please fill in both fields.")
 
# --- 4. MAIN INTERFACE ---
if not st.session_state.logged_in:
    login()
else:
    # Загружаем ВСЕ данные из файлов
    all_transactions = load_db(TRANS_FILE, ["User", "Date", "Type", "Category", "Amount", "Description"])
    all_goals = load_db(GOALS_FILE, ["User", "Name", "Target"])
 
    # Фильтруем данные: оставляем только те, что принадлежат текущему пользователю
    user_name = st.session_state.user_name
    df = all_transactions[all_transactions["User"] == user_name].copy()
    user_goals = all_goals[all_goals["User"] == user_name].copy()
 
    # Sidebar
    with st.sidebar:
        st.title("Settings")
        st.write(f"Logged as: **{user_name}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.caption("v2.5 Database Edition")
 
    st.title(f"Hello, {user_name.split()[0]}! 👋")
 
    tab_dash, tab_add, tab_goals = st.tabs(["📊 Dashboard", "➕ Add Transaction", "🎯 Goals"])
 
    # --- TAB: DASHBOARD ---
    with tab_dash:
        if not df.empty:
            df["Amount"] = pd.to_numeric(df["Amount"])
            total_inc = df[df["Type"] == "Income"]["Amount"].sum()
            total_exp = df[df["Type"] == "Expense"]["Amount"].sum()
        else:
            total_inc, total_exp = 0.0, 0.0
 
        balance = total_inc - total_exp
 
        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Balance", f"{balance:,.2f} €")
        m2.metric("Total Income", f"{total_inc:,.2f} €")
        m3.metric("Total Expenses", f"{total_exp:,.2f} €", delta=f"-{total_exp:,.2f}", delta_color="inverse")
 
        st.write("---")
 
        if not df.empty:
            col_chart, col_table = st.columns([1.2, 1])
 
            with col_chart:
                chart_view = st.radio("View:", ["Expenses", "Income"], horizontal=True, label_visibility="collapsed")
                type_filter = "Expense" if chart_view == "Expenses" else "Income"
                chart_df = df[df["Type"] == type_filter]
 
                if not chart_df.empty:
                    color_scale = px.colors.sequential.Reds if type_filter == "Expense" else px.colors.sequential.Greens
                    fig_pie = px.pie(chart_df, values='Amount', names='Category', hole=0.5,
                                    title=f"{chart_view} by Category", color_discrete_sequence=color_scale)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info(f"No {chart_view.lower()} data yet.")
 
            with col_table:
                st.subheader("Recent Activity")
                # Показываем только данные пользователя
                display_df = df.sort_index(ascending=False)
                for index, row in display_df.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        icon = "🔴" if row["Type"] == "Expense" else "🟢"
                        c1.write(f"{icon} **{row['Category']}**")
                        c1.caption(f"{row['Date']} | {row['Description']}")
                        c2.write(f"**{row['Amount']:.2f} €**")
                       
                        # Удаление из общей базы
                        if c3.button("🗑️", key=f"del_{index}"):
                            # Удаляем строку из ВСЕЙ базы по её индексу
                            all_transactions = all_transactions.drop(index)
                            save_db(all_transactions, TRANS_FILE)
                            st.rerun()
        else:
            st.info("No transactions found.")
 
    # --- TAB: ADD TRANSACTION ---
    with tab_add:
        st.subheader("New Entry")
        t_type = st.segmented_control("Type", ["Expense", "Income"], default="Expense")
        cats = ["Salary", "Gift", "Investment", "Other"] if t_type == "Income" else \
               ["Food", "Transport", "Housing", "Entertainment", "Shopping", "Health", "Other"]
 
        with st.container(border=True):
            col_form1, col_form2 = st.columns(2)
            with col_form1:
                t_date = st.date_input("Date", date.today())
                t_cat = st.selectbox("Category", cats)
            with col_form2:
                t_amount = st.number_input("Amount (EUR)", min_value=0.0, step=10.0, format="%.2f")
                t_desc = st.text_input("Description")
 
            if st.button(f"Confirm {t_type}", use_container_width=True, type="primary"):
                if t_amount > 0:
                    # Создаем новую строку с привязкой к имени пользователя
                    new_entry = pd.DataFrame([{
                        "User": user_name,
                        "Date": t_date,
                        "Type": t_type,
                        "Category": t_cat,
                        "Amount": float(t_amount),
                        "Description": t_desc
                    }])
                    # Добавляем в общую базу и сохраняем
                    all_transactions = pd.concat([all_transactions, new_entry], ignore_index=True)
                    save_db(all_transactions, TRANS_FILE)
                    st.toast("Saved to Database!", icon="💾")
                    st.rerun()
 
    # --- TAB: GOALS ---
    with tab_goals:
        st.subheader("Savings Goals")
        today = date.today()
        days_left = calendar.monthrange(today.year, today.month)[1] - today.day + 1
        daily_limit = balance / days_left if balance > 0 else 0
 
        c1, c2 = st.columns(2)
        c1.metric("Days left in month", days_left)
        c2.metric("Daily Budget Available", f"{daily_limit:.2f} €")
 
        st.divider()
 
        with st.expander("➕ Create New Goal"):
            g_name = st.text_input("What are you saving for?")
            g_sum = st.number_input("Target Amount (€)", min_value=1.0)
            if st.button("Set Goal"):
                if g_name:
                    new_goal = pd.DataFrame([{"User": user_name, "Name": g_name, "Target": g_sum}])
                    all_goals = pd.concat([all_goals, new_goal], ignore_index=True)
                    save_db(all_goals, GOALS_FILE)
                    st.rerun()
 
        if not user_goals.empty:
            for i, goal in user_goals.iterrows():
                prog = min(balance / goal['Target'], 1.0) if (balance > 0 and goal['Target'] > 0) else 0
                with st.container(border=True):
                    gc1, gc2, gc3 = st.columns([4, 1, 0.5])
                    gc1.write(f"**{goal['Name']}**")
                    gc1.progress(prog)
                    gc2.write(f"**{prog*100:.1f}%**")
                    if gc3.button("🗑️", key=f"goal_{i}"):
                        all_goals = all_goals.drop(i)
                        save_db(all_goals, GOALS_FILE)
                        st.rerun()
                    st.caption(f"Target: {goal['Target']} €"
