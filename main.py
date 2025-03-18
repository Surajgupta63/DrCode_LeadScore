import os
from flask import Flask, render_template, request, redirect, session
from openai import OpenAI
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
from flask_mail import Mail, Message

app = Flask(__name__)


## Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'  # Default DB
app.config['SQLALCHEMY_BINDS'] = {
    'db1': 'sqlite:///user.db',
    'db2': 'sqlite:///leads.db'
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.secret_key = 'DrCode'


class DefaultModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class User(db.Model):
    __bind_key__ = 'db1'  # Uses user.db
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(100), unique=True)
    password     = db.Column(db.String(8))
    lead_score   = db.Column(db.Integer, nullable=False)
    status       = db.Column(db.String(10), nullable=False)
    
    def __init__(self, name, email, password, lead_score, status):
        self.name = name
        self.email = email
        self.lead_score = lead_score
        self.status = status
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))



class LeadsDB(db.Model):
    __bind_key__        = 'db2' # Uses leads.db
    sno                 = db.Column(db.Integer, primary_key = True)
    lead_id             = db.Column(db.Integer, primary_key = True)
    name                = db.Column(db.String(25), nullable = False)
    mobile_number       = db.Column(db.Integer, nullable = False)
    email               = db.Column(db.String(100), nullable = False)
    lead_source         = db.Column(db.String(500), nullable = False)
    pages_visited       = db.Column(db.Integer, nullable = False)
    time_spent          = db.Column(db.Integer, nullable = False)
    interest_score      = db.Column(db.Integer, nullable = False)
    status              = db.Column(db.String(25), nullable = False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return (
            f"{self.name} - {self.mobile_number} - {self.email} - "
        )

with app.app_context():
    db.create_all()


## Routing Setup

@app.route('/', methods=['GET', 'POST'])
def home():

    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        ## kuch karna hai

        name     = request.form['name']
        email    = request.form['email']
        password = request.form['password']
        lead_score = 5
        status     = 'cold'
        
        try:
            new_user = User(name=name, email=email, password=password, 
                            lead_score = lead_score, status = status)
            
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')

        except:
            db.session.rollback()  # Rollback changes to avoid breaking the session
            print("Error: bhai this email is already registered.")
            return render_template('signup.html', error='Already hai try new one')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # kuch karna hai
        email    = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            user.lead_score += 10
            if user.lead_score > 0 and user.lead_score < 30:
                user.status = 'cold'

            elif user.lead_score >= 30 and user.lead_score < 70:
                user.status = 'warm'

            else:
                user.status = 'hot'
            
            db.session.commit()
            session['email']    = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error = 'Invalid!!')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if session['email']:
        user = User.query.filter_by(email = session['email']).first()
    
        all_leads = User.query.all()  
        return render_template('dashboard.html', all_leads=all_leads, user=user)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=8000)