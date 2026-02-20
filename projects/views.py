from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse
import csv
from .models import Group, Membership, User, Submission, Contribution, Score, Course
from .forms import GroupForm, SubmissionForm, ScoreForm

class CustomPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy('dashboard') # Redirect to dashboard instead of password_change_done if we want a better UX

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.has_changed_password = True
        self.request.user.save()
        return response

@login_required
def dashboard(request):
    # Detect role and redirect if professor or staff
    if request.user.role == 'professor' or request.user.is_staff:
        return redirect('professor_dashboard')
        
    # Get active courses for this student
    courses = Course.objects.filter(students=request.user).order_by('-year', '-semester')
    
    # memberships for the user
    memberships = Membership.objects.filter(user=request.user).select_related('group', 'group__course')
    
    context = {
        'courses': courses,
        'memberships': memberships,
    }
    
    # Return partial if targeted, otherwise full page
    if request.headers.get('HX-Target') == 'dashboard-content':
        return render(request, 'projects/partials/dashboard_content.html', context)
        
    return render(request, 'projects/dashboard.html', context)

@login_required
def create_group(request):
    course_id = request.GET.get('course_id')
    course = get_object_or_404(Course, id=course_id) if course_id else None
    
    # Check if user is already in a group for this specific course
    if course and Membership.objects.filter(user=request.user, group__course=course).exists():
        messages.warning(request, f"你已在 {course.name} 的小組中。")
        return redirect('dashboard')

    if request.method == 'POST':
        form = GroupForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                group = form.save(commit=False)
                group.leader = request.user
                group.course = course # Link to course
                group.save()
                
                # Manual many-to-many through Membership
                selected_members = form.cleaned_data['members']
                # Add leader as a confirmed member
                Membership.objects.create(user=request.user, group=group, is_confirmed=True)
                # Add other members
                for member in selected_members:
                    Membership.objects.create(user=member, group=group, is_confirmed=False)
                
                return redirect('dashboard')
    else:
        form = GroupForm(user=request.user)
        # Filter members to those in the same course
        if course:
            form.fields['members'].queryset = User.objects.filter(
                role='student', enrolled_courses=course
            ).exclude(id=request.user.id).exclude(joined_groups__group__course=course)
            
    return render(request, 'projects/group_form.html', {'form': form, 'course': course})

@login_required
def confirm_membership(request, membership_id):
    membership = get_object_or_404(Membership, id=membership_id, user=request.user)
    if request.method == 'POST':
        membership.is_confirmed = True
        membership.save()
        
        if request.headers.get('HX-Request'):
            # IMPORTANT: We MUST return the partial that matches the button's hx-target (#dashboard-content)
            courses = Course.objects.filter(students=request.user).order_by('-year', '-semester')
            memberships = Membership.objects.filter(user=request.user).select_related('group', 'group__course')
            return render(request, 'projects/partials/dashboard_content.html', {
                'courses': courses,
                'memberships': memberships,
            })
            
        return redirect('dashboard')
    return render(request, 'projects/confirm_membership.html', {'membership': membership})

@login_required
def upload_submission(request, group_id):
    group = get_object_or_404(Group, id=group_id, members=request.user)
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.group = group
            submission.save()
            messages.success(request, "檔案上傳成功！")
            return redirect('dashboard')
    else:
        form = SubmissionForm()
    return render(request, 'projects/upload.html', {'form': form, 'group': group})

@login_required
def professor_dashboard(request):
    if request.user.role != 'professor' and not request.user.is_staff:
        return redirect('dashboard')
    courses = Course.objects.all().order_by('-year', '-semester')
    context = {'courses': courses}
    
    if request.headers.get('HX-Target') == 'professor-dashboard-content':
        return render(request, 'projects/partials/professor_dashboard_content.html', context)
        
    return render(request, 'projects/professor_dashboard.html', context)

@login_required
def course_detail(request, course_id):
    if request.user.role != 'professor' and not request.user.is_staff:
        return redirect('dashboard')
    course = get_object_or_404(Course, id=course_id)
    groups = Group.objects.filter(course=course)
    
    # Students who are not in any group in this course
    assigned_student_ids = Membership.objects.filter(group__course=course).values_list('user_id', flat=True)
    unassigned_students = course.students.exclude(id__in=assigned_student_ids)
    
    context = {
        'course': course,
        'groups': groups,
        'unassigned_students': unassigned_students,
    }
    
    if request.headers.get('HX-Target') == 'course-detail-content':
        return render(request, 'projects/partials/course_detail_content.html', context)
        
    return render(request, 'projects/course_detail.html', context)

@login_required
def grade_group(request, group_id):
    if request.user.role != 'professor' and not request.user.is_staff:
        return redirect('dashboard')
    group = get_object_or_404(Group, id=group_id)
    score, created = Score.objects.get_or_create(group=group)
    
    if request.method == 'POST':
        form = ScoreForm(request.POST, instance=score)
        if form.is_valid():
            form.save()
            messages.success(request, f"{group.name} 評分成功！")
            return redirect('professor_dashboard')
    else:
        form = ScoreForm(instance=score)
    
    submissions = Submission.objects.filter(group=group).order_by('-uploaded_at')
    contributions = Contribution.objects.filter(group=group)
    
    return render(request, 'projects/grading.html', {
        'group': group,
        'form': form,
        'submissions': submissions,
        'contributions': contributions
    })

@login_required
def export_grades_csv(request):
    if request.user.role != 'professor' and not request.user.is_staff:
        return redirect('dashboard')
    
    course_id = request.GET.get('course_id')
    course = get_object_or_404(Course, id=course_id) if course_id else None
    
    filename = f"grades_{course.name}.csv" if course else "all_grades.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # Fix for Chinese characters in Excel
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['學號', '姓名', '組別', '計畫名稱', '小組分數', '貢獻度(%)', '貢獻度描述'])
    
    memberships = Membership.objects.select_related('user', 'group', 'group__course', 'group__score').all()
    if course:
        memberships = memberships.filter(group__course=course)
    
    for m in memberships:
        score_obj = getattr(m.group, 'score', None)
        team_score = score_obj.team_base_score if score_obj else "未評分"
        
        # Get contribution for this specific student in this group
        contrib = Contribution.objects.filter(group=m.group, student=m.user).first()
        pct = f"{contrib.percentage}%" if contrib else "未填寫"
        desc = contrib.description if contrib else ""
        
        writer.writerow([
            m.user.student_id,
            m.user.first_name,
            m.group.name,
            m.group.project_name,
            team_score,
            pct,
            desc
        ])
    
    return response
