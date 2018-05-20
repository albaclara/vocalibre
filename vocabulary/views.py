from django.shortcuts import render, redirect
from .forms import ChooseLanguageForm
from .models import Category
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib
from webob.compat import url_quote
import re





def ChooseLanguage(request):

	#On récupère les langues pour lesquelles il y a des enregistrements
	endpoint = "http://sparql.0x010c.fr/bigdata/namespace/wdq/sparql/"

	sparql = SPARQLWrapper(endpoint)


	querystring = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

select DISTINCT ?language ?native ?codewd ?iso
where {
  ?record prop:P2 entity:Q2 .
  ?record prop:P4 ?language .
  ?language prop:P12 ?codewd.
  ?language prop:P12 ?wikidataId .

  BIND(uri(concat("http://www.wikidata.org/entity/", ?wikidataId)) as ?wikidataItem).

    SERVICE <https://query.wikidata.org/sparql> {
        ?wikidataItem wdt:P218 ?iso.
        ?wikidataItem wdt:P1705 ?native.
    }
   SERVICE wikibase:label {
    bd:serviceParam wikibase:language "fr,en" .}
} 
	"""

	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()
	
	listIso=[]
	dicoLabel={}
	listLabel=[]
	
	for result in resultats["results"]["bindings"]:
		isoLang=result["iso"]["value"]
		labelLang=result["native"]["value"]
		
		
		if isoLang not in listIso:
			listIso.append(isoLang)
			dicoLabel[labelLang]=isoLang
			listLabel.append(labelLang)
	
	listLabel.sort()
	
	listLanguages=[]
	for label in listLabel:
		listLanguages.append((dicoLabel[label], label))
		
	
	return render(request, 'vocabulary/chooseLanguage.html', locals())





def ChooseTranslation(request, langApr):

	#On récupère les langues existantes
	endpoint = "https://query.wikidata.org/sparql"

	sparql = SPARQLWrapper(endpoint)

	querystring = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

 SELECT ?iso ?native WHERE {
  ?language wdt:P218 ?iso.
  ?language wdt:P1705 ?native.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],fr". }
}  """
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()
	print('-----------')

	listLabels = []
	dicoLanguages= {}
	for result in resultats["results"]["bindings"]:
		labelLang=result["native"]["value"]
		codeLang=result["iso"]["value"]
		listLabels.append(labelLang)
		dicoLanguages[labelLang]=codeLang
		
	listLabels=sorted(listLabels, key=lambda s: s.lower())
	listLanguages=[]
	for language in listLabels:
		listLanguages.append((dicoLanguages[language], language))
	
	return render(request, 'vocabulary/chooseTranslation.html', locals())
		
	
def ChooseSubject(request, langApr, langUt):
	endpoint = "https://query.wikidata.org/sparql"
 
	sparql = SPARQLWrapper(endpoint)
	
	listCats=[]
	dicoCats={}
	for category in Category.objects.all():
		idcat=category.wikidataId
	
		querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?label1 WHERE {
  wd:"""+idcat+""" rdfs:label ?label.
  OPTIONAL {wd:"""+idcat+""" rdfs:label ?label1.
  FILTER(LANG(?label1) = '"""+langUt+"""')
  }
  FILTER(LANG(?label) = '"""+langApr+"""')
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
			if "label1" in resultats["results"]["bindings"][0]:
				nameUt=resultats["results"]["bindings"][0]["label1"]["value"]
			else:
				nameUt=''
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
  ?ident wdt:P31 wd:"""+idcat+""".		# instance or subclass of »"""+idcat+"""«
  ?ident rdfs:label ?label.				 # store label in ?label
  ?ident wdt:P18 ?image .
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
	
	listCats= sorted(listCats, key=lambda s: s.lower())
	
	listSubjects=[]
	for cat in listCats:
		listSubjects.append((cat, dicoCats[cat][0], dicoCats[cat][1], dicoCats[cat][2]))
	
	return render(request, 'vocabulary/chooseSubject.html', locals())
	
	
	
	
def DisplayWords(request, langApr, langUt, subject):
	
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
  wd:"""+subject+""" rdfs:label ?label.
  OPTIONAL {wd:"""+subject+""" rdfs:label ?label1.
  FILTER(LANG(?label1) = '"""+langUt+"""')
  }
  FILTER(LANG(?label) = '"""+langApr+"""')
}
LIMIT 1
	"""
	
	sparql.setQuery(querystring)
	sparql.setReturnFormat(JSON)
	resultats = sparql.query().convert()
	if len(resultats["results"]["bindings"])>0:
		nameSubjectApr=resultats["results"]["bindings"][0]["label"]["value"]
		if "label1" in resultats["results"]["bindings"][0]:
			nameSubjectUt=resultats["results"]["bindings"][0]["label1"]["value"]
		else:
			nameSubjectUt=''
	else:
		nameSubjectApr=''
		nameSubjectUt=''
	
	
	#Requête pour les mots
	querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?label ?label1  WHERE {
  ?ident wdt:P31|wdt:P279 wd:"""+subject+""".		# instance or subclass of »"""+subject+"""«
  ?ident rdfs:label ?label.		
  ?ident wdt:P18 ?image.		 # store label in ?label
  ?ident wikibase:sitelinks ?linkcount .
  OPTIONAL { ?ident rdfs:label ?label1.	
  FILTER (lang(?label1)=\""""+langUt+"""\")}			 # store label in ?label
  ?ident wdt:P18 ?image .
  FILTER (lang(?label)=\""""+langApr+"""\")
  
}
ORDER BY DESC(?linkcount)
LIMIT 12

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
		
		print('------------')
		print(labelApr)
		
		#Requête pour l'image
		querystring="""
SELECT DISTINCT ?item ?itemLabel ?image
WHERE
{
  ?item wdt:P31|wdt:P279 wd:"""+subject+""". 
  ?item rdfs:label ?itemLabel .
  ?item wdt:P18 ?image .
  FILTER(str(?itemLabel) = \""""+labelApr+"""\")
  FILTER (LANG(?itemLabel)=\""""+langApr+"""\")
}
		"""
		
		print(querystring)
		sparql.setQuery(querystring)
		sparql.setReturnFormat(JSON)
		resultats = sparql.query().convert()
		
		
		if len(resultats["results"]["bindings"])>0:
			image=resultats["results"]["bindings"][0]["image"]["value"]
		else:
			image=''
			
		
		print('---------------')
		print(image)
		
			
		labelsWords.add(labelApr)
		
		
		#Requête pour le son
		querystring = """

PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

select ?fichier ?label
where {
    ?record prop:P2 entity:Q2 .
    ?record prop:P3 ?fichier.
    ?record prop:P4 ?language .
  
    ?record prop:P5 ?locutor .
    ?locutor llp:P4 ?languageStatement .
    ?languageStatement llv:P4 ?language .
    ?languageStatement llq:P16 ?languageLevel .
  	
  
  
    ?record rdfs:label ?label.
    ?language prop:P12 ?wikidataId .

    BIND(uri(concat("http://www.wikidata.org/entity/", ?wikidataId)) as ?wikidataItem).

    SERVICE <https://query.wikidata.org/sparql> {
        ?wikidataItem wdt:P218 ?iso.
    }

    SERVICE wikibase:label {
        bd:serviceParam wikibase:language "fr,en" .
    }
    FILTER(str(?label) = \""""+labelApr+"""\")
    FILTER(str(?iso) = '"""+langApr+"""')

} 
ORDER BY DESC(?languageLevel)
LIMIT 1
		"""
		
		sparql1.setQuery(querystring)
		sparql1.setReturnFormat(JSON)
		resultats = sparql1.query().convert()
		
		if len(resultats["results"]["bindings"])>0:
			son=resultats["results"]["bindings"][0]["fichier"]["value"]
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
		
		

def AllWords(request, langApr):
	
	listWords=set()
	for category in Category.objects.all():
		idcat=category.wikidataId
		
		
		endpoint = "https://query.wikidata.org/sparql"
		sparql = SPARQLWrapper(endpoint)
		
		querystring = """
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?label ?label1  WHERE {
  ?ident wdt:P31|wdt:P279 wd:"""+idcat+""".	
  ?ident rdfs:label ?label.		
  ?ident wdt:P18 ?image.		 # store label in ?label
  ?ident wikibase:sitelinks ?linkcount .
  ?ident wdt:P18 ?image .
  FILTER (lang(?label)=\""""+langApr+"""\")
  
}
ORDER BY DESC(?linkcount)
LIMIT 12
"""		
		
		sparql.setQuery(querystring)
		sparql.setReturnFormat(JSON)
		resultats = sparql.query().convert()
	
		for result in resultats["results"]["bindings"]:
			labelApr=result["label"]["value"]
			listWords.add(labelApr)
		
	listWords=list(listWords)
	listWords=sorted(listWords, key=lambda s: s.lower())
	
	return render(request, 'vocabulary/allWords.html', locals())
		
			
