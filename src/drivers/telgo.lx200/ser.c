/***************************************************************************
                          ser.c  -  description
                             -------------------
    begin                : Wed Jun 7 2000
    copyright            : (C) 2000 by Andre Luiz de Amorim
    email                : andre@astro.ufsc.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
/* This file contains the functions for serial communication */

#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <signal.h>
#include <termios.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "errors.h"
#include "ser.h"

static void rdtimeout(int signumber);
static int set_minchars(ser_info *serial, int nbytes);
static ser_info *sertmp;

#ifdef COMMTEST

/* This example program writes a string in port `tty', and waits until
   timeout for a response. */


char teste[] = "Write test...";
unsigned char buf[25];
char tty[]   = "/dev/ttyS1";


int main(void)
{
	int result;
	ser_info porta;

	open_serial(&porta, tty);
	if (porta.err_code != ERR_OK) return(-1);
	puts("Communication test.\n\n");

	/* 9600,8e1 */
	porta.baudrate = B9600;
	porta.parity = PAR_EVEN;
	porta.stopbits = 1;
	porta.timeout = 10;
	porta.minchars = 25;
	porta.waitread = FALSE;
	set_serial(&porta);
	write_serial(&porta, teste, strlen(teste));

	if (read_serial(&porta, buf, 24))
	printf("Text received: %s\n\n", buf);
	else printf("Read timeout.\n\n");

	close_serial(&porta);
	return(0);
}
#endif /* COMMTEST */


int is_valid_serial(ser_info *serial)
{
	if ((serial == NULL)           ||
	    (serial->tty_name == NULL) ||
	    (serial->tio == NULL)      ||
	    (serial->oldtio == NULL))
		return(FALSE);
	return(TRUE);
}


ser_info *open_serial(char *ttyname)
{
        ser_info *serial;

/* Allocate memory for the structures */
	serial = (ser_info *) calloc(sizeof(ser_info), 1);
	if (serial == NULL) return (NULL);

	serial->tio =    (struct termios *) calloc(sizeof(struct termios), 1);
	serial->oldtio = (struct termios *) calloc(sizeof(struct termios), 1);
	serial->tty_name = (char *) calloc(strlen(ttyname), sizeof(char));

	if (serial->tio == NULL    ||
	    serial->oldtio == NULL ||
	    serial->tty_name == NULL) {
                free(serial->tio);
		free(serial->oldtio);
		free(serial->tty_name);
		free(serial);
		return(NULL);
	}

	serial->err_code = ERR_OK;
	signal(SIGALRM, rdtimeout);
	strcpy(serial->tty_name, ttyname);

	serial->ttyfd = open(serial->tty_name, O_RDWR | O_NOCTTY);
	if (serial->ttyfd < 0) {
		serial->err_code = ERR_OPENTTY;
		close_serial(serial);
		return (NULL);
	}

/* Save current config */
	tcgetattr(serial->ttyfd, serial->oldtio);
	serial->isopen = TRUE;
	return (serial);
}


int close_serial(ser_info *serial)
{
	if (!is_valid_serial(serial)) return(ERR_MEM);
	signal(SIGALRM, SIG_DFL);
/* Restore terminal to its previous state; free memory */ 
	if (serial->isopen) {
		tcsetattr(serial->ttyfd,TCSANOW,serial->tio);
		close(serial->ttyfd);
	}
	free(serial->tio);
	free(serial->oldtio);
	free(serial->tty_name);
	free(serial);
	return(ERR_OK);
}


int set_serial(ser_info *serial)
{
	if (!is_valid_serial(serial)) return(ERR_MEM);
	if (!serial->isopen) {
		serial->err_code = ERR_SERIAL;
		return(ERR_SERIAL);
	}
	memset(serial->tio, 0, sizeof(struct termios));

	cfsetospeed(serial->tio, serial->baudrate);
	cfsetispeed(serial->tio, serial->baudrate);

/* Set byte size to 8bit, enable reading and set local mode */
	serial->tio->c_cflag |= CS8 | CLOCAL | CREAD;
	switch (serial->parity) {
	case PAR_NONE:
		serial->tio->c_iflag |= IGNPAR;
		serial->tio->c_cflag &= ~PARENB;
		break;

	case PAR_EVEN:
		serial->tio->c_iflag &= ~IGNPAR;
		serial->tio->c_cflag |= PARENB;
		serial->tio->c_cflag &= ~PARODD;
		break;

	case PAR_ODD:
		serial->tio->c_iflag &= ~IGNPAR;
		serial->tio->c_cflag |= PARENB;
		serial->tio->c_cflag &= PARODD;
		break;
	default:
		serial->err_code = ERR_PARITY;
		return(ERR_PARITY);
	}

	if (serial->stopbits == 1)
		serial->tio->c_cflag &= ~CSTOPB;
	else if (serial->stopbits ==2)
		serial->tio->c_cflag |= CSTOPB;
	else {
		serial->err_code = ERR_STOPB;
		return(ERR_STOPB);
	}

/* Raw input */
	serial-> tio->c_lflag = 0;

	serial->tio->c_cc[VTIME] = serial->timeout;
	if (serial->waitread)
		serial->tio->c_cc[VMIN] = serial->minchars;

	tcsetattr(serial->ttyfd,TCSANOW,serial->tio);
	return(ERR_OK);
}


int write_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes)
{
	int result;

	if (!is_valid_serial(serial)) return(ERR_MEM);
	if (!serial->isopen) {
		serial->err_code = ERR_SERIAL;
		return(0);
	}
	result = write(serial->ttyfd, buf, nbytes);
	if (result < nbytes) {
		serial->err_code = ERR_WRITE;
		return(result);
	}
	serial->err_code = ERR_OK;
	return(result);
}


int read_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes)
{
	int result;

	if (!is_valid_serial(serial)) return(ERR_MEM);
	if (!serial->isopen) {
		serial->err_code = ERR_SERIAL;
		return(0);
	}
	serial->err_code = ERR_OK;

/* Set the minimum number of chars to read before returning */
	if (serial->waitread && (serial->minchars != nbytes)) {
		if (set_minchars(serial, nbytes) != ERR_OK) {
			serial->err_code = ERR_SERIAL;
			return(0);
		}
	}
/* save serial stuff for alarm() timeout. */
	sertmp = serial;
	
	alarm(serial->timeout);
	result = read(serial->ttyfd, buf, nbytes);
	alarm(0);
	serial->bytesread = result;
	if (result < nbytes)
		serial->err_code = ERR_READ;
	return(result);
}


static int set_minchars(ser_info *serial, int nbytes)
{
	if (!is_valid_serial(serial))
		return(ERR_MEM);
	if (!serial->waitread)
		return(ERR_READ);
	serial->minchars = nbytes;
	serial->tio->c_cc[VMIN] = nbytes;
	tcsetattr(serial->ttyfd,TCSANOW,serial->tio);
	return(ERR_OK);
}

static void rdtimeout(int signumber)
{
	fprintf(stderr, "Serial communication failed, closing %s...\n", sertmp->tty_name);
	if (sertmp != NULL) close_serial(sertmp);
	/* exit(-1); */
}

