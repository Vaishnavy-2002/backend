# Generated manually to add default values for is_featured and is_verified

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0003_remove_feedback_updated_at_alter_feedback_order_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE feedback ALTER COLUMN is_featured SET DEFAULT 0;",
            reverse_sql="ALTER TABLE feedback ALTER COLUMN is_featured DROP DEFAULT;"
        ),
        migrations.RunSQL(
            "ALTER TABLE feedback ALTER COLUMN is_verified SET DEFAULT 0;",
            reverse_sql="ALTER TABLE feedback ALTER COLUMN is_verified DROP DEFAULT;"
        ),
        # Update existing NULL values to false (0)
        migrations.RunSQL(
            "UPDATE feedback SET is_featured = 0 WHERE is_featured IS NULL;",
            reverse_sql="UPDATE feedback SET is_featured = NULL WHERE is_featured = 0;"
        ),
        migrations.RunSQL(
            "UPDATE feedback SET is_verified = 0 WHERE is_verified IS NULL;",
            reverse_sql="UPDATE feedback SET is_verified = NULL WHERE is_verified = 0;"
        ),
    ]
