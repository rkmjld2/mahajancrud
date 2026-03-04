import streamlit as st
import mysql.connector
import pandas as pd
import os
from datetime import date

# ------------------ SSL FILE PATH (keep if needed, otherwise remove ssl params) ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ssl_path = os.path.join(BASE_DIR, "isrgrootx1.pem")  # ← you may remove if not needed

# ------------------ DATABASE CONNECTION ------------------
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["database"]["host"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            database=st.secrets["database"]["database"],  # should be "medical_app"
            port=st.secrets["database"].get("port", 3306),
            # ssl_ca=ssl_path,          # ← comment out if still getting CA errors
            # ssl_verify_cert=True,
            use_pure=True               # recommended for Streamlit Cloud stability
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Connection failed: {err}")
        return None

# ------------------ CREATE ------------------
def create_record(patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO patients 
        (patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status)
        cursor.execute(query, values)
        conn.commit()
        st.success("Patient record added successfully!")
    except mysql.connector.Error as err:
        st.error(f"Error adding record: {err}")
    finally:
        conn.close()

# ------------------ READ ------------------
def read_records():
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM patients ORDER BY id DESC", conn)
        return df
    except Exception as e:
        st.error(f"Error reading records: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ------------------ UPDATE ------------------
def update_record(id, patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        query = """
        UPDATE patients 
        SET patient_id=%s, name=%s, age=%s, gender=%s, phone=%s, email=%s, 
            address=%s, diagnosis=%s, doctor_id=%s, admission_date=%s, status=%s
        WHERE id=%s
        """
        values = (patient_id, name, age, gender, phone, email, address, diagnosis, doctor_id, admission_date, status, id)
        cursor.execute(query, values)
        conn.commit()
        st.success(f"Patient ID {id} updated successfully!")
    except mysql.connector.Error as err:
        st.error(f"Error updating record: {err}")
    finally:
        conn.close()

# ------------------ DELETE ------------------
def delete_record(id):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id=%s", (id,))
        conn.commit()
        st.success(f"Record ID {id} deleted successfully!")
    except mysql.connector.Error as err:
        st.error(f"Error deleting record: {err}")
    finally:
        conn.close()

# ------------------ SEARCH ------------------
def search_record(keyword):
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        query = """
            SELECT * FROM patients
            WHERE name LIKE %s 
               OR patient_id LIKE %s 
               OR phone LIKE %s 
               OR email LIKE %s 
               OR address LIKE %s 
               OR diagnosis LIKE %s
        """
        params = (f"%{keyword}%",) * 6
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Search error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ------------------ UI ------------------
st.title("Medical App - Patient Management (CRUD)")

menu = st.sidebar.selectbox(
    "Menu", ["Create", "Read", "Update", "Delete", "Search"]
)

# ────────────────────────────────────────────────
# CREATE
# ────────────────────────────────────────────────
if menu == "Create":
    st.subheader("Add New Patient")

    col1, col2 = st.columns(2)
    with col1:
        patient_id = st.text_input("Patient ID", max_chars=20)
        name = st.text_input("Full Name", max_chars=100)
        age = st.number_input("Age", min_value=0, max_value=150, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    with col2:
        phone = st.text_input("Phone", max_chars=15)
        email = st.text_input("Email", max_chars=100)
        doctor_id = st.number_input("Doctor ID", min_value=1, step=1)

    address = st.text_area("Address", height=80)
    diagnosis = st.text_input("Diagnosis", max_chars=255)

    col3, col4 = st.columns(2)
    with col3:
        admission_date = st.date_input("Admission Date", value=date.today())
    with col4:
        status = st.selectbox("Status", ["Active", "Discharged", "Critical"])

    if st.button("Save Patient"):
        if not name.strip():
            st.warning("Name is required!")
        else:
            create_record(
                patient_id, name, age, gender, phone, email, address,
                diagnosis, doctor_id, admission_date, status
            )

# ────────────────────────────────────────────────
# READ
# ────────────────────────────────────────────────
elif menu == "Read":
    st.subheader("All Patients")
    df = read_records()
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No records found or connection issue.")

# ────────────────────────────────────────────────
# UPDATE
# ────────────────────────────────────────────────
elif menu == "Update":
    st.subheader("Update Patient")

    id_to_update = st.number_input("Patient ID (from database)", min_value=1, step=1)

    if id_to_update:
        # Optional: pre-fill form if you want (needs extra SELECT query)
        # For simplicity we keep it manual for now

        col1, col2 = st.columns(2)
        with col1:
            patient_id = st.text_input("New Patient ID", max_chars=20)
            name = st.text_input("New Name", max_chars=100)
            age = st.number_input("New Age", min_value=0, max_value=150, step=1)
            gender = st.selectbox("New Gender", ["Male", "Female", "Other"])
        with col2:
            phone = st.text_input("New Phone", max_chars=15)
            email = st.text_input("New Email", max_chars=100)
            doctor_id = st.number_input("New Doctor ID", min_value=1, step=1)

        address = st.text_area("New Address", height=80)
        diagnosis = st.text_input("New Diagnosis", max_chars=255)

        col3, col4 = st.columns(2)
        with col3:
            admission_date = st.date_input("New Admission Date", value=date.today())
        with col4:
            status = st.selectbox("New Status", ["Active", "Discharged", "Critical"])

        if st.button("Update Patient"):
            update_record(
                id_to_update, patient_id, name, age, gender, phone, email, address,
                diagnosis, doctor_id, admission_date, status
            )

# ────────────────────────────────────────────────
# DELETE
# ────────────────────────────────────────────────
elif menu == "Delete":
    st.subheader("Delete Patient")
    id_to_delete = st.number_input("ID to Delete", min_value=1, step=1)
    if st.button("Delete"):
        if id_to_delete:
            delete_record(id_to_delete)
        else:
            st.warning("Enter a valid ID")

# ────────────────────────────────────────────────
# SEARCH (improved to search more fields)
# ────────────────────────────────────────────────
elif menu == "Search":
    st.subheader("Search Patients")
    keyword = st.text_input("Search by name, patient_id, phone, email, address, diagnosis...")
    if st.button("Search") or keyword:
        if keyword:
            df = search_record(keyword)
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("No matching records found.")
        else:
            st.info("Enter a keyword to search")
