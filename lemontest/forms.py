from apex.forms import RegisterForm
from wtforms import validators

class LifetechEmailRegisterForm(RegisterForm):
    def validate_email(form, field):
        if not field.data.lower().endswith(u"@lifetech.com"):
            raise validators.ValidationError('You must register with a lifetech.com email address.')