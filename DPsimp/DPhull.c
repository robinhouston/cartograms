/*  				7-6-91      Jack Snoeyink
Recursive implementation of the Douglas Peucker line simplification
algorithm based on path hulls
*/
#include "DP.h"
#include "PH.h"

PATH_HULL *left, *right;	/* Path Hull: \va{left} and \va{right} portions and tag vertex \va{PHtag}. */
POINT *PHtag;


void Build(i, j)		/* Build Path Hull for the chain from vertex $i$ to vertex $j$.   */
     POINT *i, *j;
{
  register POINT *k;

  A_Mode(0);

  PHtag = i + (j - i) / 2;

  Hull_Init(left, PHtag, PHtag - 1);
  for (k = PHtag - 2; k >= i; k--)
    Hull_Add(left, k);
/*  printf("LEFT "); Hull_Print(left);/**/

  Hull_Init(right, PHtag, PHtag + 1);
  for (k = PHtag + 2; k <= j; k++)
    Hull_Add(right, k);
/*  printf("RIGHT "); Hull_Print(right);/**/
}
  
void DP(i, j)
     POINT *i, *j;
{
  static double ld, rd, len_sq;
  static HOMOG l;
  POINT *le, *re;

  if (j - i > 1)
    {
  CROSSPROD_2CCH(*i, *j, l);
#ifdef ANIMATE
  A_UpdateH();
  A_DrawLine(l);
#endif
  len_sq = DOTPROD_2C(l,l);

      Find_Extreme(left, l, &le, &ld);
      Find_Extreme(right, l, &re, &rd);
      
      if (ld <= rd)
	{
	  if (rd * rd > EPSILON_SQ * len_sq)
	    {
	      if (PHtag == re)
		Build(i, re);
	      else
		Split(right, re);
	      /*	    printf("RIGHT Backup "); Hull_Print(right);/**/
	      A_AddSplit(re);
	      DP(i, re);
	      Build(re, j);
	      DP(re, j);
	    }
	}
      else
	if (ld * ld > EPSILON_SQ * len_sq)
	  {
	    Split(left, le);
/*	    printf("LEFT Backup "); Hull_Print(left);/**/
	    A_AddSplit(le);
	    DP(le, j);
	    Build(i, le);
	    DP(i, le);
	  }
    }
}




main(argc,argv)
    int argc;
    char **argv;
{
  Parse(argc, argv);
  Init("DPhull");
  left = (PATH_HULL *) malloc(sizeof(PATH_HULL));
  right = (PATH_HULL *) malloc(sizeof(PATH_HULL));

  do
    {
      Get_Points();
#ifdef ANIMATE
      A_modes[0] = "Build";
      A_modes[1] = "FindExtr.";
      A_modes[2] = "Split";
      A_Setup(3);
#endif 
      Start_Timing();
      Build(V, V + n - 1);
      DP(V, V + n - 1);
      A_UpdateH();
      End_Timing(TRUE);
      Print_Result(FALSE); /**/
    }
  while (looping);
#ifdef ANIMATE
  A_Quit();
#endif 
}


