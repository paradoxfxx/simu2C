/*
COPYRIGHT (C) 2016  Roberto Bucher (roberto.bucher@supsi.ch)

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
*/

#include <pyblock.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

double get_run_time();

void step(int Flag, python_block *block)
{
  double t;
  double initTime = block->realPar[0];
  double Val = block->realPar[1];
  double * y;

  y = (double *) block->y[0];
  switch(Flag){
  case OUT:
    t = get_run_time();
    if(t<initTime) y[0] = 0.0;
    else           y[0] = Val;
    break;
  case INIT:
    y[0]=0.0;
    break;
  case END:
    y[0]=0.0;
    break;
  default:
    break;
  }
}
  
