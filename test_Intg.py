from control import *
from scipy import size
import numpy as np
from control import tf2ss, TransferFunction
from scipy import mat, array, shape, size, zeros
from numpy import reshape, hstack
import os

intg = tf(1,[1,-1],1)
stepTime = 1.0
stepValue = 1.0
Tsamp = 1.0

class RCPblk:
    def __init__(self, *args):  
        if len(args) == 8:
            (fcn,pin,pout,nx,uy,realPar,intPar,str) = args
        elif len(args) == 7:
            (fcn,pin,pout,nx,uy,realPar,intPar) = args
            str=''
        else:
            raise ValueError("Needs 6 or 7 arguments; received %i." % len(args))
        
        self.fcn = fcn
        self.pin = array(pin)
        self.pout = array(pout)
        self.nx = array(nx)
        self.uy = array(uy)
        self.realPar = array(realPar)
        self.intPar = array(intPar)
        self.str = str

    def __str__(self):
        """String representation of the Block"""
        str =  "Function           : " + self.fcn.__str__() + "\n"
        str += "Input ports        : " + self.pin.__str__() + "\n"
        str += "Output ports      : " + self.pout.__str__() + "\n"
        str += "Nr. of states      : " + self.nx.__str__() + "\n"
        str += "Relation u->y      : " + self.uy.__str__() + "\n"
        str += "Real parameters    : " + self.realPar.__str__() + "\n"
        str += "Integer parameters : " + self.intPar.__str__() + "\n"
        str += "String Parameter   : " + self.str.__str__() + "\n"
        return str

def stepBlk(pout, initTime, Val):
    if(size(pout) != 1):
        raise ValueError("Block should have 1 output port; received %i." % size(pout))
    blk = RCPblk('step',[],pout,[0,0],0,[initTime, Val],[])
    return blk

def dssBlk(pin,pout,sys,X0=[]):
    if isinstance(sys, TransferFunction):
        sys=tf2ss(sys)

    nin = size(pin)
    ni = shape(sys.B)[1];
    if (nin != ni):
        raise ValueError("Block have %i inputs: received %i input ports" % (nin,ni))
    
    no = shape(sys.C)[0]
    nout = size(pout)
    if(no != nout):
        raise ValueError("Block have %i outputs: received %i output ports" % (nout,no))
        
    a  = reshape(sys.A,(1,size(sys.A)),'C')
    b  = reshape(sys.B,(1,size(sys.B)),'C')
    c  = reshape(sys.C,(1,size(sys.C)),'C')
    d  = reshape(sys.D,(1,size(sys.D)),'C')
    nx = shape(sys.A)[0]

    if(size(X0) == nx):
        X0 = reshape(X0,(1,size(X0)),'C')
    else:
        X0 = mat(zeros((1,nx)))

    indA = 0
    indB = nx*nx
    indC =indB + nx*ni
    indD = indC + nx*no
    indX = indD + ni*no
    intPar = [nx,ni,no,indA, indB, indC, indD, indX]
    realPar = hstack((a,b,c,d,X0))

    if d.any() == True:
        uy = 1
    else:
        uy = 0
    
    blk = RCPblk('dss',pin,pout,[0,nx],uy,realPar,intPar)
    return blk

def printBlk(pin):
    blk = RCPblk('print',pin,[],[0,0],1,[],[])
    return blk

def detBlkSeq(Nodes, blocks):
    class blkDep:
        def __init__(self, block, blkL, nodeL):
            self.block = block
            self.block_in = []

            if len(block.pin) != 0:
                for node in block.pin:
                    if nodeL[node].block_in[0].uy == 1:
                        self.block_in.append(nodeL[node].block_in[0])              
  
            
        def __str__(self):
            txt  = 'Block: ' + self.block.fcn.__str__() + '\n'
            txt += 'Inputs\n'
            for item in self.block_in:
                txt += item.fcn + '\n'
            txt += '\n'
            return txt

    class nodeClass:
        def __init__(self, N):
            self.PN = N
            self.block_in = []
            self.block_out = []

        def __str__(self):
            txt  = 'Node: ' + self.PN.__str__() + '\n'
            txt += ' Blocks in:\n'
            for item in self.block_in:
                try:
                    txt += item.fcn + '\n'
                except:
                    txt += 'None\n'
            txt += ' Blocks out:\n'
            for item in self.block_out:
                try:
                    txt += item.fcn + '\n'
                except:
                    txt += 'None\n'
            return txt

    def fillNodeList(nN,blks):
        nL = []
        nL.append(nodeClass(0))
        for n in range(1, nN+1):
            node = nodeClass(n)
            nL.append(node)
        for blk in blks:
            for n in blk.pin:
                nL[n].block_out.append(blk)
            for n in blk.pout:
                nL[n].block_in.append(blk)
        return nL
    
    blks = []
    blks2order = []

    nodes = fillNodeList(Nodes, blocks)

    # First search block with no input and no output

    for blk in blocks:
        if blk.uy == 0:
            if len(blk.pin) == 0 and len(blk.pout) == 0:
                blks.insert(0, blk)
            else:
                blks.append(blk)
        else:
            block = blkDep(blk, blocks, nodes)
            blks2order.append(block)
   
    # Order the remaining blocks
    counter = 0
    while len(blks2order) != counter:
        blk = blks2order.pop(0)
        if len(blk.block_in) == 0:
            blks.append(blk.block)
            counter = 0

            try:
                node = blk.block.pout[0]

                for bk in nodes[node].block_out:
                    el=[el for el in blks2order if el.block == bk]
                    try:
                        el[0].block_in.remove(blk.block)
                    except:
                        pass
            except:
                pass
        else:
            blks2order.append(blk)
            counter += 1

    # Check if remain blocks in blks2order -> Algeabric loop!
    if len(blks2order) != 0:
        for item in blks2order:
            print(item.block)
        raise ValueError("Algeabric loop!")
    
    return blks

def genCode(model, Tsamp, blocks, rkstep = 10):
    maxNode = 0
    for blk in blocks:
        for n in range(0,size(blk.pin)):
            if blk.pin[n] > maxNode:
                maxNode = blk.pin[n]
        for n in range(0,size(blk.pout)):
            if blk.pout[n] > maxNode:
                maxNode = blk.pout[n]

    # Check outputs not connected together!
    outnodes = zeros(maxNode+1)
    for blk in blocks:
        for n in range(0,size(blk.pout)):
            if outnodes[blk.pout[n]] == 0:
                outnodes[blk.pout[n]] = 1
            else:
                raise ValueError('Problem in diagram: outputs connected together!')           
    
    Blocks = detBlkSeq(maxNode, blocks)
    if size(Blocks) == 0:
        raise ValueError('No possible to determine the block sequence')
    
    fn = model + '.c'
    f=open(fn,'w')
    strLn = "#include <pyblock.h>\n#include <stdio.h>\n\n"
    f.write(strLn)
    N = size(Blocks)

    totContBlk = 0
    for blk in Blocks:
        totContBlk += blk.nx[0]

    f.write("/* Function prototypes */\n\n")

    for blk in Blocks:
        strLn = "void " + blk.fcn + "(int Flag, python_block *block);\n"
        f.write(strLn)

    f.write("\n")

    strLn = "double " + model + "_get_tsamp()\n"
    strLn += "{\n"
    strLn += "  return (" + str(Tsamp) + ");\n"
    strLn += "}\n\n"
    f.write(strLn)

    strLn = "python_block block_" + model + "[" + str(N) + "];\n\n"
    f.write(strLn);

    for n in range(0,N):
        blk = Blocks[n]
        if (size(blk.realPar) != 0):
            strLn = "static double realPar_" + str(n) +"[] = {"
            strLn += str(mat(blk.realPar).tolist())[2:-2] + "};\n"
            f.write(strLn)
        if (size(blk.intPar) != 0):
            strLn = "static int intPar_" + str(n) +"[] = {"
            strLn += str(mat(blk.intPar).tolist())[2:-2] + "};\n"
            f.write(strLn)
        strLn = "static int nx_" + str(n) +"[] = {"
        strLn += str(mat(blk.nx).tolist())[2:-2] + "};\n"
        f.write(strLn)
    f.write("\n")

    f.write("/* Nodes */\n")
    for n in range(1,maxNode+1):
        strLn = "static double Node_" + str(n) + "[] = {0.0};\n"
        f.write(strLn)

    f.write("\n")

    f.write("/* Input and outputs */\n")
    for n in range(0,N):
        blk = Blocks[n]
        nin = size(blk.pin)
        nout = size(blk.pout)
        if (nin!=0):
            strLn = "static void *inptr_" + str(n) + "[]  = {"
            for m in range(0,nin):
                strLn += "0,"
            strLn = strLn[0:-1] + "};\n"
            f.write(strLn)
        if (nout!=0):
            strLn = "static void *outptr_" + str(n) + "[] = {"
            for m in range(0,nout):
                strLn += "0,"
            strLn = strLn[0:-1] + "};\n"
            f.write(strLn)

    f.write("\n\n")

    f.write("/* Initialization function */\n\n")
    strLn = "int " + model + "_init()\n"
    strLn += "{\n"
    f.write(strLn)
    for n in range(0,N):
        blk = Blocks[n]
        nin = size(blk.pin)
        nout = size(blk.pout)

        if (nin!=0):
            for m in range(0,nin):
                strLn = "  inptr_" + str(n) + "[" + str(m) + "]  = (void *) Node_" + str(blk.pin[m]) + ";\n"
                f.write(strLn)
        if (nout!=0):
            for m in range(0,nout):
                strLn = "  outptr_" + str(n) + "[" + str(m) + "] = (void *) Node_" + str(blk.pout[m]) + ";\n"
                f.write(strLn)
    f.write("\n")

    f.write("/* Block definition */\n\n")
    for n in range(0,N):
        blk = Blocks[n]
        nin = size(blk.pin)
        nout = size(blk.pout)

        strLn =  "  block_" + model + "[" + str(n) + "].nin  = " + str(nin) + ";\n"
        strLn += "  block_" + model + "[" + str(n) + "].nout = " + str(nout) + ";\n"

        port = "nx_" + str(n)
        strLn += "  block_" + model + "[" + str(n) + "].nx   = " + port + ";\n"

        if (nin == 0):
            port = "NULL"
        else:
            port = "inptr_" + str(n)
        strLn += "  block_" + model + "[" + str(n) + "].u    = " + port + ";\n"
        if (nout == 0):
            port = "NULL"
        else:
            port = "outptr_" + str(n)
        strLn += "  block_" + model + "[" + str(n) + "].y    = " + port + ";\n"
        if (size(blk.realPar) != 0):
            par = "realPar_" + str(n)
        else:
            par = "NULL"
        strLn += "  block_" + model + "[" + str(n) + "].realPar = " + par + ";\n"
        if (size(blk.intPar) != 0):
            par = "intPar_" + str(n)
        else:
            par = "NULL"
        strLn += "  block_" + model + "[" + str(n) + "].intPar = " + par + ";\n"
        strLn += "  block_" + model + "[" + str(n) + "].str = " +'"' + blk.str + '"' + ";\n"
        strLn += "  block_" + model + "[" + str(n) + "].ptrPar = NULL;\n"
        f.write(strLn)
        f.write("\n")
    f.write("\n")

    f.write("/* Set initial outputs */\n\n")

    for n in range(0,N):
        blk = Blocks[n]
        strLn = "  " + blk.fcn + "(INIT, &block_" + model + "[" + str(n) + "]);\n"
        f.write(strLn)
    f.write("\n")

    for n in range(0,N):
        blk = Blocks[n]
        strLn = "  " + blk.fcn + "(OUT, &block_" + model + "[" + str(n) + "]);\n"
#        f.write(strLn)
    f.write("\n")

    for n in range(0,N):
        blk = Blocks[n]
        if (blk.nx[1] != 0):
            strLn = "  " + blk.fcn + "(STUPD, &block_" + model + "[" + str(n) + "]);\n"
            f.write(strLn)
    f.write("}\n\n")

    f.write("/* ISR function */\n\n")
    strLn = "int " + model + "_isr(double t)\n"
    strLn += "{\n"
    f.write(strLn)

    if (totContBlk != 0):
        f.write("int i, j;\n")
        f.write("double h;\n\n")

    for n in range(0,N):
        blk = Blocks[n]
        strLn = "  " + blk.fcn + "(OUT, &block_" + model + "[" + str(n) + "]);\n"
        f.write(strLn)
    f.write("\n")

    for n in range(0,N):
        blk = Blocks[n]
        if (blk.nx[1] != 0):
            strLn = "  " + blk.fcn + "(STUPD, &block_" + model + "[" + str(n) + "]);\n"
            f.write(strLn)
    f.write("\n")

    if (totContBlk != 0):
        strLn = "  h = " + model + "_get_tsamp()/" + str(rkstep) + ";\n\n"
        f.write(strLn)

        for n in range(0,N):
            blk = Blocks[n]
            if (blk.nx[0] != 0):
                strLn = "  block_" + model + "[" + str(n) + "].realPar[0] = h;\n"
                f.write(strLn)
            
        strLn = "  for(i=0;i<" + str(rkstep) + ";i++){\n"
        f.write(strLn)
        for n in range(0,N):
            blk = Blocks[n]
            if (blk.nx[0] != 0):
                strLn = "    " + blk.fcn + "(OUT, &block_" + model + "[" + str(n) + "]);\n"
                f.write(strLn)

        for n in range(0,N):
            blk = Blocks[n]
            if (blk.nx[0] != 0):
                strLn = "    " + blk.fcn + "(STUPD, &block_" + model + "[" + str(n) + "]);\n"
                f.write(strLn)

        f.write("  }\n")

    f.write("}\n")

    f.write("/* Termination function */\n\n")
    strLn = "int " + model + "_end()\n"
    strLn += "{\n"
    f.write(strLn)
    for n in range(0,N):
        blk = Blocks[n]
        strLn = "  " + blk.fcn + "(END, &block_" + model + "[" + str(n) + "]);\n"
        f.write(strLn)
    f.write("}\n\n")
    f.close()

Print = printBlk([1])
LTI_discrete = dssBlk([2],[1],  intg,  0)
Step = stepBlk([2],  stepTime,  stepValue)

blks = [Print,LTI_discrete,Step,]

fname = 'testIntg'
os.mkdir("./testIntg_gen")
os.chdir("./testIntg_gen")
genCode(fname, Tsamp, blks)

os.chdir("..")
