#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, sys, struct, time, threading, os, random

# ESTATS
DISCONNECTED = 1
WAIT_REG = 2
REGISTERED = 3
ALIVE = 4


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


def agafardada(int,list):
	h = list[int]
	h = h.split(' ')
	h = h[1].split('\n')
	return h[0]

def agafardada2(int,list):
	h = list[int]
	h = h.split(' ')
	return h[0]

def lectura_fitxer_cfg():
	global nom_servidor, MACServidor, UDPport, TCPport
	f=open("server.cfg","r")
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
	return package

def respondre_registre(): ## TODO: Falta fer kuan adressa diferent
	global num_random
	if diccionari_noms_equips.get(nom_client) == DISCONNECTED:
		if num_random=="000000":
			num_random = ""
			for x in range(6):
				num_random = num_random + str(random.randint(0,9))
			paquet = crear_paquet(REGISTER_ACK, num_random)
			diccionari_noms_equips[nom_client] = REGISTERED
		else:
			paquet = crear_paquet(REGISTER_NACK, "000000")
	else:
		paquet = crear_paquet(REGISTER_ACK, num_random)

	socket_udp.sendto(paquet, address)

def mantenir_comunicacio():
	global num_random
	address_bo = address
	num_random_bo = num_random
	data, address = socket_udp.recvfrom(78)
	tractar_paquet()
	if can_answer() and address_bo==address and num_random_bo == num_random:
		paquet = crear_paquet(ALIVE_ACK, num_random)
	elif can_answer():
		paquet = crear_paquet(ALIVE_NACK, num_random)
	else:
		paquet = crear_paquet(ALIVE_REJ, num_random)
	socket_udp.sendto(paquet, address)


lectura_fitxer_cfg()
lectura_fitxer_equips()
obrir_socket_UDP()

while True:
	data, address = socket_udp.recvfrom(78)
	tractar_paquet(data)
	if can_answer():
		respondre_registre()
		while True:
			mantenir_comunicacio()
	else:
		paquet = crear_paquet(REGISTER_REJ, "000000")
		socket_udp.sendto(paquet, address)
