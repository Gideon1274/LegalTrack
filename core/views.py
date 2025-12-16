from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings
from django import forms
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from .forms import (
    CaseDetailsForm,
    CaseSubmissionForm,
    ChecklistItemForm,
    StaffAccountCreateForm,
    StaffAccountUpdateForm,
    StaffSearchForm,
)
from .models import AuditLog, Case, CaseDocument, CustomUser


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


def _require_super_admin(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if getattr(request.user, 'role', None) != 'super_admin':
        messages.error(request, 'Not authorized.')
        return redirect('dashboard')
    return None

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

        if user.role == 'capitol_receiving':
            pending_cases = Case.objects.filter(status='not_received').order_by('-created_at')[:25]
            received_unassigned = Case.objects.filter(status='received', assigned_to__isnull=True).order_by('-received_at')[:25]
            context.update({
                'pending_cases': pending_cases,
                'received_unassigned': received_unassigned,
            })

        elif user.role == 'capitol_examiner':
            my_cases = Case.objects.filter(assigned_to=user).order_by('-assigned_at')[:50]
            context.update({'my_cases': my_cases})

        template = 'core/dashboard_capitol.html'

    return render(request, template, context)


@login_required
def user_management(request):
    denial = _require_super_admin(request)
    if denial:
        return denial

    form = StaffSearchForm(request.GET or None)
    users_qs = CustomUser.objects.exclude(id=request.user.id).order_by('-date_joined')

    if form.is_valid():
        q = (form.cleaned_data.get('q') or '').strip()
        role = (form.cleaned_data.get('role') or '').strip()

        if q:
            users_qs = users_qs.filter(
                Q(email__icontains=q) |
                Q(full_name__icontains=q) |
                Q(username__icontains=q)
            )
        if role:
            users_qs = users_qs.filter(role=role)

    paginator = Paginator(users_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page') or 1)

    return render(request, 'core/user_management.html', {
        'role_display': request.user.get_role_display(),
        'search_form': form,
        'page_obj': page_obj,
    })


@login_required
def audit_logs(request):
    denial = _require_super_admin(request)
    if denial:
        return denial

    qs = AuditLog.objects.select_related('actor', 'target_user').all()
    action = (request.GET.get('action') or '').strip()
    q = (request.GET.get('q') or '').strip()

    if action:
        qs = qs.filter(action=action)
    if q:
        qs = qs.filter(
            Q(target_object__icontains=q) |
            Q(actor__email__icontains=q) |
            Q(target_user__email__icontains=q)
        )

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page') or 1)

    return render(request, 'core/audit_logs.html', {
        'role_display': request.user.get_role_display(),
        'page_obj': page_obj,
        'action_filter': action,
        'q_filter': q,
        'actions': AuditLog.ACTION_CHOICES,
    })


@login_required
def export_audit_logs_csv(request):
    denial = _require_super_admin(request)
    if denial:
        return denial

    qs = AuditLog.objects.select_related('actor', 'target_user').all()
    action = (request.GET.get('action') or '').strip()
    q = (request.GET.get('q') or '').strip()
    if action:
        qs = qs.filter(action=action)
    if q:
        qs = qs.filter(
            Q(target_object__icontains=q) |
            Q(actor__email__icontains=q) |
            Q(target_user__email__icontains=q)
        )

    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(['created_at', 'action', 'actor_email', 'target_user_email', 'target_object', 'ip_address'])
    for row in qs.order_by('-created_at'):
        writer.writerow([
            row.created_at.isoformat(),
            row.action,
            getattr(row.actor, 'email', '') if row.actor else '',
            getattr(row.target_user, 'email', '') if row.target_user else '',
            row.target_object,
            row.ip_address or '',
        ])
    return response


@login_required
def create_staff_account(request):
    denial = _require_super_admin(request)
    if denial:
        return denial

    if request.method == 'POST':
        form = StaffAccountCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            temp_password = user.generate_temp_password()
            user.set_password(temp_password)
            # Pending Activation until the user activates and sets a new password.
            user.must_change_password = False
            user.account_status = 'pending'
            user.save(created_by=request.user)

            activation_link = user.issue_activation(
                request=request,
                temp_password=temp_password,
                send_email=getattr(settings, 'LEGALTRACK_SEND_EMAILS', True),
            )
            activation_sent = bool(getattr(settings, 'LEGALTRACK_SEND_EMAILS', True))
            show_activation_link = bool(getattr(settings, 'LEGALTRACK_SHOW_ACTIVATION_LINK', False))

            AuditLog.objects.create(
                actor=request.user,
                action='activation_email_sent',
                target_user=user,
                target_object=f"User: {user.email}",
                details={'account_status': user.account_status}
            )

            return render(request, 'core/user_created.html', {
                'role_display': request.user.get_role_display(),
                'created_user': user,
                'temp_password': temp_password,
                'activation_sent': activation_sent,
                'activation_link': activation_link,
                'show_activation_link': show_activation_link,
            })
    else:
        form = StaffAccountCreateForm()

    return render(request, 'core/user_create.html', {
        'role_display': request.user.get_role_display(),
        'form': form,
    })


@login_required
def edit_staff_account(request, user_id):
    denial = _require_super_admin(request)
    if denial:
        return denial

    target = get_object_or_404(CustomUser, id=user_id)
    if target.id == request.user.id:
        messages.error(request, 'You cannot edit your own account here.')
        return redirect('user_management')

    if request.method == 'POST':
        form = StaffAccountUpdateForm(request.POST, instance=target)
        if form.is_valid():
            before = {
                'full_name': target.full_name,
                'designation': target.designation,
                'position': target.position,
            }
            updated = form.save()
            after = {
                'full_name': updated.full_name,
                'designation': updated.designation,
                'position': updated.position,
            }

            AuditLog.objects.create(
                actor=request.user,
                action='update_user',
                target_user=updated,
                target_object=f"User: {updated.email}",
                details={'before': before, 'after': after}
            )

            messages.success(request, 'User details updated.')
            return redirect('user_management')
    else:
        form = StaffAccountUpdateForm(instance=target)

    return render(request, 'core/user_edit.html', {
        'role_display': request.user.get_role_display(),
        'target_user': target,
        'form': form,
    })


@login_required
@require_POST
def toggle_staff_active(request, user_id):
    denial = _require_super_admin(request)
    if denial:
        return denial

    target = get_object_or_404(CustomUser, id=user_id)
    if target.id == request.user.id:
        messages.error(request, 'You cannot change your own status.')
        return redirect('user_management')

    if target.account_status == 'active':
        target.account_status = 'inactive'
        target.save(update_fields=['account_status', 'is_active'])

        AuditLog.objects.create(
            actor=request.user,
            action='deactivate_user',
            target_user=target,
            target_object=f"User: {target.email}",
            details={'account_status': target.account_status}
        )

        messages.success(request, 'Account deactivated.')
        return redirect('user_management')

    # Reactivation path
    if target.account_status == 'inactive':
        # If never activated, restore to pending and require activation link.
        if target.activated_at is None:
            target.account_status = 'pending'
            target.save(update_fields=['account_status', 'is_active'])
            messages.info(request, 'Account restored to Pending Activation. Use Resend Activation to onboard the user.')
            return redirect('user_management')

        target.account_status = 'active'
        target.save(update_fields=['account_status', 'is_active'])

        AuditLog.objects.create(
            actor=request.user,
            action='reactivate_user',
            target_user=target,
            target_object=f"User: {target.email}",
            details={'account_status': target.account_status}
        )

        messages.success(request, 'Account reactivated.')
        return redirect('user_management')

    # Pending accounts can't be directly activated by Super Admin toggle.
    messages.info(request, 'This account is Pending Activation. Use Resend Activation if needed.')
    return redirect('user_management')


@login_required
@require_POST
def resend_activation(request, user_id):
    denial = _require_super_admin(request)
    if denial:
        return denial

    target = get_object_or_404(CustomUser, id=user_id)
    if target.account_status != 'pending':
        messages.info(request, 'Activation can only be resent for Pending Activation accounts.')
        return redirect('user_management')

    temp_password = target.generate_temp_password()
    target.set_password(temp_password)
    target.temp_password_created_at = timezone.now()
    target.save(update_fields=['password', 'temp_password_created_at'])

    activation_link = target.issue_activation(
        request=request,
        temp_password=temp_password,
        send_email=getattr(settings, 'LEGALTRACK_SEND_EMAILS', True),
    )
    activation_sent = bool(getattr(settings, 'LEGALTRACK_SEND_EMAILS', True))
    show_activation_link = bool(getattr(settings, 'LEGALTRACK_SHOW_ACTIVATION_LINK', False))

    AuditLog.objects.create(
        actor=request.user,
        action='activation_email_sent',
        target_user=target,
        target_object=f"User: {target.email}",
        details={'resend': True}
    )

    if activation_sent:
        if show_activation_link:
            messages.success(request, mark_safe(
                'Activation email resent. Dev link: '
                f'<a href="{activation_link}">{activation_link}</a>'
            ))
        else:
            messages.success(request, 'Activation email resent.')
    else:
        messages.success(request, mark_safe(
            'Activation email is disabled in this environment. Copy this activation link: '
            f'<a href="{activation_link}">{activation_link}</a>'
        ))
    return redirect('user_management')


@login_required
def set_password_view(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            if request.user.role != 'super_admin':
                cutoff = timezone.now() - timedelta(days=30)
                recent_changes = AuditLog.objects.filter(
                    actor=request.user,
                    action__in=['password_reset_complete', 'reset_password'],
                    created_at__gte=cutoff,
                ).count()
                if recent_changes >= 2:
                    messages.error(request, 'Password change limit reached. Contact the Super Admin for approval.')
                    return redirect('dashboard')

            form.save()
            request.user.must_change_password = False
            request.user.save(update_fields=['must_change_password'])
            update_session_auth_hash(request, request.user)

            AuditLog.objects.create(
                actor=request.user,
                action='reset_password',
                target_object=f"User: {request.user.email}",
                details={'forced_reset': True}
            )

            messages.success(request, 'Password updated.')
            return redirect('dashboard')
    else:
        form = SetPasswordForm(request.user)

    return render(request, 'core/set_password.html', {
        'role_display': request.user.get_role_display(),
        'form': form,
    })


def _lgu_can_edit_case(user, case: Case) -> bool:
    return bool(
        getattr(user, 'role', None) == 'lgu_admin' and
        case.submitted_by_id == user.id and
        case.status in {'not_received', 'returned'}
    )


def _ensure_checklist_item(case: Case, *, doc_type: str, required: bool) -> None:
    items = list(case.checklist or [])
    for item in items:
        if isinstance(item, dict) and (item.get('doc_type') == doc_type):
            item['required'] = bool(required)
            item['uploaded'] = CaseDocument.objects.filter(case=case, doc_type=doc_type).exists()
            case.checklist = items
            case.save(update_fields=['checklist', 'updated_at'])
            return

    items.insert(0, {
        'doc_type': doc_type,
        'required': bool(required),
        'uploaded': CaseDocument.objects.filter(case=case, doc_type=doc_type).exists(),
    })
    case.checklist = items
    case.save(update_fields=['checklist', 'updated_at'])


def _upsert_case_document(*, case: Case, doc_type: str, uploaded_file, actor: CustomUser | None):
    doc_type = (doc_type or '').strip()
    if not doc_type or not uploaded_file:
        return None

    doc, created = CaseDocument.objects.get_or_create(
        case=case,
        doc_type=doc_type,
        defaults={'uploaded_by': actor},
    )
    if not created and doc.file:
        try:
            doc.file.delete(save=False)
        except Exception:
            pass
    doc.file = uploaded_file
    doc.uploaded_by = actor
    doc.save(update_fields=['file', 'uploaded_by', 'updated_at'])
    return doc

@login_required
def submit_case(request):
    if request.user.role != 'lgu_admin':
        messages.error(request, "Only LGU Admins can submit cases.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CaseDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            case = form.save(commit=False)
            case.submitted_by = request.user
            case.save()

            endorsement = form.cleaned_data.get('endorsement_letter')
            if endorsement:
                _upsert_case_document(case=case, doc_type='Endorsement Letter', uploaded_file=endorsement, actor=request.user)
                _ensure_checklist_item(case, doc_type='Endorsement Letter', required=True)

            AuditLog.objects.create(
                actor=request.user,
                action='case_create',
                target_object=f"Case: {case.tracking_id}",
                details={'client': case.client_name}
            )

            messages.success(request, f"Draft created: {case.tracking_id}. Continue uploading documents.")
            return redirect('case_wizard', tracking_id=case.tracking_id, step=2)
    else:
        form = CaseDetailsForm()

    return render(request, 'core/submit_case.html', {
        'step': 1,
        'form': form,
        'case': None,
        'is_edit': False,
    })


@login_required
def edit_case(request, tracking_id):
    case = get_object_or_404(Case, tracking_id=tracking_id)
    if not _lgu_can_edit_case(request.user, case):
        messages.error(request, "You cannot edit this case.")
        return redirect('case_detail', tracking_id=case.tracking_id)
    return redirect('case_wizard', tracking_id=case.tracking_id, step=1)


@login_required
def case_wizard(request, tracking_id, step: int):
    case = get_object_or_404(Case, tracking_id=tracking_id)

    if request.user.role != 'lgu_admin':
        messages.error(request, 'Only LGU Admins can edit submissions.')
        return redirect('dashboard')

    if not _lgu_can_edit_case(request.user, case):
        messages.error(request, 'This case can no longer be edited.')
        return redirect('case_detail', tracking_id=case.tracking_id)

    step = int(step or 1)
    if step not in (1, 2, 3):
        return redirect('case_wizard', tracking_id=case.tracking_id, step=1)

    if step == 1:
        if request.method == 'POST':
            form = CaseDetailsForm(request.POST, request.FILES, instance=case)
            if form.is_valid():
                form.save()

                endorsement = form.cleaned_data.get('endorsement_letter')
                if endorsement:
                    _upsert_case_document(case=case, doc_type='Endorsement Letter', uploaded_file=endorsement, actor=request.user)
                    _ensure_checklist_item(case, doc_type='Endorsement Letter', required=True)

                AuditLog.objects.create(
                    actor=request.user,
                    action='case_update',
                    target_object=f"Case: {case.tracking_id}",
                    details={'step': 1}
                )
                messages.success(request, 'Details saved.')
                return redirect('case_wizard', tracking_id=case.tracking_id, step=2)
        else:
            form = CaseDetailsForm(instance=case)

        return render(request, 'core/submit_case.html', {
            'step': 1,
            'form': form,
            'case': case,
            'is_edit': True,
            'documents': list(case.documents.all()),
        })

    if step == 2:
        FormSet = forms.formset_factory(ChecklistItemForm, extra=5)

        initial = []
        for item in (case.checklist or []):
            if isinstance(item, dict):
                initial.append({
                    'doc_type': item.get('doc_type', ''),
                    'required': bool(item.get('required', False)),
                })

        if request.method == 'POST':
            formset = FormSet(request.POST, request.FILES)
            if formset.is_valid():
                new_checklist = []
                for f in formset:
                    cd = f.cleaned_data
                    if not cd:
                        continue
                    if cd.get('delete'):
                        continue
                    doc_type = (cd.get('doc_type') or '').strip()
                    if not doc_type:
                        continue

                    uploaded_file = cd.get('file')
                    if uploaded_file:
                        _upsert_case_document(case=case, doc_type=doc_type, uploaded_file=uploaded_file, actor=request.user)

                    has_doc = CaseDocument.objects.filter(case=case, doc_type=doc_type).exists()
                    new_checklist.append({
                        'doc_type': doc_type,
                        'required': bool(cd.get('required', False)),
                        'uploaded': bool(has_doc),
                    })

                # Keep endorsement letter item present if a file exists.
                if CaseDocument.objects.filter(case=case, doc_type='Endorsement Letter').exists():
                    if not any((i.get('doc_type') == 'Endorsement Letter') for i in new_checklist):
                        new_checklist.insert(0, {'doc_type': 'Endorsement Letter', 'required': True, 'uploaded': True})

                case.checklist = new_checklist
                if case.status == 'returned':
                    case.status = 'not_received'
                case.save(update_fields=['checklist', 'status', 'updated_at'])

                AuditLog.objects.create(
                    actor=request.user,
                    action='case_update',
                    target_object=f"Case: {case.tracking_id}",
                    details={'step': 2, 'items': len(new_checklist)}
                )

                messages.success(request, 'Checklist and uploads saved.')
                return redirect('case_wizard', tracking_id=case.tracking_id, step=3)
        else:
            formset = FormSet(initial=initial)

        return render(request, 'core/submit_case.html', {
            'step': 2,
            'formset': formset,
            'case': case,
            'is_edit': True,
            'documents': list(case.documents.all()),
        })

    # step == 3
    checklist = []
    for item in (case.checklist or []):
        if not isinstance(item, dict):
            continue
        doc_type = (item.get('doc_type') or '').strip()
        if not doc_type:
            continue
        checklist.append({
            'doc_type': doc_type,
            'required': bool(item.get('required', False)),
            'uploaded': CaseDocument.objects.filter(case=case, doc_type=doc_type).exists(),
        })

    if request.method == 'POST':
        if case.status == 'returned':
            case.status = 'not_received'
            case.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            actor=request.user,
            action='case_update',
            target_object=f"Case: {case.tracking_id}",
            details={'step': 3, 'finalized': True}
        )
        messages.success(request, f"Case {case.tracking_id} submitted.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    return render(request, 'core/submit_case.html', {
        'step': 3,
        'case': case,
        'is_edit': True,
        'documents': list(case.documents.all()),
        'checklist': checklist,
    })


@login_required
def case_detail(request, tracking_id):
    case = get_object_or_404(Case, tracking_id=tracking_id)

    # LGU can only edit if status == not_received
    can_edit = (
        request.user.role == 'lgu_admin' and
        case.submitted_by == request.user and
        case.status in {'not_received', 'returned'}
    )

    can_receive = (
        request.user.role == 'capitol_receiving' and
        case.status in {'not_received', 'returned'}
    )

    can_return = (
        request.user.role == 'capitol_receiving' and
        case.status == 'not_received'
    )

    can_assign = (
        request.user.role == 'capitol_receiving' and
        case.status == 'received' and
        case.assigned_to_id is None
    )

    examiners = None
    if can_assign:
        examiners = CustomUser.objects.filter(role='capitol_examiner', is_active=True).order_by('full_name', 'email')

    return render(request, 'core/case_detail.html', {
        'case': case,
        'documents': list(case.documents.all()),
        'can_edit': can_edit,
        'can_receive': can_receive,
        'can_return': can_return,
        'can_assign': can_assign,
        'examiners': examiners,
    })


@login_required
@require_POST
def receive_case(request, tracking_id):
    case = get_object_or_404(Case, tracking_id=tracking_id)

    if request.user.role != 'capitol_receiving':
        messages.error(request, "Only Capitol Receiving Staff can receive cases.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    if case.status not in {'not_received', 'returned'}:
        messages.error(request, "This case cannot be received in its current status.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    case.status = 'received'
    case.received_at = timezone.now()
    case.received_by = request.user
    case.save()

    AuditLog.objects.create(
        actor=request.user,
        action='case_receipt',
        target_object=f"Case: {case.tracking_id}",
        details={'new_status': case.status}
    )

    messages.success(request, f"Case {case.tracking_id} marked as Received.")
    return redirect('case_detail', tracking_id=case.tracking_id)


@login_required
@require_POST
def return_case(request, tracking_id):
    case = get_object_or_404(Case, tracking_id=tracking_id)

    if request.user.role != 'capitol_receiving':
        messages.error(request, "Only Capitol Receiving Staff can return cases.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    if case.status != 'not_received':
        messages.error(request, "Only pending cases can be returned to the LGU.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    reason = (request.POST.get('reason') or '').strip()
    if not reason:
        messages.error(request, "Return reason is required.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    case.status = 'returned'
    case.return_reason = reason
    case.returned_at = timezone.now()
    case.returned_by = request.user
    case.save()

    AuditLog.objects.create(
        actor=request.user,
        action='case_status_change',
        target_object=f"Case: {case.tracking_id}",
        details={'new_status': case.status, 'reason': reason}
    )

    messages.success(request, f"Case {case.tracking_id} returned to LGU.")
    return redirect('case_detail', tracking_id=case.tracking_id)


@login_required
@require_POST
def assign_case(request, tracking_id):
    case = get_object_or_404(Case, tracking_id=tracking_id)

    if request.user.role != 'capitol_receiving':
        messages.error(request, "Only Capitol Receiving Staff can assign cases.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    if case.status != 'received' or case.assigned_to_id is not None:
        messages.error(request, "This case is not eligible for assignment.")
        return redirect('case_detail', tracking_id=case.tracking_id)

    examiner_id = request.POST.get('examiner_id')
    examiner = get_object_or_404(CustomUser, id=examiner_id, role='capitol_examiner', is_active=True)

    case.assigned_to = examiner
    case.assigned_at = timezone.now()
    case.status = 'in_review'
    case.save()

    AuditLog.objects.create(
        actor=request.user,
        action='case_assignment',
        target_object=f"Case: {case.tracking_id}",
        details={
            'new_status': case.status,
            'assigned_to': examiner.email,
        }
    )

    messages.success(request, f"Case {case.tracking_id} assigned.")
    return redirect('case_detail', tracking_id=case.tracking_id)