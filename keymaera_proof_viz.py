# requires pygraphvis (installed via conda with https://anaconda.org/alubbock/pygraphviz)
# dot -c had to be entered in the conda command line at least once before running for this to work

import matplotlib.pyplot as plt
import networkx as nx
import argparse

import numpy as np

import lark
from lark import Lark
from lark.visitors import Interpreter
from lark.visitors import Visitor

import os

colormap_graph = {"QE": "#ff7f68", "dC": "#dab65b", "dW": "#c27dd3", "dIRule": "#89cd89"}
colormap_HTML = {"QE": "tomato", "dC": "goldenrod", "dW": "mediumorchid", "dIRule": "limegreen"}
default_color_graph = "#4bd2ff"
default_color_HTML = "deepskyblue"

proof_parser = Lark(r"""
    start: _thing*

    _thing: (step | "<(" branch ")" (";")*)*

    step: (type ["(" args ")"] (";")*)

    type: WORD

    args : [ARG ("," ARG)*]
    ARG  : ((["'"] WORD "==" ESCAPED_STRING) | ESCAPED_STRING)

    branch: _STRING ":" path "," _STRING ":" path

    path: _thing

    _STRING : ESCAPED_STRING
    ?word: WORD

    %import common.WORD
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS

    %ignore WS


    """, start='start')
    
# This visitor class traverses the parsed tree when invoked and generate the digraph as it does so
# Each function corresponds do a different token in the parser
class KYX_Visitor(Interpreter):

    # Initialize a blank tree structure for the digraph
    def __init__(self):
        self.T = []
        self.N_VERTICIES = 0
        self.LAST_VERTEX = 0
        self.N_BRANCHES = 0
        self.labels = {}
    
    def start(self, tree):
        KYX_Visitor.path(self, tree)
    
    # Visit each step and branch in order
    def path(self, tree):
        for subtree in tree.children:
            KYX_Visitor.visit(self, subtree)
    
    # If a proof branch (such as "Use"/"Show") is encountered, treat each branch path as a separate tree and traverse each one
    def branch(self, tree):
        BRANCH_VERTEX = self.LAST_VERTEX
        self.N_BRANCHES += 1
        
        for subtree in tree.children:
            KYX_Visitor.visit(self, subtree)
            
            # Reset the last vertex when we finish with a branch so the first node of the new branch
            # links to the original branch node
            self.LAST_VERTEX =  BRANCH_VERTEX

    def step(self, tree):
    
        # Set the node number to the next vertex number and apply the correct label
        tree.num = self.N_VERTICIES
        self.labels[self.N_VERTICIES] = tree.children[0].children[0].value
        
        # If the tree has more than one node, link this node to the last one and advance
        if(self.N_VERTICIES>0):
            self.T.append([self.LAST_VERTEX, tree.num])
            
        self.LAST_VERTEX=self.N_VERTICIES
        self.N_VERTICIES+=1

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Produces a graph visualization of KeymaeraX proof tactics')
    parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='A KeymaeraX tactic file to process.')
    parser.add_argument('--outdir', dest="outdir", metavar='OUTDIR', type=str, default="", help='Image and HTML file output directory (default is current directory).')
    parser.add_argument('--Gnodesep', dest="Gnodesep", metavar='N', type=str, default="10", help='Gnodesep argument for graphviz. Controls the horizontal separation between nodes (default 10).')
    parser.add_argument('--Granksep', dest="Granksep", metavar='N', type=str, default="3", help='Granksep argument for graphviz. Controls the vertical separation between each "layer" of nodes (default 3).')
    args = parser.parse_args()

    for proof_file in args.files:

        # Extract the base filename from the full filename (with extension)
        filename = proof_file[:proof_file.rfind(".")]

        # Read proof from file, starting at "Tactic" and ending at "End.", adding each line in between to the proof string
        file = open(proof_file, "r")
        proof = ""
        lines = file.readlines()
        start = -1
        end = -1
        for i,line in enumerate(lines):
            if("Tactic" in line):
                start = i+1
                break
                
        if(start<0):
            print("ERROR: Start of proof (the 'Tactic' line) not found.")
            file.close()
            os._exit(0)
            
        for i,line in enumerate(lines[start:]):
            if("End." in line):
                end = start+i-2
                break
            proof += line
            
        if(end<0):
            print("ERROR: End of proof (the 'End.' line) not found.")
            file.close()
            os._exit(0)
            
        file.close()
        
        # Generate a parse tree of the proof
        tree = proof_parser.parse(proof)
        print("Proof Tree for", proof_file)
        print(tree)
        print()
        
        #all_tokens = tree.scan_values(lambda v: True)

        # Iterate over the parsed tree and construct a set of edges to populate the displayed digraph
        visitor = KYX_Visitor()
        visitor.visit(tree)
        
        # Create a digraph to hold the tree
        DG = nx.DiGraph()            
        
        # If we have a single vertex, we duplicate it, link them together, and position it over the original
        # This is done to avoid a bug in the Windows version of graphviz that prevents a single node from being rendered
        if(visitor.N_VERTICIES==1):
            visitor.T.append([0,1])
            visitor.labels[1] = ""
            
        DG.add_edges_from(visitor.T)
        
        # Generate positions for each node on the digraph using networkx
        pos = nx.nx_agraph.graphviz_layout(DG, prog="dot", args="-Gnodesep="+args.Gnodesep+" -Granksep="+args.Granksep)
        
        # Transform the positions into something readable by networkx
        for i in pos.keys():
            pos[i]=(pos[i][0],pos[i][1])
            
        # If we have one node, position the duplicate node over the original to hide it
        if(visitor.N_VERTICIES==1):
            pos[1] = pos[0]
            
        # Draw the edges of the diagram
        plt.figure(figsize=(5+visitor.N_BRANCHES, 8))
        nx.draw(DG, pos, node_size=0, alpha=0.5, node_color="blue", with_labels=False)
        
        # Color each node
        for steptype in colormap_graph.keys():
        
            pos_current = {}
            labels_current = {}
            
            # Look for all nodes of a specific type and apply the appropriate color
            for i in [x for x in visitor.labels.keys() if visitor.labels[x]==steptype]:
                pos_current[i]=pos.pop(i)
                labels_current[i]=visitor.labels.pop(i)
            
            # Draw each node as a label
            nx.draw_networkx_labels(DG, pos_current, labels_current, font_size=22, alpha=1, font_color="black", bbox={"ec": "k", "fc": colormap_graph[steptype], "alpha": 1})
        
        # Proof steps that don't have a specific color are drawn as the default color
        nx.draw_networkx_labels(DG, pos, visitor.labels, font_size=22, alpha=1, font_color="black", bbox={"ec": "k", "fc": default_color_graph, "alpha": 1})
        plt.axis("equal")
        
        # Create missing out directories if needed
        if (args.outdir!='') and (not os.path.exists(args.outdir)):
            os.makedirs(args.outdir)
        
        # Write image
        print("Writing diagram to", os.path.join(args.outdir,filename+".png"))
        plt.savefig(os.path.join(args.outdir,filename+".png"))
        
        # Output the proof as a color-coded HTML file
        f = open(os.path.join(args.outdir,filename+".html"), "w")
        print("Writing HTML file to", os.path.join(args.outdir,filename+".html"))
        f.write("<style> body {font-family:Lucida Sans;color:dimgrey} </style>")
        for i in range(start,end):
            line = lines[i]
            begin = len(line)-len(line.lstrip())
            line = line[:begin].replace(" ","&emsp;") + line[begin:]
            
            for steptype in colormap_HTML.keys():
                line = line.replace(steptype, "<span style=\"color:"+colormap_HTML[steptype]+"\">"+steptype+"</span>")
            
            for steptype in visitor.labels.values():
                line = line.replace(steptype, "<span style=\"color:"+default_color_HTML+"\">"+steptype+"</span>")
                
            f.write(line+"<br>")
            
        f.close()