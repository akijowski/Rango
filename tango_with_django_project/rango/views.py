from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
#import my custom encode/decode method
from django.shortcuts import encode_url
from django.shortcuts import decode_url
#import the Category model
from rango.models import Category
from rango.models import Page

from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from datetime import datetime


def index(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)
	
	# Set a Test Cookie to see if it appears in Register()
    #request.session.set_test_cookie()
    
	#Query the database for a list of ALL categories currently stored.
	#Order the categories by no. likes in descending order.
	#Retrieve the top 5 only - or all if less than 5.
	#Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:5]
    context_dict = {'categories': category_list}
	
	# The following two lines are new.
	# We loop through each category returned, and create a URL attribute.
	# This attribute stores an encoded URL (e.g. spaces replaced with underscores).
    for category in category_list:
		#category.url = category.name.replace(' ', '_')	
		category.url = encode_url(category.name)
	
	page_list = Page.objects.order_by('-views')[:5]
	context_dict['pages'] = page_list
	
	# Obtain our Response object early so we can add cookie information
	response = render_to_response('rango/index.html', context_dict, context)
	
	# Get the number of visitors to the site
	# We use COOKIES.get() function to obtain the visits cookie
	# If the cookie exists, the value returned is casted to an integer
	# If the cookie doesn't exist, we default to zero and cast that
	visits = int(request.COOKIES.get('visits', '0'))
	
	# Does the cookie last_visit exist?
	if request.COOKIES.has_key('last_visit'):
		# Yes it does! Get the cookie's value
		last_visit = request.COOKIES['last_visit']
		# Cast the value to a Python date/time object
		last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
		
		# If it's been more than a day
		if (datetime.now() - last_visit_time).days > 0:
			# Reassign the value of the cookie to +1 of what it was
			response.set_cookie('visits', visits+1)
			# Update the last visit cookie, too
			response.set_cookie('last_visit', datetime.now())
			
	else:
		# Cookie last_visit doesn't exist, so create it to the current time
		response.set_cookie('last_visit', datetime.now())
		
	# Return response back to user, updating any cookies
	# return response
	
    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    #context_dict = {'boldmessage': "I am bold font from the context"}
    
    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    # return HttpResponse("Rango Says: Here is the About page! <br> <a href='/rango'>Go Back</a>")
    context = RequestContext(request)
    
    context_dict = {'secondmessage': "This is another bold message"}
    
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
	# Request our context from the request passed to us.
	context = RequestContext(request)
	
	#Change underscores in the category name to spaces.
	# URLs don't handle spaces well, so we encode them as underscores.
	# We can then simply replace the underscores with spaces again to get the name.
	category_name = category_name_url.replace('_', ' ')
	
	# Create a context dictionary which we can pass to the template rendering engine
	# We start by containing the name of the category passed by the user
	context_dict = {'category_name': category_name}
	
	try:
		#Can we find a category with the given name?
		#If we can't, the .get() method raises a DoesNotExist error
		#So the .get() method returns one model instance or raises an exception.
		category = Category.objects.get(name=category_name)
		
		#Retrieve all of the associated pages.
		#Note that filter returns >= 1 model instance.
		pages = Page.objects.filter(category=category)
		
		#Adds our results list to the template context under name pages
		context_dict['pages'] = pages
		#We also add the category object from the database to the context dictionary.
		#We'll use this in the template to verify that the category exists.
		context_dict['category'] = category
		
		#Add the category_name_url to the dictionary for the addPage form
		context_dict['category_name_url'] = category_name_url
	except Category.DoesNotExist:
		# We get here if we didn't find the specified category.
		# Don't do anything - the template displays the "no category found" message for us.
		pass
	
	# Go render the response and return it to the client
	return render_to_response('rango/category.html', context_dict, context)

def add_category(request):
	# Get the context from the request
	context = RequestContext(request)
	
	# A HTTP Post?
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		
		# Have we been provided a valid form?
		if form.is_valid():
			# Save the new category to the database
			form.save(commit=True)
			
			# Now call the index() view
			# The user will be shown the homepage
			return index(request)
		else:
			# The supplied form contained errors - just print them to the terminal
			print form.errors
	else:
		# If the request was not a POST, display the form to enter details
		form = CategoryForm()
		
	# Bad form (or form details), no form supplied...
	# Render the form with error messages (if any).
	return render_to_response('rango/add_category.html', {'form': form}, context)

def add_page(request, category_name_url):
	context = RequestContext(request)
	
	category_name = decode_url(category_name_url)
	if request.method == 'POST':
		form = PageForm(request.POST)
		
		if form.is_valid():
			# This time we can not commit straight away.
			# Not all fields are automatically populated!
			page = form.save(commit=False)
			
			# Retrieve the associated Category object so we can add it
			# Wrap the code in a try block - check if the category actually exists!
			try:
				cat = Category.objects.get(name=category_name)
				page.category = cat
			except Category.DoesNotExist:
				# If we get here, the category does not exist.
				# Go back and render the add category form as a way of saying the category does not exist
				return render_to_response('rango/add_category.html', {}, context)
				
			# Also, create a default value for the number of views
			page.views = 0
			
			# With this, we can then save our new model instance.
			page.save()
			
			# Now that the page is saved, display the category instead
			return category(request, category_name_url)
		else:
			print form.errors
	else:
		form = PageForm()
		
	return render_to_response( 'rango/add_page.html',
			{'category_name_url': category_name_url,
			'category_name': category_name, 'form': form},
			 context)

def register(request):
	# like before, get the request's context
	context = RequestContext(request)
	
	# See if a Test Cookie from Index() was received.
	#if request.session.test_cookie_worked():
		#print ">>> TEST COOKIE WORKED!"
		#request.session.delete_test_cookie()
	
	# A boolean value for telling the template whether the registration was succesful.
	# Set to False initially, change to True when registration is successful.
	registered = False
	
	# If it's a HTTP POST, we're interested in processing form data
	if request.method == 'POST':
		# Attempt to grab information from the raw form information
		# Note that we make use of both UserForm and UserProfileForm
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		
		# If the two forms are valid
		if user_form.is_valid() and profile_form.is_valid():
			# Save the user's form data to the database.
			user = user_form.save()
			
			# Now we hash the password with the set_password method
			# Once hashed, we can update the user object.
			user.set_password(user.password)
			user.save()
			
			# Now sort out the UserProfile instance.
			# Since we need to set the user attribute ourselves, we set commit=False.
			# This delays saving the model until we're ready to avoid integrity problems
			profile = profile_form.save(commit=False)
			# Reference the User model instance to the UserProfile
			profile.user = user
			
			# Did the user provide a profile picture
			# If so, we need to get it from the input form and put it in the UserProfile model
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			
			# Now we can save the UserProfile model instance
			profile.save()
			
			# Update our variable to tell the template registration was successful
			registered = True
			
		# Invalid form or forms - mistakes or something else?
		# Print problems to the terminal
		# They'll also be shown to the user.
		else:
			print user_form.errors, profile_form.errors
		
	# Not a HTTP POST, so we render our form using two ModelForm instances
	# These forms will be blank, ready for user input.
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
		
	# Render the template depending on the context
	return render_to_response(
			'rango/register.html',
			{'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
			context)

def user_login(request):
	context = RequestContext(request)
	
	# If the request is a POST, try to pull out the relevant information
	if request.method == 'POST':
		# Gather the username and password provided by the user.
		# This information is obtained from the login form
		username = request.POST['username']
		password = request.POST['password']
		
		# Use Django's machinery to attempt to see if the username and password
		# combination is valid - a User object is returned if it is.
		user = authenticate(username=username, password=password)
		
		# If we have a User object, the details are correct.
		# If none (Python's way of representing the absence of a value, no User
		# with matching credentials was found.
		if user is not None:
			# Is the account active? It could be disabled.
			if user.is_active:
				# If the account is valid and active, we can log the user in
				# We'll send the user back to the homepage.
				login(request, user)
				return HttpResponseRedirect('/rango/')
			else:
				# An inactive account was used - no logging in!
				return HttpResponse("Your Rango account is disabled.")
		else:
			# Bad login details were provided (from authenticate()). So we can't log the user in.
			print "Invalid login details: {0}, {1}".format(username,password)
			return HttpResponse("Invalid login details supplied.")
		
	# The request is not a POST, so display the login form
	# This scenario would most likely be a GET
	else:
		# No context variables to pass to the templay system, hence the
		# blank dictionary object
		return render_to_response('rango/login.html', {}, context)
		
@login_required
def restricted(request):
	context = RequestContext(request)
	return render_to_response('rango/restricted.html', {}, context)
	
# Use the login required decorator to ensure only those logged in can access the view
@login_required
def user_logout(request):
	# Since we know the user is logged in, we can now just log them out
	logout(request)
	
	# Take the user back to the homepage
	return HttpResponseRedirect('/rango/')