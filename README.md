# Surface Explorer — Multi-Variable Function Visualizer

An interactive Tkinter application for visualizing multi-variable functions. Pick variable values on the left panel and watch the resulting plot update in real-time on the right.

## Features

- **Dynamic number of variables**: Set any n ≥ 1
- **Interactive variable pickers**: Click on 2D plots to pick values for pairs of variables
- **Real-time updates**: Plots update instantly as you change variables
- **Multiple plot types**:
  - **n = 1**: 2D line plot of x₁ vs f(x₁)
  - **n = 2**: 3D surface plot of f(x₁, x₂)
  - **n ≥ 3**: Final variable plot (3D surface for even n, line graph for odd n)
- **Scrollable variable panel**: Easily access all variable pickers for large n
- **Custom functions**: Enter any mathematical expression using standard Python/numpy syntax

## Usage

1. Set the number of variables (n)
2. Enter a function of x₁, x₂, ..., xₙ
3. Click the **Update** button or press Enter
4. Pick values for variables using the 2D plots on the left
5. Adjust the z/w ranges in the right panel to zoom in/out

## Function Syntax

Use standard Python/numpy functions:

```
sqrt(x1**2 + x2**2 + x3**2 + x4**2)
sin(x1) * cos(x2) + exp(-x3**2)
x1*x2*x3*x4 / (1 + x1**2 + x2**2 + x3**2 + x4**2)
```

Available functions: `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `sqrt`, `abs`, `sinh`, `cosh`, `tanh`, `arcsin`, `arccos`, `arctan`, `log2`, `ceil`, `floor`, `maximum`, `minimum`, `pow`, `pi`, `e`

## Requirements

- Python 3.7+
- tkinter
- numpy
- matplotlib

## Installation

```bash
git clone https://github.com/fredjt/surface-explorer.git
cd surface-explorer
python surface_explorer.py
```
