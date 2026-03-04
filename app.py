import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# ────────────────────────────────────────────────
# DATABASE CONNECTION
# ────────────────────────────────────────────────
def get_connection():
    try:
        return mysql.connector.connect(
            host=st.secrets["database"]["host"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            database=st.secrets["database"]["database"],
            port=st.secrets["database"].get("port", 3306),
            use_pure=True
        )
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None

# ────────────────────────────────────────────────
# HELPER: Get one patient by id
# ────────────────────────────────────────────────
def get_patient_by_id(patient_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        query = "SELECT * FROM patients WHERE id = %s"
        df = pd.read_sql(query, conn, params=(patient_id,))
        if df.empty:
            return None
        return df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Error fetching patient: {e}")
        return None
    finally:
        conn.close()

# ────────────────────────────────────────────────
# CREATE
# ────────────────────────────────────────────────
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
        values = (
            patient_id, name, age, gender, phone, email,
            address or None, diagnosis or None, doctor_id,
            admission_date, status
        )
        cursor.execute(query, values)
        conn.commit()
        st.success("Patient record added successfully!")
    except mysql.connector.Error as err:
        st.error(f"Error adding record: {err}")
    finally:
        conn.close()

# ────────────────────────────────────────────────
# READ
# ────────────────────────────────────────────────
def read_records():
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM patients ORDER BY id DESC", conn)
    except Exception as e:
        st.error(f"Error reading records: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ────────────────────────────────────────────────
# UPDATE
# ────────────────────────────────────────────────
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
        values = (
            patient_id, name, age, gender, phone, email,
            address or None, diagnosis or None, doctor_id,
            admission_date, status, id
        )
        cursor.execute(query, values)
        conn.commit()
        st.success(f"Patient ID {id} updated successfully!")
    except mysql.connector.Error as err:
        st.error(f"Error updating record: {err}")
    finally:
        conn.close()

# ────────────────────────────────────────────────
# DELETE
# ────────────────────────────────────────────────
def delete_record(id):
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id=%s", (id,))
        conn.commit()
        st.success(f"Record ID {id} deleted!")
    except mysql.connector.Error as err:
        st.error(f"Error deleting record: {err}")
    finally:
        conn.close()

# ────────────────────────────────────────────────
# SEARCH - FIXED VERSION
# ────────────────────────────────────────────────
def search_record(keyword):
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        # Handle wildcard search like "search * from patients"
        search_term = keyword.strip()
        if search_term.lower() == "search * from patients" or search_term == "*":
            # Return all records for wildcard search
            return pd.read_sql("SELECT * FROM patients ORDER BY id DESC", conn)
        
        # Regular search across multiple fields
        param = f"%{search_term}%"
        query = """
        SELECT * FROM patients
        WHERE patient_id LIKE %s
           OR CAST(id AS CHAR) LIKE %s
           OR name LIKE %s
           OR CAST(age AS CHAR) LIKE %s
           OR gender LIKE %s
           OR phone LIKE %s
           OR email LIKE %s
           OR address LIKE %s
           OR diagnosis LIKE %s
           OR CAST(doctor_id AS CHAR) LIKE %s
        """
        df = pd.read_sql(query, conn, params=(param, param, param, param, param, param, param, param, param, param))
        return df
    except Exception as e:
        st.error(f"Search error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ────────────────────────────────────────────────
# STREAMLIT UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="Patient Management", layout="wide")
st.title("Medical App – Patient Management")

menu = st.sidebar.selectbox(
    "Choose Action",
    ["Create Patient", "View All Patients", "Update Patient", "Delete Patient", "Search Patients"]
)

# ── CREATE ───────────────────────────────────────
if menu == "Create Patient":
    st.subheader("Add New Patient")

    col1, col2 = st.columns(2)
    with col1:
        patient_id = st.text_input("Patient ID", max_chars=20)
        name = st.text_input("Full Name*", max_chars=100)
        age = st.number_input("Age", min_value=0, max_value=150, value=30)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    with col2:
        phone = st.text_input("Phone", max_chars=15)
        email = st.text_input("Email", max_chars=100)
        doctor_id = st.number_input("Doctor ID", min_value=1, value=1)

    address = st.text_area("Address", height=80)
    diagnosis = st.text_input("Diagnosis", max_chars=255)

    col3, col4 = st.columns(2)
    with col3:
        admission_date = st.date_input("Admission Date", value=date.today())
    with col4:
        status = st.selectbox("Status", ["Active", "Discharged", "Critical"])

    if st.button("Save New Patient", type="primary"):
        if not name.strip():
            st.error("Name is required!")
        else:
            create_record(
                patient_id.strip() or None,
                name.strip(),
                age,
                gender,
                phone.strip() or None,
                email.strip() or None,
                address.strip() or None,
                diagnosis.strip() or None,
                doctor_id,
                admission_date,
                status
            )

# ── READ ─────────────────────────────────────────
elif menu == "View All Patients":
    st.subheader("All Patients")
    df = read_records()
    if df.empty:
        st.info("No patients found.")
    else:
        st.dataframe(df, use_container_width=True)

# ── UPDATE ───────────────────────────────────────
elif menu == "Update Patient":
    st.subheader("Update Patient")

    patient_id_to_edit = st.number_input("Enter Patient ID to edit", min_value=1, step=1, value=1)

    patient_data = None
    if patient_id_to_edit > 0:
        patient_data = get_patient_by_id(patient_id_to_edit)

    if patient_data:
        st.info(f"Editing Patient ID: {patient_id_to_edit} – {patient_data.get('name', 'Unknown')}")

        col1, col2 = st.columns(2)
        with col1:
            new_patient_id = st.text_input("Patient ID", value=patient_data.get('patient_id', ''), max_chars=20)
            new_name = st.text_input("Full Name*", value=patient_data.get('name', ''), max_chars=100)
            new_age = st.number_input("Age", min_value=0, max_value=150, value=int(patient_data.get('age') or 0))
            new_gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                                    index=["Male", "Female", "Other"].index(patient_data.get('gender') or "Male"))
        with col2:
            new_phone = st.text_input("Phone", value=patient_data.get('phone', ''), max_chars=15)
            new_email = st.text_input("Email", value=patient_data.get('email', ''), max_chars=100)
            new_doctor_id = st.number_input("Doctor ID", min_value=1, value=int(patient_data.get('doctor_id') or 1))

        new_address = st.text_area("Address", value=patient_data.get('address', ''), height=80)
        new_diagnosis = st.text_input("Diagnosis", value=patient_data.get('diagnosis', ''), max_chars=255)

        col3, col4 = st.columns(2)
        with col3:
            current_date = patient_data.get('admission_date')
            if isinstance(current_date, str):
                try:
                    current_date = date.fromisoformat(current_date.split(' ')[0])
                except:
                    current_date = date.today()
            new_admission_date = st.date_input("Admission Date", value=current_date or date.today())
        with col4:
            new_status = st.selectbox("Status", ["Active", "Discharged", "Critical"],
                                    index=["Active", "Discharged", "Critical"].index(patient_data.get('status') or "Active"))

        if st.button("Save Changes", type="primary"):
            update_record(
                patient_id_to_edit,
                new_patient_id.strip() or None,
                new_name.strip(),
                new_age,
                new_gender,
                new_phone.strip() or None,
                new_email.strip() or None,
                new_address.strip() or None,
                new_diagnosis.strip() or None,
                new_doctor_id,
                new_admission_date,
                new_status
            )
    else:
        if patient_id_to_edit > 0:
            st.warning(f"No patient found with ID {patient_id_to_edit}")
        st.info("Enter a valid Patient ID above to start editing.")

# ── DELETE ───────────────────────────────────────
elif menu == "Delete Patient":
    st.subheader("Delete Patient")
    id_to_delete = st.number_input("Patient ID to delete", min_value=1, step=1)
    if st.button("Delete Patient", type="primary"):
        if id_to_delete:
            delete_record(id_to_delete)
        else:
            st.warning("Enter a valid ID")

# ── SEARCH ───────────────────────────────────────
elif menu == "Search Patients":
    st.subheader("Search Patients")
    keyword = st.text_input("Search by name, patient ID, phone, email, diagnosis...")
    if keyword:
        df = search_record(keyword.strip())
        if df.empty:
            st.info("No matching records found.")
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info("Type something to search...")
