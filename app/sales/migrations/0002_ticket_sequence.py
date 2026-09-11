from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("sales", "0001_initial")]

    operations = [
        migrations.RunSQL(
            "CREATE SEQUENCE ticket_ticketid_seq START WITH 1",
            "DROP SEQUENCE ticket_ticketid_seq",
        )
    ]
