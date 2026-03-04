import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# ────────────────────────────────────────────────
# CONFIG (run once)
# ────────────────────────────────────────────────
st.set_page_config(page_title="Patient Management", layout="wide")

# Test if basic Streamlit works
st.title("Medical App – Patient Management")
st.caption("If you see this title → Streamlit basics are working. Issue is likely DB/secrets or later code.")

# ────────────────────────────────────────────────
# CONNECTION (only one definition!)
# ────────────────────────────────────────────────
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["database"]["host"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            database=st.secrets["database"]["database"],
            port=st.secrets["database"].get("port", 3306),
            use_pure=True
        )
        return conn
    except Exception as err:  # broader catch to show real error
        st.error(f"Connection failed: {str(err)}")
        return None

# ────────────────────────────────────────────────
# DEBUG INFO (safe to run early - shows secrets structure without exposing values)
# ────────────────────────────────────────────────
with st.expander("🔍 Debug – Connection & Secrets Check (click to expand)"):
    st.caption("Remove or comment this block once app is stable.")
    try:
        if "database" in st.secrets:
            db_section = st.secrets["database"]
            st.write("Secrets structure looks OK (keys exist)")
            st.write("Database name from secrets:", db_section.get("database", "MISSING"))
            st.write("Host from secrets:", db_section.get("host", "MISSING"))
        else:
            st.error("No 'database' section found in secrets.toml / Cloud secrets!")

        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            st.success(f"Actually connected to: **{current_db}**")

            cursor.execute("SHOW TABLES LIKE 'patients'")
            if cursor.fetchone():
                st.success("Table 'patients' exists")
                count_df = pd.read_sql("SELECT COUNT(*) AS cnt FROM patients", conn)
                st.write(f"Rows in patients table: **{count_df['cnt'].iloc[0]}**")
            else:
                st.warning("Table 'patients' does NOT exist in this database")

            cursor.execute("SHOW TABLES")
            tables = [r[0] for r in cursor.fetchall()]
            st.write("All tables:", tables or "None found")

            conn.close()
        else:
            st.error("Could not connect – check secrets values (host/user/pass/db/port)")
    except Exception as e:
        st.error(f"Debug failed: {str(e)}")

# ────────────────────────────────────────────────
# CRUD FUNCTIONS (only after connection & debug)
# ────────────────────────────────────────────────
def get_patient_by_id(patient_id):
    conn = get_connection()
    if not conn: return None
    try:
        df = pd.read_sql("SELECT * FROM patients WHERE id = %s", conn, params=(patient_id,))
        return df.iloc[0].to_dict() if not df.empty else None
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return None
    finally:
        conn.close()

def create_record(patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status):
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO patients (patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status))
        conn.commit()
        st.success("Record created!")
    except Exception as e:
        st.error(f"Create failed: {e}")
    finally:
        conn.close()

# (add read_records, update_record, delete_record, search_record the same way – I kept them minimal here)

def read_records():
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM patients ORDER BY id DESC", conn)
    except:
        return pd.DataFrame()
    finally:
        conn.close()

# ... paste your update_record, delete_record, search_record here (same as before, no changes needed) ...

# ────────────────────────────────────────────────
# MAIN UI
# ────────────────────────────────────────────────
menu = st.sidebar.selectbox(
    "Choose Action",
    ["Create Patient", "View All Patients", "Update Patient", "Delete Patient", "Search Patients"]
)

# Your if-elif blocks for each menu option go here (copy-paste from your original code)
# Example for View All:
if menu == "View All Patients":
    st.subheader("All Patients")
    df = read_records()
    if df.empty:
        st.info("No patients found (or table empty / missing)")
    else:
        st.dataframe(df, use_container_width=True)

# ... rest of your menu logic ...
