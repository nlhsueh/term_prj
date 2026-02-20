from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
import io
from .models import User, CourseConfig, Group, Submission, Contribution, Score
from .forms import CSVImportForm

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('student_id', 'username', 'role', 'has_changed_password')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('student_id', 'role', 'has_changed_password')}),
    )
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
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            count = 0
            for row in reader:
                # Expecting columns: student_id, name
                student_id = row.get('student_id')
                name = row.get('name')
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
                    if created:
                        user.set_password(password)
                        user.save()
                    count += 1
            self.message_user(request, f"Successfully imported {count} students.")
            return redirect("..")
        
        form = CSVImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_form.html", payload)

admin.site.register(CourseConfig)
admin.site.register(Group)
admin.site.register(Submission)
admin.site.register(Contribution)
admin.site.register(Score)
