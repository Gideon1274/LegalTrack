from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from core import auth_views

urlpatterns = [
    path("", include("core.urls")),
    path("admin/", admin.site.urls),
    
    # Custom Auth Routes
    path("accounts/login/", auth_views.LegalTrackLoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.logout_view, name="logout"),
    path("accounts/activate/<path:token>/", auth_views.activate_account, name="activate_account"),
    path("accounts/password_reset/", auth_views.ThrottledPasswordResetView.as_view(), name="password_reset"),
    path("accounts/reset/<uidb64>/<token>/", auth_views.LoggedPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    
    # Removed include("django.contrib.auth.urls") to avoid conflicts
]

# Append static/media files correctly
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)