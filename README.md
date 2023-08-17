# KeymaeraProofViz
A KeymaeraX proof tactic visualizer. Produces trees that visually represent KeymeraX proof tactics.
## Installation
KeymaeraProofViz requires graphviz (https://graphviz.org/download/) to be installed.
Installation can be done using conda, pip, or manually. Note that the graphviz `dot` utility needs to be run at least once before using KeymaeraProofViz.
### Conda
```
conda env create -f keymaera_proof_viz.yml
dot -c
```
### Pip
```
pip install -r requirements.txt
dot -c
```
### Manual
```
conda install matplotlib
conda install -c alubbock pygraphviz
conda install lark
conda install networkx
dot -c
```
## Usage
KeymaeraProofViz takes in any number of .kyx proof tactic files and produces a graph visualization and highlighted HTML version of each one.

`keymaera_proof_viz.py [-h] [--outdir OUTDIR] [--Gnodesep N] [--Granksep N] FILE [FILE ...]`

It accepts the following command line options:
```
-h, --help       print a help message and exit
--outdir OUTDIR  changes the file output directory to OUTDIR instead of the current directory
--Gnodesep N     Gnodesep argument for graphviz. Controls the horizontal separation between nodes (default 10).
--Granksep N     Granksep argument for graphviz. Controls the vertical separation between each "layer" of nodes (default 3).
```
