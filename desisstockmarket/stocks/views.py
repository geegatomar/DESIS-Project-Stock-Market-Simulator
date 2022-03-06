from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

stocks = [
    {'id': 1, 'name': 'GOOGL'},
    {'id': 2, 'name': 'MCRSFT'},
    {'id': 3, 'name': 'ADOBE'},
]


def home(request):
    context = {'stocks': stocks}
    return render(request, 'stocks/home.html', context)


def info(request, id):
    # TODO: Typically later we will be picking out the entry from the database.
    return HttpResponse(id)
