# accounts/context_processors.py

def user_role_context(request):
    if request.user.is_authenticated:
        return {
            'is_doctor':  request.user.role == 'DOCTOR',
            'is_patient': request.user.role == 'PATIENT',
            'is_admin':   request.user.role == 'ADMIN' or request.user.is_superuser,
            'user_role':  request.user.role,
        }
    return {
        'is_doctor':  False,
        'is_patient': False,
        'is_admin':   False,
        'user_role':  None,
    }