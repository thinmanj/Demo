#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models
from decimal import Decimal
from django.db.models import Avg, Max, Min, Sum
import datetime


# Create your models here.
class Team(models.Model):
	name = models.CharField(max_length=200, unique=True)

	def __unicode__(self):
		return self.name

class Metric(models.Model):
	team = models.ForeignKey(Team)
	name = models.CharField(max_length=50, unique=True)
	description = models.CharField(max_length=200, default="No description")
	expectedValue = models.IntegerField("Expected Metric", default=0)
	hourlyRate = models.DecimalField("Hourly Rate ($)", max_digits=6,decimal_places=2, default=Decimal('0'))

	class Meta:
		unique_together = (("team", "name"),)

	def __unicode__(self):
		return "%s"%(self.name)

	def dateSpan(self):
		#
		# To get the 4 week span
		#

		toDate = self.metricdata_set.aggregate(toDate=Max('metricDate'))['toDate']
		delta = datetime.timedelta(21)
		fromDate = toDate - delta
		return fromDate, toDate

	def lastDate(self):
		#
		# Get the most recent week
		#

		return self.metricdata_set.aggregate(toDate=Max('metricDate'))['toDate']

	#Yellow columns
	def completed_units(self):
		fromDate, toDate = self.dateSpan()
		return self.metricdata_set.filter(status=True).exclude(value=0).filter(metricDate__range=(fromDate, toDate)).aggregate(sum=Sum('value'))['sum']

	def team_size(self):
		return self.metricdata_set.filter(status=True).exclude(value=0).filter(metricDate=self.lastDate()).count()

	def high_result(self):
		fromDate, toDate = self.dateSpan()
		return self.metricdata_set.filter(status=True).exclude(value=0).filter(metricDate__range=(fromDate, toDate)).aggregate(max=Max('value'))['max']

	def average_result(self):
		fromDate, toDate = self.dateSpan()
		return self.metricdata_set.filter(status=True).exclude(value=0).filter(metricDate__range=(fromDate, toDate)).aggregate(avg=Avg('value'))['avg']

	def low_result(self):
		fromDate, toDate = self.dateSpan()
		return self.metricdata_set.filter(status=True).exclude(value=0).filter(metricDate__range=(fromDate, toDate)).aggregate(min=Min('value'))['min']

	#Green columns
	def cost_per_unit(self):
		cu = self.completed_units()
		if not cu:
			return "NA"
		#return (self.hourlyRate*self.team_size()*160)/self.completed_units()
		return self.four_week_cost()/cu

	def unit_cost_goal(self):

		d = self.expectedValue*self.team_size()
		if not d:
			return "NA"

		return self.four_week_cost()/(self.expectedValue*self.team_size())

	def hours_per_task(self):
		if not self.expectedValue:
			return "NA"
		else:
			return 40.0/(self.expectedValue/4)

	def four_week_cost(self):
		return self.hourlyRate*self.team_size()*160

	def annual_cost(self):
		return self.four_week_cost()*13

class TeamMember(models.Model):
	team = models.ForeignKey(Team)
	oId = models.CharField("oDesk ID", max_length=50, unique=True)
	name = models.CharField(max_length=100)

	def __unicode__(self):
		return "%s - %s"%(self.team.name, self.name)

class File(models.Model):
	name = models.CharField("File Name", max_length=50)
	uploadDate = models.DateTimeField(auto_now=True)
	data = models.TextField("File Data")
	status = models.TextField("Uplad Status")

	class Meta:
		unique_together = (("name", "uploadDate"),)

	def __unicode__(self):
		return u"%s [%s]"%(self.name, self.uploadDate)

class MetricData(models.Model):
	member = models.ForeignKey(TeamMember)
	metric = models.ForeignKey(Metric)
	fileLoaded = models.ForeignKey(File, null=True)
	metricDate = models.DateField()
	value = models.IntegerField("Metric Value")
	status = models.BooleanField(default=True)

	class Meta:
		verbose_name_plural = "Metrics Data"

	def __unicode__(self):
		return u"%s - %s (%d) [%s]"%(self.member.name, self.metric.name, self.value, self.metricDate)

