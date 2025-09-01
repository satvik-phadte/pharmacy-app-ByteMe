from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, PharmacyLocation, Medicine, Inventory, CustomerLocation

class UserRegistrationForm(UserCreationForm):
    is_pharmacy = forms.BooleanField(
        required=False,
        label="Register as Pharmacy",
        help_text="Check this box if you are registering as a pharmacy"
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'is_pharmacy')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Required. 150 characters or fewer."
        self.fields['password1'].help_text = "Your password must contain at least 8 characters."
        self.fields['password2'].help_text = "Enter the same password as before, for verification."

class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')

class PharmacyLocationForm(forms.ModelForm):
    class Meta:
        model = PharmacyLocation
        fields = ['name', 'address', 'latitude', 'longitude', 'phone']
        widgets = {
            'latitude': forms.NumberInput(attrs={'step': 'any', 'id': 'latitude'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'id': 'longitude'}),
        }

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'generic_name', 'description', 'category']

class InventoryForm(forms.ModelForm):
    new_medicine_name = forms.CharField(
        max_length=200,
        required=False,
        label="New Medicine Name",
        help_text="If the medicine doesn't exist, enter a new medicine name here"
    )
    new_medicine_generic = forms.CharField(
        max_length=200,
        required=False,
        label="Generic Name (Optional)",
        help_text="Generic name for the new medicine"
    )
    
    class Meta:
        model = Inventory
        fields = ['medicine', 'quantity', 'price', 'is_available', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make medicine field not required since we can create new ones
        self.fields['medicine'].required = False
        self.fields['medicine'].help_text = "Select an existing medicine or create a new one below"

class CustomerLocationForm(forms.ModelForm):
    class Meta:
        model = CustomerLocation
        fields = ['address', 'latitude', 'longitude']
        widgets = {
            'latitude': forms.NumberInput(attrs={'step': 'any', 'id': 'customer_latitude'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'id': 'customer_longitude'}),
        }

class MedicineSearchForm(forms.Form):
    medicine_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Enter medicine name...'})
    )
    max_distance = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=10,
        help_text="Maximum distance in kilometers"
    )
