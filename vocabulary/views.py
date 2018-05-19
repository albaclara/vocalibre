from django.shortcuts import render, redirect
from .forms import ChooseLanguageForm
from .models import Category
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib
from webob.compat import url_quote
import re




def ChooseLanguage(request):
	
	#
	
	
	
	#On récupère les langues pour lesquelles il y a des enregistrements
	endpoint = "http://sparql.0x010c.fr/bigdata/namespace/wdq/sparql/"

	sparql = SPARQLWrapper(endpoint)

	querystring = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

select DISTINCT ?language ?languageLabel
where {
  ?record prop:P2 entity:Q2 .
  ?record prop:P4 ?language .
   SERVICE wikibase:label {
	bd:serviceParam wikibase:language "fr,en" .}
} """
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()

	listLanguages = []
	for result in resultats["results"]["bindings"]:
		labelLang=result["languageLabel"]["value"]
		urlLang=result["language"]["value"]
		print('------------')
		print(urlLang)
		recupcode=re.search(r'/([^/]*?)$', urlLang)
		
		if recupcode:
			codeLang=recupcode.group(1)
		
			listLanguages.append((codeLang, labelLang))
	
	return render(request, 'vocabulary/chooseLanguage.html', locals())
		
		
	
def ChooseSubject(request, langApr):
	endpoint = "https://query.wikidata.org/sparql"
 
	sparql = SPARQLWrapper(endpoint)

	langApr="fr"
	langUt='oc'
	
	listCats=[]
	dicoCats={}
	for category in Category.objects.all():
		idcat=category.wikidataId
	
		querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?label1  WHERE {
  wd:"""+idcat+""" rdfs:label ?label.
  wd:"""+idcat+""" rdfs:label ?label1.
  FILTER(LANG(?label) = '"""+langApr+"""')
  FILTER(LANG(?label1) = '"""+langUt+"""')
}
LIMIT 1
		"""
		
		sparql.setQuery(querystring)
		sparql.setReturnFormat(JSON)
		resultats = sparql.query().convert()
		print('-----------------')
		print(resultats)
		if len(resultats["results"]["bindings"])>0:
			nameApr=resultats["results"]["bindings"][0]["label"]["value"]
			nameUt=resultats["results"]["bindings"][0]["label1"]["value"]
		else:
			nameApr=''
			nameUt=''
		
		
		#Requête pour une image de la catégorie
		querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?image  WHERE {
  ?color wdt:P31 wd:"""+idcat+""".		# instance or subclass of »"""+idcat+"""«
  ?color rdfs:label ?label.				 # store label in ?label
  ?color wdt:P18 ?image .
  FILTER (lang(?label)=\""""+langApr+"""\")
}
LIMIT 1

	"""
		sparql.setQuery(querystring)
		sparql.setReturnFormat(JSON)
		resultats = sparql.query().convert()
		
		if len(resultats["results"]["bindings"])>0:
			image=resultats["results"]["bindings"][0]["image"]["value"]
			
		else:
			image=''
		
		listCats.append(idcat)
		dicoCats[idcat]=(nameApr, nameUt, image)
	
	listCats=sorted_list = sorted(listCats, key=lambda s: s.lower())
	
	listSubjects=[]
	for cat in listCats:
		listSubjects.append((cat, dicoCats[cat][0], dicoCats[cat][1], dicoCats[cat][2]))
	
	return render(request, 'vocabulary/chooseSubject.html', locals())
	
	
	
	
def DisplayWords(request, langApr, subject):
	langUt='oc'
	
	endpoint = "https://query.wikidata.org/sparql"
	endpoint1 = "http://sparql.0x010c.fr/bigdata/namespace/wdq/sparql/"
 
	sparql = SPARQLWrapper(endpoint)
	sparql1 = SPARQLWrapper(endpoint1)

		
		
	#Requête pour le nom de la catégorie
	querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?label1  WHERE {
wd:"""+subject+""" rdfs:label ?label ;  rdfs:label ?label1.
FILTER(LANG(?label) = '"""+langApr+"""')
FILTER(LANG(?label1) = '"""+langUt+"""')
}
LIMIT 1
	"""
	
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()
	print('-----------------')
	print(resultats)
	if len(resultats["results"]["bindings"])>0:
		nameSubjectApr=resultats["results"]["bindings"][0]["label"]["value"]
		nameSubjectUt=resultats["results"]["bindings"][0]["label1"]["value"]
	else:
		nameSubjectApr=''
		nameSubjectUt=''
	
	
	#Requête pour les mots
	querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?color ?label ?label1 ?image (lang(?label) AS ?language)  WHERE {
  ?color wdt:P31 wd:"""+subject+""".		# instance or subclass of »"""+subject+"""«
  ?color rdfs:label ?label.				 # store label in ?label
  OPTIONAL { ?color rdfs:label ?label1.	
  FILTER (lang(?label1)=\""""+langUt+"""\")}			 # store label in ?label
  ?color wdt:P18 ?image .
  FILTER (lang(?label)=\""""+langApr+"""\")
  
}
LIMIT 9

	"""
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()

	labelsWords = set()
	dicoWords={}
	for result in resultats["results"]["bindings"]:
		labelApr=result["label"]["value"]
		if "label1" in result:
			labelUt=result["label1"]["value"]
		else:
			labelUt=''
		image=result["image"]["value"]
			
		print(image)
		
		labelsWords.add(labelApr)
		
		#Requête pour le son
		querystring = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
		
select DISTINCT ?record ?label ?son
where {
  ?record prop:P2 entity:Q2 .
  ?record prop:P3 ?son.
  ?record rdfs:label ?label.
  FILTER (str(?label) = '"""+labelApr+"""').

}

LIMIT 1
"""
		sparql1.setQuery(querystring)
		sparql1.setReturnFormat(JSON)
		resultats = sparql1.query().convert()
		
		if len(resultats["results"]["bindings"])>0:
			son=resultats["results"]["bindings"][0]["son"]["value"]
			searchext=re.search(r'\.([^\.]*?)$', son)
			if searchext:
				extension=searchext.group(1)
			else:
				son=''
				extension=''
			
		else:
			son=''
			extension=''
	
		
		
		
		dicoWords[labelApr]=(image, son, extension, labelUt)
	labelsWords=sorted_list = sorted(labelsWords, key=lambda s: s.lower())
	
	listWords=[]
	for word in labelsWords:
		listWords.append((word, dicoWords[word][0], dicoWords[word][1], dicoWords[word][2], dicoWords[word][3]))
	
	return render(request, 'vocabulary/displayWords.html', locals())
		
		
		
		
