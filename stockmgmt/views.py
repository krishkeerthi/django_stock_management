from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from tablib import Dataset
import csv, xlrd
import os
from .models import *
from .forms import *
from .resources import StockResource
#for pdf 
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph


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
	queryset = Stock.objects.filter(user_id = request.user)
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
									
		if form['export_to_CSV'].value() == True:
			x = datetime.datetime.now()
			filename = "ListOfStocks" +str(x.strftime("%x")) + ".csv"

			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="%s"' %filename
			writer = csv.writer(response)
			writer.writerow(['CATEGORY', 'ITEM NAME', 'QUANTITY'])
			instance = queryset
			for stock in instance:
			 writer.writerow([stock.category, stock.item_name, stock.quantity])
			return response

		if form['export_to_PDF'].value() == True:
			buffer = io.BytesIO()

			# container for the 'Flowable' objects
			elements = []
			cm = 2.54
			user = str(request.user).capitalize()

			doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=15 * cm, leftMargin=15 * cm, topMargin=10 * cm, bottomMargin=0)

			data= [ ['YOUR STOCK MANAGEMENT', '', user ],
			['','LIST OF STOCKS',''],
			['CATEGORY','ITEM NAME', 'QUANTITY']]

			for stock in queryset:
				lst =[stock.category, stock.item_name, stock.quantity]
				data.append(lst)

			t=Table(data, colWidths=200, rowHeights=50)
			t.setStyle(TableStyle([('GRID',(0,2),(-1,-1), 1, colors.black)]))

			elements.append(t)
			# write the document to disk
			doc.build(elements)

			buffer.seek(0)
			x = datetime.datetime.now()
			fname = "ListOfStocks" +str(x.strftime("%x")) + ".pdf"

			return FileResponse(buffer, as_attachment = True, filename = fname)
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
		fs =form.save(commit = False)
		fs.user = request.user
		fs.save()
		messages.success(request, 'Item Added Successfully ')
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
		messages.success(request, 'Category Added Successfully ')
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

    	messages.success(request, "File Uploaded Successfully ")
    	return redirect('/list_items')
        
        #return HttpResponseRedirect('/success/url/')
        
    context= {
    	"form" : form
    }

    return render(request, 'upload_items.html', context)

def handle_uploaded_file(request,filename):
	#loc = r'C:\Users\hp\OneDrive\Documents\StockSample.xlsx'
	queryset = Stock.objects.filter(user = request.user)

	wb = xlrd.open_workbook(file_contents = filename.read())
	sheet = wb.sheet_by_index(0)

	for i in range(1, sheet.nrows):
		cate = sheet.cell_value(i,0)
		itemName = sheet.cell_value(i,1)
		quant = sheet.cell_value(i,2)
		visited = False

		c, created = Category.objects.get_or_create(name = cate.title())

		for instance in queryset:
			if instance.category == c and instance.item_name == itemName.title():
				instance.quantity += quant
				instance.save()
				visited = True
				break

		if not visited:
			s = Stock(category = c, item_name = itemName.title() , quantity = quant, user = request.user )
			s.save()

		queryset = Stock.objects.filter(user = request.user)


def update_items(request, pk):
	queryset = Stock.objects.get(id=pk, user = request.user)
	form = StockUpdateForm(instance=queryset)
	if request.method == 'POST':
		form = StockUpdateForm(request.POST, instance=queryset)
		if form.is_valid():
			form.save()
			messages.success(request, 'Updated Successfully ')
			return redirect('/list_items')

	context = {
		'form':form
	}
	return render(request, 'add_items.html', context)

def delete_items(request, pk):
	queryset = Stock.objects.get(id=pk, user = request.user)
	if request.method == 'POST':
		queryset.delete()
		messages.success(request, 'Deleted Successfully')
		return redirect('/list_items')
	return render(request, 'delete_items.html')

def stock_detail(request, pk):
	queryset = Stock.objects.get(id=pk, user = request.user)
	context = {
		'queryset':queryset
	}
	return render(request, 'stock_detail.html',context)

def issue_items(request, pk):
	queryset = Stock.objects.get(id=pk, user = request.user)
	form = IssueForm(request.POST or None, instance=queryset)
	if form.is_valid():
		instance = form.save(commit=False)
		#instance.receive_quantity = 0
		instance.quantity -= instance.issue_quantity
		instance.receive_by = form['issue_to'].value()
		instance.issue_by = str(request.user)
		messages.success(request, "Issued SUCCESSFULLY. " + str(instance.quantity) + " " + str(instance.item_name) + "s are now left in Store")
		instance.save()

		issue_history = StockHistory(
			#id = instance.id, 
			last_updated = instance.last_updated,
			category_id = instance.category_id,
			item_name = instance.item_name, 
			quantity = instance.quantity, 
			receive_by = instance.receive_by, 
			issue_by = instance.issue_by, 
			issue_quantity = instance.issue_quantity,
			user_id = instance.user_id
			)
		issue_history.save()

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
	queryset = Stock.objects.get(id=pk, user = request.user)
	form = ReceiveForm(request.POST or None, instance=queryset)
	if form.is_valid():
		instance = form.save(commit=False)
		#instance.issue_quantity = 0
		instance.quantity += instance.receive_quantity
		instance.receive_by = str(request.user)
		instance.save()

		receive_history = StockHistory(
			#id = instance.id, 
			last_updated = instance.last_updated,
			category_id = instance.category_id,
			item_name = instance.item_name, 
			quantity = instance.quantity, 
			receive_quantity = instance.receive_quantity, 
			receive_by = instance.receive_by,
			user_id = instance.user_id
			)
		receive_history.save()
		messages.success(request, "Received SUCCESSFULLY. " + str(instance.quantity) + " " + str(instance.item_name)+"s are now available in Store")

		return redirect('/stock_detail/'+str(instance.id))
		# return HttpResponseRedirect(instance.get_absolute_url())
	context = {
			"title": 'Receive ' + str(queryset.item_name),
			"instance": queryset,
			"form": form,
			"username": 'Receive By: ' + str(request.user),
		}
	return render(request, "add_items.html", context)


def reorder_level(request, pk):
	queryset = Stock.objects.get(id=pk, user = request.user)
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
	queryset = StockHistory.objects.filter(user_id = request.user)
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
			queryset = queryset.filter(item_name__icontains = item_name )

		if(start_date != '' and end_date != ''):
			queryset = StockHistory.objects.filter(last_updated__range = [start_date, end_date] )
		
		if form['export_to_CSV'].value() == True:
			x = datetime.datetime.now()
			filename = "ListOfStocks" +str(x.strftime("%x")) + ".csv"

			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="%s"' % filename
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

		if form['export_to_PDF'].value() == True:
			buffer = io.BytesIO()

			# container for the 'Flowable' objects
			elements = []
			cm = 2.54
			user = str(request.user).capitalize()

			doc = SimpleDocTemplate(buffer, rightMargin=5 * cm, leftMargin=5 * cm, topMargin=10 * cm, bottomMargin=0)

			data= [ ['YOUR STOCK MANAGEMENT','','' ,'','','','',user],
			['','','' ,'HISTORY OF STOCKS','', '', '',''],
			['CATEGORY','ITEM NAME', 'QUANTITY',Paragraph('ISSUE QUANTITY'), Paragraph('RECEIVE QUANTITY'), 'RECEIVE BY', 'ISSUE BY',Paragraph('LAST UPDATED')]]

			for stock in queryset:
				time = stock.last_updated.strftime("%d/%m/%Y, %H:%M:%S")
				lst =[Paragraph(str(stock.category)), Paragraph(stock.item_name), stock.quantity, stock.issue_quantity, stock.receive_quantity, stock.receive_by, stock.issue_by, Paragraph(time) ]
				data.append(lst)

			t=Table(data, colWidths=70, rowHeights=50)
			t.setStyle(TableStyle([('GRID',(0,2),(-1,-1), 1, colors.black)]))

			elements.append(t)
			# write the document to disk
			doc.build(elements)

			buffer.seek(0)
			x = datetime.datetime.now()
			fname = "HistoryOfStocks" +str(x.strftime("%x")) + ".pdf"

			return FileResponse(buffer, as_attachment = True, filename = fname)

		context = {
		"form": form,
		"header": header,
		"queryset": queryset,
	}
	return render(request, "list_history.html",context)


def register(request):
	form = CustomUserCreationForm(request.POST)
	if request.method == "POST":
		if form.is_valid():
			user = form.save()
			user.is_active = True
			login(request, user)

		return redirect("/list_items")

	return render(request, "register.html", {"form" : form, "title" : "Sign Up"})


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationFormWithInactiveUsersOkay(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                #messages.info(request, f"You are now logged in as {username}")
                return redirect('/list_items')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationFormWithInactiveUsersOkay()

    return render(request, "login.html", {"form":form, "title" : "Log in"})

def logout_request(request):
    logout(request)

    return render(request, "logout.html")
