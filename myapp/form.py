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
from .models import PurchaseRequest, LoadingPartResult

class PurchaseRequestForm(forms.ModelForm):
    part_order = forms.ModelMultipleChoiceField(
        queryset=Carline.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Carline (pilih salah satu atau beberapa)"
    )

    class Meta:
        model = PurchaseRequest
        fields = [
            'registered_no',
            'section',
            'purchase_by',
            'budget_ref_no',
            'part_order',
            'estimated_price',
            'deadline',
            'requested',
        ]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['deadline'].input_formats = ['%Y-%m-%dT%H:%M']
 