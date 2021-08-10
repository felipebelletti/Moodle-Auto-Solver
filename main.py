# -*- coding: utf-8 -*-
import requests, re, time, os, sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from random import randint

if os.name == 'nt':    #arrumar bugs compatibilidade windows
	os.system("color") #fix bcolors
	os.system("chcp 65001 >nul 2>&1 & set PYTHONIOENCODING=utf-8") #fix unicode

class bcolors:
    PURPLE = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def detectar_novas_atividades(curso_nome, curso_url):
	d.get(curso_url)
	global source
	source = d.page_source.encode('utf-8')
	if 'Não concluído' in source or 'Sem envio' in source:
		return 1 #tem tarefas a serem feitas
	else:
		return 0 #sem tarefas para fazermos

error_strings = ['Esta tarefa aceitará envios a partir de', 'Enviado para avaliação', 'Enviada(s)']
def erronatarefa(inputstr):
	for x in error_strings:
		if x in inputstr:
			return True
	return False

def log(msg, parse=2):
	p = ">"
	print bcolors.YELLOW+str(p)*parse+bcolors.ENDC+' '+msg+bcolors.ENDC

###################### webdriver setup ######################
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("download.default_directory=/dev/null")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
d = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)

###################### login ######################
d.get('https://ead.cp2.g12.br/')

if "Error: Database connection failed" in d.page_source:
	#print bcolors.PURPLE+"Error: Database connection failed",bcolors.ENDC
	log('EAD '+bcolors.RED+'offline'+bcolors.ENDC+' zzzzz'+bcolors.ENDC)
	d.quit()
	exit(1)

userfield = d.find_element_by_name('username')
passfield = d.find_element_by_name('password')

#user = raw_input("Username: ")
#passwd = raw_input("Password: ")

#userfield.send_keys(user)
#passfield.send_keys(passwd)
passfield.send_keys(Keys.RETURN)

if "Por favor tente outra vez" in d.page_source: ##se passar disso: login feito com sucesso
	log('Login error, check your credentials')
	d.quit()
	exit(1)

log('Logado com '+bcolors.OKGREEN+'sucesso\n')

source1 = d.page_source.encode('utf-8')

if 'O sistema está em manutenção e não está disponível no momento.' in source1:
	log('EAD '+bcolors.RED+'indisponivel'+bcolors.ENDC+': O sistema está em manutenção e não está disponível no momento.')
	d.quit()
	exit(1)

nomes_cursos = re.findall('\<p\>\<strong\>(.*?)<\/strong>', source1)
links_cursos = re.findall('href="(https:\/\/ead\.cp2\.g12\.br\/course\/view\.php.*?)"', source1)

cursos = []
#print '| CURSO |\t\t| URL |'
for i in range(0, len(nomes_cursos)):
	#print str(" ".join(nomes_cursos[i].split(" ")[1:4])).replace("-", "").lstrip(" ").rstrip(" ")
	cursos.append('{nome_curso}|{link_curso}'.format(nome_curso=str(" ".join(nomes_cursos[i].split(" ")[1:4])).replace("-", "").lstrip(" ").rstrip(" "), link_curso=links_cursos[i]))

## pegar cookies do selenium para trabalho futuro ##
cookies_list = d.get_cookies()
cookies_dict = {}
for cookie in cookies_list:
	cookies_dict[cookie['name']] = cookie['value']

log('Checkando por novas atividades em cada um dos cursos..')
for curso in cursos:
	abas = []
	curso_nome = curso.split("|")[0]
	curso_url = curso.split("|")[1]
	log('Checking %s..'%(curso_nome))
	d.get(curso_url)
	if 'section=0' in d.page_source.encode('utf-8'): #curso tem abas diferentes
		pattern = 'class="dropdown-item" href="{curso_url}&amp;section=(.*?)">'.format(curso_url=curso_url.replace('/', '\/').replace('.', '\.').replace('?', '\?'))
		abascurso = re.findall(pattern, d.page_source.encode('utf-8'))
		for aba in abascurso:
			if len(str(aba)) >= 3:
				pass
			else:
				#print aba
				abas.append(curso_url + "&section=" + str(aba))
	else:
		abas.append(curso_url)
	#print abas

	for curso_url in abas:
		if detectar_novas_atividades(curso_nome, curso_url) == 1:
			### detectar multi abas ###
			if 'section' in curso_url:
				existemabas = True
				abaatual = curso_url.split("=")[-1]
			else:
				existemabas = False
			if existemabas == True:
				#print "[%s - %s] existem atividades FALTANDO"%(curso_nome, abaatual)
				pass
			else:
				#print "[%s] existem atividades FALTANDO"%(curso_nome)
				pass

			srcmain = d.page_source.encode('utf-8') # fix some bugs

			### games do moodle com conteudo disciplinar ###
			games_moodle = re.findall('div class="activityinstance"><a class="" onclick="" href="https:\/\/ead\.cp2\.g12\.br\/mod\/game\/view\.php\?id=(.*?)">', srcmain)
			if len(games_moodle) >= 1:
				for tarefa in games_moodle:
					d.get(str("https://ead.cp2.g12.br/mod/game/view.php?id="+str(tarefa)))
					if erronatarefa(d.page_source.encode('utf-8')) == False:
						if existemabas == True:
							log("[%s - %s] TAREFA GAME COM ENVIO OBRIGATORIO DE QUESTOES DIDATICAS, faça: %s"%(curso_nome, abaatual, str("https://ead.cp2.g12.br/mod/game/view.php?id="+str(tarefa))), parse=4)
						else:
							log("[%s] TAREFA GAME COM ENVIO OBRIGATORIO DE QUESTOES DIDATICAS, faça: %s"%(curso_nome, str("https://ead.cp2.g12.br/mod/game/view.php?id="+str(tarefa))), parse=4)

			### forms do moodle com conteudo disciplinar ###
			tarefas_forms_moodle = re.findall('div class="activityinstance"><a class="" onclick="" href="https:\/\/ead\.cp2\.g12\.br\/mod\/feedback\/view\.php\?id=(.*?)">', srcmain)
			if len(tarefas_forms_moodle) >= 1:
				for tarefa in tarefas_forms_moodle:
					d.get(str("https://ead.cp2.g12.br/mod/feedback/view.php?id="+str(tarefa)))
					if erronatarefa(d.page_source.encode('utf-8')) == False:
						if existemabas == True:
							log("[%s - %s] TAREFA FEEDBACK COM ENVIO OBRIGATORIO DE QUESTOES DIDATICAS, faça: %s"%(curso_nome, abaatual, str("https://ead.cp2.g12.br/mod/feedback/view.php?id="+str(tarefa))), parse=4)
						else:
							log("[%s] TAREFA FEEDBACK COM ENVIO OBRIGATORIO DE QUESTOES DIDATICAS, faça: %s"%(curso_nome, str("https://ead.cp2.g12.br/mod/feedback/view.php?id="+str(tarefa))), parse=4)
			
			### submeter arquivos de disciplinas pro moodle ###
			tarefas_submit_arquivos_moodle = re.findall('div class="activityinstance"><a class="" onclick="" href="https:\/\/ead\.cp2\.g12\.br\/mod\/assign\/view\.php\?id=(.*?)">', srcmain)
			if len(tarefas_submit_arquivos_moodle) >= 1:
				for tarefa in tarefas_submit_arquivos_moodle:
					d.get(str("https://ead.cp2.g12.br/mod/assign/view.php?id="+str(tarefa)))
					if erronatarefa(d.page_source.encode('utf-8')) == False:
						if existemabas == True:
							log("[%s - %s] TAREFA ASSIGN COM ENVIO OBRIGATORIO DE ARQUIVO DIDATICO, faça: %s"%(curso_nome, abaatual, str("https://ead.cp2.g12.br/mod/assign/view.php?id="+str(tarefa))), parse=4)
						else:
							log("[%s] TAREFA ASSIGN COM ENVIO OBRIGATORIO DE ARQUIVO DIDATICO, faça: %s"%(curso_nome, str("https://ead.cp2.g12.br/mod/assign/view.php?id="+str(tarefa))), parse=4)
					#raw_input()

			### submeter quizes na plataforma do moodle ###
			quizes = re.findall('div class="activityinstance"><a class="" onclick="" href="https:\/\/ead\.cp2\.g12\.br\/mod\/quiz\/view\.php\?id=(.*?)">', srcmain)
			if len(quizes) >= 1:
				for tarefa in quizes:
					d.get(str("https://ead.cp2.g12.br/mod/quiz/view.php?id="+str(tarefa)))
					if erronatarefa(d.page_source.encode('utf-8')) == False:
						if existemabas == True:
							log("[%s - %s] QUIZ SOBRE CONTEUDO DIDATICO, faça: %s"%(curso_nome, abaatual, str("https://ead.cp2.g12.br/mod/quiz/view.php?id="+str(tarefa))), parse=4)
						else:
							log("[%s] QUIZ SOBRE CONTEUDO DIDATICO, faça: %s"%(curso_nome, str("https://ead.cp2.g12.br/mod/quiz/view.php?id="+str(tarefa))), parse=4)

			######### assinalar todos os forms como feitos #########
			ids = re.findall('\<input type="hidden" name="id" value="(.*?)"', source) #obter todos os ids
			sesskeys = re.findall('\<input type="hidden" name="sesskey" value="(.*?)"', source) #obter todos as sesskeys
			if len(ids) >= 1:
				if existemabas == True:
					#print '[%s - %s] %d checkboxes para assinalar..'%(curso_nome, abaatual, len(ids))
					pass
				else:
					#print '[%s] %d checkboxes para assinalar..'%(curso_nome, len(ids))
					pass
				for i in range(0, len(ids)): #assinalar todas as checkboxes
					data = {"id": ids[i], "completionstate":"1", "fromajax":"1", "sesskey":sesskeys[i]}
					r = requests.post('https://ead.cp2.g12.br/course/togglecompletion.php', cookies=cookies_dict, data=data)
					if 'OK' in r.text and not 'Erro' in r.text:
						if existemabas == True:
							#print '[%s - %s] Checkbox assinalada'%(curso_nome, abaatual)
							pass
						else:
							#print '[%s] Checkbox assinalada'%curso_nome
							pass
					else:
						if existemabas == True:
							log('[%s] Falha em assinalar checkbox id=%s, sesskey=%s'%(curso_nome,ids[i], sesskeys[i]), parse=4)
							#print r.text.encode('utf-8')
						else:
							log('[%s - %s] Falha em assinalar checkbox id=%s, sesskey=%s'%(curso_nome, abaatual, ids[i], sesskeys[i]), parse=4)
							#print r.text.encode('utf-8')

			### verificar checkboxes com links externos e/ou checkboxes com acesso obrigatorio do link para checkagem da checkbox ###
			external_links_checkboxes = re.findall('class="activityinstance"><a class="" onclick="" href="(.*?)"', source) #checkboxes que dependem do click em url
			if len(external_links_checkboxes) >= 1:
				if existemabas == True:
					#print '[%s - %s] %d checkboxes dependentes do acesso a URL..'%(curso_nome, abaatual, len(external_links_checkboxes))
					pass
				else:
					#print '[%s] %d checkboxes dependentes do acesso a URL..'%(curso_nome, len(external_links_checkboxes))
					pass
				for url in external_links_checkboxes:
					if existemabas == True:
						#print '[%s - %s] Acessando %s (url obrigatoria para checkagem de checkbox)..'%(curso_nome, abaatual, url)
						pass
					else:
						#print '[%s] Acessando %s (url obrigatoria para checkagem de checkbox)..'%(curso_nome, url)
						pass
					if 'forms' in url or 'docs.google.com' in url:
						d.get(url)
						ask1 = raw_input('[ATENCAO] Curso %s exige o preenchimento do formulario %s (%s)\n\tvoce quer mesmo que o script faca isso para voce? [y/N]: '%(curso_nome, url, d.title.encode('utf-8')))
						if ask1.lower().startswith('y'):
							########################## resolver automaticamente formularios do Google ##########################
							############ obter ordenamento dos campos de texto ############
							ordem_campos_texto = re.findall('aria-level="." aria-describedby="..">(.*?)\<span class="freebirdFormviewerComponentsQuestionBaseRequiredAsterisk', d.page_source.encode('utf-8'))
							if 'nome' in ordem_campos_texto:
								#print '[gForms] idx nome field => %d'%(ordem_campos_texto.index('nome'))
								idxnome = ordem_campos_texto.index('nome')
							elif 'Nome' in ordem_campos_texto:
								#print '[gForms] idx nome field => %d'%(ordem_campos_texto.index('Nome'))
								idxnome = ordem_campos_texto.index('Nome')
							elif 'NOME' in ordem_campos_texto:
								#print '[gForms] idx nome field => %d'%(ordem_campos_texto.index('NOME'))
								idxnome = ordem_campos_texto.index('NOME')
							else:
								log('[gForms] nao conseguimos identificar idx nome')
								break
							if 'turma' in ordem_campos_texto:
								#print '[gForms] idx turma field => %d'%(ordem_campos_texto.index('turma'))
								idxturma = ordem_campos_texto.index('turma')
							elif 'Turma' in ordem_campos_texto:
								#print '[gForms] idx turma field => %d'%(ordem_campos_texto.index('Turma'))
								idxturma = ordem_campos_texto.index('Turma')
							elif 'TURMA' in ordem_campos_texto:
								#print '[gForms] idx turma field => %d'%(ordem_campos_texto.index('TURMA'))
								idxturma = ordem_campos_texto.index('TURMA')
							else:
								log('[gForms] nao conseguimos identificar idx turma')
								break
							############ interpretando respostas e gerando respostas validas e randomicas ############
							#totalrespostas = re.findall('data-value=(.*?)role="radio"', d.page_source.encode('utf-8'))
							perguntas_obrigatorias = re.findall('role="heading" aria-level="." aria-describedby="...">(.*?)Pergunta obrigatória', d.page_source.encode('utf-8'))
							textboxes = d.find_elements_by_class_name("quantumWizTextinputPaperinputInput")
							radiobuttons = d.find_elements_by_class_name("docssharedWizToggleLabeledLabelWrapper")
							checkboxes = d.find_elements_by_class_name("quantumWizTogglePapercheckboxInnerBox")
							submitbutton = d.find_element_by_class_name("appsMaterialWizButtonPaperbuttonContent")						

							#textboxes[idxnome].send_keys("Felipe Belletti") ############ nome aqui ############
							#textboxes[idxturma].send_keys("1301") ############ turma aqui ############
							nomealuno = raw_input("[gForms] Seu Nome: ")
							turmaaluno = raw_input("[gForms] Sua Turma: ")
							textboxes[idxnome].send_keys(nomealuno) ############ nome aqui ############
							textboxes[idxturma].send_keys(turmaaluno) ############ turma aqui ############
							respostas_por_questao = len(radiobuttons) / len(perguntas_obrigatorias)
							#print respostas_por_questao
							x=0
							for pergunta in perguntas_obrigatorias:
								escolha = randint(x, respostas_por_questao+x-1) #0, 3 ; 4, 7
								log('[gForms] %s => resposta: %s'%(pergunta, escolha))
								radiobuttons[escolha].click()
								x+=int(respostas_por_questao)
							log('[gForms] Submetendo formulario..')
							submitbutton.click() #submeter as respostas
							try:
								assert('Sua resposta foi registrada.') in d.page_source.encode('utf-8')
							except:
								log('[gForms] Erro ao submeter as respostas')
								#print d.page_source.encode('utf-8')
					else:
						d.get(url)

d.quit()


raw_input("\nvoce nao precisa tirar print da tela, eu nao vou fechar, juro :)")
'''
problemas do script:
o ead de sociologia é super malfeito e entregou todas as atividades do ano numa vez só. oque o script faz?
checka todas as boxes como se fossem novas, alem do mais, deveriam ser. its not my fault, culpa de sociologia
nao tem oque fazer a nao ser criar um tratamento especial pra sociologia, e eu quero mais que isso se foda, ta funcionando logo ta ok
'''