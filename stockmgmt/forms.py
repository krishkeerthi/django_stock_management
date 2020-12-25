from django import forms

from .models import Stock,StockHistory,Category

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class StockCreateForm(forms.ModelForm):
	class Meta:
		model = Stock
		fields = ['category', 'item_name', 'quantity']
	def clean_category(self):
		category = self.cleaned_data.get('category')
		if not category:
			raise forms.ValidationError('This field is required')
		return category


	def clean_item_name(self):
		item_name = self.cleaned_data.get('item_name')
		if not item_name:
			raise forms.ValidationError('This field is required')

		for instance in Stock.objects.all():
			if instance.item_name == item_name:
				raise forms.ValidationError(item_name + ' does exist already!')
		return item_name

class CategoryCreateForm(forms.ModelForm):
	class Meta:
		model = Category
		fields = ['name']

	def clean_name(self):
		category = self.cleaned_data.get('name')

		if not category:
			raise forms.ValidationError('This field is required')

		for instance in Category.objects.all():
			if instance.name == category:
				raise forms.ValidationError(category + ' exists already!')

		return category

class StockUploadForm(forms.ModelForm):
	file = forms.FileField()
	class Meta:
		model = Stock
		fields = ['file']

class StockSearchForm(forms.ModelForm):
   export_to_CSV = forms.BooleanField(required = False)
   export_to_PDF = forms.BooleanField(required = False)
   class Meta:
    model = Stock
    fields = ['category', 'item_name']

class StockHistorySearchForm(forms.ModelForm):
   export_to_CSV = forms.BooleanField(required = False)
   export_to_PDF = forms.BooleanField(required = False)
   start_date = forms.DateTimeField(required = False)
   end_date = forms.DateTimeField(required = False)
   class Meta:
    model = StockHistory
    #widgets = {'start_date' : DateInput()}
    fields = ['category', 'item_name', 'start_date', 'end_date']

class StockUpdateForm(forms.ModelForm):
	class Meta:
		model = Stock
		fields = ['category', 'item_name', 'quantity']

class IssueForm(forms.ModelForm):
	class Meta:
		model = Stock
		fields = ['issue_quantity', 'issue_to']


class ReceiveForm(forms.ModelForm):
	class Meta:
		model = Stock
		fields = ['receive_quantity']

class ReorderLevelForm(forms.ModelForm):
	class Meta:
		model = Stock
		fields = ['reorder_level']

class CustomUserCreationForm(UserCreationForm):
	email = forms.EmailField()
	class Meta():
		model = User
		fields = ["username" , "email", "password1", "password2"]

class AuthenticationFormWithInactiveUsersOkay(AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass
