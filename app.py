import streamlit as st
import mysql.connector
import pandas as pd
import os

# ------------------ SSL FILE PATH ------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ssl_path = os.path.join(BASE_DIR, "isrgrootx1.pem")

# ------------------ DATABASE CONNECTION ------------------

import streamlit as st
import mysql.connector
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ssl_path = os.path.join(BASE_DIR, "isrgrootx1.pem")

def get_connection():
    return mysql.connector.connect(
        host=st.secrets["database"]["host"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        database=st.secrets["database"]["database"],
        port=st.secrets["database"]["port"],
        ssl_ca=ssl_path,
        ssl_verify_cert=True,
        # ssl_verify_identity=True   ← REMOVE or comment this line
    )
# ------------------ CREATE ------------------

def create_record(name, age, address):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (name, age, address) VALUES (%s, %s, %s)",
        (name, age, address)
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

def update_record(id, name, age, address):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE patients SET name=%s, age=%s, address=%s WHERE id=%s",
        (name, age, address, id)
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
        WHERE name LIKE %s OR address LIKE %s
    """
    df = pd.read_sql(
        query,
        conn,
        params=(f"%{keyword}%", f"%{keyword}%")
    )
    conn.close()
    return df

# ------------------ UI ------------------

st.title("Medical App - Patient CRUD")

menu = st.sidebar.selectbox(
    "Menu", ["Create", "Read", "Update", "Delete", "Search"]
)

# CREATE
if menu == "Create":
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=1)
    address = st.text_input("Address")

    if st.button("Save"):
        create_record(name, age, address)
        st.success("Record Added Successfully")

# READ
elif menu == "Read":
    st.dataframe(read_records())

# UPDATE
elif menu == "Update":
    id = st.number_input("ID", min_value=1)
    name = st.text_input("New Name")
    age = st.number_input("New Age", min_value=1)
    address = st.text_input("New Address")

    if st.button("Update"):
        update_record(id, name, age, address)
        st.success("Record Updated Successfully")

# DELETE
elif menu == "Delete":
    id = st.number_input("ID to Delete", min_value=1)

    if st.button("Delete"):
        delete_record(id)
        st.success("Record Deleted Successfully")

# SEARCH
elif menu == "Search":
    keyword = st.text_input("Search keyword")

    if st.button("Search"):
        st.dataframe(search_record(keyword))


