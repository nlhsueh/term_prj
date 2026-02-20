from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import csv
import io
from .models import User, Course, Group, Submission, Contribution, Score
from .forms import CSVImportForm

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('student_id', 'first_name', 'username', 'role', 'display_groups', 'has_changed_password')
    list_filter = ('role', 'has_changed_password')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Custom Info', {'fields': ('student_id', 'role', 'has_changed_password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    # We explicitly omit 'groups' and 'user_permissions' from fieldsets to avoid confusion 
    # since this project uses a custom Group model.
    
    def display_groups(self, obj):
        return ", ".join([g.name for g in obj.joined_groups.all()])
    display_groups.short_description = '所屬小組'

    actions = ['reset_password']

    @admin.action(description="Reset password to student ID's last 4 digits")
    def reset_password(self, request, queryset):
        for user in queryset:
            if user.student_id:
                new_password = user.student_id[-4:]
                user.set_password(new_password)
                user.has_changed_password = False
                user.save()
        self.message_user(request, "Passwords reset successfully.")

    def get_urls(self):
        urls = super().get_urls()
        return urls # Remove import-csv from UserAdmin

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'semester')
    filter_horizontal = ('students',)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:course_id>/import-csv/', self.import_csv, name='course-import-csv'),
        ]
        return my_urls + urls

    def import_csv(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            rows = list(csv.reader(io_string))
            if not rows:
                self.message_user(request, "The CSV file is empty.", level=messages.WARNING)
                return redirect("..")
            
            # Determine if first row is a header
            first_row = [str(c).strip().lower() for c in rows[0]]
            has_header = 'student_id' in first_row or '学号' in first_row or '學號' in first_row
            
            if has_header:
                # Find indices by header names
                try:
                    id_idx = first_row.index('student_id') if 'student_id' in first_row else (first_row.index('學號') if '學號' in first_row else first_row.index('学号'))
                    name_idx = first_row.index('name') if 'name' in first_row else (first_row.index('姓名') if '姓名' in first_row else 1)
                except ValueError:
                    id_idx, name_idx = 0, 1
                data_start = 1
            else:
                # No header, assume column 0 is ID, column 1 is Name
                id_idx, name_idx = 0, 1
                data_start = 0

            count = 0
            for row in rows[data_start:]:
                if len(row) > max(id_idx, name_idx):
                    student_id = row[id_idx].strip()
                    name = row[name_idx].strip()
                    if student_id and name:
                        username = student_id
                        password = student_id[-4:]
                        user, created = User.objects.update_or_create(
                            username=username,
                            defaults={
                                'student_id': student_id,
                                'first_name': name,
                                'role': 'student',
                            }
                        )
                        if created or not user.has_changed_password:
                            user.set_password(password)
                            user.save()
                        
                        course.students.add(user)
                        count += 1
            self.message_user(request, f"Successfully imported {count} students to {course.name}.")
            return redirect("..")
        
        form = CSVImportForm()
        payload = {"form": form, "course": course}
        return render(request, "admin/csv_form.html", payload)

# admin.site.register(Course) is handled by @admin.register
admin.site.register(Group)
admin.site.register(Submission)
admin.site.register(Contribution)
admin.site.register(Score)
