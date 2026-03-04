import streamlit as st
import mysql.connector
import pandas as pd

# ------------------ SECURE CONNECTION ------------------


import os   # ✅ ADD THIS LINE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["database"]["host"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        database=st.secrets["database"]["database"],
        port=st.secrets["database"]["port"],
        ssl_ca=ssl_path,
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        tls_versions=["TLSv1.2", "TLSv1.3"]
    )
# ------------------ CREATE ------------------

def create_record(name, age, city):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (name, age, address) VALUES (%s, %s, %s)",
        (name, age, city)
    )
    conn.commit()
    conn.close()

# ------------------ READ ------------------

def read_records():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM patients", conn)
    conn.close()
    return df

# ------------------ UPDATE ------------------

def update_record(id, name, age, city):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET name=%s, age=%s, city=%s WHERE id=%s",
        (name, age, city, id)
    )
    conn.commit()
    conn.close()

# ------------------ DELETE ------------------

def delete_record(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id=%s", (id,))
    conn.commit()
    conn.close()

# ------------------ SEARCH ------------------

def search_record(keyword):
    conn = get_connection()
    query = """
        SELECT * FROM patients
        WHERE name LIKE %s OR city LIKE %s
    """
    df = pd.read_sql(query, conn,
                     params=(f"%{keyword}%", f"%{keyword}%"))
    conn.close()
    return df

# ------------------ UI ------------------

st.title("Medical App - Student CRUD")

menu = st.sidebar.selectbox(
    "Menu", ["Create", "Read", "Update", "Delete", "Search"]
)

if menu == "Create":
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=1)
    city = st.text_input("address")

    if st.button("Save"):
        create_record(name, age, address)
        st.success("Record Added")

elif menu == "Read":
    st.dataframe(read_records())

elif menu == "Update":
    id = st.number_input("ID", min_value=1)
    name = st.text_input("New Name")
    age = st.number_input("New Age", min_value=1)
    address = st.text_input("New address")

    if st.button("Update"):
        update_record(id, name, age, address)
        st.success("Record Updated")

elif menu == "Delete":
    id = st.number_input("ID to Delete", min_value=1)

    if st.button("Delete"):
        delete_record(id)
        st.success("Record Deleted")

elif menu == "Search":
    keyword = st.text_input("Search keyword")

    if st.button("Search"):

        st.dataframe(search_record(keyword))


