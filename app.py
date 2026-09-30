from flask import Flask, render_template, request, redirect, send_file, session
import pandas as pd
import plotly.express as px
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
# Allowed columns for sorting
VALID_COLUMNS = [
    "Student_ID",
    "Student_Name",
    "Course",
    "Completion",
    "Quiz_Score"
]
app = Flask(__name__)
app.secret_key = "learning_dashboard_secret"

# ---------------- LOGIN PAGE ---------------- #

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    # Read SQLite Database

    conn = sqlite3.connect("students.db")

    original_df = pd.read_sql_query(
        "SELECT * FROM students",
        conn
    )

    conn.close()

    df = original_df.copy()

    # ---------------- SEARCH ---------------- #

    search = request.args.get("search", "")

    if search:
        df = df[
            df["Student_Name"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # ---------------- COURSE FILTER ---------------- #

    course = request.args.get("course", "All")

    if course != "All":
        df = df[df["Course"] == course]

    # ---------------- SORTING ---------------- #

    sort_by = request.args.get("sort", "Student_ID")
    order = request.args.get("order", "asc")


    if sort_by not in VALID_COLUMNS:
        sort_by = "Student_ID"

    ascending = (order == "asc")

    df = df.sort_values(

        by=sort_by,
        ascending=ascending
    )
    # ---------------- PERFORMANCE STATUS ---------------- #

    df["Status"] = "Needs Improvement"

    df.loc[df["Quiz_Score"] >= 90, "Status"] = "Excellent"

    df.loc[
        (df["Quiz_Score"] >= 75) &
        (df["Quiz_Score"] < 90),
        "Status"
    ] = "Good"

    df.loc[
        (df["Quiz_Score"] >= 60) &
        (df["Quiz_Score"] < 75),
        "Status"
    ] = "Average"

    # ---------------- DROPDOWN ---------------- #

    courses = ["All"] + sorted(
        original_df["Course"].unique().tolist()
    )

    # ---------------- KPI CARDS ---------------- #

    total_students = len(df)

    if len(df) > 0:

        avg_completion = round(
            df["Completion"].mean(),
            2
        )

        avg_score = round(
            df["Quiz_Score"].mean(),
            2
        )

        top_students = (
            df.sort_values(
                by="Quiz_Score",
                ascending=False
            )
            .head(3)
            .reset_index(drop=True)
        )

    else:

        avg_completion = 0
        avg_score = 0
        top_students = pd.DataFrame()

    # ---------------- ANALYTICS INSIGHTS ---------------- #

    if len(df) > 0:

        course_avg = (
            df.groupby("Course")["Quiz_Score"]
            .mean()
            .round(2)
        )

        best_course = course_avg.idxmax()
        best_course_score = course_avg.max()

        lowest_course = course_avg.idxmin()
        lowest_course_score = course_avg.min()

    else:

        best_course = "-"
        best_course_score = 0

        lowest_course = "-"
        lowest_course_score = 0

    # ---------------- LEADERBOARD ---------------- #

    ranking = (
        df.sort_values(
            by="Quiz_Score",
            ascending=False
        )[[
            "Student_ID",
            "Student_Name",
            "Course",
            "Quiz_Score",
            "Status"
        ]]
        .reset_index(drop=True)
    )
    ranking["Student_ID"] = pd.to_numeric(
    ranking["Student_ID"],
    errors="coerce"
    )
    ranking.index += 1
    ranking.index.name = "Rank"

    # ---------------- BAR CHART ---------------- #

    fig = px.bar(
        df,
        x="Student_Name",
        y="Quiz_Score",
        color="Quiz_Score",
        text="Quiz_Score",
        title="Student Quiz Scores"
    )

    fig.update_layout(
        template="plotly_white",
        height=500,
        title_x=0.5
    )

    chart = fig.to_html(full_html=False)

    # ---------------- PIE CHART ---------------- #

    course_count = df["Course"].value_counts()

    pie = px.pie(
        values=course_count.values,
        names=course_count.index,
        hole=0.4,
        title="Course Distribution"
    )

    pie.update_layout(
        height=500,
        title_x=0.5
    )

    course_chart = pie.to_html(full_html=False)

    # ---------------- STUDENT RECORDS ---------------- #

    # ---------------- PAGINATION ---------------- #

    page = request.args.get("page", 1, type=int)

    per_page = 10

    total_records = len(df)

    total_pages = (total_records + per_page - 1) // per_page

    start = (page - 1) * per_page

    end = start + per_page

    student_records = df.iloc[start:end]

    return render_template(
        "dashboard.html",
        total_students=total_students,
        avg_completion=avg_completion,
        avg_score=avg_score,
        best_course=best_course,
        best_course_score=best_course_score,
        lowest_course=lowest_course,
        lowest_course_score=lowest_course_score,
        top_students=top_students,
        ranking=ranking,
        student_records=student_records,
        chart=chart,
        course_chart=course_chart,
        search=search,
        courses=courses,
        selected_course=course,
        page=page,
        total_pages=total_pages,
        sort_by=sort_by,
        order=order
    )
# ---------------- ADD STUDENT ---------------- #

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "user" not in session:
        return redirect("/")
    if request.method == "POST":

        name = request.form["name"]
        course = request.form["course"]
        completion = request.form["completion"]
        score = request.form["score"]

        conn = sqlite3.connect("students.db")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT MAX(Student_ID) FROM students"
        )

        max_id = cursor.fetchone()[0]

        if max_id is None:
            new_id = 1
        else:
            new_id = max_id + 1

        cursor.execute(
        """
        INSERT INTO students
        (
            Student_ID,
            Student_Name,
            Course,
            Completion,
            Quiz_Score
        )
        VALUES (?, ?, ?, ?, ?)
        """,

        (
            new_id,
            name,
            course,
            completion,
            score
        )
    )

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template(
        "add_student.html"
    )
# ---------------- EDIT STUDENT ---------------- #

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user" not in session:
        return redirect("/")
    conn = sqlite3.connect("students.db")

    if request.method == "POST":

        name = request.form["name"]
        course = request.form["course"]
        completion = request.form["completion"]
        score = request.form["score"]

        conn.execute(
            """
            UPDATE students
            SET Student_Name=?,
                Course=?,
                Completion=?,
                Quiz_Score=?
            WHERE Student_ID=?
            """,
            (
                name,
                course,
                completion,
                score,
                id
            )
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    student = pd.read_sql_query(
        f"SELECT * FROM students WHERE Student_ID={id}",
        conn
    )

    conn.close()

    return render_template(
        "edit_student.html",
        student=student.iloc[0]
    )
# ---------------- DELETE STUDENT ---------------- #

@app.route("/delete/<int:id>")
def delete_student(id):
    if "user" not in session:
        return redirect("/")
    conn = sqlite3.connect("students.db")

    conn.execute(
        "DELETE FROM students WHERE Student_ID=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")
# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")
# ---------------- DOWNLOAD CSV ---------------- #

@app.route("/download")
def download():

    conn = sqlite3.connect("students.db")

    df = pd.read_sql_query(
        "SELECT * FROM students",
        conn
    )

    conn.close()

    search = request.args.get("search", "")

    if search:
        df = df[
            df["Student_Name"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    course = request.args.get("course", "All")
    if course != "All":
        df = df[df["Course"] == course]
    # Sorting

    sort_by = request.args.get("sort", "Student_ID")
    order = request.args.get("order", "asc")
    if sort_by not in VALID_COLUMNS:
        sort_by = "Student_ID"

    df = df.sort_values(
        by=sort_by,
        ascending=(order == "asc")
    )

    df.to_csv(
        "report.csv",
        index=False
    )

    return send_file(
        "report.csv",
        as_attachment=True
    )
@app.route("/pdf")
def pdf_report():

    conn = sqlite3.connect("students.db")

    df = pd.read_sql_query(
        "SELECT * FROM students",
        conn
    )

    conn.close()

    # Search filter
    search = request.args.get("search", "")

    if search:
        df = df[
            df["Student_Name"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # Course filter
    course = request.args.get("course", "All")
    if course != "All":
        df = df[df["Course"] == course]
    # Sorting

    sort_by = request.args.get("sort", "Student_ID")
    order = request.args.get("order", "asc")

    pdf_file = "student_report.pdf"
    pdf = SimpleDocTemplate(pdf_file)
    if sort_by not in VALID_COLUMNS:
        sort_by = "Student_ID"

    df = df.sort_values(
        by=sort_by,
        ascending=(order == "asc")
    )

    data = [df.columns.tolist()] + df.values.tolist()

    table = Table(data)

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")
        ])
    )

    pdf.build([table])

    return send_file(
        pdf_file,
        as_attachment=True
    )

    # remaining PDF code...

# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)