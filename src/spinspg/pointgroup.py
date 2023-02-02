"""Spin point group."""
from __future__ import annotations

from collections import deque

import numpy as np
from spglib import get_pointgroup
from spgrep.pointgroup import pg_dataset
from spgrep.utils import ndarray2d_to_integer_tuple

from spinspg.utils import NDArrayInt

# Representatives for a geometric crystal class. The first descriptions are chosen for "-42m", "32", "3m", "-3m" and "-6m2".
# Choose unique axis c for "mm2".
POINT_GROUP_REPRESENTATIVES = {
    # Triclinic
    "1": 0,
    "-1": 0,
    # Monoclinic
    "2": 1,  # unique axis-b
    "m": 1,  # unique axis-b
    "2/m": 0,
    # Orthorhombic
    "222": 0,
    "mm2": 2,  # unique axis-c
    "mmm": 0,
    # Tetragonal
    "4": 0,
    "-4": -0,
    "4/m": 0,
    "422": 0,
    "4mm": 0,
    "-42m": 0,  # -42m
    "4/mmm": 0,
    # Hexagonal
    "3": 0,
    "-3": 0,
    "32": 0,  # 312
    "3m": 0,  # 3m1
    "-3m": 0,  # -31m
    "6": 0,
    "-6": 0,
    "6/m": 0,
    "622": 0,
    "6mm": 0,
    "-6m2": 0,  # -6m2
    "6/mmm": 0,
    # Cubic
    "23": 0,
    "m-3": 0,
    "432": 0,
    "-43m": 0,
    "m-3m": 0,
}

# See Table 2.1.3.1 of ITA (2016) for symmetry directions for each crystal family.
# The first entry in equivalent symmetry directions are chosen as possible.
# Exception for tertiary axes of "432", "-43m", and "m-3m"
POINT_GROUP_GENERATORS = {
    # Triclinic
    "1": [0],  # 1
    "-1": [1],  # -1
    # Monoclinic (unique axis b): [010] [010]
    "2": [1],  # 2
    "m": [1],  # m
    "2/m": [1, 3],  # 2, m
    # Orthorhombic: [100] [010] [001]
    "222": [3, 2, 1],  # 2_100, 2_010, 2_001
    "mm2": [3, 2, 1],  # m_100, m_010, 2_001
    "mmm": [7, 6, 5],  # m_100, m_010, m_001
    # Tetragonal: [001] [100]/[010] [1-10]/[110]
    "4": [2],  # 4^+
    "-4": [2],  # -4^+
    "4/m": [2, 5],  # 4^+, m
    "422": [2, 5, 7],  # 4^+, 2_100, 2_1-10
    "4mm": [2, 5, 7],  # 4^+, m_100, m_1-10
    "-42m": [2, 5, 7],  # -4^+, 2_100, m_1-10
    "4/mmm": [2, 9, 13, 15],  # 4^+, m_001, m_100, m_1-10
    # Hexagonal: [001] [100]/[010]/[-1-10] [1-10]/[120]/[-2-10]
    "3": [1],  # 3^+
    "-3": [4],  # -3^+
    "32": [1, 3],  # 3^+, *, 2_1-10
    "3m": [1, 4],  # 3^+, m_100, *
    "-3m": [7, 9],  # -3^+, *, m_1-10
    "6": [5],  # 6^+
    "-6": [5],  # -6^+
    "6/m": [5, 9],  # 6^+, m
    "622": [5, 7, 9],  # 6^+, 2_100, 2_1-10
    "6mm": [5, 7, 9],  # 6^+, m_100, m_1-10
    "-6m2": [5, 7, 9],  # -6^+, m_100, 2_1-10
    "6/mmm": [5, 15, 19, 21],  # 6^+, m_001, m_100, m_1-10
    # Cubic: [100]/[010]/[010] [111]/[1-1-1]/[-11-1]/[-1-11] [1-10]/[110]/[01-1]/[011]/[-101]/[101]
    "23": [3, 4],  # 2_100, 3^+_111
    "m-3": [15, 16],  # m_100, -3^+_111
    "432": [19, 4, 18],  # 4^+_100, 3^+_111, 2_01-1
    "-43m": [17, 4, 16],  # -4^+_100, 3^+_111, m_01-1
    "m-3m": [27, 28, 42],  # m_100, -3^+_111, m_01-1
}

# R -> r -> B -> spin point group types
# Litvin (1977) used Cartesian coordinates for spin rotations while our tabulation uses crystallographic axes.
# - Litvin (1977) seems to use "-4m2" as a representative of "-42m"
SPIN_POINT_GROUP_TYPES = {
    "1": {
        "1": {
            "1": [
                (1, [0]),
            ],
        },
    },
    "-1": {
        "-1": {
            "1": [
                (2, [0]),
            ],
        },
        "1": {
            "2": [
                (3, [1]),
            ],
            "m": [
                (4, [1]),
            ],
            "-1": [
                (5, [1]),
            ],
        },
    },
    "2": {
        "2": {
            "1": [
                (6, [0]),
            ]
        },
        "1": {
            "2": [
                (7, [1]),
            ],
            "m": [
                (8, [1]),
            ],
            "-1": [
                (9, [1]),
            ],
        },
    },
    "m": {
        "m": {
            "1": [
                (10, [0]),
            ],
        },
        "1": {
            "2": [
                (11, [1]),
            ],
            "m": [
                (12, [1]),
            ],
            "-1": [
                (13, [1]),
            ],
        },
    },
    "2/m": {
        "2/m": {
            "1": [
                (14, [0, 0]),
            ],
        },
        "2": {
            "2": [
                (15, [0, 1]),
            ],
            "m": [
                (16, [0, 1]),
            ],
            "-1": [
                (17, [0, 1]),
            ],
        },
        "m": {
            "2": [
                (18, [1, 0]),
            ],
            "m": [
                (19, [1, 0]),
            ],
            "-1": [
                (20, [1, 0]),
            ],
        },
        "-1": {
            "2": [
                (21, [1, 1]),
            ],
            "m": [
                (22, [1, 1]),
            ],
            "-1": [
                (23, [1, 1]),
            ],
        },
        "1": {
            "222": [
                (24, [3, 2]),  # Changed(24): 2_100, 2_010
            ],
            "mm2": [
                (25, [1, 3]),
                (26, [3, 2]),
                (27, [3, 1]),
            ],
            "2/m": [
                (28, [1, 3]),
                (29, [1, 2]),
                (30, [2, 3]),
                (31, [2, 1]),
                (32, [3, 2]),
                (33, [3, 1]),
            ],
        },
    },
    "mm2": {
        "mm2": {
            "1": [(34, [0, 0, 0])],
        },
        "2": {
            "2": [(35, [1, 1, 0])],
            "m": [(36, [1, 1, 0])],
            "-1": [(37, [1, 1, 0])],
        },
        "m": {
            "2": [(38, [0, 1, 1])],
            "m": [(39, [0, 1, 1])],
            "-1": [(40, [0, 1, 1])],
        },
        "1": {
            "222": [(41, [3, 2, 1])],  # Changed(41): 2_100, 2_010, 2_001
            "mm2": [
                (42, [3, 2, 1]),
                (43, [3, 1, 2]),
            ],
            "2/m": [
                (44, [3, 2, 1]),
                (45, [3, 1, 2]),
                (46, [2, 1, 3]),
            ],
        },
    },
    "222": {
        "222": {
            "1": [(47, [0, 0, 0])],
        },
        "2": {
            "2": [(48, [0, 1, 1])],
            "m": [(49, [0, 1, 1])],
            "-1": [(50, [0, 1, 1])],
        },
        "1": {
            "222": [
                (51, [3, 2, 1]),  # Changed(51): 2_100, 2_010, 2_001
            ],
            "mm2": [(52, [3, 2, 1])],
            "2/m": [(53, [1, 2, 3])],
        },
    },
    "mmm": {
        "mmm": {
            "1": [(54, [0, 0, 0])],
        },
        "2/m": {
            "2": [(55, [0, 1, 1])],
            "m": [(56, [0, 1, 1])],
            "-1": [(57, [0, 1, 1])],
        },
        "mm2": {
            "2": [(58, [0, 0, 1])],
            "m": [(59, [0, 0, 1])],
            "-1": [(60, [0, 0, 1])],
        },
        "222": {
            "2": [(61, [1, 1, 1])],
            "m": [(62, [1, 1, 1])],
            "-1": [(63, [1, 1, 1])],
        },
        "2": {
            "222": [(64, [1, 1, 3])],
            "mm2": [
                (65, [3, 3, 2]),  # Changed(65): m_100, m_100, m_010
                (66, [3, 3, 1]),  # Changed(66): m_100, m_100, 2
                (67, [1, 1, 3]),  # Changed(67): 2, 2, m_100
            ],
            "2/m": [
                (68, [3, 3, 2]),
                (69, [3, 3, 1]),
                (70, [1, 1, 2]),
                (71, [1, 1, 3]),
                (72, [2, 2, 1]),
                (73, [2, 2, 3]),
            ],
        },
        "m": {
            "222": [
                (74, [3, 2, 0]),
            ],
            "mm2": [
                (75, [3, 2, 0]),
                (76, [2, 1, 0]),
            ],
            "2/m": [
                (77, [3, 2, 0]),
                (78, [3, 1, 0]),
                (79, [2, 1, 0]),
            ],
        },
        "-1": {
            "222": [(80, [3, 2, 1])],
            "mm2": [(81, [3, 2, 1])],
            "2/m": [(82, [1, 2, 3])],
        },
        "1": {
            "mmm": [
                (83, [7, 6, 5]),
                (84, [7, 2, 1]),
                (85, [5, 3, 1]),
                (86, [1, 7, 5]),
                (87, [1, 4, 7]),
                (88, [1, 4, 3]),
                (89, [4, 5, 7]),
            ],
        },
    },
    "4": {
        "4": {
            "1": [(90, [0])],
        },
        "2": {
            "2": [(91, [1])],
            "m": [(92, [1])],
            "-1": [(93, [1])],
        },
        "1": {
            "4": [(94, [2])],
            "-4": [(95, [2])],
        },
    },
    "-4": {
        "-4": {
            "1": [(96, [0])],
        },
        "2": {
            "2": [(97, [1])],
            "m": [(98, [1])],
            "-1": [(99, [1])],
        },
        "1": {
            "4": [(100, [2])],
            "-4": [(101, [2])],
        },
    },
    "4/m": {
        "4/m": {
            "1": [
                (102, [0, 0]),
            ],
        },
        "2/m": {
            "2": [
                (103, [1, 0]),
            ],
            "m": [
                (104, [1, 0]),
            ],
            "-1": [
                (105, [1, 0]),
            ],
        },
        "-4": {
            "2": [(106, [1, 1])],
            "m": [(107, [1, 1])],
            "-1": [(108, [1, 1])],
        },
        "4": {
            "2": [(109, [0, 1])],
            "m": [(110, [0, 1])],
            "-1": [(111, [0, 1])],
        },
        "-1": {
            "4": [(112, [2, 1])],
            "-4": [(113, [2, 1])],
        },
        "m": {
            "4": [(114, [2, 0])],
            "-4": [(115, [2, 0])],
        },
        "2": {
            "222": [(116, [1, 3])],
            "mm2": [
                (117, [1, 3]),
                (118, [3, 1]),
                (119, [3, 2]),
            ],
            "2/m": [
                (120, [1, 2]),
                (121, [1, 3]),
                (122, [2, 1]),
                (123, [2, 3]),
                (124, [3, 1]),
                (125, [3, 2]),
            ],
        },
        "1": {
            "4/m": [
                (126, [2, 5]),
                (127, [2, 4]),
                (128, [6, 5]),
                (129, [6, 4]),
            ],
        },
    },
    "422": {
        "422": {
            "1": [
                (130, [0, 0, 0]),
            ],
        },
        "4": {
            "2": [
                (131, [0, 1, 1]),
            ],
            "m": [
                (132, [0, 1, 1]),
            ],
            "-1": [
                (133, [0, 1, 1]),
            ],
        },
        "222": {
            "2": [
                (134, [1, 0, 1]),
            ],
            "m": [
                (135, [1, 0, 1]),
            ],
            "-1": [
                (136, [1, 0, 1]),
            ],
        },
        "2": {
            "222": [
                (137, [3, 2, 1]),
            ],
            "mm2": [
                (138, [1, 3, 2]),
                (139, [3, 1, 2]),
            ],
            "2/m": [
                (140, [1, 2, 3]),
                (141, [2, 1, 3]),
                (142, [3, 2, 1]),
            ],
        },
        "1": {
            "422": [
                (143, [2, 5, 7]),
            ],
            "4mm": [
                (144, [2, 5, 7]),
            ],
            "-42m": [
                (145, [2, 5, 7]),
            ],
        },
    },
    "4mm": {
        "4mm": {
            "1": [(146, [0, 0, 0])],
        },
        "4": {
            "2": [(147, [0, 1, 1])],
            "m": [(148, [0, 1, 1])],
            "-1": [(149, [0, 1, 1])],
        },
        "mm2": {
            "2": [(150, [1, 0, 1])],
            "m": [(151, [1, 0, 1])],
            "-1": [(152, [1, 0, 1])],
        },
        "2": {
            "222": [(153, [3, 2, 1])],
            "mm2": [
                (154, [1, 3, 2]),
                (155, [3, 1, 2]),
            ],
            "2/m": [
                (156, [1, 2, 3]),
                (157, [2, 1, 3]),
                (158, [3, 1, 2]),
            ],
        },
        "1": {
            "422": [(159, [2, 5, 7])],
            "4mm": [(160, [2, 5, 7])],
            "-42m": [(161, [2, 7, 4])],  # Changed(161): -4, m_1-10, 2_010
        },
    },
    "-42m": {
        "-42m": {
            "1": [(162, [0, 0, 0])],
        },
        "-4": {
            "2": [(163, [0, 1, 1])],
            "m": [(164, [0, 1, 1])],
            "-1": [(165, [0, 1, 1])],
        },
        "mm2": {
            "2": [(166, [1, 1, 0])],
            "m": [(167, [1, 1, 0])],
            "-1": [(168, [1, 1, 0])],
        },
        "222": {
            "2": [(169, [1, 0, 1])],
            "m": [(170, [1, 0, 1])],
            "-1": [(171, [1, 0, 1])],
        },
        "2": {
            "222": [(172, [3, 2, 1])],
            "mm2": [
                (173, [1, 3, 2]),
                (174, [3, 1, 2]),
                (175, [3, 2, 1]),
            ],
            "2/m": [
                (176, [1, 2, 3]),
                (177, [1, 3, 2]),
                (178, [2, 1, 3]),
                (179, [2, 3, 1]),
                (180, [3, 1, 2]),
                (181, [3, 2, 1]),
            ],
        },
        "1": {
            "422": [
                (182, [2, 5, 7]),
            ],
            "4mm": [
                (183, [2, 5, 7]),
            ],
            "-42m": [
                (184, [2, 5, 7]),
                (185, [2, 7, 4]),  # Changed(185): -4, m_1-10, 2_010
            ],
        },
    },
    "4/mmm": {
        "4/mmm": {
            "1": [(186, [0, 0, 0, 0])],
        },
        "-42m": {
            "2": [(187, [1, 1, 1, 0])],
            "m": [(188, [1, 1, 1, 0])],
            "-1": [(189, [1, 1, 1, 0])],
        },
        "4mm": {
            "2": [(190, [0, 1, 0, 0])],
            "m": [(191, [0, 1, 0, 0])],
            "-1": [(192, [0, 1, 0, 0])],
        },
        "mmm": {
            "2": [
                (193, [1, 0, 0, 1]),
            ],
            "m": [
                (194, [1, 0, 0, 1]),
            ],
            "-1": [(195, [1, 0, 0, 1])],
        },
        "4/m": {
            "2": [(196, [0, 0, 1, 1])],
            "m": [(197, [0, 0, 1, 1])],
            "-1": [(198, [0, 0, 1, 1])],
        },
        "422": {
            "2": [(199, [0, 1, 1, 1])],
            "m": [(200, [0, 1, 1, 1])],
            "-1": [(201, [0, 1, 1, 1])],
        },
        "-4": {
            "222": [(202, [1, 1, 3, 2])],
            "mm2": [(203, [1, 1, 3, 2]), (204, [3, 3, 1, 2])],
            "2/m": [
                (205, [1, 1, 2, 3]),
                (206, [2, 2, 1, 3]),
                (207, [3, 3, 1, 2]),
            ],
        },
        "4": {
            "222": [(208, [0, 3, 2, 2])],
            "mm2": [
                (209, [0, 1, 3, 3]),
                (210, [0, 3, 1, 1]),
                (211, [0, 3, 2, 2]),
            ],
            "2/m": [
                (212, [0, 1, 2, 2]),
                (213, [0, 1, 3, 3]),
                (214, [0, 2, 1, 1]),
                (215, [0, 2, 3, 3]),
                (216, [0, 3, 1, 1]),
                (217, [0, 3, 2, 2]),
            ],
        },
        "2/m": {
            "222": [(218, [1, 0, 3, 2])],
            "mm2": [
                (219, [1, 0, 3, 2]),
                (220, [3, 0, 1, 2]),
            ],
            "2/m": [
                (221, [1, 0, 2, 3]),
                (222, [2, 0, 1, 3]),
                (223, [3, 0, 1, 2]),
            ],
        },
        "mm2": {
            "222": [(224, [1, 3, 0, 1])],
            "mm2": [
                (225, [1, 3, 0, 1]),
                (226, [3, 1, 0, 3]),
                (227, [3, 2, 0, 3]),
            ],
            "2/m": [
                (228, [1, 2, 0, 1]),
                (229, [1, 3, 0, 1]),
                (230, [2, 1, 0, 2]),
                (231, [2, 3, 0, 2]),
                (232, [3, 1, 0, 3]),
                (233, [3, 2, 0, 3]),
            ],
        },
        "222": {
            "222": [
                (234, [1, 3, 3, 2]),
            ],
            "mm2": [
                (235, [1, 3, 3, 2]),
                (236, [3, 1, 1, 2]),
                (237, [3, 2, 2, 1]),
            ],
            "2/m": [
                (238, [1, 2, 2, 3]),
                (239, [1, 3, 3, 2]),
                (240, [2, 1, 1, 3]),
                (241, [2, 3, 3, 1]),
                (242, [3, 1, 1, 2]),
                (243, [3, 2, 2, 1]),
            ],
        },
        "m": {
            "422": [(244, [2, 0, 5, 7])],
            "4mm": [(245, [2, 0, 5, 7])],
            "-42m": [(246, [2, 0, 5, 7])],
        },
        "-1": {
            "422": [(247, [2, 1, 5, 7])],
            "4mm": [(248, [2, 1, 5, 7])],
            "-42m": [(249, [2, 1, 7, 4])],  # Changed(249): -4, 2_001, m_1-10, 2_010
        },
        "2": {
            "mmm": [
                (250, [5, 3, 7, 2]),
                (251, [5, 7, 3, 6]),
                (252, [1, 7, 3, 2]),
                (253, [5, 1, 3, 6]),
                (254, [1, 5, 3, 2]),
                (255, [1, 5, 7, 6]),
                (256, [5, 3, 1, 4]),
                (257, [5, 7, 4, 1]),
                (258, [5, 4, 7, 2]),
                (259, [1, 3, 7, 6]),
                (260, [1, 3, 4, 5]),
                (261, [1, 4, 7, 6]),
                (262, [1, 7, 4, 5]),
                (263, [1, 4, 3, 2]),
                (264, [4, 3, 1, 5]),
                (265, [4, 7, 5, 1]),
            ],
        },
        "1": {
            "4/mmm": [
                (266, [2, 9, 13, 15]),
                (267, [2, 8, 13, 15]),
                (268, [2, 9, 5, 7]),
                (269, [2, 8, 5, 7]),
                (270, [10, 9, 13, 7]),
                (271, [10, 8, 13, 7]),
            ],
        },
    },
    "3": {
        "3": {
            "1": [(272, [0])],
        },
        "1": {
            "3": [(273, [1])],
        },
    },
    "-3": {
        "-3": {
            "1": [(274, [0])],
        },
        "3": {
            "2": [(275, [1])],
            "m": [(276, [1])],
            "-1": [(277, [1])],
        },
        "-1": {
            "3": [(278, [1])],
        },
        "1": {
            "6": [(279, [5])],
            "-3": [(280, [4])],
            "-6": [(281, [5])],
        },
    },
    "32": {
        "32": {
            "1": [(282, [0, 0])],
        },
        "3": {
            "2": [(283, [0, 1])],
            "m": [(284, [0, 1])],
            "-1": [(285, [0, 1])],
        },
        "1": {
            "32": [(286, [1, 4])],
            "3m": [(287, [1, 4])],
        },
    },
    "3m": {
        "3m": {
            "1": [(288, [0, 0])],
        },
        "3": {
            "2": [(289, [0, 1])],
            "m": [(290, [0, 1])],
            "-1": [(291, [0, 1])],
        },
        "1": {
            "32": [(292, [1, 4])],
            "3m": [(293, [1, 4])],
        },
    },
    "-3m": {
        "-3m": {
            "1": [(294, [0, 0])],
        },
        "-3": {
            "2": [(295, [0, 1])],
            "m": [(296, [0, 1])],
            "-1": [(297, [0, 1])],
        },
        "3m": {
            "2": [(298, [1, 0])],
            "m": [(299, [1, 0])],
            "-1": [(300, [1, 0])],
        },
        "32": {
            "2": [(301, [1, 1])],
            "m": [(302, [1, 1])],
            "-1": [(303, [1, 1])],
        },
        "3": {
            "222": [(304, [3, 1])],
            "mm2": [
                (305, [1, 3]),
                (306, [3, 2]),
                (307, [3, 1]),
            ],
            "2/m": [
                (308, [1, 3]),
                (309, [1, 2]),
                (310, [2, 3]),
                (311, [2, 1]),
                (312, [3, 2]),
                (313, [3, 1]),
            ],
        },
        "-1": {
            "32": [(314, [1, 4])],
            "3m": [(315, [1, 4])],
        },
        "1": {
            "622": [(316, [5, 7])],
            "-3m": [
                (317, [7, 11]),
                (318, [7, 3]),
            ],
            "6mm": [(319, [5, 7])],
            "-6m2": [
                (320, [5, 7]),
                (321, [5, 9]),  # Changed(321): -6, 2_1-10
            ],
        },
    },
    "-6": {
        "-6": {
            "1": [(322, [0])],
        },
        "3": {
            "2": [(323, [1])],
            "m": [(324, [1])],
            "-1": [(325, [1])],
        },
        "m": {
            "3": [(326, [1])],
        },
        "1": {
            "6": [(327, [5])],
            "-3": [(328, [4])],
            "-6": [(329, [5])],
        },
    },
    "6": {
        "6": {
            "1": [(330, [0])],
        },
        "3": {
            "2": [(331, [1])],
            "m": [(332, [1])],
            "-1": [(333, [1])],
        },
        "2": {
            "3": [(334, [1])],
        },
        "1": {
            "6": [(335, [5])],
            "-3": [(336, [4])],
            "-6": [(337, [5])],
        },
    },
    "622": {
        "622": {
            "1": [(338, [0, 0, 0])],
        },
        "6": {
            "2": [(339, [0, 1, 1])],
            "m": [(340, [0, 1, 1])],
            "-1": [(341, [0, 1, 1])],
        },
        "32": {
            "2": [(342, [1, 0, 1])],
            "m": [(343, [1, 0, 1])],
            "-1": [(344, [1, 0, 1])],
        },
        "3": {
            "222": [(345, [3, 2, 1])],
            "mm2": [
                (346, [1, 3, 2]),
                (347, [3, 1, 2]),
            ],
            "2/m": [
                (348, [1, 2, 3]),
                (349, [2, 1, 3]),
                (350, [3, 1, 2]),
            ],
        },
        "2": {
            "32": [(351, [1, 3, 4])],  # Changed(351): 3, 2_1-10, 2_120
            "3m": [(352, [1, 4, 5])],  # Changed(352): 3, m_100, m_010
        },
        "1": {
            "622": [(353, [5, 7, 9])],  # Changed(353): 6, 2_100, 2_1-10
            "-3m": [(354, [7, 3, 10])],  # Changed(354): 3, 2_1-10, m_120
            "6mm": [(355, [5, 7, 9])],  # Changed(355): 3, m_100, m_1-10
            "-6m2": [(356, [5, 6, 11])],
        },
    },
    "6/m": {
        "6/m": {
            "1": [(357, [0, 0])],
        },
        "-3": {
            "2": [(358, [1, 1])],
            "m": [(359, [1, 1])],
            "-1": [(360, [1, 1])],
        },
        "-6": {
            "2": [(361, [1, 0])],
            "m": [(362, [1, 0])],
            "-1": [(363, [1, 0])],
        },
        "6": {
            "2": [(364, [0, 1])],
            "m": [(365, [0, 1])],
            "-1": [(366, [0, 1])],
        },
        "2/m": {
            "3": [(367, [1, 0])],
        },
        "3": {
            "222": [(368, [1, 3])],
            "mm2": [
                (369, [1, 3]),
                (370, [3, 1]),
                (371, [3, 2]),
            ],
            "2/m": [
                (372, [1, 2]),
                (373, [1, 3]),
                (374, [2, 1]),
                (375, [2, 3]),
                (376, [3, 1]),
                (377, [3, 2]),
            ],
        },
        "2": {
            "6": [(378, [1, 3])],
            "-3": [(379, [1, 3])],
            "-6": [(380, [1, 3])],
        },
        "m": {
            "6": [(381, [5, 0])],
            "-3": [(382, [4, 0])],
            "-6": [(383, [5, 0])],
        },
        "-1": {
            "6": [(384, [5, 3])],
            "-3": [(385, [4, 3])],
            "-6": [(386, [5, 3])],
        },
        "1": {
            "6/m": [
                (387, [5, 9]),
                (388, [5, 6]),
                (389, [7, 9]),
                (390, [7, 3]),
                (391, [11, 6]),
                (392, [11, 3]),
            ],
        },
    },
    "6mm": {
        "6mm": {"1": [(393, [0, 0, 0])]},
        "6": {
            "2": [(394, [0, 1, 1])],
            "m": [(395, [0, 1, 1])],
            "-1": [(396, [0, 1, 1])],
        },
        "3m": {
            "2": [(397, [1, 0, 1])],
            "m": [(398, [1, 0, 1])],
            "-1": [(399, [1, 0, 1])],
        },
        "3": {
            "222": [(400, [3, 2, 1])],
            "mm2": [
                (401, [1, 3, 2]),
                (402, [3, 1, 2]),
            ],
            "2/m": [
                (403, [1, 2, 3]),
                (404, [2, 1, 3]),
                (405, [3, 1, 2]),
            ],
        },
        "2": {
            "32": [(406, [1, 3, 4])],  # Changed(406): 3, 2_1-10, 2_120
            "3m": [(407, [1, 4, 5])],  # Changed(407): 3, m_100, m_010
        },
        "1": {
            "622": [(408, [5, 7, 9])],  # Changed(408): 6, 2_100, 2_1-10
            "-3m": [(409, [7, 3, 10])],  # Changed(409): -3, 2_1-10, m_010
            "6mm": [(410, [5, 7, 9])],  # Changed(410): 6, m_100, m_xy
            "-6m2": [(411, [5, 7, 9])],  # Changed(411): -6, m_100, 2_1-10
        },
    },
    "-6m2": {
        "-6m2": {
            "1": [(412, [0, 0, 0])],
        },
        "-6": {
            "2": [(413, [0, 1, 1])],
            "m": [(414, [0, 1, 1])],
            "-1": [(415, [0, 1, 1])],
        },
        "3m": {
            "2": [(416, [1, 0, 1])],
            "m": [(417, [1, 0, 1])],
            "-1": [(418, [1, 0, 1])],
        },
        "32": {
            "2": [(419, [1, 1, 0])],
            "m": [(420, [1, 1, 0])],
            "-1": [(421, [1, 1, 0])],
        },
        "3": {
            "222": [(422, [1, 3, 2])],
            "mm2": [
                (423, [1, 3, 2]),
                (424, [3, 2, 1]),
                (425, [3, 1, 2]),
            ],
            "2/m": [
                (426, [1, 3, 2]),
                (427, [1, 2, 3]),
                (428, [2, 3, 1]),
                (429, [2, 1, 3]),
                (430, [3, 2, 1]),
                (431, [3, 1, 2]),
            ],
        },
        "m": {
            "32": [
                (432, [1, 3, 4]),  # Changed(432): 3, 2_1-10, 2_120
            ],
            "3m": [(433, [1, 4, 5])],  # Changed(433): 3, m_100, m_010
        },
        "1": {
            "622": [(434, [5, 7, 9])],  # Changed(434): 6, 2_100, 2_1-10
            "-3m": [
                (435, [7, 9, 4]),  # Changed(435): -3, m_1-10, 2_120
                (436, [7, 3, 10]),  # Changed(436): -3, 2_1-10, m_120
            ],
            "6mm": [(437, [5, 7, 9])],  # Changed(437): 6, m_100, m_1-10
            "-6m2": [
                (438, [5, 7, 9]),  # Changed(438): -6, m_100, 2_1-10
                (439, [5, 9, 8]),  # Changed(439): -6, 2_1-10, m_010
            ],
        },
    },
    "6/mmm": {
        "6/mmm": {
            "1": [(440, [0, 0, 0, 0])],
        },
        "-3m": {
            "2": [(441, [1, 1, 0, 1])],
            "m": [(442, [1, 1, 0, 1])],
            "-1": [(443, [1, 1, 0, 1])],
        },
        "-6m2": {
            "2": [(444, [1, 0, 1, 0])],
            "m": [(445, [1, 0, 1, 0])],
            "-1": [(446, [1, 0, 1, 0])],
        },
        "6/m": {
            "2": [(447, [0, 0, 1, 1])],
            "m": [(448, [0, 0, 1, 1])],
            "-1": [(449, [0, 0, 1, 1])],
        },
        "6mm": {
            "2": [(450, [0, 1, 0, 0])],
            "m": [(451, [0, 1, 0, 0])],
            "-1": [(452, [0, 1, 0, 0])],
        },
        "622": {
            "2": [(453, [0, 1, 1, 1])],
            "m": [(454, [0, 1, 1, 1])],
            "-1": [(455, [0, 1, 1, 1])],
        },
        "-3": {
            "222": [(456, [1, 1, 3, 2])],
            "mm2": [(457, [1, 1, 3, 2]), (458, [3, 3, 1, 2])],
            "2/m": [
                (459, [1, 1, 2, 3]),
                (460, [2, 2, 1, 3]),
                (461, [3, 3, 1, 2]),
            ],
        },
        "-6": {
            "222": [(462, [1, 0, 3, 2])],
            "mm2": [(463, [1, 0, 3, 2]), (464, [3, 0, 1, 2])],
            "2/m": [
                (465, [1, 0, 2, 3]),
                (466, [2, 0, 1, 3]),
                (467, [3, 0, 1, 2]),
            ],
        },
        "6": {
            "222": [(468, [0, 1, 3, 3])],
            "mm2": [
                (469, [0, 1, 3, 3]),
                (470, [0, 3, 2, 2]),
                (471, [0, 3, 1, 1]),
            ],
            "2/m": [
                (472, [0, 1, 3, 3]),
                (473, [0, 1, 2, 2]),
                (474, [0, 2, 3, 3]),
                (475, [0, 2, 1, 1]),
                (476, [0, 3, 2, 2]),
                (477, [0, 3, 1, 1]),
            ],
        },
        "3m": {
            "222": [
                (478, [1, 3, 0, 1]),
            ],
            "mm2": [
                (479, [3, 2, 0, 3]),
                (480, [3, 1, 0, 3]),
                (481, [1, 3, 0, 1]),
            ],
            "2/m": [
                (482, [3, 2, 0, 3]),
                (483, [2, 3, 0, 2]),
                (484, [3, 1, 0, 3]),
                (485, [1, 3, 0, 1]),
                (486, [2, 1, 0, 2]),
                (487, [1, 2, 0, 1]),
            ],
        },
        "32": {
            "222": [(488, [1, 3, 2, 3])],
            "mm2": [
                (489, [3, 1, 2, 1]),  # Changed(489): m_100, 2, m_100, 2
                (490, [3, 2, 1, 2]),  # Changed(490): m_100, m_010, 2, m_010
                (491, [1, 3, 2, 3]),
            ],
            "2/m": [
                (492, [3, 1, 2, 1]),
                (493, [2, 1, 3, 1]),
                (494, [3, 2, 1, 2]),
                (495, [1, 2, 3, 2]),
                (496, [2, 3, 1, 3]),
                (497, [1, 3, 2, 3]),
            ],
        },
        "2/m": {
            "32": [(498, [1, 0, 3, 4])],  # Changed(498): 3, 1, 2_1-10, 2_120
            "3m": [(499, [1, 0, 4, 5])],  # Changed(499): 3, 1, m_100, m_010
        },
        "3": {
            "mmm": [
                (500, [5, 1, 7, 2]),
                (501, [1, 5, 7, 6]),
                (502, [1, 5, 3, 2]),
                (503, [5, 7, 3, 6]),
                (504, [5, 3, 2, 7]),  # Corrected?(504): m_001, 2_100, 2_010, m_100
                (505, [1, 3, 6, 7]),
                (506, [1, 7, 2, 3]),
                (507, [5, 3, 4, 1]),
                (508, [5, 7, 1, 4]),
                (509, [5, 4, 3, 6]),
                (510, [1, 7, 5, 4]),
                (511, [1, 3, 5, 4]),
                (512, [1, 4, 7, 6]),
                (513, [1, 4, 3, 2]),
                (514, [4, 7, 1, 5]),
                (515, [4, 3, 5, 1]),
            ],
        },
        "-1": {
            "622": [
                (516, [5, 3, 7, 9]),  # Changed(516): 6, 2_001, 2_100, 2_1-10
            ],
            "-3m": [(517, [7, 6, 3, 10])],  # Changed(517): -3, -1, 2_1-10, m_120
            "6mm": [
                (518, [5, 3, 7, 9]),
            ],
            "-6m2": [(519, [5, 3, 7, 9])],  # Changed(519): -6, m_001, m_100, 2_1-10
        },
        "m": {
            "622": [(520, [5, 0, 7, 9])],  # Changed(520): 6, 1, 2_100, 2_1-10
            "-3m": [(521, [7, 0, 9, 4])],  # Changed(521): -3, 1, m_1-10, 2_120
            "6mm": [(522, [5, 0, 7, 9])],  # Changed(522): 6, 1, m_100, m_1-10
            "-6m2": [(523, [5, 0, 9, 8])],  # Changed(523): -6, 1, 2_1-10, m_010
        },
        "2": {
            "622": [
                (524, [1, 3, 7, 8]),  # Changed(524): 3, 2_001, 2_100, 2_010
            ],
            "-3m": [
                (525, [1, 6, 9, 10]),  # Changed(525): 3, -1, m_1-10, m_120
                (526, [1, 6, 3, 4]),  # Changed(526): 3, -1, 2_1-10, 2_120
            ],
            "6mm": [(527, [1, 3, 7, 8])],  # Changed(527): 3, 2_001, m_100, m_010
            "-6m2": [
                (528, [1, 3, 7, 8]),  # Changed(528): 3, m_001, m_100, m_010
                (529, [1, 3, 9, 10]),  # Changed(529): 3, m_001, 2_1-10, 2_120
            ],
        },
        "1": {
            "6/mmm": [
                (530, [5, 12, 19, 21]),  # Changed(530): 6, -1, m_100, m_1-10
                (531, [5, 15, 19, 21]),  # Changed(531): 6, m_001, m_100, m_1-10
                (532, [5, 12, 7, 9]),  # Changed(532): 6, -1, 2_100, 2_1-10
                (533, [5, 15, 7, 9]),  # Changed(533): 6, m_001, 2_100, 2_1-10
                (534, [13, 15, 7, 20]),  # Changed(534): -3, m_001, 2_100, m_010
                (535, [13, 3, 19, 8]),  # Changed(535): -3, 2_001, m_100, 2_010
                (536, [17, 12, 7, 21]),  # Changed(536): -6, -1, 2_100, m_1-10
                (537, [17, 3, 19, 9]),  # Changed(537): -6, 2_001, m_100, 2_1-10
            ],
        },
    },
    "23": {
        "23": {
            "1": [(538, [0, 0])],
        },
        "222": {
            "3": [(539, [0, 1])],
        },
        "1": {
            "23": [(540, [1, 4])],
        },
    },
    "m-3": {
        "m-3": {
            "1": [(541, [0, 0])],
        },
        "23": {
            "2": [(542, [1, 1])],
            "m": [(543, [1, 1])],
            "-1": [(544, [1, 1])],
        },
        "mmm": {
            "3": [(545, [0, 1])],
        },
        "222": {
            "6": [(546, [3, 5])],
            "-3": [(547, [3, 4])],
            "-6": [(548, [3, 5])],
        },
        "-1": {
            "23": [(549, [1, 4])],
        },
        "1": {
            "m-3": [(550, [13, 16])],
        },
    },
    "-43m": {
        "-43m": {
            "1": [(551, [0, 0, 0])],
        },
        "23": {
            "2": [(552, [1, 0, 1])],
            "m": [(553, [1, 0, 1])],
            "-1": [(554, [1, 0, 1])],
        },
        "222": {
            "32": [(555, [4, 1, 4])],
            "3m": [(556, [4, 1, 4])],
        },
        "1": {
            "432": [(557, [15, 4, 13])],
            "-43m": [(558, [14, 4, 12])],
        },
    },
    "432": {
        "432": {
            "1": [(559, [0, 0, 0])],
        },
        "23": {
            "2": [(560, [1, 0, 1])],
            "m": [(561, [1, 0, 1])],
            "-1": [(562, [1, 0, 1])],
        },
        "222": {
            "32": [(563, [3, 1, 3])],
            "3m": [(564, [4, 1, 4])],
        },
        "1": {
            "432": [(565, [19, 4, 18])],  # Changed(565): 4_100, 3_111, 2_01-1
            "-43m": [(566, [14, 4, 12])],  # Changed(566): -4_001, 3_111, m_1-10
        },
    },
    "m-3m": {
        "m-3m": {
            "1": [(567, [0, 0, 0])],
        },
        "m-3": {
            "2": [(568, [0, 0, 1])],
            "m": [(569, [0, 0, 1])],
            "-1": [(570, [0, 0, 1])],
        },
        "-43m": {
            "2": [(571, [1, 1, 0])],
            "m": [(572, [1, 1, 0])],
            "-1": [(573, [1, 1, 0])],
        },
        "432": {
            "2": [(574, [1, 1, 1])],
            "m": [(575, [1, 1, 1])],
            "-1": [(576, [1, 1, 1])],
        },
        "23": {
            "222": [(577, [2, 2, 1])],
            "mm2": [
                (578, [3, 3, 2]),
                (579, [1, 1, 2]),
                (580, [2, 2, 1]),
            ],
            "2/m": [
                (581, [2, 2, 3]),
                (582, [3, 3, 2]),
                (583, [1, 1, 3]),
                (584, [3, 3, 1]),
                (585, [1, 1, 2]),
                (586, [2, 2, 1]),
            ],
        },
        "mmm": {
            "32": [(587, [0, 1, 4])],
            "3m": [(588, [0, 1, 4])],
        },
        "222": {
            "622": [
                (589, [3, 5, 7]),
            ],
            "-3m": [
                (590, [6, 7, 10]),
                (591, [6, 7, 4]),
            ],
            "6mm": [(592, [3, 5, 7])],
            "-6m2": [
                (593, [3, 5, 9]),  # Changed(593): m_001, -6, 2_1-10
                (594, [3, 5, 7]),
            ],
        },
        "-1": {
            "432": [
                (595, [3, 4, 18]),  # Changed(595): 2_100, 3_111, 2_01-1
            ],
            "-43m": [(596, [3, 4, 16])],  # Changed(596): 2_100, 3_111, m_01-1
        },
        "1": {
            "m-3m": [
                (597, [27, 28, 42]),  # Changed(597): m_100, -3_111, m_01-1
                (598, [27, 28, 18]),  # Changed(598): m_100, -3_111, 2_01-1
            ],
        },
    },
}


def get_pointgroup_representative(
    symbol: str,
):
    """Return a representative of a given geometric crystal class.

    Parameters
    ----------
    symbol: symbol for geometric crystal class

    Returns
    -------
    group: (order, 3, 3)
    """
    index = POINT_GROUP_REPRESENTATIVES[symbol]
    group = pg_dataset[symbol][index]
    return group


# TODO
def get_canonical_pointgroup(prim_rotations: NDArrayInt):
    """Return representative of geometric crystal class."""
    # P^-1 @ prim_rotations @ P = canonical
    pg_symbol, _, P = get_pointgroup(prim_rotations)
    Pinv = np.linalg.inv(P)

    # Match given crystallographic point group with standardized ones in primitive basis.
    order = len(prim_rotations)
    for idx, std_rotations in enumerate(pg_dataset[pg_symbol]):
        matched = [ndarray2d_to_integer_tuple(Pinv @ r @ P) for r in prim_rotations]

        success = True
        mapping = [-1 for _ in range(order)]  # s.t. prim_rotations[mapping[i]] == std_rotations[i]
        for i, ri in enumerate(std_rotations):
            try:
                j = matched.index(ri)  # type: ignore
            except ValueError:
                success = False
                break
            mapping[i] = j
        if success:
            return pg_symbol, idx, mapping


def traverse_spin_operations(generators):
    """Construct a spin point group from given generators."""
    que = deque()
    founds = set()
    for g in generators:
        que.append(g)

    while len(que) > 0:
        g = que.pop()
        if g in founds:
            continue
        founds.add(g)

        for h in founds:
            gh = (
                ndarray2d_to_integer_tuple(np.array(g[0]) @ np.array(h[0])),
                ndarray2d_to_integer_tuple(np.array(g[1]) @ np.array(h[1])),
            )
            if gh in founds:
                continue
            que.append(gh)

    return tuple(founds)
