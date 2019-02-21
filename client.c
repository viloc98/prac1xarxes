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

#define DIMENSION       100 /* LA DIMENSIO INICIAL DELS STRINGS PER A DADES DEL CLIENT */


#define REGISTER_REQ  0x00
#define REGISTER_ACK  0x01
#define REGISTER_NACK  0x02
#define REGISTER_REJ  0x03
#define ERROR  0x09

/*Possibles estats*/
#define DISCONNECTED 0
#define WAIT_REG 1
#define REGISTERED 2
#define ALIVE 3

/*Variables temps*/
float t = 2.0;
int n = 3;
int m = 4;
int p = 8;
int s = 5;
int q = 3;



float temps_entre_paquets;
int estat;
int intents_conexio;

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
char data[50];
char* paquetbo;
char nom_server[7];



void llegirArguments(int argc, char const *argv[])
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
			printf("%s\n", file_to_read);
		}
	}
}

void readFile()
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

  printf("%s\n", client.nom);
  printf("%s\n", client.mac);
  printf("%s\n", client.server_IP);
  printf("%s\n", client.server_port);
}

char* crearPaquet(unsigned int tipusPaquet, char* num_random, char* data)
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

void obrirSocketUDP()
{

	sockUDP=socket(AF_INET,SOCK_DGRAM,0);
	if(sockUDP<0)
	{
		printf("No puc obrir socket!!!\n");
		exit(-1);
	}

	memset(&addr_cli,0,sizeof (struct sockaddr_in));
	addr_cli.sin_family=AF_INET;
	addr_cli.sin_addr.s_addr=htonl(INADDR_ANY);
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
void enviarREGISTER_REQ()
{
	int a;
	time_t timer;
	char buffer[26];
	struct tm* tm_info;

	time(&timer);
	tm_info = localtime(&timer);

	strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);

	printf("%s: envio paquet\n", buffer);
	paquetbo=crearPaquet(REGISTER_REQ, num_random, data);
	a=sendto(sockUDP,paquetbo,78,0,(struct sockaddr*)&servaddr,sizeof(servaddr));
				if(a<0)
					{
							fprintf(stderr,"Error al sendto\n");
							exit(-2);
					}
}

void tractarPaquetACK()
{
	int i, n;
	socklen_t laddr_server;

	timeout.tv_sec = temps_entre_paquets;
	timeout.tv_usec = 0.0;

	if (setsockopt(sockUDP, SOL_SOCKET, SO_RCVTIMEO,&timeout,sizeof(timeout)))
			printf("setsockopt failed\n");

	n = recvfrom(sockUDP, paquetbo, 78,0, (struct sockaddr *) &servaddr,&laddr_server);

	for (i = 0; i < 78; i++) {
		printf("%c", paquetbo[i]);
	}

	if(paquetbo[0]==REGISTER_ACK)
	{
		estat=REGISTERED;
	}

	for (i = 1;i < 8; ++i) {
		nom_server[i]=paquetbo[i];
	}
}

void faseREGISTER_ACK()
{
	int i;
	int num_paquets_enviats;
	intents_conexio=0;
	while (intents_conexio<q)
	{
		intents_conexio++;
		printf("intent de conexio: %i\n", intents_conexio);
		num_paquets_enviats=0;
		temps_entre_paquets = t;
		for (i=1; i<n; ++i)
		{
			enviarREGISTER_REQ();
			num_paquets_enviats++;
			tractarPaquetACK();
			printf("%i\n", estat);
			if (estat==REGISTERED)
			{
				return;
			}
		}
		while (estat==WAIT_REG&&num_paquets_enviats<p)
		{
			if (temps_entre_paquets<(m*t))
			{
				temps_entre_paquets = temps_entre_paquets + t;
			}
			enviarREGISTER_REQ();
			num_paquets_enviats++;
			printf("%i\n", num_paquets_enviats);
			tractarPaquetACK();
			if (estat==REGISTERED)
			{
				return;
			}
		}
		printf("Connexio fallida!!!\n");
		sleep(s);
	}
}

int main (int argc, char const *argv[])
{
	int i, n;

	estat = DISCONNECTED;
	llegirArguments(argc, argv);
	readFile();

	for (i = 0; i < sizeof(num_random); ++i)
	{
		num_random[i]='0';
	}
	obrirSocketUDP();

	estat = WAIT_REG;
	printf("entro a register ack\n");
	faseREGISTER_ACK();
	close(sockUDP);



  exit(0);
}
