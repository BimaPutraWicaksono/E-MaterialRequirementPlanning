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
from .models import PurchaseRequest, Departement, Section, Carline

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['registered_no', 'departement', 'section', 'purchase_by', 'requested', 'part_order']
        widgets = {
            'registered_no': forms.TextInput(attrs={'class': 'form-control'}),
            'departement': forms.Select(attrs={'class': 'form-select', 'id': 'id_departement'}),
            'section': forms.Select(attrs={'class': 'form-select', 'id': 'id_section'}),
            'purchase_by': forms.TextInput(attrs={'class': 'form-control'}),
            'requested': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'part_order': forms.CheckboxSelectMultiple(),
        }

class PurchaseRequestEditForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['departement', 'section', 'purchase_by', 'requested', 'part_order']
        widgets = {
            'departement': forms.Select(attrs={'class': 'form-select', 'id': 'id_departement'}),
            'section': forms.Select(attrs={'class': 'form-select', 'id': 'id_section'}),
            'purchase_by': forms.TextInput(attrs={'class': 'form-control'}),
            'requested': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'part_order': forms.CheckboxSelectMultiple(),
        }

# form supplier
from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'address', 'tel_no', 'fax_no']
        
# order
from django import forms
from .models import PurchaseOrder

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['term', 'delivery', 'supplier', 'shipped_by']
        widgets = {
            'delivery': forms.DateInput(attrs={'type': 'date'}),
        }

