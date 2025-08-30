# meters/migrations/0005_create_perm_groups.py

from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Create groups
    odecet_group, _ = Group.objects.get_or_create(name="Odecet")
    report_group, _ = Group.objects.get_or_create(name="Report")

    # Get permissions
    try:
        view_meter = Permission.objects.get(codename="view_meter")
        view_reading = Permission.objects.get(codename="view_reading")
        add_reading = Permission.objects.get(codename="add_reading")
        change_reading = Permission.objects.get(codename="change_reading")
    except Permission.DoesNotExist:
        return  # If permissions don't exist yet, skip

    # Assign permissions
    odecet_group.permissions.set([view_meter, view_reading, add_reading, change_reading])
    report_group.permissions.set([view_meter, view_reading])

def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Odecet", "Report"]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ("meters", "0003_alter_meter_slug"),
        ("auth", "0012_alter_user_first_name_max_length"),  # ensures auth is ready
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
