# medical_records/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import MedicalRecord, Prescription, LabTest


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model  = MedicalRecord
        fields = [
            'chief_complaint', 'history_of_illness', 'examination_findings',
            'diagnosis', 'treatment_plan', 'follow_up_notes',
            'blood_pressure', 'pulse_rate', 'temperature',
            'weight', 'oxygen_saturation', 'is_finalized',
        ]
        widgets = {
            'chief_complaint': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
                'placeholder': 'Main reason for visit...'
            }),
            'history_of_illness': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'History of present illness...'
            }),
            'examination_findings': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'Physical examination findings...'
            }),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'Diagnosis / Clinical impression...'
            }),
            'treatment_plan': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'Treatment plan and management...'
            }),
            'follow_up_notes': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2,
                'placeholder': 'Follow-up instructions for patient...'
            }),
            'blood_pressure':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': '120/80 mmHg'}),
            'pulse_rate':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': '72 bpm'}),
            'temperature':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': '98.6°F'}),
            'weight':             forms.TextInput(attrs={'class': 'form-input', 'placeholder': '70 kg'}),
            'oxygen_saturation':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': '98%'}),
            'is_finalized':       forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model  = Prescription
        fields = [
            'drug_name', 'generic_name', 'dosage', 'frequency',
            'route', 'duration', 'duration_unit', 'instructions', 'quantity',
        ]
        widgets = {
            'drug_name':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Drug name'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Generic name (optional)'}),
            'dosage':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 500mg'}),
            'frequency':    forms.Select(attrs={'class': 'form-input'}),
            'route':        forms.Select(attrs={'class': 'form-input'}),
            'duration':     forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'duration_unit':forms.Select(attrs={'class': 'form-input'}),
            'instructions': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Special instructions...'}),
            'quantity':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 30 tablets'}),
        }


# Inline formset — multiple prescriptions in one form
PrescriptionFormSet = inlineformset_factory(
    MedicalRecord,
    Prescription,
    form=PrescriptionForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class LabTestForm(forms.ModelForm):
    class Meta:
        model  = LabTest
        fields = ['test_name', 'urgency', 'instructions']
        widgets = {
            'test_name':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Complete Blood Count (CBC)'}),
            'urgency':      forms.Select(attrs={'class': 'form-input'}),
            'instructions': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Patient instructions (fasting, etc.)'}),
        }


LabTestFormSet = inlineformset_factory(
    MedicalRecord,
    LabTest,
    form=LabTestForm,
    extra=1,
    can_delete=True,
)