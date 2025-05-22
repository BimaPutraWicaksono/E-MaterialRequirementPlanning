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
from .models import PurchaseRequest, Carline, Section, Departement

class PurchaseRequestForm(forms.ModelForm):
    departement = forms.ModelChoiceField( 
        queryset=Departement.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Departement"
    )

    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),  # kosong dulu, nanti isi via JS
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Section"
    )

    part_order = forms.ModelMultipleChoiceField(
        queryset=Carline.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Pilih Carline",
        required=True
    )

    class Meta:
        model = PurchaseRequest
        fields = ['registered_no', 'departement', 'section', 'purchase_by', 'requested']
        widgets = {
            'registered_no': forms.TextInput(attrs={'required': True, 'class': 'form-control'}),
            'purchase_by': forms.TextInput(attrs={'required': True, 'class': 'form-control'}),
            'requested': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'departement' in self.data:
            try:
                departement_id = int(self.data.get('departement'))
                self.fields['section'].queryset = Section.objects.filter(departement_id=departement_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.departement:
            self.fields['section'].queryset = Section.objects.filter(departement=self.instance.departement)
