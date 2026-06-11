import csv

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Count, F, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import (
    Appointment, AuditLog, AuthToken, Bill, ClinicSettings, Consultation,
    Dispensing, DoctorAvailability, InventoryItem, LabRequest, LabTest,
    Medication, Notification, Patient, PatientAttachment, Payment,
    Prescription, Supplier,
)
from .permissions import ActionRolePermission, IsAdmin, IsClinicStaff, user_role
from .serializers import (
    AppointmentSerializer, AuditLogSerializer, BillSerializer,
    ClinicSettingsSerializer, ConsultationSerializer, DispensingSerializer,
    DoctorAvailabilitySerializer, InventoryItemSerializer, LabRequestSerializer,
    LabTestSerializer, LoginSerializer, MedicationSerializer,
    NotificationSerializer, PatientAttachmentSerializer, PatientSerializer,
    PaymentSerializer, PrescriptionSerializer, RegisterSerializer,
    SupplierSerializer, UserSerializer,
)

User = get_user_model()


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')


def audit(request, action_name, instance, summary):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action_name,
        entity_type=instance.__class__.__name__,
        entity_id=str(instance.pk),
        summary=summary,
        ip_address=client_ip(request),
    )


class AuditedViewSet(viewsets.ModelViewSet):
    permission_classes = [ActionRolePermission]
    role_permissions = {'default': {'admin'}}

    def perform_create(self, serializer):
        instance = serializer.save()
        audit(self.request, 'create', instance, f'Created {instance}')

    def perform_update(self, serializer):
        instance = serializer.save()
        audit(self.request, 'update', instance, f'Updated {instance}')

    def perform_destroy(self, instance):
        audit(self.request, 'delete', instance, f'Deleted {instance}')
        instance.delete()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    audit(request, 'register', user, f'Registered account {user.email}')
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    user.clinic_tokens.all().delete()
    token = AuthToken.issue(user)
    audit(request, 'login', user, f'User {user.email} signed in')
    return Response({'token': token, 'expires_in': 28800, 'user': UserSerializer(user).data})


@api_view(['POST'])
def logout(request):
    audit(request, 'logout', request.user, f'User {request.user.email} signed out')
    if request.auth:
        request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def current_user(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    user = User.objects.filter(email__iexact=request.data.get('email', ''), is_active=True).first()
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = f'http://localhost:4200/?reset_uid={uid}&reset_token={token}'
        send_mail(
            'CarePoint password reset',
            f'Use this link to reset your password: {link}',
            None, [user.email], fail_silently=True,
        )
    return Response({'detail': 'If the account exists, password reset instructions have been sent.'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(request.data.get('uid', ''))))
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({'detail': 'Invalid reset link.'}, status=400)
    if not default_token_generator.check_token(user, request.data.get('token', '')):
        return Response({'detail': 'Invalid or expired reset link.'}, status=400)
    password = request.data.get('password', '')
    if len(password) < 8:
        return Response({'detail': 'Password must contain at least 8 characters.'}, status=400)
    user.set_password(password)
    user.save(update_fields=['password'])
    user.clinic_tokens.all().delete()
    return Response({'detail': 'Password updated successfully.'})


class PatientViewSet(AuditedViewSet):
    queryset = Patient.objects.prefetch_related('attachments').order_by('-created_at')
    serializer_class = PatientSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'receptionist', 'lab', 'pharmacist', 'patient'},
        'retrieve': {'admin', 'doctor', 'receptionist', 'lab', 'pharmacist', 'patient'},
        'create': {'admin', 'doctor', 'receptionist'},
        'update': {'admin', 'doctor', 'receptionist'},
        'partial_update': {'admin', 'doctor', 'receptionist'},
        'destroy': {'admin'},
    }

    def get_queryset(self):
        if user_role(self.request.user) == 'patient':
            return self.queryset.filter(user=self.request.user)
        return self.queryset


class PatientAttachmentViewSet(AuditedViewSet):
    queryset = PatientAttachment.objects.all()
    serializer_class = PatientAttachmentSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'receptionist'}, 'retrieve': {'admin', 'doctor', 'receptionist'},
        'create': {'admin', 'doctor', 'receptionist'}, 'destroy': {'admin'},
    }

    def perform_create(self, serializer):
        instance = serializer.save(uploaded_by=self.request.user)
        audit(self.request, 'upload', instance, f'Uploaded {instance.title}')


class DoctorAvailabilityViewSet(AuditedViewSet):
    queryset = DoctorAvailability.objects.select_related('doctor').all()
    serializer_class = DoctorAvailabilitySerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'receptionist'}, 'retrieve': {'admin', 'doctor', 'receptionist'},
        'create': {'admin', 'doctor'}, 'update': {'admin', 'doctor'},
        'partial_update': {'admin', 'doctor'}, 'destroy': {'admin'},
    }


class AppointmentViewSet(AuditedViewSet):
    queryset = Appointment.objects.select_related('patient', 'doctor_user').order_by('-date', '-created_at')
    serializer_class = AppointmentSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'receptionist', 'patient'}, 'retrieve': {'admin', 'doctor', 'receptionist', 'patient'},
        'create': {'admin', 'doctor', 'receptionist', 'patient'}, 'update': {'admin', 'doctor', 'receptionist'},
        'partial_update': {'admin', 'doctor', 'receptionist'}, 'reschedule': {'admin', 'doctor', 'receptionist'},
        'queue_reminder': {'admin', 'receptionist'}, 'destroy': {'admin'},
    }

    def get_queryset(self):
        role = user_role(self.request.user)
        if role == 'patient':
            return self.queryset.filter(patient__user=self.request.user)
        if role == 'doctor':
            return self.queryset.filter(doctor_user=self.request.user)
        return self.queryset

    def perform_create(self, serializer):
        patient = serializer.validated_data.get('patient')
        instance = serializer.save(
            created_by=self.request.user,
            patient_name=serializer.validated_data.get('patient_name') or (patient.name if patient else ''),
            patient_code=serializer.validated_data.get('patient_code') or (patient.patient_id if patient else ''),
        )
        audit(self.request, 'create', instance, f'Booked appointment for {instance.patient_name}')

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        serializer = self.get_serializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(status='Confirmed', reminder_sent=False)
        audit(request, 'reschedule', appointment, f'Rescheduled {appointment.patient_name}')
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def queue_reminder(self, request, pk=None):
        appointment = self.get_object()
        notification = Notification.objects.create(
            recipient=appointment.patient.user if appointment.patient else None,
            patient=appointment.patient, appointment=appointment,
            channel=request.data.get('channel', 'in_app'),
            destination=request.data.get('destination', appointment.patient.phone if appointment.patient else ''),
            subject='Appointment reminder',
            message=f'Reminder: {appointment.appointment_type} on {appointment.date} at {appointment.time}.',
        )
        return Response(NotificationSerializer(notification).data, status=201)


class ConsultationViewSet(AuditedViewSet):
    queryset = Consultation.objects.select_related('patient', 'clinician').order_by('-created_at')
    serializer_class = ConsultationSerializer
    role_permissions = {'default': {'admin', 'doctor'}, 'destroy': {'admin'}}

    def perform_create(self, serializer):
        instance = serializer.save(clinician=self.request.user)
        audit(self.request, 'create', instance, f'Consultation for {instance.patient_name}')


class MedicationViewSet(AuditedViewSet):
    queryset = Medication.objects.order_by('name')
    serializer_class = MedicationSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'pharmacist'}, 'retrieve': {'admin', 'doctor', 'pharmacist'},
        'create': {'admin', 'pharmacist'}, 'update': {'admin', 'pharmacist'},
        'partial_update': {'admin', 'pharmacist'}, 'destroy': {'admin'},
    }


class PrescriptionViewSet(AuditedViewSet):
    queryset = Prescription.objects.prefetch_related('items').select_related('patient', 'prescriber')
    serializer_class = PrescriptionSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'pharmacist'}, 'retrieve': {'admin', 'doctor', 'pharmacist'},
        'create': {'admin', 'doctor'}, 'update': {'admin', 'doctor'},
        'partial_update': {'admin', 'doctor'}, 'destroy': {'admin'},
    }

    def perform_create(self, serializer):
        instance = serializer.save(prescriber=self.request.user)
        audit(self.request, 'create', instance, f'Prescription for {instance.patient.name}')


class BillViewSet(AuditedViewSet):
    queryset = Bill.objects.prefetch_related('items', 'payments').order_by('-created_at')
    serializer_class = BillSerializer
    role_permissions = {'default': {'admin', 'receptionist'}, 'destroy': {'admin'}}

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        bill = self.get_object()
        serializer = PaymentSerializer(data={**request.data, 'bill': bill.pk})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(received_by=request.user)
        paid = bill.payments.aggregate(total=Sum('amount'))['total'] or 0
        bill.status = 'Paid' if paid >= bill.amount else 'Partially Paid'
        bill.save(update_fields=['status'])
        audit(request, 'payment', bill, f'Payment for {bill.invoice_no}')
        return Response(PaymentSerializer(payment).data, status=201)


class LabTestViewSet(AuditedViewSet):
    queryset = LabTest.objects.order_by('name')
    serializer_class = LabTestSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'lab'}, 'retrieve': {'admin', 'doctor', 'lab'},
        'create': {'admin', 'lab'}, 'update': {'admin', 'lab'},
        'partial_update': {'admin', 'lab'}, 'destroy': {'admin'},
    }


class LabRequestViewSet(AuditedViewSet):
    queryset = LabRequest.objects.select_related('patient', 'test').order_by('-created_at')
    serializer_class = LabRequestSerializer
    role_permissions = {
        'list': {'admin', 'doctor', 'lab'}, 'retrieve': {'admin', 'doctor', 'lab'},
        'create': {'admin', 'doctor'}, 'update': {'admin', 'lab'},
        'partial_update': {'admin', 'lab'}, 'review': {'admin', 'doctor'}, 'destroy': {'admin'},
    }

    def perform_create(self, serializer):
        instance = serializer.save(requested_by=self.request.user)
        audit(self.request, 'create', instance, f'Requested {instance.test.name}')

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        item = self.get_object()
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.status = 'Reviewed'
        item.save(update_fields=['reviewed_by', 'reviewed_at', 'status'])
        return Response(self.get_serializer(item).data)


class SupplierViewSet(AuditedViewSet):
    queryset = Supplier.objects.order_by('name')
    serializer_class = SupplierSerializer
    permission_classes = [IsAdmin]


class InventoryItemViewSet(AuditedViewSet):
    queryset = InventoryItem.objects.select_related('medication', 'supplier').order_by('expiry_date')
    serializer_class = InventoryItemSerializer
    role_permissions = {'default': {'admin', 'pharmacist'}, 'destroy': {'admin'}}

    def get_queryset(self):
        if self.request.query_params.get('low_stock') == 'true':
            return self.queryset.filter(quantity__lte=F('reorder_level'))
        return self.queryset


class DispensingViewSet(AuditedViewSet):
    queryset = Dispensing.objects.select_related('patient', 'inventory_item').order_by('-dispensed_at')
    serializer_class = DispensingSerializer
    role_permissions = {'default': {'admin', 'pharmacist'}, 'destroy': {'admin'}}

    def perform_create(self, serializer):
        instance = serializer.save(dispensed_by=self.request.user)
        audit(self.request, 'dispense', instance, f'Dispensed to {instance.patient.name}')


class NotificationViewSet(AuditedViewSet):
    queryset = Notification.objects.order_by('-created_at')
    serializer_class = NotificationSerializer
    role_permissions = {'default': {'admin', 'receptionist'}, 'destroy': {'admin'}}

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        item = self.get_object()
        item.status = 'Sent'
        item.sent_at = timezone.now()
        item.save(update_fields=['status', 'sent_at'])
        return Response(self.get_serializer(item).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('actor')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]


class ClinicSettingsViewSet(AuditedViewSet):
    queryset = ClinicSettings.objects.all()
    serializer_class = ClinicSettingsSerializer
    permission_classes = [IsAdmin]

    def list(self, request, *args, **kwargs):
        item, _ = ClinicSettings.objects.get_or_create(id=1)
        return Response(self.get_serializer(item).data)


@api_view(['GET'])
@permission_classes([IsClinicStaff])
def dashboard_summary(request):
    today = timezone.localdate()
    return Response({
        'total_patients': Patient.objects.count(),
        'todays_appointments': Appointment.objects.filter(date=today).count(),
        'monthly_revenue': Bill.objects.filter(
            status='Paid', created_at__month=today.month
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'pending_invoices': Bill.objects.exclude(status='Paid').count(),
        'low_stock_items': InventoryItem.objects.filter(quantity__lte=F('reorder_level')).count(),
        'pending_lab_requests': LabRequest.objects.exclude(status__in=['Completed', 'Reviewed']).count(),
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def reports(request):
    start, end = request.query_params.get('start'), request.query_params.get('end')
    bills, appointments, consultations = Bill.objects.all(), Appointment.objects.all(), Consultation.objects.all()
    if start:
        bills = bills.filter(created_at__date__gte=start)
        appointments = appointments.filter(date__gte=start)
        consultations = consultations.filter(created_at__date__gte=start)
    if end:
        bills = bills.filter(created_at__date__lte=end)
        appointments = appointments.filter(date__lte=end)
        consultations = consultations.filter(created_at__date__lte=end)
    data = {
        'revenue': bills.filter(status='Paid').aggregate(total=Sum('amount'))['total'] or 0,
        'outstanding': bills.exclude(status='Paid').aggregate(total=Sum('amount'))['total'] or 0,
        'new_patients': Patient.objects.filter(created_at__date__gte=start).count() if start else Patient.objects.count(),
        'appointments': appointments.count(),
        'common_diagnoses': list(consultations.values('diagnosis').annotate(total=Count('id')).order_by('-total')[:10]),
        'doctor_workload': list(appointments.values('doctor').annotate(total=Count('id')).order_by('-total')),
    }
    if request.query_params.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clinic-report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Metric', 'Value'])
        for key in ['revenue', 'outstanding', 'new_patients', 'appointments']:
            writer.writerow([key.replace('_', ' ').title(), data[key]])
        return response
    return Response(data)
