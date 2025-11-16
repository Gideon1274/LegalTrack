from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from .models import AuditLog, CustomUser, AuditLog
from .utils import generate_activation_token
import binascii
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
import re
from django.contrib.auth.decorators import login_required
from .forms import CaseSubmissionForm
from .models import Case, AuditLog

def activate_account(request, token):
    try:
        profile = UserProfile.objects.get(activation_token=token)
        if not profile.is_activation_valid():
            messages.error(request, "Activation link has expired.")
            return redirect('login')
        
        user = profile.user
        if user.is_active:
            messages.info(request, "Account already activated.")
            return redirect('login')

        # Clear token
        profile.activation_token = None
        profile.activation_expiry = None
        profile.save()

        # Force password change
        user.profile.must_change_password = True
        user.profile.save()
        user.is_active = True
        user.save()

        # Log activation
        AuditLog.objects.create(
            actor=user,
            action='account_activated',
            target_user=user,
            details={'method': 'email_link'}
        )

        messages.success(request, "Account activated! Please set a new password.")
        login(request, user)  # Auto-login
        return redirect('set_password')

    except (UserProfile.DoesNotExist, binascii.Error):
        messages.error(request, "Invalid activation link.")
        return redirect('login')


@login_required
def set_password_view(request):
    if not request.user.profile.must_change_password:
        return redirect('dashboard')

    if request.method == 'POST':
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password1) < 12:
            messages.error(request, "Password must be at least 12 characters.")
        elif not re.search(r'[A-Z]', password1):
            messages.error(request, "Password must contain an uppercase letter.")
        elif not re.search(r'[a-z]', password1):
            messages.error(request, "Password must contain a lowercase letter.")
        elif not re.search(r'\d', password1):
            messages.error(request, "Password must contain a number.")
        elif not re.search(r'[!@#$%^&*]', password1):
            messages.error(request, "Password must contain a special character.")
        else:
            request.user.set_password(password1)
            request.user.profile.must_change_password = False
            request.user.profile.save()
            request.user.save()
            update_session_auth_hash(request, request.user)

            AuditLog.objects.create(
                actor=request.user,
                action='password_changed',
                target_user=request.user,
                details={'reason': 'first_login'}
            )

            messages.success(request, "Password set successfully!")
            return redirect('dashboard')

    return render(request, 'core/set_password.html')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'role_display': user.get_role_display(),
    }

    if user.role == 'super_admin':
        total_users = CustomUser.objects.exclude(id=user.id).count()
        context.update({
            'section': 'super_admin',
            'total_users': total_users,
        })
        template = 'core/dashboard_superadmin.html'

    elif user.role == 'lgu_admin':
        recent_cases = user.submitted_cases.all()[:10]
        context.update({
            'section': 'lgu_admin',
            'recent_cases': recent_cases,
        })
        template = 'core/dashboard_lgu.html'

    else:  # Capitol roles
        context.update({
            'section': 'capitol_staff',
            'capitol_role': user.get_role_display(),
        })
        template = 'core/dashboard_capitol.html'

    return render(request, template, context)

@login_required
def submit_case(request):
    if request.user.role != 'lgu_admin':
        messages.error(request, "Only LGU Admins can submit cases.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CaseSubmissionForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.submitted_by = request.user
            case.save()

            # Audit
            AuditLog.objects.create(
                actor=request.user,
                action='case_create',
                target_object=f"Case: {case.tracking_id}",
                details={'client': case.client_name}
            )

            messages.success(request, f"Case {case.tracking_id} created!")
            return redirect('case_detail', tracking_id=case.tracking_id)
    else:
        form = CaseSubmissionForm()

    return render(request, 'core/submit_case.html', {'form': form})


@login_required
def case_detail(request, tracking_id):
    case = get_object_or_404(Case, tracking_id=tracking_id)

    # LGU can only edit if status == not_received
    can_edit = (request.user.role == 'lgu_admin' and
                case.submitted_by == request.user and
                case.status == 'not_received')

    return render(request, 'core/case_detail.html', {
        'case': case,
        'can_edit': can_edit,
    })