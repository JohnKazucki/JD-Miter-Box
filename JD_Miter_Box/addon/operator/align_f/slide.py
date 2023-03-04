import bpy

from ...utility.bmesh import get_connected_faces_of_vert, get_connected_verts



def get_slide_directions(verts, normal, align_dir=None):


    slide_directions = {}

    for vert in verts:

        # get the connected vertices that are not part of the selection
        connected_verts = get_connected_verts(vert, exclude_selected=True)
        connected_faces = get_connected_faces_of_vert(vert, exclude_selected=True)

        # means we have adjacent faces to build a slide direction from
        if connected_faces:
            face_N = connected_faces[0].normal
            face_tan = face_N.cross(normal)
            face_bitan = face_tan.cross(face_N)

            dir_ideal = face_bitan
            dir = dir_ideal
        # geo has no unselected slide edges or faces, so must be an internal part of the selection
        else:
            dir_ideal = normal
            # dir = dir_ideal
            dir = normal
            if align_dir:
                dir = align_dir

        
        # means there are slide edges we can use
        if connected_verts:

            # find the edge to slide on that is most in line with the ideal direction
            max_dot = 0
            for vert_end in connected_verts:
                dir_option = vert_end.co - vert.co
                dir_option = dir_option.normalized()

                dir_dot = abs(dir_option.dot(dir_ideal))
                if dir_dot > max_dot:
                    max_dot = dir_dot
                    dir = dir_option

        # append the slide direction to dirs list
        slide_directions[vert.index] = dir

    # return list
    return slide_directions