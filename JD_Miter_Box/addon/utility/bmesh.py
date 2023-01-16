import bpy
import bmesh

def get_connected_verts(vert, exclude_selected = False):
    # taken from https://blenderartists.org/t/how-to-get-vertex-position-and-connected-vertices/1185279
    # get its connected vertices (filter out the other selected)
    connected_verts=[]
    for l in vert.link_edges:
        other_vert = l.other_vert(vert)
        if exclude_selected:
            if not other_vert.select:
                connected_verts.append(other_vert)
        else:
            connected_verts.append(other_vert)

    return connected_verts

def get_connected_faces_of_vert(vert, exclude_selected = False):

    connected_faces = []

    for l in vert.link_edges:
        for f in l.link_faces:
            if exclude_selected:
                if not f.select:
                    connected_faces.append(f)
            else:
                connected_faces.append(f)

    return connected_faces