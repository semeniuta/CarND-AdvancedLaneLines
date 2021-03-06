import cv2
import numpy as np

import lanelines
import straightlanespipeline as slp
from compgraph import CompGraphRunner


def define_flat_plane_on_road(images, x_offset=0):
    '''
    Apply straightlanespipeline to images of a straight road
    and return the averaged 4 points defining the region of
    the rectangular plane on the flat road surface.

    x_offset -- number of pixels by which the region is extended sideways

    Returns a (4 x 2) matrix with each point as a row:
    [top left    ]
    [top right   ]
    [bottom right]
    [bottom left ]

    '''

    runner = CompGraphRunner(
        slp.computational_graph,
        frozen_tokens=slp.parameters
    )

    left_lines = []
    right_lines = []
    for im in images:
        runner.run(image=im)
        left = lanelines.move_line(runner['avg_line_left'], -x_offset)
        right = lanelines.move_line(runner['avg_line_right'], x_offset)

        left_lines.append(left)
        right_lines.append(right)

    avg_left = np.array(left_lines).mean(axis=0)
    avg_right = np.array(right_lines).mean(axis=0)

    res = np.array([
        avg_left[:2],
        avg_right[:2],
        avg_right[2:],
        avg_left[2:],
    ], dtype=np.float32)

    return res


def prepare_perspective_transforms(straight_images, canvas_sz, offset_x, offset_y):
    '''
    Compute perspective transformation matrices mapping from the original image
    to the corresponding bird's-eye view of the road (and vice-versa).

    straight_images -- images of a straight road
    canvas_sz -- size (cols, rows) of the resulting warped image
    offset_x, offset_y -- offsets in pixels from the edges of the warped image
    '''

    warp_src = define_flat_plane_on_road(
        straight_images,
        x_offset=0
    )

    warp_dst = lanelines.get_rectangle_corners_in_image(canvas_sz, offset_x, offset_y)

    M = cv2.getPerspectiveTransform(warp_src, warp_dst)
    Minv = cv2.getPerspectiveTransform(warp_dst, warp_src)

    return M, Minv


def prepare_perspective_transforms_custom(canvas_sz=(500, 1500)):
    '''
    Custom perspective transformation function
    '''

    OFFSET_X = 100
    OFFSET_Y = 0

    cm = np.load('serialize/camera_matrix.npy')
    dc = np.load('serialize/dist_coefs.npy')

    straight_images_files = ('test_images/straight_lines1.jpg', 'test_images/straight_lines2.jpg')
    straight_images = [lanelines.open_image(f) for f in straight_images_files]
    straight_images_undist = [cv2.undistort(im, cm, dc) for im in straight_images]

    warp_src = define_flat_plane_on_road(straight_images_undist, x_offset=0)
    warp_src[1, 0] += 8 # <- a hack
    warp_dst = lanelines.get_rectangle_corners_in_image(canvas_sz, offset_x=OFFSET_X, offset_y=OFFSET_Y)

    M = cv2.getPerspectiveTransform(warp_src, warp_dst)
    Minv = cv2.getPerspectiveTransform(warp_dst, warp_src)

    return M, Minv
