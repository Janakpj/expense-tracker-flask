import psycopg2
from datetime import date, datetime
import calendar
from flask import Flask, render_template, redirect, url_for, request, flash
import os


app = Flask(__name__)
app.secret_key = "some_secret_key"


# ---------------- DB CONNECTION ----------------
def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        port=os.environ["DB_PORT"]
    )
# ---------------- CREATE TABLES ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS addinc(
            id SERIAL PRIMARY KEY,
            fin_date DATE NOT NULL,
            income INTEGER NOT NULL,
            extra VARCHAR(100)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_table(
            id SERIAL PRIMARY KEY,
            exp_date DATE NOT NULL,
            exp_amt INTEGER NOT NULL,
            exp_cat VARCHAR(100) 
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

@app.before_first_request
def setup_database():
    init_db()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template('home.html')

# ---------------- ADD INCOME ----------------

@app.route("/add_income", methods=["GET","POST"])
def add_income():
    if request.method == "POST":
        fin_date = request.form.get("fin_date")
        income = request.form.get("income")
        extra = request.form.get("extra")

        if not fin_date or not income:
            flash("Date and Amount are required", "error")
            return redirect(url_for("add_income"))

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO addinc (fin_date, income, extra) VALUES (%s, %s, %s)",
            (fin_date, income, extra)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Income added successfully!", "success")
        return redirect(url_for("add_income"))  # or summary page

        # GET request → just show the form
    return render_template("add_income.html")

# ---------------- ADD EXPENSE ----------------
@app.route("/add_expense", methods=["GET","POST"])
def add_expense():
    if request.method == "POST":
        exp_date = request.form.get("exp_date")
        exp_amt = request.form.get("exp_amt")
        exp_cat = request.form.get("exp_cat")

        if not exp_date or not exp_amt:
            flash("Date and Amount are required", "error")
            return redirect(url_for("add_expense"))
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expense_table (exp_date, exp_amt, exp_cat) VALUES (%s, %s, %s)",
            (exp_date, exp_amt, exp_cat)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Expense added successfully!", "success")
        return redirect(url_for("add_expense"))  # or summary page

    # GET request → just show the form
    return render_template("add_expense.html")
from datetime import date
import calendar

@app.route("/view_smry", methods=["GET", "POST"])
def view_smry():
    if request.method == "POST":
        month_input = request.form.get("selected_month")

        if not month_input:
            return render_template(
                "view_smry.html",
                income=None, expense=None, balance=None
            )

        year, month = map(int, month_input.split("-"))

        start_date = date(year, month, 1)
        end_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, end_day)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT COALESCE(SUM(income), 0)
            FROM addinc
            WHERE fin_date BETWEEN %s AND %s
        """, (start_date, end_date))
        income = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(exp_amt), 0)
            FROM expense_table
            WHERE exp_date BETWEEN %s AND %s
        """, (start_date, end_date))
        expense = cur.fetchone()[0]

        cur.close()
        conn.close()

        balance = income - expense

        return render_template(
            "view_smry.html",
            income=income,
            expense=expense,
            balance=balance
        )

    return render_template(
        "view_smry.html",
        income=None, expense=None, balance=None
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

