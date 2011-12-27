CFLAGS = -O7
#CFLAGS = -g
#CFLAGS = -p
CC = gcc
#LIBOPTS = -static
LIBOPTS =
LIBS = -lfftw3 -lm

cart:main.o cart.o
	$(CC) $(CFLAGS) $(LIBOPTS) -o cart main.o cart.o $(LIBS)

cart.o:cart.c Makefile
	$(CC) $(CFLAGS) -c cart.c

cart2:main.o cart2.o
	$(CC) $(CFLAGS) $(LIBOPTS) -o cart2 main.o cart2.o $(LIBS)

cart2.o:cart2.c Makefile
	$(CC) $(CFLAGS) -c cart2.c

cartv:main.o cartv.o
	$(CC) $(CFLAGS) $(LIBOPTS) -o cartv main.o cartv.o $(LIBS)

cartv.o:cartv.c Makefile
	$(CC) $(CFLAGS) -c cartv.c

cart2v:main.o cart2v.o
	$(CC) $(CFLAGS) $(LIBOPTS) -o cart2v main.o cart2v.o $(LIBS)

cart2v.o:cart2v.c Makefile
	$(CC) $(CFLAGS) -c cart2v.c

main.o:main.c Makefile
	$(CC) $(CFLAGS) -c main.c

interp:interp.o
	$(CC) $(CFLAGS) -o interp interp.o

interp.o:interp.c Makefile
	$(CC) $(CFLAGS) -c interp.c

clean:
	rm -fv *.o

all: cart cart2 cartv cart2v interp
