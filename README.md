# JD-Align-Edge
 Edge alignment toolset


## Features

### Align Parallel
Select exactly two edges that do not share vertices to make one parallel to the other.

Makes the selected edge parallel to the active edge. <br />
The default behaviour will slide the yellow highlighted vertex (whichever is closest to the mouse) along one of its connected edges to make it parallel. <br />
The connected edge that is most in line with the mouse cursor will be used to slide the vertex. <br />
In the situation that no valid parallel edge can be found this way, the drawn edges will turn red and the UI will also reflect this. <br />
There is another alignment mode for such cases, see below. <br />

Pressing V will toggle between the Slide (default) and Absolute modes. <br />
In Absolute mode, the selected edge is made parallel to the active edge, while retaining its length. <br />
It does not take into account any of the connected geometry. <br />

In certain cases while using Absolute mode, you may need to flip the direction in which the edge is made parallel. <br />
This is done by pressing F.
