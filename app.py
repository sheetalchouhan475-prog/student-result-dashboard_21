import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(
    page_title="RGPV Result Analysis",
    layout="wide"
)

st.title("RGPV Result Analysis Dashboard")

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

        # -----------------------
        # Student Information
        # -----------------------

        roll_match = re.search(
            r'Roll No\.\s*([A-Z0-9]+)',
            text
        )

        course_match = re.search(
            r'Course\s+([A-Za-z\. ]+)',
            text
        )

        branch_match = re.search(
            r'Branch\s+([A-Z& ]+)',
            text
        )

        semester_match = re.search(
            r'Semester\s+(\d+)',
            text
        )

        name_match = re.search(
            r'Name\s+(.*?)\s+Roll\s+No',
            text,
            re.DOTALL
        )

        name = (
            " ".join(name_match.group(1).split())
            if name_match
            else pdf_file.name.replace(".pdf", "")
        )

        roll = roll_match.group(1).strip() if roll_match else "N/A"
        course = course_match.group(1).strip() if course_match else "N/A"
        branch = branch_match.group(1).strip() if branch_match else "N/A"
        semester = semester_match.group(1).strip() if semester_match else "N/A"

        # -----------------------
        # Subject Processing
        # -----------------------

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

    # -----------------------
    # Final DataFrame
    # -----------------------

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

    subject_cols = [
        c for c in final_df.columns
        if c not in base_cols
    ]

    final_df = final_df[
        base_cols + sorted(subject_cols)
    ]

    st.success(
        f"{len(uploaded_files)} Marksheets Processed Successfully"
    )

    st.subheader("Student Result Table")

    st.dataframe(
        final_df,
        use_container_width=True
    )

    # -----------------------
    # Excel Download
    # -----------------------

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        final_df.to_excel(
            writer,
            sheet_name="Results",
            index=False
        )

    st.download_button(
        label="Download Excel File",
        data=excel_buffer.getvalue(),
        file_name="RGPV_Final_Result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # -----------------------
    # Subject Wise Pie Chart
    # -----------------------

    st.subheader("Subject Wise Grade Analysis")

    selected_subject = st.selectbox(
        "Select Subject",
        sorted(subject_cols)
    )

    grades = final_df[selected_subject].dropna()

    if len(grades) > 0:

        grade_counts = grades.value_counts()

        fig, ax = plt.subplots(
            figsize=(7,7)
        )

        ax.pie(
            grade_counts.values,
            labels=grade_counts.index,
            autopct="%1.1f%%",
            startangle=90
        )

        ax.set_title(
            f"Grade Distribution - {selected_subject}"
        )

        st.pyplot(fig)

    # -----------------------
    # Theory Subject Analysis
    # -----------------------

    st.subheader(
        "Theory Subject Performance Analysis"
    )

    grade_points = {
        "A+": 10,
        "A": 9,
        "B+": 8,
        "B": 7,
        "C+": 6,
        "C": 5,
        "D": 4,
        "F": 0
    }

    theory_subjects = [
        col for col in subject_cols
        if col.endswith("-[T]")
    ]

    subject_performance = {}

    for subject in theory_subjects:

        grades = final_df[subject].dropna()

        scores = []

        for grade in grades:

            grade = str(grade).strip()

            if grade in grade_points:
                scores.append(
                    grade_points[grade]
                )

        if len(scores) > 0:

            subject_performance[subject] = (
                sum(scores) / len(scores)
            )

    if len(subject_performance) > 0:

        performance_df = pd.DataFrame({
            "Subject": list(
                subject_performance.keys()
            ),
            "Average Score": list(
                subject_performance.values()
            )
        })

        performance_df = performance_df.sort_values(
            by="Average Score",
            ascending=False
        )

        st.dataframe(
            performance_df,
            use_container_width=True
        )

        fig2, ax2 = plt.subplots(
            figsize=(8,8)
        )

        ax2.pie(
            performance_df["Average Score"],
            labels=performance_df["Subject"],
            autopct="%1.1f%%",
            startangle=90
        )

        ax2.set_title(
            "Theory Subject Performance"
        )

        st.pyplot(fig2)

        st.success(
            f"Best Subject: {performance_df.iloc[0]['Subject']}"
        )

        st.error(
            f"Weakest Subject: {performance_df.iloc[-1]['Subject']}"
        )
