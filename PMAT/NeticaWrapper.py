# -*- coding: utf-8 -*-
"""
PYTHON WRAPPER TO OPEN AND RUN BBNS DEVELOPED WITH THE NETICA GUI

Functionalities:
    * Open BBNs
    * Display BBN chracteristics
    * Display inputnode states
    * Run casefiles
    * Develop net-replacing look-up tables
    * Save and plot results of outputnodes
 
Requirements for nets developed with the Netica GUI:
    * Nets have to have a nodeset 'IN' for the inputnodes and a nodeset 'OUT' for the output nodes
    * For the inputnodes, statenames are used and have to be defined
    * For the outputnodes, statetitles are used and have to be defined numerically
    * Netica.dll has to be in the working directory
    
"""

#DEPENDENCIES
#------------

import os
import ctypes as ct
import numpy as np

#NETICA WRAPPER CLASS
#--------------------

class OpenBayesNet():
    
    def __init__ (self, netname, password):
        """
        Initialize network object. The Licensefile for the Netica.dll, if present, can be provided in the code below
        """
        
        #create new environment 
        if '/' in netname:
            directarray = netname.split('/')           
            direct  = '/'.join(directarray[0:-1])
            netname = directarray[-1]
        else: 
            direct = os.getcwd()

        self.n = ct.windll.Netica                 
        self.env = ct.c_void_p(self.n.NewNeticaEnviron_ns(password,None,None))
        self.mesg = ct.create_string_buffer('\000' * 1024)
        self.n.InitNetica2_bn(self.env, ct.byref(self.mesg))

        os.chdir(direct)
        
        #Open net from provided file
        streamer = self.n.NewFileStream_ns(netname,self.env,None)
        cnet = self.n.ReadNet_bn(streamer,0x10) #0x10 is a constant taken from Netica.h
        self.net = cnet
        
        #Disable automatic updating
        self.n.SetNetAutoUpdate_bn(self.net, 0) 
        
        #Identify input, output and intermediate nodes
        inputnodeset = ct.c_char_p('IN')
        outputnodeset = ct.c_char_p('OUT')
        outputcnodes = []
        inputcnodes = []
        all_nodes = self.n.GetNetNodes2_bn (self.net,None)
        internodes = 0
        for t in range(self.n.LengthNodeList_bn(all_nodes)):            
            cn = self.n.NthNode_bn(all_nodes,t)            
            if self.n.IsNodeInNodeset_bn(self.n.NthNode_bn(all_nodes,t),inputnodeset): inputcnodes.append(cn)
            elif self.n.IsNodeInNodeset_bn(self.n.NthNode_bn(all_nodes,t),outputnodeset): outputcnodes.append(cn)
            else: internodes+=1
        self.output, self.input= outputcnodes,inputcnodes
        self.numberofnodes = [len(inputcnodes),internodes,len(outputcnodes)]

        #Compile network
        self.n.CompileNet_bn(cnet)
     
     
    def __repr__(self):
        """
        Representation of a network object in the python command line
        """
        
        name = ct.cast(self.n.GetNetName_bn(self.net),ct.c_char_p).value
        numnodes = str(self.numberofnodes)
        
        inputnodes,outputnodes = [],[]
        for i in self.input:
            inputnodes.append(ct.cast(self.n.GetNodeName_bn(i),ct.c_char_p).value)
        inodes = ','.join(inputnodes)
        for j in self.output:
            outputnodes.append(ct.cast(self.n.GetNodeName_bn(j),ct.c_char_p).value)
        onodes = ','.join(outputnodes)
        
        return ' netname: '+ name +'\n number of nodes (i,int,o): '+ numnodes + '\n inputnodes: ' + inodes +'\n outputnodes: ' + onodes
        
    def Netname(self):
        """
        Returns the name of the network model
        """
        
        return ct.cast(self.n.GetNetName_bn(self.net),ct.c_char_p).value
                
    def Outputnodes(self):
        """
        returns an array of the names of the outputnodes
        """
        
        return [ct.cast(self.n.GetNodeName_bn(j),ct.c_char_p).value for j in self.output]
        
    def Inputnodes(self):
        """
        returns an array of the names of the inputnodes
        """
        
        return [ct.cast(self.n.GetNodeName_bn(j),ct.c_char_p).value for j in self.input]
        
    def RunCasefile (self,casefile, output = 1,ignT=0,cpT=0):
        ''' 
        Generate output form a casefile, returns a matrix with state titles of outputnode as header
        '''
        
        #retrieve characteristics of outputnodes    
        cnodes = [self.output[i] for i in range(output)]
        nroutputstates = [self.n.GetNodeNumberStates_bn(i) for i in cnodes]
        states = [[ct.cast(self.n.GetNodeStateTitle_bn(self.output[i],j),ct.c_char_p).value for j in range(nroutputstates[i])] for i in range(output)] 
        try: intstates = [[float(s) for s in t] for t in states]
        except ValueError: return "Titles of the outputnode's states should be defined numerically"
        borders = []
        for s in intstates:
            if s[0]==0:
                borders.append(np.array([0,0]+[np.average(s[i+1:i+3]) for i in range(len(s)-2)]+[s[-1]+s[1]]))
            elif s[0]<0:
                b = [np.average(s[i:i+2]) for i in range(len(s)-1)]
                interval = np.abs(b[1]-b[0])               
                borders.append(np.array([s[0]-interval/2]+b+[s[-1]+interval/2]))
            else: borders.append(np.array([0]+[np.average(s[i:i+2]) for i in range(len(s)-1)]+[s[-1]+s[0]]))
            
        #Prepare data matrix
        data = []       
        header= []
        for s in states:
            header = header + s + ['Prob','MostProb','ExpV','StdDev','Max','ProbMax','CumProb','Sim','Ign']
        data.append(header)
        
        #Walk through file
        stream = self.n.NewFileStream_ns (casefile, self.env, None)
        all_nodes = self.n.GetNetNodes2_bn(self.net,None) 
        caseposn = ct.c_long(-15) #-15 is a constant taken form Netica.h
        
        linenumber = 0
        while True:
            self.n.RetractNetFindings_bn(self.net)
            self.n.ReadNetFindings_bn (ct.byref(caseposn), stream, all_nodes, None, None) 
            if caseposn.value == -13: break #-13 is a constant taken from Netica.h
            linedata = [] 
            for i,m in enumerate(cnodes):             
                belief = ct.cast(self.n.GetNodeBeliefs_bn (m),ct.POINTER(ct.c_float))[0:nroutputstates[i]]
                try: 
                    expectedV = sum([float(states[i][j])*belief[j] for j in range(len(belief))])
                    stddev = np.sqrt(sum([((float(states[i][j])-expectedV)**2)*belief[j] for j in range(len(belief))]))
                    prob = max(belief)
                    mostprob = states[i][belief.index(max(belief))]
                    lastelement = [(index,d) for index,d in enumerate(belief) if d][-1]
                    Max = states[i][lastelement[0]]
                    probmax = lastelement[1]
                    cumprob = ProbHigherThan(borders[i],belief,cpT)
                    sim = simulate(states[i],belief,1)
                    if prob>(ignT/100): ign =  mostprob
                    else: ign = -9999
                except: 
                    #print 'Zero array returned as belief vector at linenumber: ' + str(linenumber)
                    belief = [-9999 for b in belief]                    
                    prob,mostprob,expectedV,stddev,Max,probmax,cumprob,sim,ign = -9999,-9999,-9999,-9999,-9999,-9999,-9999,-9999,-9999
                linedata = linedata + belief + [prob, mostprob, expectedV, stddev, Max, probmax,cumprob,sim,ign]
                belief,prob,mostprob,expectedV,stddev,Max,probmax,cumprob,sim,ign = 0,0,0,0,0,0,0,0,0,0   
            linedata = ['{:f}'.format(float(a)) for a in linedata]
            data.append(linedata) 
            caseposn = ct.c_long(-14) 
            linenumber+=1
        
        #delete the stream to the file
        self.n.DeleteStream_ns (stream)
       
        return data


#Additional functionalities
#--------------------------
            
def simulate(values,probs,n):    
    bins = np.add.accumulate(probs)
    try: draw = values[np.digitize(np.random.random_sample(n)*(bins[-1]), bins)]
    except: 
        array = np.digitize(np.random.random_sample(n)*(bins[-1]), bins)
        array[array == len(bins)]=len(bins)-1
        draw = values(array)
    return draw
    
def ProbHigherThan(borders,probs,threshold):
    i = np.digitize(np.array([threshold]),borders)[0] #geeft nummer van de klasse
    prob = sum(probs[i:])
    interpol = (borders[i]-threshold)/(borders[i]-borders[i-1])
    prob =  prob+interpol*probs[i-1]
    return prob
