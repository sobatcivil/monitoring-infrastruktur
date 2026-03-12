import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import os

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ConstruTrack Pro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Minimalist Navy/White Theme
st.markdown("""
    <style>
    :root {
        --primary-navy: #002B5B;
        --secondary-navy: #004080;
        --accent-blue: #0074D9;
        --success-green: #2ECC40;
        --warning-yellow: #FFDC00;
        --danger-red: #FF4136;
        --bg-white: #FFFFFF;
        --text-dark: #333333;
    }
    
    body {
        background-color: var(--bg-white);
        color: var(--text-dark);
    }
    
    .stApp {
        background-color: #f4f6f9;
    }

    .main-header {
        color: var(--primary-navy);
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        font-size: 2rem;
        border-bottom: 2px solid var(--primary-navy);
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    .navy-card {
        background-color: var(--primary-navy);
        color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stButton>button {
        background-color: var(--primary-navy);
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: var(--secondary-navy);
    }

    .progress-bar-container {
        background-color: #e0e0e0;
        border-radius: 10px;
        height: 20px;
        width: 100%;
        margin: 10px 0;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATABASE LAYER (SQLite for Demo, easily swappable for Postgres/Sheets)
# -----------------------------------------------------------------------------
DB_NAME = "construction_monitor.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Tables
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
        Email TEXT PRIMARY KEY,
        Name TEXT,
        Role TEXT,
        Password TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Projects (
        ID_Project TEXT PRIMARY KEY,
        Name TEXT,
        Location TEXT,
        Status TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Master_RAB (
        ID_RAB INTEGER PRIMARY KEY AUTOINCREMENT,
        Project_Link TEXT,
        Item_Work TEXT,
        Unit TEXT,
        Volume_Target REAL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Daily_Reports (
        ID_Report INTEGER PRIMARY KEY AUTOINCREMENT,
        RAB_Link INTEGER,
        Date TEXT,
        Volume_Actual REAL,
        Photo_URL TEXT,
        Status TEXT,
        FOREIGN KEY(RAB_Link) REFERENCES Master_RAB(ID_RAB)
    )''')
    
    # Seed Data if empty
    c.execute("SELECT count(*) FROM Users")
    if c.fetchone()[0] == 0:
        # Manager
        c.execute("INSERT INTO Users VALUES (?, ?, ?, ?)", 
                  ("manager@constru.com", "Admin Manager", "Manager", "123"))
        # Supervisor
        c.execute("INSERT INTO Users VALUES (?, ?, ?, ?)", 
                  ("supervisor@constru.com", "Site Supervisor", "Supervisor", "123"))
        
        # Projects
        c.execute("INSERT INTO Projects VALUES (?, ?, ?, ?)", 
                  ("PROJ001", "Jembatan Banjar Agung", "Banjar, Bali", "Active"))
        c.execute("INSERT INTO Projects VALUES (?, ?, ?, ?)", 
                  ("PROJ002", "Road Logistic Medco", "Papua", "Active"))
        
        # RAB Data
        c.execute("INSERT INTO Master_RAB (Project_Link, Item_Work, Unit, Volume_Target) VALUES (?, ?, ?, ?)",
                  ("PROJ001", "Pondasi Tiang", "m", 100.0))
        c.execute("INSERT INTO Master_RAB (Project_Link, Item_Work, Unit, Volume_Target) VALUES (?, ?, ?, ?)",
                  ("PROJ001", "Struktur Atas", "m3", 50.0))
        c.execute("INSERT INTO Master_RAB (Project_Link, Item_Work, Unit, Volume_Target) VALUES (?, ?, ?, ?)",
                  ("PROJ002", "Aspal Hotmix", "m2", 1000.0))
        
        # Dummy Reports
        c.execute("INSERT INTO Daily_Reports (RAB_Link, Date, Volume_Actual, Photo_URL, Status) VALUES (?, ?, ?, ?, ?)",
                  (1, "2023-10-01", 20.0, "https://via.placeholder.com/150", "Approved"))
        c.execute("INSERT INTO Daily_Reports (RAB_Link, Date, Volume_Actual, Photo_URL, Status) VALUES (?, ?, ?, ?, ?)",
                  (1, "2023-10-02", 15.0, "https://via.placeholder.com/150", "Pending"))
        
        conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION & SESSION STATE
# -----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM Users WHERE Email = ? AND Password = ?", (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Login'

# -----------------------------------------------------------------------------
# 4. UI COMPONENTS
# -----------------------------------------------------------------------------
def render_login():
    st.markdown("<h1 class='main-header'>ConstruTrack Pro</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Secure Login")
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login"):
            user = check_login(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user'] = dict(user)
                st.session_state['page'] = 'Dashboard'
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Credentials")

def render_dashboard():
    user = st.session_state['user']
    st.markdown(f"<h1 class='main-header'>Welcome, {user['Name']} ({user['Role']})</h1>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    projects = pd.read_sql("SELECT * FROM Projects", conn)
    conn.close()
    
    st.subheader("Active Projects")
    cols = st.columns(len(projects))
    
    for i, row in projects.iterrows():
        with cols[i]:
            # Calculate Progress for this project
            rab_df = pd.read_sql(f"SELECT * FROM Master_RAB WHERE Project_Link = '{row['ID_Project']}'", conn)
            report_df = pd.read_sql(f"""
                SELECT SUM(dr.Volume_Actual) as total_approved 
                FROM Daily_Reports dr 
                JOIN Master_RAB mr ON dr.RAB_Link = mr.ID_RAB 
                WHERE mr.Project_Link = '{row['ID_Project']}' AND dr.Status = 'Approved'
            """, conn)
            
            total_target = rab_df['Volume_Target'].sum()
            total_approved = report_df['total_approved'].iloc[0] if not report_df.empty else 0
            
            progress = (total_approved / total_target * 100) if total_target > 0 else 0
            
            # Color Logic
            if progress < 90: color = "var(--warning-yellow)"
            elif progress < 100: color = "var(--accent-blue)"
            else: color = "var(--success-green)"
            
            st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; border-left: 5px solid {color}; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h3>{row['Name']}</h3>
                    <p><strong>Location:</strong> {row['Location']}</p>
                    <p><strong>Status:</strong> {row['Status']}</p>
                    <div style="font-size: 1.2rem; font-weight:bold; color:{color}">{progress:.1f}% Complete</div>
                    <button onclick="window.location.href='/ProjectView?proj={row['ID_Project']}'" style="background:none; border:none; color:var(--primary-navy); cursor:pointer; text-decoration:underline;">View Details</button>
                </div>
            """, unsafe_allow_html=True)

def render_project_view(proj_id):
    conn = get_db_connection()
    
    # Project Info
    p_info = pd.read_sql(f"SELECT * FROM Projects WHERE ID_Project = '{proj_id}'", conn)
    if p_info.empty:
        st.error("Project not found")
        return
    p_row = p_info.iloc[0]
    
    st.markdown(f"<h1 class='main-header'>{p_row['Name']}</h1>", unsafe_allow_html=True)
    
    # RAB vs Actual Calculation
    rab_df = pd.read_sql(f"SELECT * FROM Master_RAB WHERE Project_Link = '{proj_id}'", conn)
    
    # Calculate Approved Volume per Item
    report_df = pd.read_sql(f"""
        SELECT dr.RAB_Link, SUM(dr.Volume_Actual) as vol
        FROM Daily_Reports dr 
        WHERE dr.Status = 'Approved'
        GROUP BY dr.RAB_Link
    """, conn)
    
    # Merge RAB with Approved Volume
    merged_df = pd.merge(rab_df, report_df, left_on='ID_RAB', right_on='RAB_Link', how='left')
    merged_df['Volume_Actual'] = merged_df['vol'].fillna(0)
    merged_df['Progress'] = (merged_df['Volume_Actual'] / merged_df['Volume_Target'] * 100).round(2)
    
    st.subheader("Progress Monitoring")
    
    for idx, row in merged_df.iterrows():
        progress = row['Progress']
        if progress < 90: color = "var(--warning-yellow)"
        elif progress < 100: color = "var(--accent-blue)"
        else: color = "var(--success-green)"
        
        st.markdown(f"""
            <div style="background:white; padding:15px; margin-bottom:10px; border-radius:8px; border:1px solid #ddd;">
                <div style="display:flex; justify-content:space-between;">
                    <strong>{row['Item_Work']}</strong>
                    <span style="color:{color}; font-weight:bold;">{progress}%</span>
                </div>
                <div class="progress-bar-container">
                    <div style="background-color:{color}; height:100%; width:{progress}%; border-radius:10px; transition: width 0.5s;"></div>
                </div>
                <small>Target: {row['Volume_Target']} {row['Unit']} | Actual: {row['Volume_Actual']} {row['Unit']}</small>
            </div>
        """, unsafe_allow_html=True)
    
    # Navigation
    if st.button("Back to Dashboard"):
        st.session_state['page'] = 'Dashboard'
        st.rerun()

def render_daily_report():
    st.markdown("<h1 class='main-header'>Submit Daily Report</h1>", unsafe_allow_html=True)
    
    if st.session_state['user']['Role'] != 'Supervisor':
        st.warning("Only Supervisors can submit reports.")
        return

    conn = get_db_connection()
    projects = pd.read_sql("SELECT * FROM Projects", conn)
    rab_df = pd.read_sql("SELECT * FROM Master_RAB", conn)
    
    project_id = st.selectbox("Select Project", projects['ID_Project'].tolist())
    
    # Filter RAB for selected project
    project_rab = rab_df[rab_df['Project_Link'] == project_id]
    item_work = st.selectbox("Select Work Item", project_rab['Item_Work'].tolist())
    
    # Get ID_RAB for the selected item
    selected_rab_id = project_rab[project_rab['Item_Work'] == item_work]['ID_RAB'].iloc[0]
    
    volume = st.number_input("Volume Actual", min_value=0.0, step=0.1)
    photo_url = st.text_input("Photo URL (Optional)", value="https://via.placeholder.com/150")
    date = st.date_input("Date", datetime.now())
    
    if st.button("Submit Report"):
        c = conn.cursor()
        c.execute("INSERT INTO Daily_Reports (RAB_Link, Date, Volume_Actual, Photo_URL, Status) VALUES (?, ?, ?, ?, ?)",
                  (selected_rab_id, str(date), volume, photo_url, "Pending"))
        conn.commit()
        conn.close()
        st.success("Report Submitted for Approval!")
        st.rerun()

def render_manager_approval():
    st.markdown("<h1 class='main-header'>Manager Approval Dashboard</h1>", unsafe_allow_html=True)
    
    if st.session_state['user']['Role'] != 'Manager':
        st.error("Access Denied. Manager Role Required.")
        return

    conn = get_db_connection()
    
    # Query Pending Reports with RAB Details
    query = """
        SELECT dr.ID_Report, dr.Date, dr.Volume_Actual, dr.Photo_URL, dr.Status, 
               mr.Item_Work, mr.Unit, mr.Project_Link, p.Name as Project_Name
        FROM Daily_Reports dr
        JOIN Master_RAB mr ON dr.RAB_Link = mr.ID_RAB
        JOIN Projects p ON mr.Project_Link = p.ID_Project
        WHERE dr.Status = 'Pending'
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        st.info("No pending reports to approve.")
    else:
        for idx, row in df.iterrows():
            with st.expander(f"Report #{row['ID_Report']} - {row['Project_Name']} ({row['Item_Work']})"):
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.metric("Date", row['Date'])
                    st.metric("Volume", f"{row['Volume_Actual']} {row['Unit']}")
                with col2:
                    st.image(row['Photo_URL'], width=150)
                with col3:
                    c1, c2 = st.columns(2)
                    if c1.button("Approve", key=f"app_{row['ID_Report']}"):
                        conn = get_db_connection()
                        conn.execute("UPDATE Daily_Reports SET Status = 'Approved' WHERE ID_Report = ?", (row['ID_Report'],))
                        conn.commit()
                        conn.close()
                        st.success("Approved!")
                        st.rerun()
                    if c2.button("Reject", key=f"rej_{row['ID_Report']}"):
                        conn = get_db_connection()
                        conn.execute("UPDATE Daily_Reports SET Status = 'Rejected' WHERE ID_Report = ?", (row['ID_Report'],))
                        conn.commit()
                        conn.close()
                        st.error("Rejected!")
                        st.rerun()

# -----------------------------------------------------------------------------
# 5. MAIN APP LOGIC
# -----------------------------------------------------------------------------
def main():
    init_db()
    init_session_state()
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("ConstruTrack")
        if st.session_state['logged_in']:
            st.write(f"**{st.session_state['user']['Name']}**")
            st.write(f"**Role:** {st.session_state['user']['Role']}")
            st.divider()
            if st.button("Logout"):
                st.session_state['logged_in'] = False
                st.session_state['user'] =
