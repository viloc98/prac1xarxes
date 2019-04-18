#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, sys, struct, time, threading, os

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
	global nomServidor, MACServidor, UDPport, TCPport
	f=open("server.cfg","r")
	linea = f.readlines()
	f.close()
	nomServidor = agafardada(0,linea)
	MACServidor = agafardada(1,linea)
	UDPport = int(agafardada(2,linea))
	TCPport = int(agafardada(3,linea))

def lectura_fitxer_equips():
	global llistaMAC, llistaNomsEquips
	f=open("equips.dat","r")
	linea = f.readlines()
	f.close()
	llistaMAC = []
	llistaNomsEquips = []
	for x in (range(len(linea))):
		if len(linea[x].strip()) != 0 :
			llistaMAC.append(agafardada(x, linea))
			llistaNomsEquips.append(agafardada2(x, linea))

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
	num_random = paquet [21:26]

def can_register():
	global nom_client
	i = 0
	j = 0
	if MAC_client in llistaMAC:
		i = 1
	if nom_client in llistaNomsEquips:
		j = 1

	if i==1 and j==1:
		return True
	else:
		return False




lectura_fitxer_cfg()
lectura_fitxer_equips()
obrir_socket_UDP()

while True:
	data, address = socket_udp.recvfrom(78)
	tractar_paquet(data)
	if can_register():
		print "paquet correcte"
		paquet = struct.pack('B',REGISTER_ACK) + "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
		socket_udp.sendto(paquet, address)
	else:
		print "paquet incorrecte"
