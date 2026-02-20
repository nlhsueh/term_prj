from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('professor', 'Professor'),
    )
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    has_changed_password = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.first_name})"

class Course(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField(default=2024)
    semester = models.CharField(max_length=10, choices=(('1', '1'), ('2', '2')), default='1')
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    group_deadline = models.DateTimeField()
    proposal_deadline = models.DateTimeField()
    final_deadline = models.DateTimeField()

    def __str__(self):
        return f"{self.year}-{self.semester} {self.name}"

class Group(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups', null=True)
    name = models.CharField(max_length=100)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_groups')
    members = models.ManyToManyField(User, through='Membership', related_name='joined_groups')
    project_name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')

class Submission(models.Model):
    TYPE_CHOICES = (
        ('proposal_draft', 'Proposal Draft'),
        ('final_report', 'Final Report'),
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='submissions/')
    version = models.IntegerField(default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Contribution(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

class Score(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    team_base_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    individual_adjustments = models.JSONField(default=dict) # {student_id: adjustment}
    professor_notes = models.TextField(blank=True)
