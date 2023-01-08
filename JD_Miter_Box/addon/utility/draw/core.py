import bpy, blf, gpu
from bgl import *
from gpu_extras.batch import batch_for_shader

from .helper import make_vertices, draw_quad


# --- SHOULD NEVER BE INSTANTIATED BY ITSELF
class JDraw_UI:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    
    @property # getter
    def coor(self):
        '''Bottom Left screen coordinates of text'''
        return [self.x, self.y]

    @coor.setter
    def coor(self, coors):
        '''Set coors with list[X,Y] of coordinates'''
        self.x = coors[0]
        self.y = coors[1]


    @property # getter
    def coorX(self):
        '''Left screen coordinates of text'''
        return self.x

    @coorX.setter
    def coorX(self, coor):
        '''Set X coordinate'''
        self.x = coor   


    @property # getter
    def coorY(self):
        '''Bottom screen coordinates of text'''
        return self.y

    @coorY.setter
    def coorY(self, coor):
        '''Set Y coordinate'''
        self.y = coor


# -------------------------------------------



# --- COMPONENT CLASSES

class JDraw_Text(JDraw_UI):

    def __init__(self, x=0, y=0, string="default", size=12, color=(1, 1, 1, 1)) -> None:

        super().__init__(x, y)

        self.string = string
        self.color = color

        self.fontsize = size
        

        self.dpi = bpy.context.preferences.system.dpi
        self.font = 0


    # from ST3 course part 5-8
    def draw(self):
        blf.size(self.font, self.fontsize, int(self.dpi))
        blf.color(self.font, *self.color)
        blf.position(self.font, self.x, self.y, 0)
        # blf.enable(0, blf.SHADOW)
        # color = (0, 1, 0, 1)
        # blf.shadow(0, 3, *color)
        blf.draw(self.font, self.string)
        # blf.disable(0, blf.SHADOW)


    # from ST3 course part 5-8
    @property #getter
    def size(self):
        '''Return the dimensions of the string'''

        blf.size(0, self.fontsize, self.dpi)
        return blf.dimensions(0, str(self.string))



class JDraw_Rect(JDraw_UI):

    def __init__(self, x=0, y=0, width=100, height=50, color=(0,0,0,.5)) -> None:

        super().__init__(x, y)

        self.width = width
        self.height = height
        self.color = color


    def draw(self):
        verts = make_vertices(self.x, self.y, self.width, self.height)
        draw_quad(vertices=verts, color=self.color)


    @property # getter
    def size(self):
        '''Return the size of the box'''
        return [self.width, self.height]

    @size.setter
    def size(self, coors):
        '''Set size with list[X,Y] of dimensions'''
        self.width = coors[0]
        self.height = coors[1]


# -------------------------------------------


# --- COMPOSITE CLASSES

class JDraw_Text_Box:
    def __init__(self, x=0, y=0, box_color=(0,0,0,.5), padding=8, 
                string="default", size=12, text_color=(1, 1, 1, 1)):
        
        self.padding = padding
        
        self.text = JDraw_Text(x=x + padding, y=y + padding, string=string, size=size)
        
        text_dims = self.text.size
        box_width = text_dims[0] + padding * 2
        box_height = text_dims[1] + padding * 2

        self.box = JDraw_Rect(x=x, y=y, width=box_width, height=box_height)


    def draw(self):
        self.box.draw()
        self.text.draw()


    @property # getter
    def coor(self):
        '''Bottom Left screen coordinates of text'''
        return self.box.coor

    @coor.setter
    def coor(self, coors):
        '''Set coors with list[X,Y] of coordinates'''
        self.box.coor = coors
        coors = [x+self.padding for x in coors]
        self.text.coor = coors



class JDraw_Text_Box_Multi:
    def __init__(self, x=0, y=0, box_color=(0,0,0,.5), padding=8, 
                strings=["default", "text"], size=12, text_color=(1, 1, 1, 1)):
        
        self.padding = padding
        self.interpadding = 5
        
        self.texts = []
        offsetY = padding

        for index, string in enumerate(strings):

            text = JDraw_Text(x=x + padding, y=y, string=string, size=size)
            sizeY = text.size[1]
            offsetY += sizeY
            
            text.coorY -= offsetY + self.interpadding*index
            self.texts.append(text)

        box_width = 0
        for text in self.texts:
            text_dims = text.size
            sizeX = text_dims[0]

            # find maximum width
            if sizeX > box_width:
                box_width = sizeX

        # add padding
        box_width += padding * 2
        # get last text object, get its bottom left corner, that's the lowest point the box needs to be
        # subtract this from the Y origin of the box, add padding, all set
        box_height = (y - self.texts[len(strings)-1].coorY) + padding

        self.box = JDraw_Rect(x=x, y=y, width=box_width, height=-box_height)


    def draw(self):
        self.box.draw()
        for text in self.texts:
            text.draw()


    @property # getter
    def coor(self):
        '''Top Left screen coordinates of text'''
        return self.box.coor

    @coor.setter
    def coor(self, coors):
        '''Set coors with list[X,Y] of coordinates'''
        self.box.coor = coors
        coors = [x+self.padding for x in coors]
        self.text.coor = coors


# -------------------------------------------