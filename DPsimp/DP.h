/*  				7-6-91      Jack Snoeyink
Declarations for the Douglas Peucker line simplification algorithm.
*/
#pragma once

#include <stdio.h>
#include <math.h>

#define FALSE 0
#define TRUE 1

#define MAX_POINTS 10001
#define TWICE_MAX_POINTS 20002

typedef double POINT[2];	/* Most data is cartesian points */
typedef double HOMOG[3];	/* Some partial calculations are homogeneous */

#define XX 0
#define YY 1
#define WW 2

#define CROSSPROD_2CCH(p, q, r) /* 2-d cartesian to homog cross product */\
 (r)[WW] = (p)[XX] * (q)[YY] - (p)[YY] * (q)[XX];\
 (r)[XX] = - (q)[YY] + (p)[YY];\
 (r)[YY] =   (q)[XX] - (p)[XX];

#define DOTPROD_2CH(p, q)	/* 2-d cartesian to homog dot product */\
 (q)[WW] + (p)[XX]*(q)[XX] + (p)[YY]*(q)[YY]


#define DOTPROD_2C(p, q)	/* 2-d cartesian  dot product */\
 (p)[XX]*(q)[XX] + (p)[YY]*(q)[YY]

#define LINCOMB_2C(a, p, b, q, r) /* 2-d cartesian linear combination */\
 (r)[XX] = (a) * (p)[XX] + (b) * (q)[XX];\
 (r)[YY] = (a) * (p)[YY] + (b) * (q)[YY];


#define MIN(a,b) ( a < b ? a : b)
#define MAX(a,b) ( a > b ? a : b)

#define OutputVertex(v) R[num_result++] = v;

extern POINT *V,		/* V is the array of input points */
   **R;				/* R is the array of output pointers to V */

extern int n,			/* number of elements in V */
  num_result,			/* number of elements in R */
  outFlag, looping;

extern double EPSILON,		/* error tolerance */
  EPSILON_SQ;			/* error tolerance squared */


void Print_Points();
POINT *Alloc_Points();		/* alloc memory */

void Parse();			/* parse command line */
void Get_Points();		/* create test cases */
double Distance();
void Init(), Output(), Print_Result(), Start_Timing(), End_Timing();



