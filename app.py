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
# UNIVERSAL SEARCH - WORKS FOR ALL SEARCH TYPES
# ────────────────────────────────────────────────
def universal_search(input_query):
    """
    Universal search that handles:
    1. Full SQL queries (SELECT * FROM patients WHERE ...)
    2. Simple keywords (john, 123)
    3. Wildcards (*, search * from patients)
    4. ID searches (id=1, 1)
    5. Date ranges (from 2026-01-01 to 2026-03-04)
    """
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = input_query.strip().lower()
        
        # 1. FULL SQL QUERY (highest priority)
        if query.startswith('select'):
            # Validate: only SELECT from patients, block dangerous operations
            if 'patients' in query and not any(danger in query for danger in ['delete', 'drop', 'update', 'insert', 'alter']):
                return pd.read_sql(input_query, conn)
        
        # 2. WILDCARD - "*" or "search * from patients" or "all"
        elif query in ['*', 'search * from patients', 'all', 'search * from patients where id=1']:
            return pd.read_sql("SELECT * FROM patients ORDER BY id DESC", conn)
        
        # 3. ID SEARCH - "id=1", "where id=1", just "1"
        elif query.isdigit() or ('id=' in query):
            id_val = None
            if query.isdigit():
                id_val = query
            elif 'id=' in query:
                id_val = query.split('id=')[1].split()[0]
            if id_val and id_val.isdigit():
                return pd.read_sql("SELECT * FROM patients WHERE id = %s ORDER BY id DESC", conn, params=(int(id_val),))
        
        # 4. DATE RANGE - "from 2026-01-01 to 2026-03-04"
        elif 'from' in query and 'to' in query and any('-' in part for part in query.split()):
            date_parts = query.replace('from', '').replace('to', '').split()
            if len(date_parts) >= 2:
                start_date = date_parts[0].strip()
                end_date = date_parts[1].strip()
                if '-' in start_date and '-' in end_date:
                    date_query = f"SELECT * FROM patients WHERE admission_date >= '{start_date}' AND admission_date <= '{end_date}' ORDER BY admission_date"
                    return pd.read_sql(date_query, conn)
        
        # 5. KEYWORD SEARCH across ALL fields (fallback)
        else:
            keyword = input_query.strip()
            param = f"%{keyword}%"
            search_query = """
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
               OR status LIKE %s
            ORDER BY id DESC
            """
            return pd.read_sql(search_query, conn, params=(param,)*11)
            
    except Exception as e:
        st.error(f"Search error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ────────────────────────────────────────────────
# STREAMLIT UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="Patient Management", layout="wide")
st.title("🏥 Medical App – Patient Management")

menu = st.sidebar.selectbox(
    "Choose Action",
    ["Create Patient", "View All Patients", "Update Patient", "Delete Patient", "🔍 Universal Search"]
)

# ── CREATE ───────────────────────────────────────
if menu == "Create Patient":
    st.subheader("➕ Add New Patient")

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

    if st.button("💾 Save New Patient", type="primary"):
        if not name.strip():
            st.error("❌ Name is required!")
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
    st.subheader("📋 All Patients")
    df = read_records()
    if df.empty:
        st.info("👥 No patients found.")
    else:
        st.dataframe(df, use_container_width=True)

# ── UPDATE ───────────────────────────────────────
elif menu == "Update Patient":
    st.subheader("✏️ Update Patient")

    patient_id_to_edit = st.number_input("Enter Patient ID to edit", min_value=1, step=1, value=1)

    patient_data = None
    if patient_id_to_edit > 0:
        patient_data = get_patient_by_id(patient_id_to_edit)

    if patient_data:
        st.info(f"🔄 Editing Patient ID: {patient_id_to_edit} – {patient_data.get('name', 'Unknown')}")

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

        if st.button("💾 Save Changes", type="primary"):
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
            st.warning(f"❌ No patient found with ID {patient_id_to_edit}")
        st.info("Enter a valid Patient ID above to start editing.")

# ── DELETE ───────────────────────────────────────
elif menu == "Delete Patient":
    st.subheader("🗑️ Delete Patient")
    id_to_delete = st.number_input("Patient ID to delete", min_value=1, step=1)
    if st.button("🗑️ Delete Patient", type="primary"):
        if id_to_delete:
            delete_record(id_to_delete)
        else:
            st.warning("❌ Enter a valid ID")

# ── UNIVERSAL SEARCH ────────────────────────────
elif menu == "🔍 Universal Search":
    st.subheader("🔍 Universal Search - ANY Search Type Works!")
    
    st.markdown("---")
    
    # Quick buttons
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
    with col_btn1:
        if st.button("⭐ All Patients", use_container_width=True):
            df = universal_search("*")
            if not df.empty:
                st.success(f"✅ Found {len(df)} patients")
                st.dataframe(df, use_container_width=True)
    with col_btn2:
        if st.button("📅 Today", use_container_width=True):
            today = date.today().isoformat()
            df = universal_search(f"DATE(admission_date) = '{today}'")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
    with col_btn3:
        if st.button("✅ Active", use_container_width=True):
            df = universal_search("Active")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
    with col_btn4:
        if st.button("🔢 By ID", use_container_width=True):
            test_id = st.number_input("Test ID", min_value=1, max_value=1000)
            df = universal_search(str(test_id))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Main search input
    st.markdown("**🔥 Enter ANY search:**")
    search_input = st.text_input(
        "SQL, keywords, id=1, *, from 2026-01-01 to 2026-03-04",
        placeholder="Examples: id=1, john, SELECT * FROM patients WHERE age>30, *"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Search Now", type="primary", use_container_width=True):
            if search_input.strip():
                with st.spinner("🔍 Searching..."):
                    df = universal_search(search_input)
                    if df.empty:
                        st.info("❌ No matching records found.")
                    else:
                        st.success(f"✅ Found {len(df)} record(s)")
                        st.dataframe(df, use_container_width=True, hide_index=False)
            else:
                st.warning("👈 Please enter search term")
    
    st.markdown("---")
    
    # Examples
    with st.expander("📚 Search Examples (Click to expand)"):
        st.markdown("""
        **🔹 Quick Searches:**
        - `*` or `search * from patients` → **All patients**
        - `1` or `id=1` → **Patient ID 1**
        - `john` → **Name contains "john"**
        
        **🔹 SQL Power:**
        - `SELECT * FROM patients WHERE id=1`
        - `SELECT * FROM patients WHERE age > 30`
        - `SELECT * FROM patients WHERE status='Active'`
        
        **🔹 Date Range:**
        - `from 2026-01-01 to 2026-03-04`
        - `SELECT * FROM patients WHERE YEAR(admission_date)=2026`
        
        **🔹 Complex:**
        - `SELECT name, phone FROM patients WHERE diagnosis LIKE '%fever%'`
        """)
