from django.test import TestCase
from django.test.client import Client
from team.models import Metric


class ImportMetricsTest(TestCase):
    def test_load_correct_csv(self):
    	"""
    	Test the load of a correct formated csv
    	"""
    	c = Client()
    	with open('metrics_example-corrected.csv') as fp:
    		response = c.post('/team/importMetrics/', {'file': fp})

    	self.assertTrue(response.content.index('team=&#39;Example&#39; metric=&#39;Example&#39; processed 36 actuals. 9 members by 4 weeks.')>0)

    def test_load_incorrect_date_csv(self):
    	"""
    	Test the load of a bad format date csv file
    	"""
    	c = Client()
    	with open('metrics_example(2).csv') as fp:
    		response = c.post('/team/importMetrics/', {'file': fp})

    	self.assertTrue(response.content.index('25/3/2012 could not parsed correctly')>0)

class DisplayTeamTest(TestCase):
	fixtures = ['team.json']

	def test_team_names_last_week(self):
		c = Client()
		response = c.post('/team/displayTeam/', {'team':'1', 'weekend':'10/14/2012'})

		self.assertTrue(response.content.index('Mayola, Ralph King')>0)

	def test_team_names_one_week_earlyer(self):
		c = Client()
		response = c.post('/team/displayTeam/', {'team':'1', 'weekend':'10/07/2012'})
		with self.assertRaises(ValueError):
			response.content.index('Mayola, Ralph King')

class DisplayTeamsListTest(TestCase):
	fixtures = ['team.json']

	def setUp(self):
		#call_setup_methods()
		self.example = Metric.objects.filter(name='Example').all()[0]

	def test_calculations_of_team(self):
		"""
		Should calculate values of excle dashboard
		"""
		self.assertEqual(self.example.completed_units(), 190)
		self.assertEqual(self.example.team_size(), 9)
		self.assertEqual(self.example.four_week_cost(), 21600)
