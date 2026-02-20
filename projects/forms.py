from django import forms
from .models import User, Group, Submission, Contribution, Score

class CSVImportForm(forms.Form):
    csv_file = forms.FileField()

class StudentMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.first_name} ({obj.student_id[-2:] if obj.student_id else ''})"

class GroupForm(forms.ModelForm):
    members = StudentMultipleChoiceField(
        queryset=User.objects.filter(role='student'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Group
        fields = ['name', 'project_name', 'project_description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '例如：第一組'
            }),
            'project_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '例如：智慧停車系統'
            }),
            'project_description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 text-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': '請簡述您的專題目標、功能與技術架構...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # Filtering logic:
            # 1. Students only
            # 2. Exclude the current leader
            # 3. Exclude students already in ANY group for THIS course (except those already in this group if editing)
            
            # Use provided course or get from instance
            current_course = course or (self.instance.course if self.instance and self.instance.pk else None)
            
            qs = User.objects.filter(role='student').exclude(id=self.user.id)
            
            if current_course:
                # enrolled in this course
                qs = qs.filter(enrolled_courses=current_course)
                
                # exclude people in other groups of this same course
                other_groups_members = User.objects.filter(
                    joined_groups__course=current_course
                )
                if self.instance and self.instance.pk:
                    other_groups_members = other_groups_members.exclude(joined_groups=self.instance)
                
                qs = qs.exclude(id__in=other_groups_members)
            else:
                # fall back to global exclusion if no course context (safety)
                qs = qs.exclude(joined_groups__isnull=False)
                
            self.fields['members'].queryset = qs

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['type', 'file']

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['student', 'description', 'percentage']

class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['team_base_score', 'professor_notes']
