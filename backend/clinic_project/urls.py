from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path


def home(request):
    return HttpResponse(
        """
        <h1>Mini Clinic Backend</h1>
        <p>Django REST API is running.</p>
        <ul>
          <li><a href="/api/">API root</a></li>
          <li><a href="/api/patients/">Patients API</a></li>
          <li><a href="/api/appointments/">Appointments API</a></li>
          <li><a href="http://localhost:4200/">Angular frontend</a></li>
        </ul>
        """,
        content_type='text/html',
    )

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/', include('clinic.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
