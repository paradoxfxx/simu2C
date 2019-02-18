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
#include <matop.h>

void dss(int Flag, python_block *block)
{
  double *a, *b, *c, *d, *X;
  int nx, ni, no;
  double * realPar = block->realPar;
  int * intPar    = block->intPar;
  int iA, iB, iC, iD, iX;
  int i;
  double *y;

  ni = intPar[1];
  no = intPar[2];
  nx = intPar[0];

  double tmpAX[nx];
  double tmpBU[nx];
  double tmpCX[no];
  double tmpDU[no];
  double tmpY[no];

  double tmpU[ni];
  double *U;
  for (i=0;i<ni;i++) {
    U = (double *) block->u[i];
    tmpU[i] = U[0];
  }

  switch(Flag){
  case OUT:
    iC = intPar[5];
    iD = intPar[6];
    iX = intPar[7];
    c = &realPar[iC];
    d = &realPar[iD];
    X = &realPar[iX];
    matmult(c,no,nx,X,nx,1,tmpCX);
    matmult(d,no,ni,tmpU,ni,1,tmpDU);
    matsum(tmpCX,no,1,tmpDU,no,1,tmpY);
    
    for(i=0;i<no;i++){
      y = (double *) block->y[i];
      y[0] = tmpY[i];
    }
    break;
  case STUPD:
    iA = intPar[3];
    iB = intPar[4];
    iX = intPar[7];
    a = &realPar[iA];
    b = &realPar[iB];
    X = &realPar[iX];
    matmult(a,nx,nx,X,nx,1,tmpAX);
    matmult(b,nx,ni,tmpU,ni,1,tmpBU);
    matsum(tmpAX,nx,1,tmpBU,nx,1,X);
    break;
  case INIT:
  case END:
    break;
  default:
    break;
  }
}
  
