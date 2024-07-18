# Python Flask Application development
# Creating a project and virtual environment using visual studio code and installing the required packages

# Import required packages

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
)  # pip install flask
from flask_sqlalchemy import SQLAlchemy  # pip install flask_sqlalchemy
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import pandas as pd
import logging

pymysql.install_as_MySQLdb()

# Initialize the app
app = Flask(__name__, template_folder="templates")
app.secret_key = "super secret key"

ENV = "dev"

if ENV == "dev":
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql://root:1504mysqlrp7%40%23@localhost:3306/loan_approval_pred"
    )
else:
    app.debug = False
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql://root:1504mysqlrp7%40%23@localhost:3306/loan_approval_pred_prod"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(1420), nullable=False)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = username
            return redirect(url_for("enter_details"))
        else:
            return "Invalid username or password"
    return render_template("login.html")


# Load the model at the start of your application
with open("random_forest_model.pkl", "rb") as f:
    model = pickle.load(f)


import logging


@app.route("/predict", methods=["POST"])
def predict():
    if "username" not in session:
        return redirect(url_for("login"))

    form_data = request.form
    data = {}

    # Convert fields to numerical values
    data["gender"] = 0 if form_data["gender"] == "Male" else 1
    data["married"] = 1 if form_data["married"] == "Yes" else 0
    data["education"] = 1 if form_data["education"] == "Graduate" else 0
    data["self_employed"] = 1 if form_data["self_employed"] == "Yes" else 0

    if form_data["property_area"] == "Rural":
        data["property_area"] = 0
    elif form_data["property_area"] == "Semiurban":
        data["property_area"] = 1
    else:
        data["property_area"] = 2

    # Include the other features
    data["dependents"] = float(form_data["dependents"])
    data["applicant_income"] = float(form_data["applicant_income"])
    data["coapplicant_income"] = float(form_data["coapplicant_income"])
    data["loan_amount"] = float(form_data["loan_amount"])
    data["loan_amount_term"] = float(form_data["loan_amount_term"])
    data["credit_history"] = float(form_data["credit_history"])

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(data, index=[0])

    # Log the DataFrame
    app.logger.info("DataFrame:\n%s", df)

    # Make a prediction
    prediction = model.predict(df)

    # Log the prediction
    app.logger.info("Prediction: %s", prediction)

    # Return the prediction only on successful /enter_details submission
    return render_template("predict.html", prediction=prediction, submitted=True)


@app.route("/enter_details", methods=["GET", "POST"])
def enter_details():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("predict.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
