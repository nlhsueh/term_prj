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
        fields = ['name', 'project_name', 'members']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # exclude the leader from member selection as they are automatically a member
            self.fields['members'].queryset = User.objects.filter(
                role='student'
            ).exclude(id=self.user.id).exclude(joined_groups__isnull=False)

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
