from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django import forms

from .models import Texto, Charla, texto_guardar
from .forms import TextoForm

import json
import base64

import logging
logger = logging.getLogger(__name__)

def enc_b64_o(o): #U: codificar objeto como json base64
	return base64.b64encode(json.dumps(o).encode('utf-8')).decode('ascii')
def enc_b64_o_r(s, dflt=None): #U: decodificar json base64
	return json.loads(base64.b64decode(s)) if not s is None else dflt

# Create your views here.
def login(request):
  return render(request, 'pa_charlas_app/login.html')

############################################################
@login_required
def texto_edit(request, pk=None, charla_pk=None): #U: sirve para crear Y editar
	texto= None #DFLT, nuevo
	if not pk is None:
		texto= get_object_or_404(Texto, pk=pk) 

	if request.method == "POST":
		form= TextoForm(request.POST, instance= texto)
		if form.is_valid():
			extra_data= enc_b64_o_r(request.POST.get('extra_form_data'),{})
			texto= texto_guardar(form, request.user, extra_data.get('charla'))
			logger.debug(f'VW texto {request.user.username} {extra_data}')
			return redirect(extra_data.get('volver_a') or '/')
	else:
		viene_de= request.META.get('HTTP_REFERER')
		form = TextoForm(instance= texto, initial={'viene_de': 'que_pasa'})
		extra_data= {'charla': charla_pk, 'volver_a': viene_de}
		return render(
			request, 
			'pa_charlas_app/base_edit.html', 
			{
				'form': form, 
				'extra_form_data': enc_b64_o(extra_data),
			})


# S: Charlas ###############################################

class CharlaCreateView(CreateView): 
	template_name= 'pa_charlas_app/base_edit.html'
	model = Charla
	fields = ['tipo','titulo'] 
	success_url= '/charla'

	def form_valid(self, form):
		self.object= form.save(commit=False)
		self.object.de_quien= self.request.user
		self.object.fh_creado= timezone.now()
		self.object.save()
		return HttpResponseRedirect(self.get_success_url())

class CharlaUpdateView(UpdateView): 
	template_name= 'pa_charlas_app/base_edit.html'
	model = Charla
	fields = ['tipo','titulo','textos'] 
	success_url= '/charla'

	def form_valid(self, form):
		self.object= form.save(commit=False)
		self.object.de_quien= self.request.user
		self.object.fh_creado= timezone.now()
		self.object.save()
		return HttpResponseRedirect(self.get_success_url())

class CharlaListView(ListView):
	template_name= 'pa_charlas_app/base_list.html'
	model = Charla
	paginate_by = 20  
	extra_context= {
		'type_name': 'charla',
		'type_url_base': 'charla',
		'create_url': '/charla/new',
		'vista_detalle': 'charla_texto_list_k',
	}

# S: Charla vista comoda ##################################
def charla_texto_list(request, charla_titulo=None, pk=None):
	logger.info(pk)
	if not pk is None:
		charla= get_object_or_404(Charla, pk=pk)
	else:
		charla= get_object_or_404(Charla, titulo= '#'+charla_titulo)
	textos= charla.textos.order_by('fh_creado').all()
	return render(request, 'pa_charlas_app/texto_list.html', {'textos': textos, 'charla': charla, 'titulo': charla.titulo})
