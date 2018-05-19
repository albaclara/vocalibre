from django import forms

class ChooseLanguageForm(forms.Form):
	language = forms.CharField(required=True)
	
	

	
