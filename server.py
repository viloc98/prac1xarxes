#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, sys, struct, time, threading, os, random, select, datetime
#variable per poder camviar la ip del servidor
ip_servidor='localhost'

# ESTATS
DISCONNECTED = 1
WAIT_REG = 2
REGISTERED = 3
ALIVE = 4

estatAlletres={1:"DISCONNECTED", 2:"WAIT_REG", 3:"REGISTERED", 4:"ALIVE"}

# TIPUS DE PAQUETS
REGISTER_REQ = 0x00
REGISTER_ACK = 0x01
REGISTER_NACK = 0x02
REGISTER_REJ = 0x03
ERROR = 0x09

ALIVE_INF = 0x10
ALIVE_ACK = 0x11
ALIVE_NACK = 0x12
ALIVE_REJ = 0x13

diccionari_adresses = {}
diccionari_num_randoms = {}
diccionari_temps_alives = {}
lock = threading.Lock()
#Funció comlementaria a les que llegeixen fitxers agafa el segon camp d'un split
def agafardada(int,list):
	h = list[int]
	h = h.split(' ')
	h = h[1].split('\n')
	return h[0]
#Funció comlementaria a les que llegeixen fitxers agafa el primer camp d'un split
def agafardada2(int,list):
	h = list[int]
	h = h.split(' ')
	return h[0]
#Funció que serveix per seleccionar el arxiu de configuració del servidor
def triarclient(argv):
	try:
		if argv[1]!="-c":
			print "Error arguments. Exemple -c nomarxiuclient(client1.cfg). Si no s'introdueix res s'obrira client.cfg"
			exit(0)
		return argv[2]

	except Exception as e:
		fitxer_cfg = "server.cfg"
		return fitxer_cfg
#Funció que llegeix el fitxer de configuració
def lectura_fitxer_cfg():
	global nom_servidor, MACServidor, UDPport, TCPport
	try:
		f=open(triarclient(sys.argv),"r")
	except:
		print "No es pot obrir fitxer configuració, tancant servidor."
		exit(0)
	linea = f.readlines()
	f.close()
	nom_servidor = agafardada(0,linea)
	MACServidor = agafardada(1,linea)
	UDPport = int(agafardada(2,linea))
	TCPport = int(agafardada(3,linea))
#Funció que llegeix el fitxer dels equips autoritzats
def lectura_fitxer_equips():
	global llistaMAC, diccionari_noms_equips
	f=open("equips.dat","r")
	linea = f.readlines()
	f.close()
	llistaMAC = []
	diccionari_noms_equips = {}
	for x in (range(len(linea))):
		if len(linea[x].strip()) != 0 :
			llistaMAC.append(agafardada(x, linea))
			diccionari_noms_equips[(agafardada2(x, linea))] = DISCONNECTED

#Funció per obrir es socket per on es transmetran tots els paquets
def obrir_socket_UDP():
	global socket_udp
	try:
		socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except:
		print "No s'ha pogut obrir el socket"
		exit()

	try:
		socket_udp.bind((ip_servidor, UDPport))
	except:
		print "No s'ha pogut fer el bind del socket"
		exit()

#Funció que retorna el nombre de segons totals des de les 00:00
def segons():
    return int(str(datetime.datetime.now().time())[0:2])*3600 + int(str(datetime.datetime.now().time())[3:5])*60 + int(str(datetime.datetime.now().time())[6:8])
#Funció que desglosa el paquet per poder analitzar-lo comodament
def tractar_paquet(paquet):
	global tipus_paquet, nom_client, MAC_client, num_random
	tipus_paquet = paquet [0]
	tipus_paquet = struct.unpack('B',tipus_paquet)
	tipus_paquet = tipus_paquet[0]
	nom_client = paquet [1:7]
	nom_client = nom_client.split('\0')
	nom_client = nom_client[0]
	MAC_client = paquet [8:20]
	num_random = paquet [21:27]
#Funció retorna true si el equip esta autoritzat fals si no
def can_answer():
	return MAC_client in llistaMAC and nom_client in diccionari_noms_equips

#Funció que retorna un paquet del tipus que se li entra per arguments ja preparat per enviar
def crear_paquet(tipus_paquet, num_random):
	if tipus_paquet == REGISTER_ACK:
		package = struct.pack('B',tipus_paquet) + nom_servidor + "\0" + MACServidor + "\0" + num_random + "\0" + str(TCPport) + "\0" + struct.pack('70B',*([0]* 70))
	elif tipus_paquet == REGISTER_NACK:
		package = struct.pack('B',tipus_paquet) + "000000" + "\0" + "000000000000" + "\0" + num_random + "\0" + "ERROR: Numero aleatori incorrecte." + "\0" + struct.pack('70B',*([0]* 70))
	elif tipus_paquet == REGISTER_REJ:
		package = struct.pack('B',tipus_paquet) + "000000" + "\0" + "000000000000" + "\0" + num_random + "\0" + "ERROR: Client no autoritzat a registrar-se" + "\0" + struct.pack('70B',*([0]* 70))
	elif tipus_paquet == ALIVE_ACK:
		package = struct.pack('B',tipus_paquet) + nom_servidor + "\0" + MACServidor + "\0" + num_random  + "\0" + struct.pack('70B',*([0]* 70))
	elif tipus_paquet == ALIVE_NACK:
		package = struct.pack('B',tipus_paquet) + "000000" + "\0" + "000000000000" + "\0" + num_random + "\0" + "ERROR: Ip o nombre aleatori incorrectes." + "\0" + struct.pack('70B',*([0]* 70))
	elif tipus_paquet == ALIVE_REJ:
		package = struct.pack('B',tipus_paquet) + "000000" + "\0" + "000000000000" + "\0" + num_random + "\0" + "ERROR: Client no autoritzat o no registrat encara." + "\0" + struct.pack('70B',*([0]* 70))
	return package

#Funció que es crida quan s'ha rebut un paquet tipus REGISTER_REQ i en respon en consequencia
def respondre_registre():
	global num_random, address, nom_client

	if diccionari_noms_equips.get(nom_client) == DISCONNECTED and MAC_client in llistaMAC:
		#Primer REGISTER_REQ rebut num aleatori a 0s
		if num_random=="000000":
			num_random = ""
			for x in range(6):
				num_random = num_random + str(random.randint(0,9))
			#Es guarden les dades per futures comprovacions
			diccionari_num_randoms [nom_client] = num_random
			diccionari_adresses [nom_client] = address[0]
			paquet = crear_paquet(REGISTER_ACK, num_random)
			print  str(datetime.datetime.now().time())[:8]+": MSG.  =>  Equip", nom_client, "passa a estat: REGISTERED"
			diccionari_noms_equips[nom_client] = REGISTERED
		else:
			paquet = crear_paquet(REGISTER_NACK, "000000")
	#El client ja estava en estat REGISTERED o ALIVE
	elif can_answer() and diccionari_adresses.get(nom_client) == address[0]:
		paquet = crear_paquet(REGISTER_ACK, diccionari_num_randoms.get(nom_client))
		diccionari_noms_equips[nom_client] = REGISTERED
		#Es fica l'estat a REGISTERED en cas de que estigues ALIVE
		print  str(datetime.datetime.now().time())[:8]+": MSG.  =>  Equip", nom_client, "passa a estat: REGISTERED"

	else:
		#Es un client no autoritzat i per tant es rebutja
		paquet = crear_paquet(REGISTER_REJ, "000000")
		socket_udp.sendto(paquet, address)

	socket_udp.sendto(paquet, address)

#Funció que es crida quan s'ha rebut un paquet tipus ALIVE_INF i en respon en consequencia
def mantenir_comunicacio():
	global num_random, address, nom_client, address_bo, num_random_bo
	#Si el client no esta en un d'aquets estats no pot enviar alive i per tant es contesta un ALIVE_REJ
	if diccionari_noms_equips.get(nom_client) == ALIVE or diccionari_noms_equips.get(nom_client) == REGISTERED:
		#Primer ALIVE_INF rebut correcte
		if can_answer() and diccionari_adresses.get(nom_client)==address[0] and diccionari_num_randoms.get(nom_client) == num_random and diccionari_noms_equips.get(nom_client) == REGISTERED:
			diccionari_noms_equips[nom_client] = ALIVE
			print  str(datetime.datetime.now().time())[:8]+": MSG.  =>  Equip", nom_client, "passa a estat: ALIVE"
			paquet = crear_paquet(ALIVE_ACK, num_random)
			lock.acquire(True)
			#Es suma 6 segons al temps màxim per rebre un altre alive
			#Cal fer el lock d'aquesta variable si no podria portar problemes a l'hora de comprovar si el temps de ALIVE_INF uñtim es correcte
			diccionari_temps_alives[nom_client] = segons() + 6
			lock.release()
		#ALIVE_INF rebut ja en estat ALIVE
		if can_answer() and diccionari_adresses.get(nom_client)==address[0] and diccionari_num_randoms.get(nom_client) == num_random and diccionari_noms_equips.get(nom_client) == ALIVE:
			paquet = crear_paquet(ALIVE_ACK, num_random)
			lock.acquire(True)
			#Es suma 9 segons al temps màxim per rebre un altre alive
			diccionari_temps_alives[nom_client] = segons() + 9
			lock.release()
		#Num aleatori o adressa incorrecta
		elif can_answer():
			paquet = crear_paquet(ALIVE_NACK, "000000")
		else:
			paquet = crear_paquet(ALIVE_REJ, "000000")
	else:
		paquet = crear_paquet(ALIVE_REJ, "000000")

	socket_udp.sendto(paquet, address)

#Funció que crida una funció segons tipus paquet rebut
def respondre_paquet():
	global tipus_paquet
	if tipus_paquet==REGISTER_REQ:
		respondre_registre()
	if tipus_paquet==ALIVE_INF:
		mantenir_comunicacio()

#Funció que rep els paquets i crida a les funcions que els tracten i decideixen que fer
def atendre_peticions():
	global address
	data, address = socket_udp.recvfrom(78)
	tractar_paquet(data)
	respondre_paquet()

#Funció que triara que fer segons la comanda que fiqui el usuari per terminal
def atendre_comandes():
	comanda = raw_input()
	if comanda == "quit":
		socket_udp.close()
		os._exit(1)
	elif comanda == "list":
		print "********************** LLISTA EQUIPS *************************"
		for x, y in diccionari_noms_equips.items():
		  print x, estatAlletres.get(y)
		print "\n************************************************************"
	else:
		print "Comanda no reconeguda."
#Funció que comprova que s'han rebut els ALIVE_INF dels clients abans del temps esperat, si no els torna a ficar DISCONNECTED
def control_alives():
	while True:
		lock.acquire(True)
		for x in diccionari_temps_alives:
			if diccionari_temps_alives[x] < segons() and diccionari_noms_equips.get(x)!=DISCONNECTED:
				diccionari_noms_equips[x]=DISCONNECTED
				print  str(datetime.datetime.now().time())[:8]+": MSG.  =>  Equip", nom_client, "passa a estat: DISCONNECTED"
				#es fica un nombre molt gran de forma que si es torna a registrar aquest client no el fiqui a desconectat si esta registrat
				diccionari_temps_alives[x] = 9999999999
		lock.release()

#Main
lectura_fitxer_cfg() #Lectura fitxer cfg
lectura_fitxer_equips() #Lectura fitxer equips autoritzats
obrir_socket_UDP() #S'obra el socket udp
thread_control_alives = threading.Thread(target=control_alives) #Es crida en un thread a part la funcio que controla els ALIVES
thread_control_alives.start()
#Continuament es mira si s'ha rebut algun paquet o bé alguna comanda ha estat introduida
while True:
	readable, writable, exceptional = select.select([socket_udp, sys.stdin], [], [])
	for s in readable:
		#Si es un paquet s'obra un thread per atendrel i aixi poder seguint rebent comandes
		if s is socket_udp:
			t = threading.Thread(target=atendre_peticions)
			t.start()
		else:
			atendre_comandes()
