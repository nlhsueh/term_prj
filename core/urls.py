from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from projects import views as project_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_change/', project_views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    
    path('', project_views.dashboard, name='dashboard'),
    path('group/create/', project_views.create_group, name='create_group'),
    path('group/confirm/<int:membership_id>/', project_views.confirm_membership, name='confirm_membership'),
    path('group/upload/<int:group_id>/', project_views.upload_submission, name='upload_submission'),
    path('professor/', project_views.professor_dashboard, name='professor_dashboard'),
    path('professor/course/<int:course_id>/', project_views.course_detail, name='course_detail'),
    path('professor/grade/<int:group_id>/', project_views.grade_group, name='grade_group'),
    path('professor/export-csv/', project_views.export_grades_csv, name='export_grades_csv'),
    path('impersonate/<int:user_id>/', project_views.impersonate_user, name='impersonate_user'),
    path('impersonate/stop/', project_views.stop_impersonating, name='stop_impersonating'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
