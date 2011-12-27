/*  				7-6-91      Jack Snoeyink
Path hulls for the Douglas Peucker line simplification algorithm.
*/
#include "DP.h"
#include "PH.h"
#include "animate.h"

#ifdef ANIMATE
void A_UpdateH()
{
  A_ClearBack();
  mycolor(myTRANSP1);
  A_DrawHull(left);
  mycolor(myTRANSP2);
  A_DrawHull(right);
  A_DrawChains();
  A_SwapBuffers();
}
#endif

void Hull_Print(h)
     PATH_HULL *h;
{
  register int i;

  printf(" hull has %d points: ", h->top - h->bot);
  for (i = h->bot; i <= h->top; i++)
    printf(" <%.3lf %.3lf> ", (*h->elt[i])[XX], (*h->elt[i])[YY]);/**/
  printf("\n");
}


void Hull_Add(h, p)		/* Add $p$ to the path hull $h$. Implements Melkman's convex hull algorithm. */
     register PATH_HULL *h;
     POINT *p;
{
  register int topflag, botflag;
  
#ifdef ANIMATE
  mycolor(myMAGENTA);
#endif
  topflag = LEFT_OF(h->elt[h->top], h->elt[h->top-1], p);
  botflag = LEFT_OF(h->elt[h->bot+1], h->elt[h->bot], p);

  if (topflag || botflag)
    {
      while (topflag)
	{
#ifdef ANIMATE
      if (A_delay > 4)
	gsync();
  A_DrawSeg(*h->elt[h->top], *p);
#endif
	  Hull_Pop_Top(h);
	  topflag = LEFT_OF(h->elt[h->top], h->elt[h->top-1], p);
	}
      while (botflag)
	{
#ifdef ANIMATE
      if (A_delay > 4)
	gsync();
  A_DrawSeg(*h->elt[h->bot], *p);
#endif
	  Hull_Pop_Bot(h);
	  botflag = LEFT_OF(h->elt[h->bot+1], h->elt[h->bot], p);
	}
#ifdef ANIMATE
      if (A_delay > 0)
	gsync();
  A_DrawSeg(*h->elt[h->top], *p);
  A_DrawSeg(*h->elt[h->bot], *p);
#endif
      Hull_Push(h, p);
    }
}


void Split(h, e)
     register PATH_HULL *h;
     POINT *e;
{
  register POINT *tmpe;
  register int tmpo;
  
  A_Mode(2);
  while ((h->hp >= 0) 
	 && ((tmpo = h->op[h->hp]), 
	     ((tmpe = h->helt[h->hp]) != e) || (tmpo != PUSH_OP)))
    {
      h->hp--;
      switch (tmpo)
	{
	case PUSH_OP:
	  h->top--;
	  h->bot++;
	  break;
	case TOP_OP:
	  h->elt[++h->top] = tmpe;
	  break;
	case BOT_OP:
	  h->elt[--h->bot] = tmpe;
	  break;
	}
    }
}


#define SLOPE_SIGN(h, p, q, l)	/* Return the sign of the projection 
				   of $h[q] - h[p]$ onto the normal 
				   to line $l$ */ \
  SGN((l[XX])*((*h->elt[q])[XX] - (*h->elt[p])[XX]) \
      + (l[YY])*((*h->elt[q])[YY] - (*h->elt[p])[YY])) 



void Find_Extreme(h, line, e, dist)
     register PATH_HULL *h;
     HOMOG line;
     POINT **e;
     register double *dist;
{
  register int 
    sbase, sbrk, mid,
    lo, m1, brk, m2, hi;
  double d1, d2;

  A_Mode(1);
  if ((h->top - h->bot) > 8) 
    {
      lo = h->bot; hi = h->top - 1;
      sbase = SLOPE_SIGN(h, hi, lo, line);
      do
	{
	  brk = (lo + hi) / 2;
#ifdef ANIMATE
  mycolor(myYELLOW);
  A_DrawSeg(*h->elt[brk], *h->elt[brk+1]);
#endif
	  if (sbase == (sbrk = SLOPE_SIGN(h, brk, brk+1, line)))
	    if (sbase == (SLOPE_SIGN(h, lo, brk+1, line)))
	      lo = brk + 1;
	    else
	      hi = brk;
	}
      while (sbase == sbrk);
      
      m1 = brk;
      while (lo < m1)
	{
	  mid = (lo + m1) / 2;
#ifdef ANIMATE
  A_DrawSeg(*h->elt[mid], *h->elt[mid+1]);
#endif
	  if (sbase == (SLOPE_SIGN(h, mid, mid+1, line)))
	    lo = mid + 1;
	  else
	    m1 = mid;
	}
      
      m2 = brk;
      while (m2 < hi) 
	{
	  mid = (m2 + hi) / 2;
#ifdef ANIMATE
  A_DrawSeg(*h->elt[mid], *h->elt[mid+1]);
#endif
	  if (sbase == (SLOPE_SIGN(h, mid, mid+1, line)))
	    hi = mid;
	  else
	    m2 = mid + 1;
	}
      
/*      printf("Extremes: <%3lf %3lf>  <%3lf %3lf>\n", 
	     (*h->elt[lo])[XX],  (*h->elt[lo])[YY],
	     (*h->elt[m2])[XX],  (*h->elt[m2])[YY]); /**/
            
#ifdef ANIMATE
  A_DrawPLdist(*h->elt[lo], line);
  A_DrawPLdist(*h->elt[m2], line);
#endif
      if ((d1 = DOTPROD_2CH(*h->elt[lo], line)) < 0) d1 = - d1;
      if ((d2 = DOTPROD_2CH(*h->elt[m2], line)) < 0) d2 = - d2;
      *dist = (d1 > d2 ? (*e = h->elt[lo], d1) : (*e = h->elt[m2], d2));
    }
  else				/* Few points in hull */
    {
      *dist = 0.0;
      for (mid = h->bot; mid < h->top; mid++)
	{
#ifdef ANIMATE
	  A_DrawPLdist(*h->elt[mid], line);
#endif
	  if ((d1 = DOTPROD_2CH(*h->elt[mid], line)) < 0) d1 = - d1;
	  if (d1 > *dist)
	    {
	      *dist = d1;
	      *e = h->elt[mid];
	    }
	}
    }
}	
  


