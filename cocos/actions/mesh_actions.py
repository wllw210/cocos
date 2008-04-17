#
# Cocos Mesh Actions
#

'''Mesh Actions

Mesh Actions
============

'''

__docformat__ = 'restructuredtext'

import math
import random
rr = random.randrange

from cocos.director import director
from cocos.mesh import TILES_MODE, GRID_MODE
from cocos.euclid import *
from base_actions import *

__all__ = [ 'MeshException',            # Mesh Exceptions
            'MeshAction',               # Base classes
            'MeshTilesAction', 'MeshGridAction',
            'QuadMoveBy',               # Basic class for skews, etc...

            'ShakyTiles',               # Tiles Actions
            'ShuffleTiles',

            'MoveCornerUp',             # QuadMoveBy Actions
            'MoveCornerDown',
            'SkewHorizontal',
            'SkewVertical',
            'Flip','FlipX','FlipY',
            'CornerSwap',         
            
            'Shaky',                    # Trembling actions
            'Liquid','Sin',             # Liquid and Sin
            'Lens',                     # Lens effect (magnifying)

            'GridNop',                  # Grid None Effect - For testing
            ]

class MeshException( Exception ):
    pass
    
class MeshAction( IntervalAction ):
    '''MeshAction is the base class of all Mesh Actions.'''
    def init( self, grid=(4,4), duration=5):
        """Initialize the Mesh Action
        :Parameters:
            `grid` : (int,int)
                Number of horizontal and vertical quads in the mesh
            `duration` : int 
                Number of seconds that the action will last
        """
        self.duration = duration
        if not isinstance(grid,Point2):
            grid = Point2( *grid)
        self.grid = grid

    def start( self ):
        self.target.mesh.init( self.grid )
        self.target.mesh.active = True

        x,y = director.get_window_size()
        self.size_x = x // self.grid.x
        self.size_y = y // self.grid.y
        

    def done( self ):
        r = super(MeshAction,self).done()
        if r:
            self.target.mesh.active = False
        return r

    def set_vertex( self, x, y, v):
        raise NotImplementedError("abstract")

    def get_vertex( self, x, y):
        raise NotImplementedError("abstract")


class MeshGridAction( MeshAction ):
    '''A MeshGrid action is an action that does transformations
    to a grid.'''
    def start( self ):
        super( MeshGridAction, self ).start()
        self.target.mesh.mesh_mode = GRID_MODE

    def get_vertex( self, x, y):
        '''Get the current vertex point value

        :Parameters:
            `x` : int 
               x-vertex
            `y` : int
               y-vertex

        :rtype: (int,int)
        '''
        idx = (x * (self.grid.y+1) + y) * 2
        x = self.target.mesh.vertex_list_idx.vertices[idx]
        y = self.target.mesh.vertex_list_idx.vertices[idx+1]
        return (x,y)

    def set_vertex( self, x, y, v):
        '''Set a vertex point is a certain value

        :Parameters:
            `x` : int 
               x-vertex
            `y` : int
               y-vertex
            `v` : (int, int)
                tuple value for the vertex
        '''
        idx = (x * (self.grid.y+1) + y) * 2
        self.target.mesh.vertex_list_idx.vertices[idx] = int(v[0])
        self.target.mesh.vertex_list_idx.vertices[idx+1] = int(v[1])


class MeshTilesAction( MeshAction ):
    '''A MeshTiles action is an action that does transformations
    to a grid composed of tiles. You can transform each tile individually'''
    def start( self ):
        super( MeshTilesAction, self ).start()
        self.target.mesh.mesh_mode = TILES_MODE

    def _get_vertex_idx( self, i, j, k ):
        if i==0 and j==0:
            idx = 0
        elif i==0 and j>0:
            idx = ( (j-1)*4 + 3 ) * 2
        elif i>0 and j==0:
            idx = ((i-1) * 4 * self.grid.y + 1 ) * 2
        else:
            idx = ((i-1) * 4 * self.grid.y + (j-1) * 4 + k) * 2

        return idx

    def _set_vertex( self, i, j, k, v ):
        if i < 0 or i > self.grid.x:
            return
        if j < 0 or j > self.grid.y:
            return
        if k< 0 or k >=4:
            return

        idx = self._get_vertex_idx( i,j,k)

        self.target.mesh.vertex_list.vertices[idx] = int(v[0])
        self.target.mesh.vertex_list.vertices[idx+1] = int(v[1])

    def set_vertex( self, x, y, v):
        '''Set a vertex point is a certain value

        :Parameters:
            `x` : int 
               x-vertex
            `y` : int
               y-vertex
            `v` : (int, int)
                tuple value for the vertex
        '''
        self._set_vertex( x, y, 2, v)
        self._set_vertex( x+1, y, 3, v)
        self._set_vertex( x+1, y+1, 0, v)
        self._set_vertex( x, y+1, 1, v)

    def get_vertex( self, x, y):
        '''Get the current vertex point value

        :Parameters:
            `x` : int 
               x-vertex
            `y` : int
               y-vertex

        :rtype: (int,int)
        '''
        idx = self._get_vertex_idx( x,y,2 )
        x = self.target.mesh.vertex_list.vertices[idx]
        y = self.target.mesh.vertex_list.vertices[idx+1]
        return (x,y)

# Don't export this class
class Tile(object):
    def __init__(self, position=(0,0), start_position=(0,0), delta=(0,0) ):
        super(Tile,self).__init__()
        self.position = position
        self.start_position = start_position
        self.delta = delta

    def __repr__(self):
        return "(start_pos: %s  pos: %s   delta:%s)" % (self.start_position, self.position, self.delta)

class ShakyTiles( MeshTilesAction ):
    '''ShakyTiles simulates a shaky floor composed of tiles

       scene.do( ShakyTiles( randrange=6, grid=(4,4), duration=10) )
    '''

    def init( self, randrange=6, *args, **kw ):
        super(ShakyTiles,self).init(*args,**kw)
        self.randrange = randrange

    def update( self, t ):
        for i in range(0, self.grid.x):
            for j in range(0, self.grid.y):
                for k in range(0,4):

                    idx = (i * 4 * self.grid.y + j * 4 + k) * 2
                    x = self.target.mesh.vertex_points[idx]
                    y = self.target.mesh.vertex_points[idx+1]

                    x += rr(-self.randrange, self.randrange)
                    y += rr(-self.randrange, self.randrange)

                    self.target.mesh.vertex_list.vertices[idx] = int(x)
                    self.target.mesh.vertex_list.vertices[idx+1] = int(y)
                
    def __reversed__(self):
        return ShakyTiles( randrange=self.randrange, grid=self.grid, y_quads=self.grid.y, duration=self.duration)

class ShuffleTiles( MeshTilesAction ):
    '''ShuffleTiles moves the tiles randomly across the screen and then put
    them back into the original place.
       scene.do( ShuffleTiles( grid=(4,4), duration=10) )
    '''

    def start(self):
        super(ShuffleTiles,self).start()
        self.tiles = {}
        self.dst_tiles = {}
        for i in range(self.grid.x):
            for j in range(self.grid.y):
                self.tiles[(i,j)] = Tile( position = Point2(i,j), 
                                          start_position = Point2(i,j), 
                                          delta= self._get_delta(i,j) )

    def place_tile(self, i, j):
        t = self.tiles[(i,j)]

        for k in range(0,4):
            idx = (i * 4 * self.grid.y + j * 4 + k) * 2

            x=0
            y=0
            
            if k==1 or k==2:
                x = self.target.mesh.x_step
            if k==2 or k==3:
                y = self.target.mesh.y_step
                
            x += t.position.x * self.target.mesh.x_step
            y += t.position.y * self.target.mesh.y_step
            
            self.target.mesh.vertex_list.vertices[idx] = int(x)
            self.target.mesh.vertex_list.vertices[idx+1] = int(y)
        
    def update( self, t ):
        if t < 1.0/3:
            self.phase_shuffle(t/ (1.0/3) )
        elif t < 2.0/3:
            self.phase_shuffle(1)
#            self.phase_sleep()
        else:
            self.phase_shuffle_back( (t-2.0/3) / (1.0/3) )

    def phase_shuffle(self, t ):
        for i in range(0, self.grid.x):
            for j in range(0, self.grid.y):
                self.tiles[(i,j)].position = self.tiles[(i,j)].start_position + self.tiles[(i,j)].delta * t
                self.place_tile(i,j)
   
    def phase_shuffle_back(self, t):
        for i in range(0, self.grid.x):
            for j in range(0, self.grid.y):
                self.tiles[(i,j)].position = self.tiles[(i,j)].start_position + self.tiles[(i,j)].delta * (1-t)
                self.place_tile(i,j)
                
    def phase_sleep(self):
        return
                
    def __reversed__(self):
        return ShuffleTiles( grid=self.grid, duration=self.duration)

    # private method
    def _get_delta(self, x, y):
        a = rr(0, self.grid.x), rr(0, self.grid.y)  
        if not self.dst_tiles.get(a, False):
            self.dst_tiles[ a ] = True
            return Point2(*a)-Point2(x,y)
        for i in range(a[0], self.grid.x):
            for j in range(self.grid.y):
                if not self.dst_tiles.get( (i,j), False):
                    self.dst_tiles[ (i,j) ] = True
                    return Point2(i,j)-Point2(x,y)
        for i in range(a[0]):
            for j in range(self.grid.y):
                if not self.dst_tiles.get( (i,j), False):
                    self.dst_tiles[ (i,j) ] = True
                    return Point2(i,j)-Point2(x,y)
        raise Exception("_get_delta() algorithm needs to be improved!. Blame the authors")

class Shaky( MeshGridAction):
    '''Shaky simulates an earthquake

       scene.do( Shaky( randrange=6, grid=(4,4), duration=10) )
    '''
    def init( self, randrange=6, *args, **kw ):
        super(Shaky,self).init(*args,**kw)
        self.randrange = randrange

    def update( self, t ):
        for i in range(0, self.grid.x+1):
            for j in range(0, self.grid.y+1):

                x = i* self.size_x
                y = j* self.size_y

                x += rr( -self.randrange, self.randrange )
                y += rr( -self.randrange, self.randrange )

                self.set_vertex( i,j, (x,y) )

    def __reversed__(self):
        return Shaky( randrange=self.randrage, grid=self.grid, duration=self.duration)

class Liquid( MeshGridAction ):
    '''Liquid simulates the liquid effect

       scene.do( Liquid( grid=(16,16), duration=10) )
    '''

    def update( self, t ):
        elapsed = t * self.duration
            
        for i in range(1, self.grid.x):
            for j in range(1, self.grid.y):
                x = i* self.size_x
                y = j* self.size_y
                xpos = (x + (math.sin(elapsed*2 + x * .01) * self.size_x))
                ypos = (y + (math.sin(elapsed*2 + y * .01) * self.size_y)) 
                self.set_vertex( i,j, (xpos,ypos) )

    def __reversed__(self):
        return Liquid( grid=self.grid, duration=self.duration)


class Sin( MeshGridAction ):
    '''Sin simulates math.sin effect both in the vertical and horizontal axis

       scene.do( Sin( vertical_sin=True, horizontal_sin=False, grid=(16,16), duration=10) )
    '''

    def init( self, horizontal_sin=True, vertical_sin=True, *args, **kw ):
        super(Sin, self).init( *args, **kw )
        self.horizontal_sin = horizontal_sin
        self.vertical_sin = vertical_sin

    def update( self, t ):
        elapsed = t * self.duration
        
        for i in range(0, self.grid.x+1):
            for j in range(0, self.grid.y+1):
                x = i* self.size_x
                y = j* self.size_y

                if self.vertical_sin:
                    xpos = (x + (math.sin(elapsed*2 + y * .01) * self.size_x))
                else:
                    xpos = x

                if self.horizontal_sin:
                    ypos = (y + (math.sin(elapsed*2 + x * .01) * self.size_y)) 
                else:
                    ypos = y

                self.set_vertex( i,j, (xpos,ypos) )

    def __reversed__(self):
        return Sin( horizontal_sin=self.horizontal_sin, vertical_sin=self.vertical_sin,
                    grid=self.grid,
                    duration=self.duration)


class Lens( MeshGridAction ):
    '''Lens simulates the a Lens / Magnifying glass effect

       scene.do( Lens(grid=(16,16), duration=10) )
    '''

    def start( self ):
        super(Lens,self).start()
        x,y = director.get_window_size()
        self.center_x = x // 2
        self.center_y = y // 2
        self.radius = y // 4
        self.lens_effect = 0.1

        self.go_left = True


    def update( self, t ):
        center_point = Point2( self.center_x, self.center_y)

        for i in range(0, self.grid.x+1):
            for j in range(0, self.grid.y+1):

                x = i* self.size_x
                y = j* self.size_y
                p = Point2( x,y )

                vect = center_point - p
                r = abs(vect)

                if r < self.radius:

                    pre_log = r/self.radius
                    if pre_log == 0:
                        pre_log = 0.001
                    l = math.log( pre_log )*self.lens_effect
                    r = math.exp( l ) * self.radius

                    vect.normalize()
                    new_vect = vect * r

                    x -= new_vect.x
                    y -= new_vect.y

                self.set_vertex( i,j, (x,y) )

#        if self.go_left:
#            self.center_x -= 2.5 
#            if self.center_x < 40:
#                self.go_left = False
#        else:
#            self.center_x += 2.5 
#            if self.center_x > 620:
#                self.go_left = True

    def __reversed__(self):
        return Lens( grid=self.grid, duration=self.duration)

class GridNop( MeshGridAction ):
    '''For testing only
    '''

    def nop_update( self, t ):
        for i in range(0, self.grid.x+1):
            for j in range(0, self.grid.y+1):
                x = i* self.size_x
                y = j* self.size_y
                self.set_vertex( i,j, (x,y) )
    def __reversed__(self):
        return GridNop( grid=self.grid, duration=self.duration)

class QuadMoveBy( MeshGridAction ):
    '''QuadMoveBy moves each vertex of the quad

       scene.do( QuadMoveBy( src0, src1, src2, src3,
               delta0, delta1, delta2, delta3,
               grid, duration) )

       Vertex positions::

            vertex3 --<-- vertex2
                |            |
                v            ^
                |            |
            vertex0 -->-- vertex1
       '''

    def init( self, 
              src0=(0,0), src1=(-1,-1), src2=(-1,-1), src3=(-1,-1),
              delta0=(0,0), delta1=(0,0), delta2=(0,0), delta3=(0,0),
              grid=(1,1),
              *args, **kw ):
        '''Initializes the QuadMoveBy

        :Parameters:
            `dst0` : (x,y)
                The bottom-left relative coordinate
            `dst1` : (x,y)
                The bottom-right relative coordinate
            `dst2` : (x,y)
                The top-right relative coordinate
            `dst3` : (x,y)
                The top-left relative coordinate
        '''

        if grid != (1,1):
            raise MeshException("Invalid grid size.")

        super( QuadMoveBy, self).init( grid, *args, **kw )
        
        x,y = director.get_window_size()
        
        if src1 == (-1,-1):
            src1 = ( x,0 )
        if src2 == (-1,-1):
            src2 = (x,y)
        if src3 == (-1,-1):
            src3 = (0,y)  

        self.src0 = Point2( *src0 )
        self.src1 = Point2( *src1 )  
        self.src2 = Point2( *src2 )
        self.src3 = Point2( *src3 )
        self.delta0 = Point2( *delta0 )
        self.delta1 = Point2( *delta1 )
        self.delta2 = Point2( *delta2 )
        self.delta3 = Point2( *delta3 )
       
    def update( self, t ):
        new_pos0 = self.src0 + self.delta0 * t
        new_pos1 = self.src1 + self.delta1 * t
        new_pos2 = self.src2 + self.delta2 * t
        new_pos3 = self.src3 + self.delta3 * t

        self.set_vertex( 0,0, new_pos0 )
        self.set_vertex( 1,0, new_pos1 )
        self.set_vertex( 1,1, new_pos2 )
        self.set_vertex( 0,1, new_pos3 )

    def __reversed__(self):
        return QuadMoveBy( self.src0 + self.delta0, self.src1 + self.delta1, self.src2 + self.delta2, self.src3 + self.delta3,
                           -self.delta0, -self.delta1, -self.delta2, -self.delta3,
                           self.grid, duration=self.duration )
    
class MoveCornerUp( QuadMoveBy ):
    '''MoveCornerUp moves the bottom-right corner to the upper-left corner in duration time'''
    def __init__(self, *args, **kw):
        x,y = director.get_window_size()
        super(MoveCornerUp, self).__init__( delta1=(-x,y), *args, **kw )

class MoveCornerDown( QuadMoveBy ):
    '''MoveCornerDown moves the upper-left corner to the bottom-right corner in duration time'''
    def __init__(self, *args, **kw):
        x,y = director.get_window_size()
        super(MoveCornerDown, self).__init__( delta3=(x,-y), *args, **kw )

class CornerSwap( QuadMoveBy ):
    '''CornerSwap moves the upper-left corner to the bottom-right corner in vice-versa in duration time.
    The resulting effect is a reflection + rotation.
    '''
    def __init__(self, *args, **kw):
        x,y = director.get_window_size()
        super(CornerSwap, self).__init__( delta1=(-x,y), delta3=(x,-y), *args, **kw )

class Flip( QuadMoveBy ):
    '''Flip moves the upper-left corner to the bottom-left corner and vice-versa, and
    moves the upper-right corner to the bottom-left corner and vice-versa, flipping the
    window upside-down, and right-left.
    '''
    def __init__(self, *args, **kw):
        x,y = director.get_window_size()
        super(Flip, self).__init__( delta0=(x,y), delta1=(-x,y), delta2=(-x,-y), delta3=(x,-y), *args, **kw )

class FlipX( QuadMoveBy ):
    '''FlipX flips the screen horizontally, moving the left corners to the right, and vice-versa.
    '''
    def __init__(self, *args, **kw):
        x,y = director.get_window_size()
        super(FlipX, self).__init__( delta0=(x,0), delta1=(-x,0), delta2=(-x,0), delta3=(x,0), *args, **kw )

class FlipY( QuadMoveBy ):
    '''FlipY flips the screen vertically, moving the upper corners to the bottom, and vice-versa.
    '''
    def __init__(self, *args, **kw):
        x,y = director.get_window_size()
        super(FlipY, self).__init__( delta0=(0,y), delta1=(0,y), delta2=(0,-y), delta3=(0,-y), *args, **kw )

class SkewHorizontal( QuadMoveBy ):
    '''SkewHorizontal skews the screen horizontally. default skew: x/3'''
    def __init__(self, delta=None, *args, **kw):
        x,y = director.get_window_size()
        if delta==None:
            delta=x//3
        super(SkewHorizontal, self).__init__( delta1=(-delta,0), delta3=(delta,0), *args, **kw )

class SkewVertical( QuadMoveBy ):
    '''SkewVertical skews the screen vertically. default skew: y/3'''
    def __init__(self, delta=None, *args, **kw):
        x,y = director.get_window_size()
        if delta==None:
            delta=y//3
        super(SkewVertical, self).__init__( delta0=(0,delta), delta2=(0,-delta), *args, **kw )