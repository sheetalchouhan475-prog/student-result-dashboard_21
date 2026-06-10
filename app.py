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
                r'([A-Z]{2,4}\d{2,4})\s*-\s*\[(T|P)\].*?(A\+|A|B\+|B|C\+|C|D|F)',
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

    # ================= LEFT + RIGHT LAYOUT =================
    col1, col2 = st.columns([1, 2])

    # ---------------- LEFT SIDE ----------------
    with col1:
        st.subheader("📊 Summary")

        total_students = len(final_df)
        total_theory = final_df["No of Theory Papers"].sum()
        total_practical = final_df["No of Practical Papers"].sum()

        st.metric("No. of Students", total_students)
        st.metric("No. of Theory Papers", total_theory)
        st.metric("No. of Practical Papers", total_practical)

    # ---------------- RIGHT SIDE ----------------
    with col2:
        st.subheader("📈 Theory Subject Bar Chart")

        theory_subjects = [col for col in subject_cols if col.endswith("-[T]")]

        subject_scores = {}

        grade_points = {
            "A+": 10, "A": 9, "B+": 8, "B": 7,
            "C+": 6, "C": 5, "D": 4, "F": 0
        }

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

            ax.bar(
                subject_scores.keys(),
                subject_scores.values()
            )

            ax.set_xlabel("Subjects")
            ax.set_ylabel("Average Score")
            ax.set_title("Theory Subject Performance")
            plt.xticks(rotation=45)

            st.pyplot(fig)

    # ---------------- TABLE ----------------
    st.subheader("Student Result Table")
    st.dataframe(final_df, use_container_width=True)

    # ---------------- DOWNLOAD ----------------
    excel_buffer = BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Results")

    st.download_button(
        "Download Excel",
        excel_buffer.getvalue(),
        file_name="RGPV_Result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )# ================= PIE CHARTS OF THEORY SUBJECTS =================

st.subheader("📊 Individual Theory Subject Analysis")

theory_subjects = [
    col for col in subject_cols
    if col.endswith("-[T]")
]

# 4 pie charts per row
for i in range(0, len(theory_subjects), 4):

    cols = st.columns(4)

    for j in range(4):

        if i + j < len(theory_subjects):

            subject = theory_subjects[i + j]

            with cols[j]:

                grades = final_df[subject].dropna()

                if len(grades) > 0:

                    grade_counts = grades.value_counts()

                    fig, ax = plt.subplots(figsize=(4, 4))

                    ax.pie(
                        grade_counts.values,
                        labels=grade_counts.index,
                        autopct="%1.1f%%",
                        startangle=90
                    )

                    ax.set_title(subject)

                    st.pyplot(fig)
                
                    st.pyplot(fig)# ================= PRACTICAL SUBJECT PIE CHARTS =================

st.subheader("🧪 Individual Practical Subject Analysis")

practical_subjects = [
    col for col in subject_cols
    if col.endswith("-[P]")
]

# 4 pie charts per row
for i in range(0, len(practical_subjects), 4):

    cols = st.columns(4)

    for j in range(4):

        if i + j < len(practical_subjects):

            subject = practical_subjects[i + j]

            with cols[j]:

                grades = final_df[subject].dropna()

                if len(grades) > 0:

                    grade_counts = grades.value_counts()

                    fig, ax = plt.subplots(figsize=(4, 4))

                    ax.pie(
                        grade_counts.values,
                        labels=grade_counts.index,
                        autopct="%1.1f%%",
                        startangle=90
                    )

                    ax.set_title(subject)

                    st.pyplot(fig)
                   
else:
    st.info("Please upload PDF marksheets")
