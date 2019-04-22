
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <poll.h>


#define DIMENSION       100 /* LA DIMENSIO INICIAL DELS STRINGS PER A DADES DEL CLIENT */

/*Tipus de paquets de registre*/
#define REGISTER_REQ  0x00
#define REGISTER_ACK  0x01
#define REGISTER_NACK  0x02
#define REGISTER_REJ  0x03
#define ERROR  0x09

/*Tipus de paquets comunicació periòdica*/
#define ALIVE_INF  0x10
#define ALIVE_ACK  0x11
#define ALIVE_NACK  0x12
#define ALIVE_REJ  0x13

/*Possibles estats*/
#define DISCONNECTED 0
#define WAIT_REG 1
#define REGISTERED 2
#define ALIVE 3

/*Estat propi utilitzat a funció tractar_paquet_ACK*/
#define UNKNOWN 99

char* ip_client = "127.0.0.1";

/*Variables temps*/
float t = 2.0;
int n = 3;
int m = 4;
int p = 8;
int s = 5;
int q = 3;
int r = 3;
int u = 3;

int restart = 0;

float temps_entre_paquets;
int estat;
int intents_conexio = 0;

char *file_to_read;
struct info_client
{
	char nom[DIMENSION];
	char mac[DIMENSION];
	char server_IP[DIMENSION];
	char server_port[DIMENSION];
};
struct info_client client;

struct sockaddr_in     servaddr, addr_cli;

struct timeval timeout;
int sockUDP, port;

char num_random[7];
char nom_server[7];
char mac_address_server[13];
char num_randomALIVE[7];
char nom_serverALIVE[7];
char mac_address_serverALIVE[13];
char data[50];
char* paquetbo;
char paquetrebutbo[78];

pthread_t threadEnviar, threadRebre, threadfase_alive;
int num_alives_per_rebre = 0;

void fase_registre();
void * fase_alive();

/*funció que llegeix els arguments*/
void llegir_arguments(int argc, char const *argv[])
{
	int i;
	/*S'asignen valors per defecte en cas de que no es passin arguments*/
	file_to_read = "client.cfg";
	for (i = 0; i < argc; ++i)
	{
		if (strcmp(argv[i],"-c")==0)
		{
			file_to_read = (char *) malloc(strlen(argv[i+1]));
			strcpy(file_to_read, argv[i+1]);
		}
	}
}
/*funció que llegeix el fitxer de configuració del client*/
void read_file()
{
	char line[256];						                /* linia */
	int line_num = 0;					                /* numero de linia */
	char resultat[4][256];	/* nom i valor del parametre els iguals els ignorem*/
	int i=0;
	int j=0;
	int x=0;
	FILE * f;
	f = fopen(file_to_read, "r");
	if (f==NULL) {fputs ("File error",stderr); exit (1);}
	while(fgets(line, 256, f) != NULL){
		for (i=0;line[i];i++)
		{
		    if (line[i]==' ')
		    {
		        j=0;
		        for (x=i+1; x<256 && line[x] != '\n';x++)
		        {
		            resultat[line_num][j]=line[x];
		            j++;
		        }
		        resultat[line_num][j] = '\0';
		        line_num++;
		        i=x;
		    }
		}
	}

	fclose(f);
	/*Anem copiant la informació del client*/
	strcpy(client.nom, resultat[0]);
	strcpy(client.mac, resultat[1]);
	strcpy(client.server_IP, resultat[2]);
	strcpy(client.server_port, resultat[3]);
}
/*funcio que crea un paquet preparat per enviar, per arguments s'entra el tipus de paquet que es vol preparar*/
char* crear_paquet(unsigned int tipusPaquet, char* num_random, char* data)
{
	int i;
	int j;
	char* paquet;
	paquet = malloc(78);
	paquet[0]=tipusPaquet;
	j=0;
	for (i = 1; i < 7; ++i)
	{
		paquet[i]=client.nom[j];
		j++;
	}
	paquet[7]='\0';
	j=0;
	for (i = 8; i < 21; ++i)
	{
		paquet[i]=client.mac[j];
		j++;
	}
	j=0;
	for (i = 21; i < 27; ++i)
	{
		paquet[i]=num_random[j];
		j++;
	}
	for (i = 27; i < 78; ++i)
	{
		paquet[i]='\0';
	}
	return paquet;
}
/*funció que obra el socket udp utilitzat per la transmissió de paquets en la fase de registre i alives*/
void obrir_socket_UDP()
{

	sockUDP=socket(AF_INET,SOCK_DGRAM,0);
	if(sockUDP<0)
	{
		printf("No puc obrir socket!!!\n");
		exit(-1);
	}

	memset(&addr_cli,0,sizeof (struct sockaddr_in));
	addr_cli.sin_family=AF_INET;
	addr_cli.sin_addr.s_addr=inet_addr(ip_client);
	addr_cli.sin_port=htons(0);

	/* Fem el binding */
	if(bind(sockUDP,(struct sockaddr *)&addr_cli,sizeof(struct sockaddr_in))<0)
	{
		fprintf(stderr,"No puc fer el binding del socket!!!\n");
								exit(-2);
	}

    memset(&servaddr, 0, sizeof(servaddr));

    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(atoi(client.server_port));
    servaddr.sin_addr.s_addr = atoi(client.server_IP);
}
/*funció per enviar el paquet de registre*/
void enviar_REGISTER_REQ()
{
	int a, j;
	/*Es fica el nombre aleatori a 000000*/
	for (j = 0; j < sizeof(num_random); ++j)
	{
		num_random[j]='0';
	}
	paquetbo=crear_paquet(REGISTER_REQ, num_random, data);
	/*S'envia paquet*/
	a=sendto(sockUDP,paquetbo,78,0,(struct sockaddr*)&servaddr,sizeof(servaddr));
				if(a<0)
					{
							fprintf(stderr,"Error al sendto\n");
							exit(-2);
					}
}
/*funció que rep el paquet i el tracta per poder analitzar-ne el contingut*/
void tractar_paquet_ACK()
{
	int i, j;
	socklen_t laddr_server;

	timeout.tv_sec = temps_entre_paquets;
	timeout.tv_usec = 0.0;

	if (setsockopt(sockUDP, SOL_SOCKET, SO_RCVTIMEO,&timeout,sizeof(timeout)))
			printf("setsockopt failed\n");

	/*Es rep un paquet*/
	recvfrom(sockUDP, paquetbo, 78,0, (struct sockaddr *) &servaddr,&laddr_server);
	if(paquetbo[0]!=REGISTER_REQ)
	{
		estat=UNKNOWN;
	}
	j=0;
	for (i = 1; i < 8; ++i)
	{
		nom_server[j]=paquetbo[i];
		j++;
	}
	j=0;
	for (i = 8; i < 21; ++i)
	{
		mac_address_server[j]=paquetbo[i];
		j++;
	}
	j=0;
	for (i = 21; i < 28; ++i)
	{
		num_random[j]=paquetbo[i];
		j++;
	}
	j=0;
	for (i = 28; i < 78; ++i)
	{
		data[j]=paquetbo[i];
		j++;
	}
	/*queda el paquet preparat per analitzar*/
}
/*funció que decideix en quin estat es troba el client després d'analitzar quin tipus de paquet es*/
void camviar_estat_rej()
{
	int i;
	if (paquetbo[0]==REGISTER_ACK)
	{
		estat=REGISTERED;
		for (i = 0; i < 78; ++i) /*resetejem paquet*/
		{
			paquetbo[i] = '\0';
		}
	/*en cas de REGISTER_REJ es tanca el client*/
	} else if (paquetbo[0]==REGISTER_REJ){
		estat=DISCONNECTED;
		printf("Rebut REGISTER_REJ, tancant el client.\n");
		printf("%s\n", data);
		exit(0);
	} else if (paquetbo[0]==REGISTER_NACK){
		if (intents_conexio==q)
		{
			printf("Rebut paquet REGISTER_NACK i intents de conexio maxims realitzats. Tancant client.\n");
			exit(0);
		} else {
			printf("Rebut paquet REGISTER_NACK iniciant intent de conexio nou.\n");
			estat=DISCONNECTED;
		}
	/*Si es rep un paquet desconegut o be un alive es tanca el client ja que el servidor sempre ha de respondre un dels anteriors*/
	} else {
		printf("Paquet rebut desconegut, tancant el client.\n");
		exit(0);
	}
}
/*funció que controla que el enviament de paquets en la fase de registre sigui el correcte*/
void fase_registre()
{
	int i;
	int num_paquets_enviats;
	/*Si el nombre d'intents de connexio supera els màxims paermesos s'atura el client*/
	while (intents_conexio<q)
	{
		intents_conexio++;
		num_paquets_enviats=0;
		/*Variable que marcara quan temps s'espera per enviar el seguent paquet*/
		temps_entre_paquets = t;
		for (i=1; i<n; ++i)
		{
			enviar_REGISTER_REQ();
			num_paquets_enviats++;
			tractar_paquet_ACK();
			if (estat!=WAIT_REG)
			{
				return;
			}
		}
		/*En cas de que no s'obtingui resposta en els primers paquets s'augmenta el temps que s'espera als paquets progresivament*/
		while (estat==WAIT_REG&&num_paquets_enviats<p)
		{
			if (temps_entre_paquets<(m*t))
			{
				temps_entre_paquets = temps_entre_paquets + t;
			}
			enviar_REGISTER_REQ();
			num_paquets_enviats++;
			tractar_paquet_ACK();
			if (estat!=WAIT_REG)
			{
				return;
			}
		}
		/*En cas de no haber-se conectat es torna a realitzar el intent sencer, sempre i quan no s'hagi superat el nombre màxim*/
		printf("Connexio fallida!!!\n");
		sleep(s);
	}
	printf("%s\n", "Intents de registre màxims realitzats. Tancant client.");
	exit(0);
}
/*Funció que envia un paquet ALIVE_INF i augmenta la variable de control d'alives per rebre*/
void * enviar_ALIVE_INF()
{
	int a;
	paquetbo=crear_paquet(ALIVE_INF, num_random, data);
	a=sendto(sockUDP,paquetbo,78,0,(struct sockaddr*)&servaddr,sizeof(servaddr));
				if(a<0)
					{
							fprintf(stderr,"Error al sendto\n");
							exit(-2);
					}
	num_alives_per_rebre = num_alives_per_rebre + 1;
	return NULL;
}
/*Funció que tracta la resposta a un ALIVE_INF*/
void * tractar_ALIVE_ACK()
{
	int i, j;
	char buffer[26];
	struct tm* tm_info;
	socklen_t laddr_server;
	time_t timer;
	time(&timer);
	tm_info = localtime(&timer);

	timeout.tv_sec = 3.0;
	timeout.tv_usec = 0.0;

	if (setsockopt(sockUDP, SOL_SOCKET, SO_RCVTIMEO,&timeout,sizeof(timeout)))
			printf("setsockopt failed\n");
	recvfrom(sockUDP, paquetrebutbo, 78,0, (struct sockaddr *) &servaddr,&laddr_server);
	if(paquetrebutbo[0]==ALIVE_ACK&&estat == REGISTERED)
	{
		/*Si es el primer es camvia el estat a ALIVE*/
		estat=ALIVE;
		strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);
		printf("%s: MSG: =>  Equip passa a l'estat: ALIVE\n", buffer);
	} else if (paquetrebutbo[0]==ALIVE_ACK){
		estat = ALIVE;
	} else if (paquetrebutbo[0]==ALIVE_NACK) {
		return NULL;
	} else if (paquetrebutbo[0]==ALIVE_REJ) {
		estat = DISCONNECTED;
		strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);
		printf("%s: MSG: =>  Equip passa a l'estat: DISCONNECTED. Rebut ALIVE_REJ. Iniciant nou proces registre.\n", buffer);
		/*S'ha rebut un ALIVE_REJ i per tant es comença des de 0 un nou proces de registre*/
		intents_conexio = 0;
		return NULL;
	}
	j=0;
	/*Es prepara el paquet per a poder analitzar-lo*/
	for (i = 1; i < 8; ++i)
	{
		nom_serverALIVE[j]=paquetrebutbo[i];
		j++;
	}
	j=0;
	for (i = 8; i < 21; ++i)
	{
		mac_address_serverALIVE[j]=paquetrebutbo[i];
		j++;
	}
	j=0;
	for (i = 21; i < 28; ++i)
	{
		num_randomALIVE[j]=paquetrebutbo[i];
		j++;
	}
	/*Es reseteja comptador alives_per_rebre ja que solament s'arriba aqui si ALIVE_ACK*/
	if (strcmp(num_randomALIVE,num_random)==0&&strcmp(nom_serverALIVE,nom_server)==0&&strcmp(mac_address_serverALIVE,mac_address_server)==0) {
		num_alives_per_rebre = 0;
	}
	for (i = 0; i < 78; ++i) /*resetejem paquet*/
	{
		paquetrebutbo[i] = '\0';
	}
	return NULL;
}
/*Funció que va cridant a les funcions enviar i rebre alives mentres el servidor respongui*/
void * fase_alive()
{
/*mentre el nombre de alive per rebre no sigui més que 3*/
/* o bé si els intents de connexio són iguals a 0 vol dir que s'ha rebut ALIVE_REJ i acaba la fase de alives*/
	while (num_alives_per_rebre<=u && intents_conexio!=0) {
		pthread_create(&threadEnviar, NULL, enviar_ALIVE_INF, NULL);
		pthread_create(&threadRebre, NULL, tractar_ALIVE_ACK, NULL);
		sleep(r);
	}

	pthread_join(threadEnviar,NULL);
	pthread_join(threadRebre,NULL);
	num_alives_per_rebre = 0;
	return NULL;
}

int main (int argc, char const *argv[])
{
	char buffer[26];
	char string[10];
	struct tm* tm_info;
	struct pollfd mypoll = { STDIN_FILENO, POLLIN|POLLPRI };
	time_t timer;
	time(&timer);
	tm_info = localtime(&timer);

		strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);

		printf("%s: MSG: =>  Equip passa a l'estat: DISCONNECTED\n", buffer);
		estat = DISCONNECTED;
		llegir_arguments(argc, argv);
		read_file();
		obrir_socket_UDP();
		while (restart == 0)
		{
		strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);
		printf("%s: MSG: =>  Equip passa a l'estat: WAIT_REG\n", buffer);
		estat = WAIT_REG;
		fase_registre();
		camviar_estat_rej();
		if (estat==REGISTERED) {
			strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);
			printf("%s: MSG: =>  Equip passa a l'estat: REGISTERED\n", buffer);
			pthread_create(&threadfase_alive, NULL, fase_alive, NULL);
		}
		/*Es comprova si s'ha rebut alguna comanda*/
		/*es pa un poll per si el client es tanca sol perque no ha rebut 3 alives no es quedi esperant a una comanda per acabar de tancar*/
		while (num_alives_per_rebre<=u&&(estat==ALIVE||estat==REGISTERED)) {
			if(poll(&mypoll, 1, 100) )
			{
					scanf("%9s", string);
					if (strcmp(string, "quit")==0) {
						exit(0);
					}
			}
		}
		pthread_join(threadfase_alive,NULL);

	}
	close(sockUDP);
  exit(0);
}
