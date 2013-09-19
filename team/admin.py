#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib import admin
from models import Team, Metric, TeamMember, File, MetricData

class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0

class TeamAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [TeamMemberInline]

class MetricAdmin(admin.ModelAdmin):
    list_display = ['team', 'name', 'completed_units', 'cost_per_unit', 'unit_cost_goal',
    	'hours_per_task', 'team_size','description', 'expectedValue', 'hourlyRate',
    	'team_size', 'four_week_cost', 'annual_cost', 'high_result', 'average_result', 
    	'low_result']
    list_editable = ['name', 'description', 'expectedValue', 'hourlyRate']
    list_filter = ['team', 'name']

class TeamMemberAdmin(admin.ModelAdmin):
    list_display =['team', 'name']

class FileAdmin(admin.ModelAdmin):
    list_display =['name', 'uploadDate']

class MetricDataAdmin(admin.ModelAdmin):
    list_display =['member', 'metric', 'metricDate', 'value', 'status']



admin.site.register(Team, TeamAdmin)
admin.site.register(Metric, MetricAdmin)
admin.site.register(TeamMember, TeamMemberAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(MetricData, MetricDataAdmin)