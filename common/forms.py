from common.models import User, Token
from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField

class RegisterForm(UserCreationForm):
    """
    This is a generic Django form tailored to the Account model.
    
    """
    class Meta:
        # The model this form creates
        model = User
        
        # The fields to display on the form, in the given order
        fields = ("username", "email")
        
        # Any overrides of field classes
        field_classes = {'username': UsernameField}
    
    # Username is collected as part of the core UserCreationForm, so we just need
    # to add a field to (optionally) capture email.
    email = forms.EmailField(help_text="A valid email address. Used for password resets and sending you renewal notices.", required=True)