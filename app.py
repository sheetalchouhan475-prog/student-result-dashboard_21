import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Result Analysis", layout="wide")

st.markdown(
    "<h1 style='text-align:center;'>Result Analysis</h1>",
    unsafe_allow_html=True
)

uploaded_files = st.file_uploader(
    "Upload RGPV Marksheets",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    student_rows = []

    for pdf_file in uploaded_files:

        text = ""

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        roll_match = re.search(r'Roll No\.\s*([A-Z0-9]+)', text)
        course_match = re.search(r'Course\s+([A-Za-z\. ]+)', text)
        branch_match = re.search(r'Branch\s+([A-Z& ]+)', text)
        semester_match = re.search(r'Semester\s+(\d+)', text)
        name_match = re.search(r'Name\s+(.*?)\s+Roll\s+No', text, re.DOTALL)

        name = (
            " ".join(name_match.group(1).split())
            if name_match
            else pdf_file.name.replace(".pdf", "")
        )

        roll = roll_match.group(1).strip() if roll_match else "N/A"
        course = course_match.group(1).strip() if course_match else "N/A"
        branch = branch_match.group(1).strip() if branch_match else "N/A"
        semester = semester_match.group(1).strip() if semester_match else "N/A"

        theory_count = 0
        practical_count = 0

        row = {
            "Name": name,
            "Roll No": roll,
            "Course": course,
            "Branch": branch,
            "Semester": semester
        }

        lines = text.split("\n")

        for line in lines:
            match = re.search(
                r'([A-Z]{2,4}\d{2,4})\s*-\s*(T|P).*?(A\+|A|B\+|B|C\+|C|D|F)',
                line
            )

            if match:
                subject_code = match.group(1)
                paper_type = match.group(2)
                grade = match.group(3).replace(" ", "")

                subject_name = f"{subject_code}-[{paper_type}]"
                row[subject_name] = grade

                if paper_type == "T":
                    theory_count += 1
                else:
                    practical_count += 1

        row["No of Theory Papers"] = theory_count
        row["No of Practical Papers"] = practical_count

        student_rows.append(row)

    final_df = pd.DataFrame(student_rows)

    base_cols = [
        "Name",
        "Roll No",
        "Course",
        "Branch",
        "Semester",
        "No of Theory Papers",
        "No of Practical Papers"
    ]

    subject_cols = [c for c in final_df.columns if c not in base_cols]

    final_df = final_df[base_cols + sorted(subject_cols)]

    # ---------------- HEADER ----------------
    course_name = final_df["Course"].iloc[0] if "Course" in final_df.columns else "N/A"
    branch_name = final_df["Branch"].iloc[0] if "Branch" in final_df.columns else "N/A"
    semester_no = final_df["Semester"].iloc[0] if "Semester" in final_df.columns else "N/A"

    st.markdown(
        f"""
        <h3 style='text-align:center; color:blue;'>
        Course: {course_name} | Branch: {branch_name} | Semester: {semester_no}
        </h3>
        """,
        unsafe_allow_html=True
    )

    st.success(f"{len(uploaded_files)} Marksheets Processed Successfully")

    # ---------------- SUMMARY ----------------
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 Summary")
        st.metric("No. of Students", len(final_df))
        st.metric("Theory Papers", final_df["No of Theory Papers"].sum())
        st.metric("Practical Papers", final_df["No of Practical Papers"].sum())

    with col2:
        st.subheader("📈 Theory Subject Performance")

        theory_subjects = [col for col in subject_cols if col.endswith("-[T]")]

        grade_points = {
            "A+": 10, "A": 9, "B+": 8, "B": 7,
            "C+": 6, "C": 5, "D": 4, "F": 0
        }

        subject_scores = {}

        for subject in theory_subjects:
            grades = final_df[subject].dropna()

            scores = [
                grade_points[str(g).strip()]
                for g in grades
                if str(g).strip() in grade_points
            ]

            if scores:
                subject_scores[subject] = sum(scores) / len(scores)

        if subject_scores:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(subject_scores.keys(), subject_scores.values())
            plt.xticks(rotation=45)
            st.pyplot(fig)

    # ---------------- TABLE ----------------
    st.subheader("Student Result Table")
    st.dataframe(final_df, use_container_width=True)

    # ================= 4 PIE CHARTS =================
    st.subheader("📊 Individual Theory Subject Pie Charts")

    theory_subjects = [col for col in subject_cols if col.endswith("-[T]")]

    selected_subjects = theory_subjects[:4]   # first 4 subjects

    cols = st.columns(4)

    for i, subject in enumerate(selected_subjects):

        with cols[i]:

            st.caption(subject)

            grades = final_df[subject].dropna()

            if len(grades) > 0:

                grade_counts = grades.value_counts()

                fig, ax = plt.subplots(figsize=(3, 3))

                ax.pie(
                    grade_counts.values,
                    labels=grade_counts.index,
                    autopct="%
