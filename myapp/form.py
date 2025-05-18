from django import forms
from .models import ExcelFile
     
class ExcelFileForm(forms.ModelForm):
    class Meta:
        model = ExcelFile
        fields = ['file']

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select an Excel file')
        
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


# request order
from django import forms
from .models import PurchaseRequest, Carline

class PurchaseRequestForm(forms.ModelForm):
    part_order = forms.ModelMultipleChoiceField(
        queryset=Carline.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Pilih Carline",
        required=True
    )

    class Meta:
        model = PurchaseRequest
        fields = ['registered_no', 'section', 'purchase_by', 'requested']
        widgets = {
            'registered_no': forms.TextInput(attrs={'required': True}),
            'section': forms.TextInput(attrs={'required': True}),
            'purchase_by': forms.TextInput(attrs={'required': True}),
            'requested': forms.CheckboxInput(),
        }