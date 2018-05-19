from django.db import models

# Create your models here.

class Category(models.Model):
	wikidataId=models.CharField(max_length=255, verbose_name='Wikidata ID')
	name=models.CharField(max_length=255, verbose_name='name')

	def __str__(self):
		return str(self.wikidataId)+' ('+self.name+')'
