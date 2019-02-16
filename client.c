#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define DIMENSION       100 /* LA DIMENSIO INICIAL DELS STRINGS PER A DADES DEL CLIENT */

char *fitxer_a_llegir;
struct info_client
{
	char nom[DIMENSION];
	char mac[DIMENSION];
	char server_IP[DIMENSION];
	char server_port[DIMENSION];
};
struct info_client client;

void llegirArguments(int argc, char const *argv[])
{
	int i;
	for (i = 0; i < argc; ++i)
	{
		if (strcmp(argv[i],"-c")==0)
		{
			fitxer_a_llegir = (char *) malloc(strlen(argv[i+1]));
			strcpy(fitxer_a_llegir, argv[i+1]);
			printf("%s\n", fitxer_a_llegir);
		}
	}
}

void llegirFitxerCfg()
{
	char line[256];						                /* linia */
	int line_num = 0;					                /* numero de linia */
	char resultat[4][256];	/* nom i valor del parametre els iguals els ignorem*/
	int k=0;
	int i=0;
	int j=0;
	int x=0;
	FILE * f;
	f = fopen(fitxer_a_llegir, "r");

	if (f==NULL) {fputs ("File error",stderr); exit (1);}
	while(fgets(line, 256, f) != NULL){
		j=0;
		for (i=0;i<256;i++)
		{
			if (line[i]==' ')
			{
				for (x=i+1; x<256 && line[x] != '\n';x++)
				{
					resultat[k][j]=line[x];
					j++;
				}
        resultat[k][j] = '\0';
				k++;
			}
		}
		line_num++;
	}
	fclose(f);

	/*Anem copiant la informació del client*/
	strcpy(client.nom, resultat[0]);
	strcpy(client.mac, resultat[1]);
	strcpy(client.server_IP, resultat[2]);
	strcpy(client.server_port, resultat[3]);

	printf("Llegits parametres arxius de configuració.\n");

  printf("%s\n", client.nom);
  printf("%s\n", client.mac);
  printf("%s\n", client.server_IP);
  printf("%s\n", client.server_port);
}

int main (int argc, char const *argv[])
{
	llegirArguments(argc, argv);
	llegirFitxerCfg();
  exit(0);
}
