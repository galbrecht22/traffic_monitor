# Generated by Django 3.0.5 on 2021-02-09 19:51

from django.db import migrations, models
import djongo.models.fields
import traffic_monitor.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Route',
            fields=[
                ('route_id', models.CharField(max_length=70, primary_key=True, serialize=False)),
                ('route_name', models.CharField(default='', max_length=70)),
                ('trips', djongo.models.fields.ArrayField(model_container=traffic_monitor.models.RouteTrip)),
            ],
        ),
        migrations.CreateModel(
            name='RouteTrip',
            fields=[
                ('trip_id', models.CharField(max_length=70, primary_key=True, serialize=False)),
                ('destination', models.CharField(default='', max_length=200)),
                ('departure_time', models.CharField(default='', max_length=70)),
                ('departure_timestamp', models.IntegerField(default=0)),
                ('travel_time', models.IntegerField(default=0)),
                ('delay', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='StopTime',
            fields=[
                ('stop_id', models.CharField(default='', max_length=70, primary_key=True, serialize=False)),
                ('stop_name', models.CharField(default='', max_length=200)),
                ('reference_timestamp', models.IntegerField(default=0)),
                ('reference_time', models.CharField(default='', max_length=70)),
                ('actual_timestamp', models.IntegerField(default=0)),
                ('actual_time', models.CharField(default='', max_length=70)),
                ('delay', models.IntegerField(default=0)),
                ('is_predicted', models.BooleanField(default=False)),
                ('is_next', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('trip_id', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('route_id', models.CharField(default='', max_length=30)),
                ('route_name', models.CharField(default='', max_length=70)),
                ('departure_time', models.CharField(default='', max_length=70)),
                ('destination', models.CharField(default='', max_length=200)),
                ('delay', models.IntegerField(default=0)),
                ('location', djongo.models.fields.EmbeddedField(model_container=traffic_monitor.models.Location)),
                ('stop_times', djongo.models.fields.ArrayField(model_container=traffic_monitor.models.StopTime)),
                ('next_stop_index', models.IntegerField(default=0)),
                ('next_stop_name', models.CharField(default='', max_length=200)),
                ('state', models.CharField(default='', max_length=10)),
                ('latest_update', models.CharField(default='', max_length=70)),
            ],
        ),
    ]
