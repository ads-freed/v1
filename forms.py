from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, FileField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[Optional(), Length(0, 120)])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class ProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[Optional(), Length(0, 120)])
    password = PasswordField('New Password', validators=[Optional()])
    password2 = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Update Profile')

class TicketForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(1, 200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    attachment = FileField('Attachment', validators=[Optional()])
    submit = SubmitField('Create Ticket')

class TicketReplyForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    attachment = FileField('Attachment', validators=[Optional()])
    submit = SubmitField('Submit Reply')

class PrivateMessageForm(FlaskForm):
    recipient = SelectField('Recipient', coerce=int, validators=[DataRequired()])
    body = TextAreaField('Message', validators=[DataRequired()])
    attachment = FileField('Attachment', validators=[Optional()])
    submit = SubmitField('Send Message')

class UserPermissionsForm(FlaskForm):
    can_create_ticket = BooleanField('Can Create Tickets')
    can_view_ticket = BooleanField('Can View Tickets')
    can_reply_ticket = BooleanField('Can Reply Tickets')
    can_edit_ticket = BooleanField('Can Edit Tickets')
    can_delete_ticket = BooleanField('Can Delete Tickets')
    submit = SubmitField('Update Permissions')
