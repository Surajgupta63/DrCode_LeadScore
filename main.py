import os
from flask import Flask, render_template, request, redirect, session
from openai import OpenAI
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
from flask_mail import Mail, Message
from chatbot import get_openai_response

app = Flask(__name__)

## Mail Setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587  # SMTP port (587 for TLS, 465 for SSL)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'dr.code63@gmail.com'
app.config['MAIL_PASSWORD'] = 'ergx aiju rgat xfii'  # App Password hai

mail = Mail(app)

def send_email(recipient, name, status):
    subject = "Bhai ab kuch kharid bhi le yrr!!"
    body = f"Hello {name},\n\n Tumhara status {status} hai! Our team will contact you soon.\n\nBest Regards,\nDrCode"
    
    msg = Message(subject, sender="dr.code63@gmail.com", recipients=[recipient])
    msg.body = body

    try:
        mail.send(msg)
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")


def check_lead_score(email, new_score):
    # Fetch the lead from DB
    lead = User.query.filter_by(email=email).first()

    if lead:
        # Check karo lead score crosses the threshold
        if new_score >= 0 and new_score < 30:
            send_email(lead.email, lead.name, 'cold')
        elif new_score >= 30 and new_score < 70:
            send_email(lead.email, lead.name, 'warm')
        else:
            send_email(lead.email, lead.name, 'hot')

        return f"Lead score updated to {new_score} for {lead.name}"
    
    return "Lead not found"



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
            db.session.rollback()  # Rollback kar do to avoid breaking the session
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
            check_lead_score(user.email, user.lead_score)
            session['email']    = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error = 'Invalid!!')

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        query = request.form['query']
        try:
            response = get_openai_response(question=query)
            print("AI ka Response: ", response)
        except Exception as e:
            print(f"Error fetching query is: {str(e)}")


    if session['email']:
        user = User.query.filter_by(email = session['email']).first()
    
        all_leads = User.query.all() 
        count = 0 
        for lead in all_leads:
            count += 1
        return render_template('dashboard.html', all_leads=all_leads, user=user, count = count)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=8000)