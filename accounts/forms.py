# accounts/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import CustomUser, DoctorProfile, PatientProfile, DoctorAccessKey


class PatientRegistrationForm(forms.ModelForm):
    """Standard registration for patients"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password'
        })
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email',
                  'phone_number', 'gender', 'date_of_birth']
        widgets = {
            'first_name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'username':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'phone_number':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'gender':        forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'PATIENT'
        user.is_active = True
        user.is_verified = True
        if commit:
            user.save()
            PatientProfile.objects.create(user=user)
        return user


class DoctorRegistrationForm(forms.Form):
    """
    Doctor registration using Admin-generated Access Key.
    Key validation is the security gatekeeper.
    """
    first_name  = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}))
    last_name   = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}))
    username    = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email       = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@hospital.com'}))
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}))
    license_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medical license number'}))
    password1   = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create password'}))
    password2   = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))
    access_key  = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control access-key-input',
            'placeholder': 'MEDI-XXXX-XXXX-XXXX',
            'style': 'text-transform: uppercase; letter-spacing: 2px; font-family: monospace;'
        }),
        help_text='Enter the unique Access Key provided by your Administrator.'
    )

    def clean_access_key(self):
        key_value = self.cleaned_data.get('access_key', '').strip().upper()
        try:
            key_obj = DoctorAccessKey.objects.get(key=key_value)
        except DoctorAccessKey.DoesNotExist:
            raise ValidationError('❌ Invalid Access Key. Contact your Administrator.')

        is_valid, message = key_obj.is_valid()
        if not is_valid:
            raise ValidationError(f'❌ {message}')

        return key_value

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email

    def save(self):
        data = self.cleaned_data
        key_obj = DoctorAccessKey.objects.get(key=data['access_key'])

        # Create the user
        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password1'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number', ''),
            role='DOCTOR',
            is_verified=True,  # Auto-verified via key
        )

        # Create doctor profile
        DoctorProfile.objects.create(
            user=user,
            specialty=key_obj.specialty,
            license_number=data['license_number'],
        )

        # Mark key as used
        key_obj.mark_used(user)

        return user


class MediConnectLoginForm(AuthenticationForm):
    """Custom styled login form"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
# accounts/forms.py — ADD this new form
from .models import StaffAccessKey, StaffProfile


class StaffRegistrationForm(forms.Form):
    """Staff registration via Admin-generated key"""

    first_name  = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First name'}))
    last_name   = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last name'}))
    username    = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Username'}))
    email       = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'your@hospital.com'}))
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'+880 1XXX XXX XXX'}))
    employee_id = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Employee ID (e.g. EMP-001)'}))

    password1   = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Create password'}))
    password2   = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder':'Confirm password'}))

    access_key  = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control access-key-input',
            'placeholder': 'STAFF-XXXX-XXXX-XXXX',
            'style': 'text-transform: uppercase; letter-spacing: 2px; font-family: monospace;'
        }),
        help_text='Enter the Access Key provided by your Administrator.'
    )

    def clean_access_key(self):
        key_value = self.cleaned_data.get('access_key', '').strip().upper()
        try:
            key_obj = StaffAccessKey.objects.get(key=key_value)
        except StaffAccessKey.DoesNotExist:
            raise forms.ValidationError('❌ Invalid Access Key. Contact your Administrator.')

        is_valid, message = key_obj.is_valid()
        if not is_valid:
            raise forms.ValidationError(f'❌ {message}')

        return key_value

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def save(self):
        data = self.cleaned_data
        key_obj = StaffAccessKey.objects.get(key=data['access_key'])

        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password1'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number', ''),
            role=key_obj.role,
            is_verified=True,
        )

        StaffProfile.objects.create(
            user=user,
            department=key_obj.department,
            designation=key_obj.designation,
            employee_id=data['employee_id'],
        )

        key_obj.mark_used(user)
        return user