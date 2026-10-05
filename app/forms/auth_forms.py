from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required"),
        Email(message="Please provide a valid email address", check_deliverability=False)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required")
    ])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    """User registration form."""
    name = StringField("Full Name", validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required"),
        Email(message="Please provide a valid email address", check_deliverability=False)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])
    role = SelectField("Role", choices=[
        ("Engineer", "Engineer (Operator)"),
        ("Admin", "Admin (Administrator)")
    ], default="Engineer")
    submit = SubmitField("Create Account")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError("An account with this email address already exists.")
