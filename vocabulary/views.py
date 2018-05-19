from django.shortcuts import render, redirect
from .forms import ChooseLanguageForm
from .models import Category
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib
from webob.compat import url_quote
import re




def ChooseLanguage(request):

	form = ChooseLanguageForm(request.POST or None)
	listLanguages=[('oc','occitan'), ('fr','french')]
	
	return render(request, 'vocabulary/chooseLanguage.html', locals())
		
		
	
def ChooseSubject(request, lang):
	endpoint = "https://query.wikidata.org/sparql"
 
	sparql = SPARQLWrapper(endpoint)

	
	
	listCats=[]
	dicoCats={}
	for category in Category.objects.all():
		idcat=category.wikidataId
		
		
		#Requête pour le nom de la catégorie
		querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label  WHERE {
  wd:"""+idcat+""" rdfs:label ?label.
  FILTER(LANG(?label) = '"""+lang+"""')
}
LIMIT 1

    """
		
		sparql.setQuery(querystring)
		sparql.setReturnFormat(JSON)
		resultats = sparql.query().convert()
		
		if len(resultats["results"]["bindings"])>0:
			name=resultats["results"]["bindings"][0]["label"]["value"]
		else:
			name=''
		
		
		#Requête pour une image de la catégorie
		querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?image  WHERE {
  ?color wdt:P31 wd:"""+idcat+""".        # instance or subclass of »"""+idcat+"""«
  ?color rdfs:label ?label.                 # store label in ?label
  ?color wdt:P18 ?image .
  FILTER (lang(?label)=\""""+lang+"""\")
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
		dicoCats[idcat]=(name, image)
	
	listCats=sorted_list = sorted(listCats, key=lambda s: s.lower())
	
	listSubjects=[]
	for cat in listCats:
		listSubjects.append((cat, dicoCats[cat][0], dicoCats[cat][1]))
	
	return render(request, 'vocabulary/chooseSubject.html', locals())
	
	
	
	
def DisplayWords(request, lang, subject):
	
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

SELECT ?label  WHERE {
  wd:"""+subject+""" rdfs:label ?label.
  FILTER(LANG(?label) = '"""+lang+"""')
}
LIMIT 1

    """
    
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()
	
	if len(resultats["results"]["bindings"])>0:
		nameSubject=resultats["results"]["bindings"][0]["label"]["value"]
	else:
		nameSubject=''
    
    
    #Requête pour les mots
	querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?color ?label ?image (lang(?label) AS ?language)  WHERE {
  ?color wdt:P31 wd:"""+subject+""".        # instance or subclass of »"""+subject+"""«
  ?color rdfs:label ?label.                 # store label in ?label
  ?color wdt:P18 ?image .
  FILTER (lang(?label)=\""""+lang+"""\")
  
}
LIMIT 9

    """
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()

	labelsWords = set()
	dicoWords={}
	for result in resultats["results"]["bindings"]:
		label=result["label"]["value"]
		image=result["image"]["value"]
			
		print(image)
		
		labelsWords.add(label)
		
		#Requête pour le son
		querystring = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
		
select DISTINCT ?record ?label ?son
where {
  ?record prop:P2 entity:Q2 .
  ?record prop:P3 ?son.
  ?record rdfs:label ?label.
  FILTER (str(?label) = '"""+label+"""').

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
	
		
		
		
		dicoWords[label]=(image, son, extension)
	labelsWords=sorted_list = sorted(labelsWords, key=lambda s: s.lower())
	
	listWords=[]
	for word in labelsWords:
		listWords.append((word, dicoWords[word][0], dicoWords[word][1], dicoWords[word][2]))
	
	return render(request, 'vocabulary/displayWords.html', locals())
		
		
		
		
