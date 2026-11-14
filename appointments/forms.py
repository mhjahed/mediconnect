# appointments/forms.py

from django import forms
from django.utils import timezone
from .models import Appointment


class AppointmentBookingForm(forms.ModelForm):
    """Step form for booking — date, time slot, complaint"""

    class Meta:
        model  = Appointment
        fields = ['appointment_date', 'chief_complaint']
        widgets = {
            'appointment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'min': str(timezone.now().date()),
            }),
            'chief_complaint': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Briefly describe your symptoms or reason for visit...',
            }),
        }

    def clean_appointment_date(self):
        date = self.cleaned_data.get('appointment_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError('Please select a future date.')
        return date


class GoogleMeetSetupForm(forms.ModelForm):
    """Doctor fills this to attach Google Meet link"""

    custom_meeting_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input',
        }),
        help_text='Override default time (optional).'
    )

    class Meta:
        model  = Appointment
        fields = ['meet_link', 'meet_notes', 'start_time', 'end_time']
        widgets = {
            'meet_link': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://meet.google.com/xxx-xxxx-xxx',
            }),
            'meet_notes': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Pre-consultation instructions for the patient...',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-input',
                'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-input',
                'type': 'time',
            }),
        }

    def clean_meet_link(self):
        link = self.cleaned_data.get('meet_link', '')
        if link and 'meet.google.com' not in link:
            raise forms.ValidationError(
                'Please enter a valid Google Meet link (meet.google.com/...)'
            )
        return link