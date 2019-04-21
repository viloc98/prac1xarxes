#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, sys, struct, time, threading, os, random, threading, select

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

def agafardada(int,list):
	h = list[int]
	h = h.split(' ')
	h = h[1].split('\n')
	return h[0]

def agafardada2(int,list):
	h = list[int]
	h = h.split(' ')
	return h[0]

def triarclient(argv):
	try:
		if argv[1]!="-c":
			print "Error arguments. Exemple -c nomarxiuclient(client1.cfg). Si no s'introdueix res s'obrira client.cfg"
			exit(0)
		return argv[2]

	except Exception as e:
		fitxer_cfg = "server.cfg"
		return fitxer_cfg

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

def obrir_socket_UDP():
	global socket_udp
	try:
		socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except:
		print "No s'ha pogut obrir el socket"
		exit()

	try:
		socket_udp.bind(('localhost', UDPport))
	except:
		print "No s'ha pogut fer el bind del socket"
		exit()

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

def can_answer():
	global nom_client
	i = 0
	j = 0
	if MAC_client in llistaMAC:
		i = 1
	if nom_client in diccionari_noms_equips:
		j = 1

	if i==1 and j==1:
		return True
	else:
		return False

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
		package = struct.pack('B',tipus_paquet) + "000000" + "\0" + "000000000000" + "\0" + num_random + "\0" + "ERROR: Client no autoritzat." + "\0" + struct.pack('70B',*([0]* 70))
	elif tipus_paquet == ALIVE_REJ:
		package = struct.pack('B',tipus_paquet) + "000000" + "\0" + "000000000000" + "\0" + num_random + "\0" + "ERROR: Client no autoritzat o no registrat encara." + "\0" + struct.pack('70B',*([0]* 70))
	return package

def respondre_registre():
	global num_random, address, nom_client
	if diccionari_noms_equips.get(nom_client) == DISCONNECTED:
		if num_random=="000000":
			num_random = ""
			for x in range(6):
				num_random = num_random + str(random.randint(0,9))
			print nom_client
			diccionari_num_randoms [nom_client] = num_random
			diccionari_adresses [nom_client] = address
			paquet = crear_paquet(REGISTER_ACK, num_random)
			diccionari_noms_equips[nom_client] = REGISTERED
		else:
			paquet = crear_paquet(REGISTER_NACK, "000000")
	elif diccionari_num_randoms.get(nom_client)==num_random and diccionari_adresses.get(nom_client) == address:
		paquet = crear_paquet(REGISTER_ACK, diccionari_num_randoms.get(nom_client))
		diccionari_noms_equips[nom_client] = REGISTERED

	else:
		paquet = crear_paquet(REGISTER_REJ, "000000")
		socket_udp.sendto(paquet, address)

	socket_udp.sendto(paquet, address)

def mantenir_comunicacio():
	global num_random, address, nom_client, address_bo, num_random_bo
	if diccionari_noms_equips.get(nom_client) == ALIVE or diccionari_noms_equips.get(nom_client) == REGISTERED:
		if can_answer() and diccionari_adresses.get(nom_client)==address and diccionari_num_randoms.get(nom_client) == num_random:
			diccionari_noms_equips[nom_client] = ALIVE
			paquet = crear_paquet(ALIVE_ACK, num_random)
		elif can_answer():
			paquet = crear_paquet(ALIVE_NACK, num_random)
		else:
			paquet = crear_paquet(ALIVE_REJ, num_random)
	else:
		paquet = crear_paquet(ALIVE_REJ, num_random)

	socket_udp.sendto(paquet, address)

def respondre_paquet():
	global tipus_paquet
	if tipus_paquet==REGISTER_REQ:
		respondre_registre()
	if tipus_paquet==ALIVE_INF:
		mantenir_comunicacio()


def atendre_peticions():
	global address
	data, address = socket_udp.recvfrom(78)
	tractar_paquet(data)
	if can_answer():
		respondre_paquet()


def atendre_comandes():
	comanda = raw_input()
	if comanda == "quit":
		os._exit(1)
	elif comanda == "list":
		print "********************** LLISTA EQUIPS *************************"
		for x, y in diccionari_noms_equips.items():
		  print x, estatAlletres.get(y)
		print "\n************************************************************"
	else:
		print "Comanda no reconeguda."

lectura_fitxer_cfg()
lectura_fitxer_equips()
obrir_socket_UDP()
while True:
	readable, writable, exceptional = select.select([socket_udp, sys.stdin], [], [])
	for s in readable:
		if s is socket_udp:
			t = threading.Thread(target=atendre_peticions)
			t.start()
		else:
			atendre_comandes()
