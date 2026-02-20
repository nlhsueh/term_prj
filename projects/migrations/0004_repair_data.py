from django.db import migrations

def repair_data(apps, schema_editor):
    Group = apps.get_model('projects', 'Group')
    Membership = apps.get_model('projects', 'Membership')
    Course = apps.get_model('projects', 'Course')
    User = apps.get_model('projects', 'User')

    # 1. Fix Course Semester and Name typos
    for course in Course.objects.all():
        changed = False
        if '{{' in course.semester or not course.semester in ['1', '2']:
            course.semester = '1'
            changed = True
        if '{{' in course.name:
            if ' (' in course.name:
                course.name = course.name.split(' (')[0]
            else:
                course.name = course.name.replace('{{ item.course.semester }}', '').replace('()', '').strip()
            changed = True
        if changed:
            course.save()

    # 2. Ensure all leaders have memberships
    for group in Group.objects.all():
        # Check for membership using user_id and group_id
        # We use filter().exists() and create() to be safe with M2M through models in migrations
        if not Membership.objects.filter(group=group, user=group.leader).exists():
            Membership.objects.create(group=group, user=group.leader, is_confirmed=True)
            print(f"Added leader {group.leader.username} to group {group.name}")
        else:
            m = Membership.objects.get(group=group, user=group.leader)
            if not m.is_confirmed:
                m.is_confirmed = True
                m.save()

class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0003_group_project_description'),
    ]

    operations = [
        migrations.RunPython(repair_data),
    ]
