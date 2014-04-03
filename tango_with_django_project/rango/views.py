from django.http import HttpResponse

def index(request):
    return HttpResponse("Rango says Hello World! <br> <a href='./about'>About</a>")

def about(request):
    return HttpResponse("Rango Says: Here is the About page! <br> <a href='/rango'>Go Back</a>")
