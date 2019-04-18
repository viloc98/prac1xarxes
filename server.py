#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, sys, struct, time, threading, os

def agafardada(int,list):
	h = list[int]
	h = h.split(' ')
	h = h[1].split('\n')
	return h[0]

def agafardada2(int,list):
	h = list[int]
	h = h.split(' ')
	return h[0]

def lecturaFitxerCFG():
	global nomServidor, MACServidor, UDPport, TCPport
	f=open("server.cfg","r")
	linea = f.readlines()
	f.close()
	nomServidor = agafardada(0,linea)
	MACServidor = agafardada(1,linea)
	UDPport = int(agafardada(2,linea))
	TCPport = int(agafardada(3,linea))

def lecturaFitxerEquips():
	f=open("equips.dat","r")
	linea = f.readlines()
	f.close()
	llistaMAC = []
	llistaNomsEquips = []
	for x in (range(len(linea))):
		if len(linea[x].strip()) != 0 :
			llistaMAC.append(agafardada(x, linea))
			llistaNomsEquips.append(agafardada2(x, linea))

def obrirSocketUDP():
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


lecturaFitxerCFG()
lecturaFitxerEquips()
obrirSocketUDP()

while True:
	data, address = socket_udp.recvfrom(78)
	print data
