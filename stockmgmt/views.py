from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from tablib import Dataset
import csv, xlrd
import os
from .models import *
from .forms import *
from .resources import StockResource


# Create your views here.
def home(request):
	title = "Welcome: This is the Home Page"
	text = "Here you have lot of fun"
	context = {
		"title" : title,
		"text" : text,
	}
	return redirect('/list_items')
	#return render(request, "home.html", context)

@login_required
def list_items(request):
	header = "LIST OF ITEMS"
	queryset = Stock.objects.all()
	form = StockSearchForm(request.POST or None)
	context = {
		"header" : header,
		"queryset" : queryset,
		"form" : form,
	}

	if request.method == 'POST':
                category = form['category'].value()
		item_name = form['item_name'].value()

		if(category != ''):
			queryset = queryset.filter(category_id = category)

		if(item_name != ""):
			queryset = queryset.filter(item_name__icontains = item_name)
									)
		if form['export_to_CSV'].value() == True:
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="List of stocks.csv"'
			writer = csv.writer(response)
			writer.writerow(['CATEGORY', 'ITEM NAME', 'QUANTITY'])
			instance = queryset
			for stock in instance:
			 writer.writerow([stock.category, stock.item_name, stock.quantity])
			return response
		context = {
		"form": form,
		"header": header,
		"queryset": queryset,
		}
	return render(request, "list_items.html", context)

@login_required
def add_items(request):
	form = StockCreateForm(request.POST or None)

	if form.is_valid():
		form.save()
		messages.success(request, 'Successfully Saved')
		return redirect('/list_items')

	context ={
		"form" : form,
		"title" : "Add Item"
	}
	return render(request, "add_items.html", context)

@login_required
def add_category(request):
	form = CategoryCreateForm(request.POST or None)

	if form.is_valid():
		form.save()
		messages.success(request, 'Category Successfully Saved')
		return redirect('/list_items')

	context = {
		"form" : form,
		"title" : "Add Category"
	}

	return render(request, "add_category.html", context)

@login_required
def upload_items(request):
    form = StockUploadForm(request.POST, request.FILES)
    #text = request.FILES['file'].temporary_file_path
 
    if form.is_valid():
    	#form.save() 	
    	handle_uploaded_file(request,request.FILES['file'])
    	#uploaded_file = request.FILES['file']

    	messages.success(request, "File successfully uploaded")
    	return redirect('/list_items')
        
        #return HttpResponseRedirect('/success/url/')
        
    context= {
    	"form" : form
    }

    return render(request, 'upload_items.html', context)

def handle_uploaded_file(request,filename):
	#loc = r'C:\Users\hp\OneDrive\Documents\StockSample.xlsx'

	wb = xlrd.open_workbook(file_contents = filename.read())
	sheet = wb.sheet_by_index(0)

	for i in range(1, sheet.nrows):
		c, created = Category.objects.get_or_create(name = sheet.cell_value(i,0))
		s = Stock(category = c, item_name = sheet.cell_value(i,1) , quantity = sheet.cell_value(i,2) )
		s.save()



def update_items(request, pk):
	queryset = Stock.objects.get(id=pk)
	form = StockUpdateForm(instance=queryset)
	if request.method == 'POST':
		form = StockUpdateForm(request.POST, instance=queryset)
		if form.is_valid():
			form.save()
			messages.success(request, 'Successfully Saved')
			return redirect('/list_items')

	context = {
		'form':form
	}
	return render(request, 'add_items.html', context)

def delete_items(request, pk):
	queryset = Stock.objects.get(id=pk)
	if request.method == 'POST':
		queryset.delete()
		messages.success(request, 'Deleted Successfully')
		return redirect('/list_items')
	return render(request, 'delete_items.html')

def stock_detail(request, pk):
	queryset = Stock.objects.get(id=pk)
	context = {
		'queryset':queryset
	}
	return render(request, 'stock_detail.html',context)

def issue_items(request, pk):
	queryset = Stock.objects.get(id=pk)
	form = IssueForm(request.POST or None, instance=queryset)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.receive_quantity = 0
		instance.quantity -= instance.issue_quantity
		instance.receive_by = form['issue_to'].value()
		instance.issue_by = str(request.user)
		messages.success(request, "Issued SUCCESSFULLY. " + str(instance.quantity) + " " + str(instance.item_name) + "s are now left in Store")
		instance.save()

		return redirect('/stock_detail/'+str(instance.id))
		# return HttpResponseRedirect(instance.get_absolute_url())

	context = {
		"title": 'Issue ' + str(queryset.item_name),
		"queryset": queryset,
		"form": form,
		"username": 'Issue By: ' + str(request.user),
	}
	return render(request, "add_items.html", context)



def receive_items(request, pk):
	queryset = Stock.objects.get(id=pk)
	form = ReceiveForm(request.POST or None, instance=queryset)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.issue_quantity = 0
		instance.quantity += instance.receive_quantity
		instance.receive_by = str(request.user)
		instance.save()
		messages.success(request, "Received SUCCESSFULLY. " + str(instance.quantity) + " " + str(instance.item_name)+"s are now available in Store")

		return redirect('/stock_detail/'+str(instance.id))
		# return HttpResponseRedirect(instance.get_absolute_url())
	context = {
			"title": 'Reaceive ' + str(queryset.item_name),
			"instance": queryset,
			"form": form,
			"username": 'Receive By: ' + str(request.user),
		}
	return render(request, "add_items.html", context)


def reorder_level(request, pk):
	queryset = Stock.objects.get(id=pk)
	form = ReorderLevelForm(request.POST or None, instance=queryset)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.save()
		messages.success(request, "Reorder level for " + str(instance.item_name) + " is updated to " + str(instance.reorder_level))

		return redirect("/list_items")
	context = {
			"instance": queryset,
			"form": form,
		}
	return render(request, "add_items.html", context)

@login_required
def list_history(request):
	header = 'HISTORY OF ITEMS'
	queryset = StockHistory.objects.all()
	form = StockHistorySearchForm(request.POST or None)
	context = {
		"form" : form,
		"header": header,
		"queryset": queryset,
	}

	if request.method == 'POST':
                category = form['category'].value()
		item_name = form['item_name'].value()
		start_date = form['start_date'].value()
		end_date = form['end_date'].value()

		if (category != ''):
			queryset = queryset.filter(category_id=category)

		if(item_name != ''):
			queryset = queryset.filter(item_name__icontains = item_name)

		if(start_date != '' and end_date != ''):
			queryset = StockHistory.objects.filter(last_updated__range = [form['start_date'].value(),
														form['end_date'].value() ] )
		
		if form['export_to_CSV'].value() == True:
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="Stock History.csv"'
			writer = csv.writer(response)
			writer.writerow(
				['CATEGORY', 
				'ITEM NAME',
				'QUANTITY', 
				'ISSUE QUANTITY', 
				'RECEIVE QUANTITY', 
				'RECEIVE BY', 
				'ISSUE BY', 
				'LAST UPDATED'])
			instance = queryset
			for stock in instance:
				writer.writerow(
				[stock.category, 
				stock.item_name, 
				stock.quantity, 
				stock.issue_quantity, 
				stock.receive_quantity, 
				stock.receive_by, 
				stock.issue_by, 
				stock.last_updated])
			return response

		context = {
		"form": form,
		"header": header,
		"queryset": queryset,
	}
	return render(request, "list_history.html",context)
