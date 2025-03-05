from django import forms
from .models import Item, ExcelFile, Machine, SealUnit

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nameDash', 'numberDash', 'levelDash', 'categoryDash', 'januaryDash', 'februaryDash', 'marchDash', 'aprilDash', 'mayDash', 'juneDash', 'julyDash', 'augustDash', 'septemberDash', 'octoberDash', 'novemberDash', 'decemberDash', 'averageDash']
       
class ExcelFileForm(forms.ModelForm):
    class Meta:
        model = ExcelFile
        fields = ['file']

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select an Excel file')

class Machine(forms.ModelForm):
    class Meta:
        model = Machine
        fields = [
             'machineNumberMachine', 'partNameMachine', 'partNumberMachine', 'levelMarkingMachine'
        ]
        
class SealUnit(forms.ModelForm):
    class Meta:
        model = SealUnit
        fields = [
           'machineNumberSealUnit', 'partNameSealUnit', 'partNumberSealUnit', 'levelMarkingSealUnit'
        ]
        
# SPP

from .models import Carline  

class CarlineForm(forms.ModelForm):
    class Meta:
        model = Carline
        fields = ['name']
        
        # Menambahkan placeholder di dalam widgets
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter carline name'}),
        }
        

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)