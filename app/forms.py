from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateTimeField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from app.models import User, Listing, Reservation

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('driver', 'Driver'), ('passenger', 'Passenger')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ListingForm(FlaskForm):
    origin = StringField('Origin', validators=[DataRequired(), Length(max=100)])
    destination = StringField('Destination', validators=[DataRequired(), Length(max=100)])
    departure_time = DateTimeField('Departure Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')
    available_seats = IntegerField('Available Seats', validators=[DataRequired(), NumberRange(min=0)]) # Existing, added NumberRange
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)]) # Existing, added NumberRange
    submit = SubmitField('Submit Listing')

class ReservationForm(FlaskForm):
    seats_reserved = IntegerField('Seats to Reserve', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Reserve Seats')
