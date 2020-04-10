from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from app import open_dataframes


class LoginForm(FlaskForm):
    username = TextAreaField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordar usuario')
    submit = SubmitField('Sign In')


class TablesForm(FlaskForm):
    records = IntegerField('Registros ', validators=[DataRequired()])
    dataset = SelectField('dataset',choices=[("rutas.csv", "Rutas"), ("21_rutas_accel.csv", "Aceleraciones")])
    submit = SubmitField('Ver')


class VehicleMapForm(FlaskForm):
    day = SelectField(
        'Dia',
        choices=[(i, i) for i in range(1, 20)],
        coerce=int,
        validators=[DataRequired()])

    variable = SelectField('Variable')
    submit = SubmitField('Ver')


class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Por favor ingrese un usuario diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Por favor ingrese un email diferente.')