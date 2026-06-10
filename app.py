import streamlit as st
import pdfplumber
import pandas as pd
import re
import matplotlib.pyplot as plt
from io import BytesIO
import zipfile

st.set_page_config(page_title="Result Analysis", layout="wide")

st.markdown("<h1 style='text-align:center;'>Result Analysis</h1>", unsafe_allow_html=True)

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

        name = " ".join(name_match.group(1).split()) if name_match else pdf_file.name.replace(".pdf", "")

        row = {
            "Name": name,
            "Roll No": roll_match.group(1).strip() if roll_match else "N/A",
            "Course": course_match.group(1).strip() if course_match else "N/A",
            "Branch": branch_match.group(1).strip() if branch_match else "N/A",
            "Semester": semester_match.group(1).strip() if semester_match else "N/A",
        }

        theory_count = 0
        practical_count = 0

        for line in text.split("\n"):
            match = re.search(
                r'([A-Z]{2,4}\d{2,4})\s*-\s*\[(T|P)\].*?(A\+|A|B\+|B|C\+|C|D|F)',
                line
            )

            if match:
                subject_code = match.group(1)
                paper_type = match.group(2)
                grade = match.group(3)

                row[f"{subject_code}-[{paper_type}]"] = grade

                if paper_type == "T":
                    theory_count += 1
                else:
                    practical_count += 1

        row["No of Theory Papers"] = theory_count
        row["No of Practical Papers"] = practical_count

        student_rows.append(row)

    final_df = pd.DataFrame(student_rows)

    base_cols = [
        "Name", "Roll No", "Course", "Branch",
        "Semester", "No of Theory Papers",
        "No of Practical Papers"
    ]

    subject_cols = [c for c in final_df.columns if c not in base_cols]
    final_df = final_df[base_cols + sorted(subject_cols)]

    course_name = final_df["Course"].iloc[0]
    branch_name = final_df["Branch"].iloc[0]
    semester_no = final_df["Semester"].iloc[0]

    st.markdown(
        f"<h3 style='text-align:center;color:blue;'>Course: {course_name} | Branch: {branch_name} | Semester: {semester_no}</h3>",
        unsafe_allow_html=True
    )

    st.success(f"{len(uploaded_files)} Marksheets Processed Successfully")

    grade_points = {
        "A+": 10, "A": 9, "B+": 8, "B": 7,
        "C+": 6, "C": 5, "D": 4, "F": 0
    }

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Summary")
        st.metric("Students", len(final_df))
        st.metric("Theory Papers", final_df["No of Theory Papers"].sum())
        st.metric("Practical Papers", final_df["No of Practical Papers"].sum())

    theory_subjects = [c for c in subject_cols if c.endswith("-[T]")]

    with col2:
        subject_scores = {}

        for subject in theory_subjects:
            grades = final_df[subject].dropna()
            scores = [grade_points[g] for g in grades if g in grade_points]

            if scores:
                subject_scores[subject] = sum(scores) / len(scores)

        if subject_scores:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(subject_scores.keys(), subject_scores.values())
            plt.xticks(rotation=45)
            st.pyplot(fig)

    st.subheader("Student Result Table")
    st.dataframe(final_df, use_container_width=True)

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False)

    st.download_button(
        "Download Excel",
        excel_buffer.getvalue(),
        "RGPV_Result.xlsx"
    )

    st.subheader("Individual Theory Subject Analysis")

    for i in range(0, len(theory_subjects), 4):
        cols = st.columns(4)

        for j in range(4):
            if i + j < len(theory_subjects):
                subject = theory_subjects[i + j]

                with cols[j]:
                    grades = final_df[subject].dropna()
                    if len(grades):
                        fig, ax = plt.subplots(figsize=(4, 4))
                        counts = grades.value_counts()
                        ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
                        ax.set_title(subject)
                        st.pyplot(fig)

    theory_zip = BytesIO()
    with zipfile.ZipFile(theory_zip, "w") as z:
        for subject in theory_subjects:
            grades = final_df[subject].dropna()
            if len(grades):
                fig, ax = plt.subplots(figsize=(5, 5))
                counts = grades.value_counts()
                ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
                ax.set_title(subject)

                img = BytesIO()
                fig.savefig(img, format="png", bbox_inches="tight")
                z.writestr(f"{subject}.png", img.getvalue())
                plt.close(fig)

    st.download_button(
        "馃摜 Download All Theory Pie Charts",
        theory_zip.getvalue(),
        "Theory_Pie_Charts.zip"
    )

    practical_subjects = [c for c in subject_cols if c.endswith("-[P]")]

    st.subheader("Individual Practical Subject Analysis")

    for i in range(0, len(practical_subjects), 4):
        cols = st.columns(4)

        for j in range(4):
            if i + j < len(practical_subjects):
                subject = practical_subjects[i + j]

                with cols[j]:
                    grades = final_df[subject].dropna()
                    if len(grades):
                        fig, ax = plt.subplots(figsize=(4, 4))
                        counts = grades.value_counts()
                        ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
                        ax.set_title(subject)
                        st.pyplot(fig)

    practical_zip = BytesIO()
    with zipfile.ZipFile(practical_zip, "w") as z:
        for subject in practical_subjects:
            grades = final_df[subject].dropna()
            if len(grades):
                fig, ax = plt.subplots(figsize=(5, 5))
                counts = grades.value_counts()
                ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
                ax.set_title(subject)

                img = BytesIO()
                fig.savefig(img, format="png", bbox_inches="tight")
                z.writestr(f"{subject}.png", img.getvalue())
                plt.close(fig)

    st.download_button(
        "馃摜 Download All Practical Pie Charts",
        practical_zip.getvalue(),
        "Practical_Pie_Charts.zip"
    )

    st.subheader("Theory Subject Performance")

    theory_scores = {}
    for subject in theory_subjects:
        grades = final_df[subject].dropna()
        scores = [grade_points[g] for g in grades if g in grade_points]

        if scores:
            theory_scores[subject] = sum(scores) / len(scores)

    if theory_scores:
        best_subject = max(theory_scores, key=theory_scores.get)
        weakest_subject = min(theory_scores, key=theory_scores.get)

        c1, c2 = st.columns(2)

        with c1:
            st.success(f"Best Theory Subject: {best_subject} ({theory_scores[best_subject]:.2f})")

        with c2:
            st.error(f"Weakest Theory Subject: {weakest_subject} ({theory_scores[weakest_subject]:.2f})")

else:
    st.info("Please upload PDF marksheets")
