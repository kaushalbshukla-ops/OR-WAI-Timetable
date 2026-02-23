import streamlit as st
import pandas as pd
import glob
import random

st.set_page_config(page_title="IIM Ranchi - OR Timetable Portal", page_icon="🏫", layout="centered")

# --- 1. Automated Data Processing ---
@st.cache_data
def process_data():
    all_files = glob.glob("*.csv")
    student_records = []
    course_info = {}
    
    for file in all_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            faculty, subject, header_idx = "Unknown", "Unknown", -1
            
            # Extract Faculty and Subject dynamically from the first few rows
            for i, line in enumerate(lines[:10]):
                if "Faculty Name" in line:
                    parts = line.split(',')
                    if len(parts) > 1 and parts[1].strip():
                        faculty = parts[1].strip()
                if "Student ID" in line and "Student Name" in line:
                    header_idx = i
                    break
            
            for i in range(max(0, header_idx)):
                if "Faculty Name" not in lines[i] and "Group Mail ID" not in lines[i]:
                    potential_subj = lines[i].split(',')[0].strip()
                    if potential_subj and potential_subj != "SN":
                        subject = potential_subj
            
            if subject == "Unknown": subject = file.split('.')[0]
            course_info[subject] = faculty
            
            # Map students to subjects
            if header_idx != -1:
                df = pd.read_csv(file, skiprows=header_idx)
                df.columns = df.columns.str.strip()
                if 'Student ID' in df.columns and 'Student Name' in df.columns:
                    for _, row in df.iterrows():
                        student_records.append({
                            'Student ID': str(row['Student ID']).strip().upper(),
                            'Student Name': str(row['Student Name']).strip(),
                            'Subject': subject
                        })
        except Exception:
            pass # Skip invalid files safely
            
    return pd.DataFrame(student_records), course_info

# --- 2. Timetable Generation ---
@st.cache_data
def generate_timetable(course_info):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    slots = ['09:00 AM - 10:30 AM', '11:00 AM - 12:30 PM', '02:00 PM - 03:30 PM', '04:00 PM - 05:30 PM']
    
    timetable = []
    all_subjects = list(course_info.keys())
    idx = 0
    
    # Automated clash-free distribution across the week
    for day in days:
        for slot in slots:
            if idx < len(all_subjects):
                subj = all_subjects[idx]
                timetable.append({
                    'Subject': subj,
                    'Faculty Name': course_info[subj],
                    'Day': day,
                    'Time Slot': slot,
                    'Room': f'CR-{random.randint(1, 8)}'
                })
                idx += 1
                
    return pd.DataFrame(timetable)

# --- Initialize System ---
student_df, course_info = process_data()
if not student_df.empty:
    master_schedule = generate_timetable(course_info)

# --- 3. UI and Login System ---
st.title("📚 Weekly Timetable Portal")
st.markdown("Welcome. Please log in with your credentials to view your personalized schedule.")

if student_df.empty:
    st.warning("System Setup: Please upload the course CSV files to the GitHub repository to activate the system.")
else:
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("First Name (e.g., Aakriti)")
        with col2:
            student_id = st.text_input("Roll Number (e.g., H001-24)")
        submit_button = st.form_submit_button("Access Timetable")

    if submit_button:
        if student_name and student_id:
            # Case-insensitive partial matching for easy login
            user_data = student_df[
                (student_df['Student ID'].str.contains(student_id, case=False, na=False)) & 
                (student_df['Student Name'].str.contains(student_name, case=False, na=False))
            ]
            
            if not user_data.empty:
                st.balloons()
                full_name = user_data.iloc[0]['Student Name']
                st.success(f"Login Successful! Welcome, {full_name}.")
                
                enrolled_subjects = user_data['Subject'].tolist()
                personal_schedule = master_schedule[master_schedule['Subject'].isin(enrolled_subjects)]
                
                st.subheader("🗓️ Your Weekly Schedule")
                
                # Create a visual calendar grid
                calendar_view = personal_schedule.pivot(index='Time Slot', columns='Day', values='Subject')
                calendar_view = calendar_view.fillna("---")
                
                # Ensure days are in correct order if present
                day_order = [d for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] if d in calendar_view.columns]
                st.dataframe(calendar_view[day_order], use_container_width=True)
                
                st.subheader("👨‍🏫 Course Details & Faculty")
                st.table(personal_schedule[['Subject', 'Faculty Name', 'Day', 'Time Slot', 'Room']].reset_index(drop=True))
                
            else:
                st.error("Credentials not found. Please verify your Name and Roll Number.")
        else:
            st.warning("Please enter both Name and Roll Number.")
