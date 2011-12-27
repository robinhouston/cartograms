/*
 * 7-6-91      Jack Snoeyink procedures for testing/timing line simplification
 */

#include "DP.h"
#include "animate.h"
#include <sys/types.h>
#include <sys/times.h>

#define LAST 9

POINT *V, **R;

float  p[MAX_POINTS][2];

int n, num_result;
int outFlag, looping = 0;

double EPSILON = 0.0,		/* error tolerance */
  EPSILON_SQ = 0.0;

static int  cycler, CycleFlag = FALSE;

static int file_active = 0;

FILE *infp;
#define REC_LENGTH 144
char buffer[145];

POINT *Alloc_Points(n)
     int n; 
{ 	
  void *calloc();

  return ((POINT *) calloc(n, sizeof(POINT)));
}

void Print_Points(P, n, flag)
     POINT **P;
     int n, flag;
{
  int i;

  printf("%d points\n", n);
  if (flag)
    for (i = 0; i < n; i++)
      printf("%d: %.4f %.4f \n", i, (*(P[i]))[XX], (*(P[i]))[YY]);	/**/
  fflush(stdout);
}

void Print_Result(flag)
     int flag;
{
  if (!CycleFlag)
    Print_Points(R, num_result, flag);
}


#define TWO_PI 6.28318531


void fatalError(msg, var)
     char *msg, *var;
{
  fprintf(stderr, msg, *var);
  exit(1);
}

void ReadLine()
{
  int i;

  if (file_active = looping = (fread(&n, sizeof(int), 1, infp) == 1)) {
    fread(p[0], sizeof(float), 2*n, infp);
    for (i = 0; i < n; i++) {
      V[i][XX] = (double) p[i][0];
      V[i][YY] = (double) p[i][1];
    }
    while ((V[0][XX] == V[n-1][XX]) && (V[0][YY] == V[n-1][YY])) n--;
  }
}

void Parse(argc, argv)
    int argc;
    char **argv;
{
  double LEFT, RIGHT, BOTTOM, TOP;
#ifdef ANIMATE
  int xl, xh, yl, yh;

  yl = 0; 
  yh = getgdesc(GD_YPMAX);
  xl = 0;
  xh = getgdesc(GD_XPMAX);
  A_delay = 4;
  A_swapinterval = 2;
#endif /* ANIMATE */

  --argc; argv++;

  n = 50;
  cycler = 0;
  file_active = 0;

  while ((argc > 0) && (argv[0][0] == '-'))
      {
	if (!strcmp(argv[0], "-n")) {
	    if (sscanf(argv[1], "%d", &n) != 1) 
	      fatalError("ERROR -- \"%d\": bad n\n", (char *)(argv[1]));
	    argv += 2;
	    argc -= 2;
	}

#ifdef ANIMATE
	else if ((argc >= 2) && !strcmp(argv[0], "-d")) {
	    if (sscanf(argv[1], "%d", &A_delay) != 1) {
		fprintf(stderr, "ERROR -- \"%s\": bad delay\n", argv[1]);
		exit(1);
	      }
	    argv += 2;
	    argc -= 2;
	}
	else if ((argc >= 2) && !strcmp(argv[0], "-i")) {
	    if (sscanf(argv[1], "%d", &A_swapinterval) != 1) {
		fprintf(stderr, "ERROR -- \"%s\": bad swap interval\n", 
			argv[1]);
		exit(1);
	      }
	    argv += 2;
	    argc -= 2;
	}
	else if (!strcmp(argv[0], "-m")) {
	    argv++;
	    --argc;
	    A_modeq = 1;
	  }
	else if (!strcmp(argv[0], "-a")) {
	    argv++;
	    --argc;
	    A_ack = 1;
	  }
	else if (!strcmp(argv[0], "-pos")) {
	    if (sscanf(argv[1], "%d,%d,%d,%d", &xl, &xh, &yl, &yh) != 4) {
		fprintf(stderr, "ERROR -- \"%s\": unrecognized pos.\n",
			argv[1]);
		exit(1);
	    }
	    argv += 2;
	    argc -= 2;
	}
#endif /* ANIMATE */

	else if (!strcmp(argv[0], "-k")) {
	    if (sscanf(argv[1], "%d", &cycler) != 1) 
	      fatalError("ERROR -- \"%d\": bad kind of test case\n-k Test Case:    0/all\n   1/circle, 2/prtb circ, 3/mon random, 4/non-mon random,\n   5/ prtb zig-zag, 6/cnvx zig-zag, 7/cncv zig-zag, 8/spiral\n", (char *)(argv[1]));
	    argv += 2;
	    argc -= 2;
	  }
	else if (!strcmp(argv[0], "-e")) {
	    if (sscanf(argv[1], "%lf", &EPSILON) != 1)
	      fatalError("ERROR -- \"%lf\": bad epsilon\n", (char *)(argv[1]));
	    EPSILON_SQ = EPSILON * EPSILON;
	    argv += 2;
	    argc -= 2;
	  }
	else if (!strcmp(argv[0], "-f")) {
	  infp = fopen(argv[1], "r");
	  if (infp == NULL) 
	    fatalError("Could not open input file %s\n", (char *)(argv[1]));
	  fgets(buffer, REC_LENGTH, infp);
	  if (strncmp("my format", buffer, 9) != 0)
	    fatalError("File not in my format: %s\n", buffer);
	  sscanf(buffer, "my format %lg%lg%lg%lg",&LEFT, &RIGHT, &BOTTOM, &TOP);
	  file_active = 1;
	  argv += 2;
	  argc -= 2;
	}
	else if (!strcmp(argv[0], "-l")) {
	    if (sscanf(argv[1], "%d", &looping) != 1) 
	      fatalError("ERROR -- \"%d\": bad l\n", (char *)(argv[1]));
	    argv += 2;
	    argc -= 2;
	  }
	else if (!strcmp(argv[0], "-h")) {
	    argv++;
	    --argc;
	    fprintf(stderr, 
"usage: basic -n # no. pts  -k # test case  -l loop# -f file of test cases\n -e epsilon/n"
#ifdef ANIMATE
"   -d # anim. delay  -i # swap interval  -pos (xl,xh,yl,yh)\n"
"   -m display modes -a wait for space\n"
#endif /* ANIMATE */
);
	    exit(1);
	}
      }
#ifdef ANIMATE
  prefposition(xl, xh, yl, yh);
  aspect = ((double) xh - xl) / ((double) yh - yl);/**/
#endif /* ANIMATE */
}

#define SIGN(x) (x < 0 ? -1 : (x > 0 ? 1 : 0))

#define DET2(a, b, c, d)	/* 2x2 determinant */\
  ((a)*(d) - (c)*(b)) 
#define DETPts(p, q)		/* 2x2 determinant for points */\
  DET2(p[XX], p[YY], q[XX], q[YY])

int intersect(a, b, c, d)	/* check if (ab) \cap (cd) */
     POINT a, b, c, d;
{
  register double ab = DETPts(a, b);
  register double ac = DETPts(a, c);
  register double ad = DETPts(a, d);
  register double bc = DETPts(b, c);
  register double bd = DETPts(b, d);
  register double cd = DETPts(c, d);
  register double abc = bc - ac + ab;
  register double abd = bd - ad + ab;
  register double acd = cd - ad + ac;
  register double bcd = cd - bd + bc;

  return ((SIGN(abc)*SIGN(abd) == -1) && (SIGN(acd)*SIGN(bcd) == -1));
}


void swapV(i, j)
     int i,j;
{
  double tmp;

  tmp = V[i][XX]; V[i][XX] = V[j][XX]; V[j][XX] = tmp;
  tmp = V[i][YY]; V[i][YY] = V[j][YY]; V[j][YY] = tmp;
}


void untangle()
{
  int i, j, 
  oi, oj, 
  ti, tj, 
  k, l, flag, tmpflag;
  
  do
    {
      oi = random() % n;
      flag = 0;
      for (i = 0; i < n; i++)
	{
	  ti = (oi + i) % n;
	  oj = random() % n;
	  for (j = 0; j < n; j++)
	    {
	      tj = (oj + j) % n;
	      if ((ti + n + 1 - tj) % n > 2)
		if (intersect(V[ti], V[(ti+1)%n], V[tj], V[(tj+1)%n]))
		  {
		    flag = TRUE;
		    if (tj < ti + 1) tj = tj + n;
		    for (k = ti + 1, l = tj; k < l; k++, l--)
		      swapV(k % n, l % n);
		    break;
		  }
	    }
	}
    }
  while (flag);
}				/* working */



void Get_Points()
{
  double tmp;
  register int i;

  if (file_active) 
    ReadLine();
  else if (CycleFlag)
    looping = CycleFlag = (++cycler < LAST);
  else
    {
      if (looping)
	looping--;		/* decrement # of iterations */

      if (cycler < 0 || cycler > LAST) 
	{
	  printf("-k Test Case:    0/all\n");
	  printf("   1/circle, 2/prtb circ, 3/mon random, 4/non-mon random,\n");
	  printf("   5/ prtb zig-zag, 6/cnvx zig-zag, 7/cncv zig-zag, 8/spiral\n");
	  fflush(stdout);
	  exit(1);
	}
      if (cycler == 0)
	looping = CycleFlag = cycler = 1;
    }
  switch (cycler)
    {
    case 1:
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = n / 2.0 * cos((TWO_PI * i) / n);
	  V[i][YY] = n / 2.0 * sin((TWO_PI * i) / n);
	}
      break;

    case 2:
      for (i = 0; i < n; i++)
	{
	  tmp = n/2.0 + drand48() * n/40.0;
	  V[i][XX] = tmp * cos((TWO_PI * i) / n);
	  V[i][YY] = tmp * sin((TWO_PI * i) / n);
	}
      break;

    case 3:
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = (double) i;
	  V[i][YY] = ((double) n) * drand48();
	}
      break;
      
    case 4:
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = n/2.0 * drand48();
	  V[i][YY] = n/2.0 * drand48();
	}
      untangle();/**/
      break;

    case 5:
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = (double) i - n/2.0;
	  V[i][YY] = ((double)(i % 2) - 0.5) * i + n/10.0 * drand48();
	}
      break;

    case 6:
      tmp = sqrt((double) n);
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = (double) i - n/2.0;
	  V[i][YY] = ((double)(i % 2) - 0.5) * sqrt((double) i) * tmp;
	}
      break;

    case 7:
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = (double) i - n/2.0;
	  V[i][YY] = (((double)(i % 2) - 0.5) * i)/n*i;
	}
      break;

    case 8:
      for (i = 0; i < n; i++)
	{
	  V[i][XX] = i * cos(TWO_PI * (i % 3) / 3.0);
	  V[i][YY] = i * sin(TWO_PI * (i % 3) / 3.0);
	}
      break;
    case LAST:
      n = 1;
    }

/*  Print_Points(V, n, TRUE); /**/
}




struct tms      starttime, endtime;

void Start_Timing()
{
  times(&starttime);
}

void  End_Timing(flag)
     int flag;
{
  times(&endtime);
  if (flag != 0)
    printf("%d  in %d  out %d  %ld ticks  %.3f secs %d\n", cycler, n, num_result,
	   (endtime.tms_utime - starttime.tms_utime),
	   (float) (endtime.tms_utime - starttime.tms_utime) / 100.0, flag);
}

void Output(i, j)
     int i, j;
{
  if (outFlag)
    {
      outFlag = FALSE;
      OutputVertex(V+i);
    }
      OutputVertex(V+j);
}


void Init(name)
     char *name;
{
  srand48((long) 123);

  V = Alloc_Points(MAX_POINTS);
  R = (POINT **) calloc(MAX_POINTS, sizeof(POINT *));

#ifdef ANIMATE
  A_Init(name);
#endif /* ANIMATE */
}  



