#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/types.h>
#include <unistd.h>

#define DIMENSION       100 /* LA DIMENSIO INICIAL DELS STRINGS PER A DADES DEL CLIENT */

#define REGISTER_REQ  0x00
#define REGISTER_ACK  0x01
#define REGISTER_NACK  0x02
#define REGISTER_REJ  0x03
#define ERROR  0x09

char *file_to_read;
struct info_client
{
	char nom[DIMENSION];
	char mac[DIMENSION];
	char server_IP[DIMENSION];
	char server_port[DIMENSION];
};
struct info_client client;

struct sockaddr_in	addr_server,addr_cli;
struct hostent *ent;
int sockUDP, port;
char num_random[6];
char data[50];

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
	char* paquet = malloc(78);
	paquet[0]=tipusPaquet;
	j=0;
	for (i = 1; i < 7; ++i)
	{
		paquet[i]=client.nom[j];
		j++;
	}
	paquet[7]='\0';
	j=0;
	for (i = 8; i < 20; ++i)
	{
		paquet[i]=client.mac[j];
		j++;
	}
	j=0;
	printf("%s\n", num_random);
	for (i = 21; i < 28; ++i)
	{
		paquet[i]=num_random[j];
		j++;
	}
	for (i = 29; i<78; ++i)
	{
		paquet[i]='\0';
	}
	return paquet;
}

int main (int argc, char const *argv[])
{
	int i;
	llegirArguments(argc, argv);
	readFile();

	for (i = 0; i < sizeof(num_random); ++i)
	{
		num_random[i]='0';
	}
	crearPaquet(REGISTER_REQ, num_random, data);
  exit(0);
}
