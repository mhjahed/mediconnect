# payments/forms.py  — Bangladesh Payment Forms

from django import forms
from .models import PaymentRecord


class BankTransferForm(forms.ModelForm):
    """Form for Bank Transfer payment submission"""

    class Meta:
        model  = PaymentRecord
        fields = [
            'bank_name',
            'bank_account_holder',
            'bank_account_number',
            'bank_transaction_id',
            'bank_branch',
            'payment_notes',
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'e.g. Dutch-Bangla Bank, BRAC Bank, Islami Bank...',
            }),
            'bank_account_holder': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Full name of the account holder',
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Your bank account number',
            }),
            'bank_transaction_id': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Transaction/Reference ID from your bank receipt',
            }),
            'bank_branch': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Branch name (optional)',
            }),
            'payment_notes': forms.Textarea(attrs={
                'class':       'form-input',
                'rows':        3,
                'placeholder': 'Any additional notes about this payment...',
            }),
        }

    def clean_bank_transaction_id(self):
        txn = self.cleaned_data.get('bank_transaction_id', '').strip()
        if not txn:
            raise forms.ValidationError('Transaction ID is required for bank transfer.')
        return txn


class MobileBankingForm(forms.ModelForm):
    """Form for bKash / Nagad / Rocket / Upay"""

    class Meta:
        model  = PaymentRecord
        fields = [
            'mobile_sender_number',
            'mobile_number',
            'mobile_transaction_id',
            'payment_notes',
        ]
        widgets = {
            'mobile_sender_number': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Your number (from which you sent)',
                'type':        'tel',
            }),
            'mobile_number': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Recipient number (our bKash/Nagad number)',
                'type':        'tel',
            }),
            'mobile_transaction_id': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Transaction ID (e.g. 8N7A3D2X1K)',
            }),
            'payment_notes': forms.Textarea(attrs={
                'class':       'form-input',
                'rows':        2,
                'placeholder': 'Additional notes...',
            }),
        }

    def clean_mobile_transaction_id(self):
        txn = self.cleaned_data.get('mobile_transaction_id', '').strip()
        if not txn:
            raise forms.ValidationError('Transaction ID is required.')
        return txn


class OtherPaymentForm(forms.ModelForm):
    """Form for any other payment method"""

    class Meta:
        model  = PaymentRecord
        fields = [
            'other_method_name',
            'other_reference',
            'payment_notes',
        ]
        widgets = {
            'other_method_name': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'e.g. Western Union, Cash in Hand, Cheque...',
            }),
            'other_reference': forms.TextInput(attrs={
                'class':       'form-input',
                'placeholder': 'Reference / Receipt number',
            }),
            'payment_notes': forms.Textarea(attrs={
                'class':       'form-input',
                'rows':        3,
                'placeholder': 'Describe the payment method and any relevant details...',
            }),
        }