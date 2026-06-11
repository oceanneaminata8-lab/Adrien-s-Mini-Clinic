from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet, AuditLogViewSet, BillViewSet, ClinicSettingsViewSet,
    ConsultationViewSet, DispensingViewSet, DoctorAvailabilityViewSet,
    InventoryItemViewSet, LabRequestViewSet, LabTestViewSet, MedicationViewSet,
    NotificationViewSet, PatientAttachmentViewSet, PatientViewSet,
    PrescriptionViewSet, SupplierViewSet, current_user, dashboard_summary,
    login, logout, password_reset_confirm, password_reset_request, register, reports,
)

router = DefaultRouter()
router.register('patients', PatientViewSet)
router.register('patient-attachments', PatientAttachmentViewSet)
router.register('availability', DoctorAvailabilityViewSet)
router.register('appointments', AppointmentViewSet)
router.register('consultations', ConsultationViewSet)
router.register('medications', MedicationViewSet)
router.register('prescriptions', PrescriptionViewSet)
router.register('bills', BillViewSet)
router.register('lab-tests', LabTestViewSet)
router.register('lab-requests', LabRequestViewSet)
router.register('suppliers', SupplierViewSet)
router.register('inventory', InventoryItemViewSet)
router.register('dispensing', DispensingViewSet)
router.register('notifications', NotificationViewSet)
router.register('audit-logs', AuditLogViewSet)
router.register('settings', ClinicSettingsViewSet)

urlpatterns = [
    path('auth/register/', register),
    path('auth/login/', login),
    path('auth/logout/', logout),
    path('auth/me/', current_user),
    path('auth/password-reset/', password_reset_request),
    path('auth/password-reset-confirm/', password_reset_confirm),
    path('dashboard/', dashboard_summary),
    path('reports/', reports),
    path('', include(router.urls)),
]
