"""
The Intelligent Investor — Hybrid Pygame + Tkinter Life Simulator (V8)
A dense, living 2D side-scrolling life sim with pixel-art procedural rendering.
Includes the Ultra Procedural Radio DAW (Stereo, Effects, 8 Genres, Algorithmic Composition).
"""

import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")

import pygame
import sys
import math
import random
import threading
import time
import io
import wave
import struct
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# ══════════════════════════════════════════════════════════════════════════════
#  PYGAME CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

SCREEN_W   = 1280
SCREEN_H   = 720
FPS        = 60
PIXEL_SIZE = 5          # Each "virtual pixel" = 5x5 real pixels
GRAVITY    = 900        # px/s²
MOVE_SPEED = 160        # px/s
JUMP_VEL   = -420       # px/s

# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (all RGB tuples)
# ══════════════════════════════════════════════════════════════════════════════

SK  = (255, 218, 168); SKD = (220, 180, 130)
HR  = ( 60,  35,  10); HRD = ( 35,  20,   5)
EY  = ( 20,  20,  40)
SH  = (255, 255, 255); SHB = (220, 220, 240)
PN  = ( 60,  80, 160); PND = ( 40,  55, 120)
SH2 = ( 80,  50,  30)
BK  = (  0,   0,   0); TR  = None
WL  = ( 25,  28,  50); WL2 = ( 30,  34,  60)
FL  = ( 45,  35,  25); FL2 = ( 55,  43,  30)
BD  = (100,  60,  40); BD2 = ( 80,  45,  28)
PL  = (220, 200, 180)
SH3 = (180, 140, 100); SH4 = (160, 120,  80)
TV1 = ( 20,  20,  25); TV2 = ( 10,  10,  15)
TVS = ( 30, 130, 200); TVG = ( 60, 200, 100)
PC1 = ( 30,  32,  40); PC2 = ( 20,  22,  30)
MN1 = ( 10,  10,  15)
MN2 = ( 15, 200, 255); MNA = (  0, 100, 180)
KB  = ( 40,  42,  50); MSE = ( 50,  52,  62)
LMP = (255, 220,  80); LMB = ( 60,  55,  40)
WND = (100, 160, 220); WNF = ( 50,  40,  30)
RP  = (180,  60,  60); RP2 = (140,  40,  40); RP3 = (200, 180,  50)
PL2 = ( 40,  80,  40); PL3 = ( 30,  60,  30); PT  = (100,  70,  40)
DOR = ( 60,  40,  20); DRK = ( 80,  60,  30); DH  = (200, 160,  60)

# ══════════════════════════════════════════════════════════════════════════════
#  PIXEL ART MATRICES
# ══════════════════════════════════════════════════════════════════════════════

PLAYER_A = [
    [TR,  TR,  TR,  TR,  TR,  HR,  HR,  HR,  HR,  HR,  TR,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  HR,  HR,  HRD, HRD, HR,  HR,  HR,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  HR,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  HR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SK,  SK,  EY,  SK,  SK,  EY,  SK,  SK,  SK,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SK,  SK,  SKD, SKD, SKD, SK,  SK,  SK,  SK,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  TR,  TR,  TR,  TR ],
    [TR,  TR,  SK,  SH,  SHB, SH,  SH,  SH,  SH,  SH,  SHB, SH,  SK,  TR,  TR,  TR ],
    [TR,  TR,  SK,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SK,  TR,  TR,  TR ],
    [TR,  TR,  SK,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SK,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PN,  PN,  PN,  PN,  PN,  PN,  PN,  PN,  PN,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PN,  PND, PN,  PN,  PN,  PN,  PN,  PND, PN,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PND, PN,  PN,  TR,  TR,  PN,  PN,  PND, TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SH2, SH2, SH2, TR,  TR,  SH2, SH2, SH2, TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  SH2, SH2, SH2, SH2, TR,  TR,  SH2, SH2, SH2, SH2, TR,  TR,  TR,  TR ],
    [TR,  TR,  SH2, SH2, SH2, TR,  TR,  TR,  TR,  SH2, SH2, SH2, TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR ],
]

PLAYER_B = [
    [TR,  TR,  TR,  TR,  TR,  HR,  HR,  HR,  HR,  HR,  TR,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  HR,  HR,  HRD, HRD, HR,  HR,  HR,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  HR,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  HR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SK,  SK,  EY,  SK,  SK,  EY,  SK,  SK,  SK,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  SK,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SK,  SK,  SKD, SKD, SKD, SK,  SK,  SK,  SK,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  TR,  TR,  TR,  TR ],
    [TR,  SK,  TR,  SH,  SHB, SH,  SH,  SH,  SH,  SH,  SHB, SH,  TR,  SK,  TR,  TR ],
    [SK,  SK,  TR,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  TR,  SK,  SK,  TR ],
    [SK,  SK,  TR,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  SH,  TR,  SK,  SK,  TR ],
    [TR,  TR,  TR,  PN,  PN,  PN,  PN,  PN,  PN,  PN,  PN,  PN,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  PN,  PND, PN,  PN,  PN,  PN,  PN,  PND, PN,  TR,  TR,  TR,  TR ],
    [TR,  PN,  PN,  PN,  PN,  TR,  TR,  TR,  TR,  PN,  PN,  PN,  PN,  TR,  TR,  TR ],
    [TR,  PN,  PN,  PN,  PN,  TR,  TR,  TR,  TR,  PN,  PN,  PN,  PN,  TR,  TR,  TR ],
    [TR,  PN,  PN,  PN,  TR,  TR,  TR,  TR,  TR,  TR,  PN,  PN,  PN,  TR,  TR,  TR ],
    [TR,  PND, PN,  PN,  TR,  TR,  TR,  TR,  TR,  TR,  PN,  PN,  PND, TR,  TR,  TR ],
    [TR,  SH2, SH2, SH2, TR,  TR,  TR,  TR,  TR,  TR,  SH2, SH2, SH2, TR,  TR,  TR ],
    [SH2, SH2, SH2, SH2, TR,  TR,  TR,  TR,  TR,  TR,  SH2, SH2, SH2, SH2, TR,  TR ],
    [SH2, SH2, SH2, TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  SH2, SH2, SH2, TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR ],
]

BED_SPRITE = [
    [BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2],
    [BD2,BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD, BD2],
    [BD2,PL, PL, PL, PL, PL, SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,BD, BD2],
    [BD2,PL, PL, PL, PL, PL, SH3,SH4,SH3,SH3,SH4,SH3,SH3,SH4,SH3,SH3,SH4,SH3,BD, BD2],
    [BD2,PL, PL, PL, PL, PL, SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,BD, BD2],
    [BD2,BD, BD, BD, BD, BD, SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,BD, BD2],
    [BD2,BD, BD, BD, BD, BD, SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,BD, BD2],
    [BD2,BD, BD, BD, BD, BD, SH3,SH4,SH3,SH3,SH4,SH3,SH3,SH4,SH3,SH3,SH4,SH3,BD, BD2],
    [BD2,BD, BD, BD, BD, BD, SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,SH3,BD, BD2],
    [BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2,BD2],
    [BD2,FL, FL, BD2,FL, FL, BD2,FL, FL, FL, FL, FL, FL, FL, FL, BD2,FL, FL, BD2,BD2],
    [TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR ],
]

TV_SPRITE = [
    [TR, TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TR ],
    [TV1,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV1],
    [TV1,TV2,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TV2,TV1],
    [TV1,TV2,TVS,TVG,TVG,TVG,TVS,TVS,TVG,TVG,TVG,TVS,TV2,TV1],
    [TV1,TV2,TVS,TVG,TVS,TVG,TVS,TVS,TVG,TVS,TVG,TVS,TV2,TV1],
    [TV1,TV2,TVS,TVG,TVG,TVG,TVS,TVS,TVG,TVG,TVG,TVS,TV2,TV1],
    [TV1,TV2,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TV2,TV1],
    [TV1,TV2,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TVS,TV2,TV1],
    [TV1,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV2,TV1],
    [TR, TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TR ],
    [TR, TR, TR, TV1,TV1,TV1,TV1,TV1,TV1,TV1,TV1,TR, TR, TR ],
    [TR, TR, TR, TV1,TR, TR, TR, TR, TR, TR, TV1,TR, TR, TR ],
]

PC_SPRITE = [
    [TR, TR, MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,TR, TR ],
    [TR, MN1,MN1,MNA,MNA,MNA,MNA,MNA,MNA,MNA,MNA,MNA,MNA,MNA,MNA,MN1,MN1,TR ],
    [TR, MN1,MNA,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MNA,MN1,TR ],
    [TR, MN1,MNA,MN2,MNA,MNA,MN2,MN2,MN2,MN2,MN2,MN2,MNA,MNA,MN2,MNA,MN1,TR ],
    [TR, MN1,MNA,MN2,MNA,MNA,MN2,MN2,MN2,MN2,MN2,MN2,MNA,MNA,MN2,MNA,MN1,TR ],
    [TR, MN1,MNA,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MNA,MN1,TR ],
    [TR, MN1,MNA,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MN2,MNA,MN1,TR ],
    [TR, MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,MN1,TR ],
    [TR, TR, TR, TR, TR, TR, TR, MN1,MN1,MN1,MN1,TR, TR, TR, TR, TR, TR, TR ],
    [PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1],
    [PC2,KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, PC2],
    [PC2,KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, KB, PC2],
    [PC2,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC2],
    [PC2,PC2,PC2,PC2,PC2,PC2,PC2,MSE,MSE,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2],
    [PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2],
    [TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR, TR ],
]

WINDOW_SPRITE = [
    [WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WND,WND,WND,WNF,WNF,WND,WND,WND,WNF],
    [WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF],
    [WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF,WNF],
]

LAMP_SPRITE = [
    [TR, TR, LMP,TR, TR],
    [TR, LMP,LMP,LMP,TR],
    [TR, LMP,LMP,LMP,TR],
    [TR, TR, LMB,TR, TR],
    [TR, TR, LMB,TR, TR],
    [TR, TR, LMB,TR, TR],
    [TR, TR, LMB,TR, TR],
    [TR, LMB,LMB,LMB,TR],
    [LMB,LMB,LMB,LMB,LMB],
    [TR, TR, TR, TR, TR],
]

PLANT_SPRITE = [
    [TR, PL2,TR, TR, PL2,TR],
    [PL2,PL3,PL2,PL2,PL3,TR],
    [PL2,PL2,PL3,PL2,PL2,PL2],
    [TR, PL2,PL2,PL2,PL2,TR],
    [TR, TR, PL2,PL2,TR, TR],
    [TR, TR, PT, PT, TR, TR],
    [TR, PT, PT, PT, PT, TR],
    [TR, PT, PT, PT, PT, TR],
]

# NPC partner sprite
NP1 = (210, 140,  90)   # NPC skin light
NP2 = (180, 110,  70)   # NPC skin shadow
NPC_HR = (120,  55,  20) # auburn hair
NPC_HD = ( 90,  35,  10) # hair dark
NPC_EY = ( 40,  20,  60) # violet eyes
NPC_TC = ( 40, 150, 150) # teal dress
NPC_TD = ( 25, 110, 110) # teal dark
NPC_PT = ( 60,  40, 100) # purple leggings
NPC_PD = ( 40,  25,  75) # pants dark
NPC_SH = (200, 170, 130) # shoe

NPC_SPRITE = [
    [TR,  TR,  TR,  TR,  TR,  NPC_HR,NPC_HR,NPC_HR,NPC_HR,NPC_HR,TR,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  NPC_HR,NPC_HR,NPC_HD,NPC_HD,NPC_HR,NPC_HR,NPC_HR,TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NPC_HR,NP1,  NP1,  NP1,  NP1,  NP1,  NPC_HR,NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NP1,  NP1,  NPC_EY,NP1,  NPC_EY,NP1,  NP1,  NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NP1,  NP1,  NP1,  NP1,  NP1,  NP1,  NP1,  NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NP1,  NP2,  NP2,  NP1,  NP1,  NP1,  NP1,  NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NPC_TC,NPC_TD,NPC_TC,NPC_TC,NPC_TC,NPC_TD,NPC_TC,NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  NPC_HR,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_HR,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  NPC_TC,NPC_TD,NPC_TC,NPC_TC,NPC_TC,NPC_TD,NPC_TC,TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,TR,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  NP1,  NP1,  TR,  TR,  NP1,  NP1,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  NP1,  NP1,  TR,  TR,  NP1,  NP1,  TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  NPC_SH,NPC_SH,TR,  TR,  NPC_SH,NPC_SH,TR,  TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  NPC_SH,NPC_SH,NPC_SH,TR,  TR,  NPC_SH,NPC_SH,NPC_SH,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  NPC_SH,NPC_SH,NPC_SH,TR,  TR,  NPC_SH,NPC_SH,NPC_SH,TR,  TR,  TR,  TR ],
    [TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR,  TR ],
]

KID_SPRITE = [
    [TR, TR, NPC_HR,NPC_HR,NPC_HR,NPC_HR,TR, TR],
    [TR, NPC_HR,NP1,NP1,NP1,NP1,NPC_HR,TR],
    [TR, NPC_HR,NP1,NPC_EY,NP1,NPC_EY,TR, TR],
    [TR, TR, NP1,NP1,NP1,NP1,TR, TR],
    [TR, NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,NPC_TC,TR],
    [TR, NPC_TC,NPC_TD,NPC_TC,NPC_TC,NPC_TD,NPC_TC,TR],
    [TR, TR, NPC_PT,NPC_PT,NPC_PT,NPC_PT,TR, TR],
    [TR, TR, NPC_PT,TR, TR, NPC_PT,TR, TR],
    [TR, TR, NPC_SH,TR, TR, NPC_SH,TR, TR]
]

NPC_SPEECH = [
    "Stonks going up?",
    "I believe in you!",
    "Did you check the PC?",
    "Buy the dip!",
    "You got this!",
]

DOOR_SPRITE = [
    [DOR,DOR,DOR,DOR,DOR,DOR,DOR,DOR],
    [DOR,DRK,DRK,DRK,DRK,DRK,DRK,DOR],
    [DOR,DRK,DOR,DOR,DOR,DOR,DRK,DOR],
    [DOR,DRK,DOR,DOR,DOR,DOR,DRK,DOR],
    [DOR,DRK,DOR,DOR,DOR,DOR,DRK,DOR],
    [DOR,DRK,DRK,DRK,DRK,DRK,DRK,DOR],
    [DOR,DOR,DOR,DOR,DOR,DOR,DOR,DOR],
    [DOR,DOR,DOR,DOR,DOR,DOR,DOR,DOR],
    [DOR,DOR,DH, DH, DOR,DOR,DOR,DOR],
    [DOR,DOR,DH, DH, DOR,DOR,DOR,DOR],
    [DOR,DOR,DOR,DOR,DOR,DOR,DOR,DOR],
    [DOR,DRK,DRK,DRK,DRK,DRK,DRK,DOR],
    [DOR,DRK,DOR,DOR,DOR,DOR,DRK,DOR],
    [DOR,DRK,DOR,DOR,DOR,DOR,DRK,DOR],
    [DOR,DRK,DOR,DOR,DOR,DOR,DRK,DOR],
    [DOR,DRK,DRK,DRK,DRK,DRK,DRK,DOR],
    [DOR,DOR,DOR,DOR,DOR,DOR,DOR,DOR],
    [DOR,DOR,DOR,DOR,DOR,DOR,DOR,DOR],
]

SHELF_SPRITE = [
    [PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1],
    [PC2,(200,60,60),(180,60,60),(180,100,40),(180,100,40),(60,120,180),(60,120,180),(80,160,80),(80,160,80),(160,60,160),(160,60,160),PC2],
    [PC2,(200,60,60),(180,60,60),(180,100,40),(180,100,40),(60,120,180),(60,120,180),(80,160,80),(80,160,80),(160,60,160),(160,60,160),PC2],
    [PC2,(200,60,60),(180,60,60),(180,100,40),(180,100,40),(60,120,180),(60,120,180),(80,160,80),(80,160,80),(160,60,160),(160,60,160),PC2],
    [PC2,(200,60,60),(200,60,60),(180,100,40),(180,100,40),(60,120,180),(60,120,180),(80,160,80),(80,160,80),(160,60,160),(160,60,160),PC2],
    [PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1],
    [PC2,(220,180,40),(220,180,40),(80,80,200),(80,80,200),(200,100,40),(200,100,40),(60,160,160),(60,160,160),(200,80,80),(200,80,80),PC2],
    [PC2,(220,180,40),(220,180,40),(80,80,200),(80,80,200),(200,100,40),(200,100,40),(60,160,160),(60,160,160),(200,80,80),(200,80,80),PC2],
    [PC2,(220,180,40),(220,180,40),(80,80,200),(80,80,200),(200,100,40),(200,100,40),(60,160,160),(60,160,160),(200,80,80),(200,80,80),PC2],
    [PC2,(220,180,40),(220,180,40),(80,80,200),(80,80,200),(200,100,40),(200,100,40),(60,160,160),(60,160,160),(200,80,80),(200,80,80),PC2],
    [PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1],
    [PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2],
    [PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2,PC2],
    [PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1,PC1],
]


# ══════════════════════════════════════════════════════════════════════════════
#  PIXEL RENDERER
# ══════════════════════════════════════════════════════════════════════════════

class PixelRenderer:
    def __init__(self, surface: pygame.Surface, pixel_size: int = PIXEL_SIZE):
        self.surf = surface
        self.ps   = pixel_size

    def draw_sprite(self, matrix, x: int, y: int, flip_h: bool = False):
        rows = matrix
        if flip_h:
            rows = [list(reversed(row)) for row in matrix]
        for ry, row in enumerate(rows):
            for rx, col in enumerate(row):
                if col is None: continue
                pygame.draw.rect(self.surf, col, pygame.Rect(x + rx * self.ps, y + ry * self.ps, self.ps, self.ps))

# ══════════════════════════════════════════════════════════════════════════════
#  GAME WORLD OBJECTS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WorldObject:
    name: str; x: int; y: int; sprite: list; interact_label: str = ""; interact_radius: int = 80
    def draw(self, renderer: PixelRenderer): renderer.draw_sprite(self.sprite, self.x, self.y)
    def can_interact(self, px: int, py: int) -> bool:
        cx = self.x + (len(self.sprite[0]) * PIXEL_SIZE) // 2
        cy = self.y + (len(self.sprite) * PIXEL_SIZE) // 2
        return math.hypot(px - cx, py - cy) < self.interact_radius

# ══════════════════════════════════════════════════════════════════════════════
#  ULTRA PROCEDURAL RADIO DAW
# ══════════════════════════════════════════════════════════════════════════════

class ProceduralRadio:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2)
        
        self.sample_rate = 22050
        self.channel = pygame.mixer.Channel(0)
        self.playing = False
        
        self.master_volume = 0.5
        
        self.genres = [
            "Hip Hop", "Metal", "Techno", "House", 
            "Middle Eastern", "Funk", "Jazz", "Blues"
        ]
        self.genre_idx = 0
        self.current_track_name = "Radio Off"
        self._thread = None
        
        self.mix = {
            "kick":   {"vol": 1.0, "pan":  0.0},
            "snare":  {"vol": 0.8, "pan":  0.0},
            "hats":   {"vol": 0.5, "pan":  0.3},
            "bass":   {"vol": 0.9, "pan":  0.0},
            "chords": {"vol": 0.5, "pan": -0.4},
            "lead":   {"vol": 0.7, "pan":  0.2},
            "guitarL":{"vol": 0.8, "pan": -0.8},
            "guitarR":{"vol": 0.8, "pan":  0.8}
        }
        
        self.scales = {
            "minor": [1.0, 1.122, 1.189, 1.335, 1.498, 1.587, 1.782, 2.0],
            "harmonic_minor": [1.0, 1.122, 1.189, 1.335, 1.498, 1.587, 1.888, 2.0],
            "phrygian_dominant": [1.0, 1.059, 1.260, 1.335, 1.498, 1.587, 1.782, 2.0],
            "dorian": [1.0, 1.122, 1.189, 1.335, 1.498, 1.682, 1.782, 2.0],
            "blues": [1.0, 1.189, 1.335, 1.414, 1.498, 1.782, 2.0]
        }
        
        self.progressions = [
            [0, 5, 2, 6],
            [0, 3, 4, 0],
            [0, 5, 3, 4],
            [0, 0, 0, 0]
        ]

    def toggle(self):
        self.playing = not self.playing
        if self.playing: self._generate_and_play()
        else: self.channel.stop(); self.current_track_name = "Radio Off"

    def next_track(self):
        if not self.playing: self.playing = True
        self.genre_idx = (self.genre_idx + 1) % len(self.genres)
        self._generate_and_play()

    def prev_track(self):
        if not self.playing: self.playing = True
        self.genre_idx = (self.genre_idx - 1) % len(self.genres)
        self._generate_and_play()

    def vol_up(self):
        self.master_volume = min(1.0, self.master_volume + 0.1)

    def vol_down(self):
        self.master_volume = max(0.0, self.master_volume - 0.1)

    def _generate_and_play(self):
        genre = self.genres[self.genre_idx]
        self.current_track_name = f"Composing {genre}... (Wait 3s)"
        if self._thread and self._thread.is_alive(): return
        self._thread = threading.Thread(target=self._compose_track, args=(genre,), daemon=True)
        self._thread.start()

    def _compose_track(self, genre):
        bpm = 120
        scale_name = "minor"
        prog = self.progressions[0]
        is_swing = False
        
        if genre == "Hip Hop": bpm=85; scale_name="minor"; prog=self.progressions[3]
        elif genre == "Metal": bpm=160; scale_name="harmonic_minor"; prog=self.progressions[2]
        elif genre == "Techno": bpm=135; scale_name="minor"; prog=self.progressions[0]
        elif genre == "House": bpm=124; scale_name="dorian"; prog=self.progressions[0]
        elif genre == "Middle Eastern": 
            bpm=95; scale_name="phrygian_dominant"; prog=self.progressions[3]
            motif = [1.0, 1.059, 1.260, 1.335, 1.498, 1.587, 1.888, 2.0]
        elif genre == "Funk": bpm=110; scale_name="dorian"; prog=self.progressions[1]
        elif genre == "Jazz": bpm=125; scale_name="dorian"; prog=self.progressions[1]; is_swing=True
        elif genre == "Blues": bpm=80; scale_name="blues"; prog=self.progressions[1]; is_swing=True

        scale = self.scales[scale_name]
        beat_dur = 60.0 / bpm
        total_beats = 96
        samples = int(self.sample_rate * beat_dur * total_beats)
        
        L = [0.0] * samples
        R = [0.0] * samples
        
        base_root = random.uniform(55.0, 82.41)
        motif = [random.choice(scale) for _ in range(8)] 
        
        for beat in range(total_beats):
            sec = self._get_section(beat)
            start_idx = int(beat * beat_dur * self.sample_rate)
            
            env = 1.0
            if beat < 8: env = beat / 8.0
            if beat > 88: env = (96 - beat) / 8.0
            
            bar = beat // 4
            chord_idx = prog[bar % 4]
            chord_root = base_root * scale[chord_idx]
            
            if sec != "intro" and sec != "outro":
                if genre in ["Techno", "House"] or (genre == "Metal" and sec == "drop"):
                    self._kick(L, R, start_idx, beat_dur, 1.0 * env)
                    if genre == "Metal" and sec == "drop" and beat % 2 != 0:
                        self._kick(L, R, start_idx + int(beat_dur/2 * self.sample_rate), beat_dur/2, 0.8 * env)
                elif genre in ["Hip Hop", "Funk", "Blues", "Middle Eastern", "Jazz"]:
                    if beat % 4 == 0:
                        self._kick(L, R, start_idx, beat_dur, 1.0 * env, deep=(genre=="Hip Hop"))
                    elif beat % 4 == 2:
                        self._kick(L, R, start_idx + int(beat_dur/2 * self.sample_rate), beat_dur, 0.7 * env, deep=(genre=="Hip Hop"))

                if genre != "Middle Eastern" and beat % 4 == 2:
                    self._snare(L, R, start_idx, beat_dur, 0.8 * env)

                if sec in ["build", "drop"]:
                    self._hat(L, R, start_idx, beat_dur*0.1, 0.5 * env)
                    off_idx = start_idx + int((beat_dur * (0.66 if is_swing else 0.5)) * self.sample_rate)
                    self._hat(L, R, off_idx, beat_dur*0.1, 0.3 * env)

            if beat % 4 == 0 and (sec == "intro" or sec == "outro" or genre in ["House", "Techno"]):
                vol_pad = 0.8 if sec in ["intro", "outro"] else 0.5
                for i in [0, 2, 4]:
                    self._synth(L, R, start_idx, beat_dur * 4, chord_root * scale[i % len(scale)], "sine", vol_pad * env, "chords", att=0.5, rel=1.0)

            if sec in ["verse", "build", "drop"]:
                osc = "saw" if genre in ["Techno", "House"] else "triangle"
                if genre == "Metal":
                    self._synth(L, R, start_idx, beat_dur/2, chord_root, "dist", 0.8 * env, "bass", att=0.01, rel=0.1)
                    self._synth(L, R, start_idx + int(beat_dur/2 * self.sample_rate), beat_dur/2, chord_root, "dist", 0.8 * env, "bass", att=0.01, rel=0.1)
                elif genre in ["Blues", "Jazz"]:
                    walk_note = chord_root * scale[(beat % 4) % len(scale)]
                    self._synth(L, R, start_idx, beat_dur, walk_note, osc, 0.9 * env, "bass", att=0.05, rel=0.2)
                else:
                    self._synth(L, R, start_idx, beat_dur*0.8, chord_root, osc, 0.9 * env, "bass", att=0.05, rel=0.3)

            if sec == "drop" or (genre == "Middle Eastern" and sec != "outro"):
                if genre == "Metal":
                    self._synth(L, R, start_idx, beat_dur, chord_root * 2, "dist", 0.7 * env, "guitarL", att=0.05, rel=0.2)
                    self._synth(L, R, start_idx, beat_dur, chord_root * 2, "dist", 0.7 * env, "guitarR", att=0.05, rel=0.2)
                else:
                    osc = "square" if genre in ["Techno", "House"] else "saw"
                    step_dur = beat_dur / 2.0
                    for step in range(2):
                        if random.random() > 0.2:
                            m_note = base_root * motif[(beat * 2 + step) % len(motif)] * 2.0
                            if genre == "Middle Eastern": m_note *= 2.0
                            s_idx = start_idx + int(step * step_dur * self.sample_rate)
                            self._synth(L, R, s_idx, step_dur, m_note, osc, 0.6 * env, "lead", att=0.02, rel=0.1, vib=(genre=="Middle Eastern"))

        delay_samps = int(self.sample_rate * beat_dur * 0.75)
        for i in range(delay_samps, len(L)):
            L[i] += L[i - delay_samps] * 0.2
            R[i] += R[i - delay_samps] * 0.2

        max_L = max(max(L), abs(min(L))) or 1.0
        max_R = max(max(R), abs(min(R))) or 1.0
        master_max = max(max_L, max_R)
        mult = (32767 / master_max) * self.master_volume
        
        packed = bytearray()
        for l, r in zip(L, R):
            pl = max(-32767, min(32767, int(l * mult)))
            pr = max(-32767, min(32767, int(r * mult)))
            packed.extend(struct.pack('<hh', pl, pr))

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(packed)
        
        wav_io.seek(0)
        sound = pygame.mixer.Sound(file=wav_io)
        if self.playing:
            self.channel.play(sound, loops=-1)
            self.current_track_name = f"🎵 [{genre}] Vol: {int(self.master_volume*100)}%"

    def _get_section(self, b):
        if b < 16: return "intro"
        if b < 48: return "verse"
        if b < 64: return "build"
        if b < 80: return "drop"
        return "outro"

    def _write(self, Lbuf, Rbuf, idx, val, chan):
        if idx >= len(Lbuf): return
        pan = self.mix[chan]["pan"]
        vol = self.mix[chan]["vol"]
        l_pan = 1.0 - pan if pan > 0 else 1.0
        r_pan = 1.0 + pan if pan < 0 else 1.0
        Lbuf[idx] += val * vol * l_pan
        Rbuf[idx] += val * vol * r_pan

    def _kick(self, L, R, s, d, v, deep=False):
        decay = 10 if deep else 20
        freq = 60.0 if deep else 150.0
        samples = int(self.sample_rate * d * (0.8 if deep else 0.4))
        for i in range(samples):
            t = i / self.sample_rate
            f = freq * math.exp(-t * decay)
            val = math.sin(2 * math.pi * f * t) * math.exp(-t * (5 if deep else 10)) * v
            self._write(L, R, s+i, val, "kick")

    def _snare(self, L, R, s, d, v):
        samples = int(self.sample_rate * d * 0.3)
        for i in range(samples):
            t = i / self.sample_rate
            env = math.exp(-t * 25)
            val = (math.sin(2*math.pi*200*t)*math.exp(-t*40)*0.5 + random.uniform(-1,1)*0.5) * env * v
            self._write(L, R, s+i, val, "snare")

    def _hat(self, L, R, s, d, v):
        samples = int(self.sample_rate * d)
        for i in range(samples):
            t = i / self.sample_rate
            val = random.uniform(-1, 1) * math.exp(-t * 40) * v
            self._write(L, R, s+i, val, "hats")

    def _synth(self, L, R, s, d, f, osc, v, chan, att=0.01, rel=0.1, vib=False):
        samples = int(self.sample_rate * d)
        att_s = max(1, int(self.sample_rate * att))
        rel_s = max(1, int(self.sample_rate * rel))
        for i in range(samples):
            t = i / self.sample_rate
            env = 1.0
            if i < att_s: env = i / att_s
            elif i > samples - rel_s: env = (samples - i) / rel_s
            
            cf = f + (math.sin(2*math.pi*6*t)*(f*0.02) if vib else 0)
            phase = (t * cf) % 1.0
            
            if osc == "square": val = 1.0 if phase < 0.5 else -1.0
            elif osc == "saw": val = 2.0 * phase - 1.0
            elif osc == "triangle": val = 4.0 * abs(phase - 0.5) - 1.0
            elif osc == "dist": val = math.tanh(math.sin(2 * math.pi * cf * t) * 6.0)
            else: val = math.sin(2 * math.pi * cf * t)
                
            self._write(L, R, s+i, val * env * v, chan)


# ══════════════════════════════════════════════════════════════════════════════
#  RAIN SYSTEM & DUST MOTES
# ══════════════════════════════════════════════════════════════════════════════

class RainSystem:
    def __init__(self, window_rect: pygame.Rect):
        self.wr     = window_rect
        self.drops: List[List] = []
        for _ in range(60):
            self.drops.append(self._new_drop())

    def _new_drop(self) -> list:
        x = random.randint(self.wr.left, self.wr.right)
        y = random.randint(self.wr.top, self.wr.bottom)
        speed = random.uniform(120, 300)
        length = random.randint(4, 12)
        return [x, y, speed, length]

    def update(self, dt: float):
        for d in self.drops:
            d[1] += d[2] * dt
            if d[1] > self.wr.bottom:
                d[0] = random.randint(self.wr.left, self.wr.right)
                d[1] = self.wr.top

    def draw(self, surf: pygame.Surface):
        for d in self.drops:
            x, y, _, length = d
            pygame.draw.line(surf, (160, 200, 240), (int(x), int(y)), (int(x), int(y + length)), 1)

class DustMotes:
    def __init__(self, n=25):
        self.motes = []
        for _ in range(n):
            self.motes.append(self._new())

    def _new(self):
        return {
            "x": random.uniform(0, SCREEN_W),
            "y": random.uniform(100, SCREEN_H - 150),
            "vx": random.uniform(-8, 8),
            "vy": random.uniform(-4, 4),
            "alpha": random.randint(20, 70),
            "r": random.randint(1, 2),
        }

    def update(self, dt):
        for m in self.motes:
            m["x"] += m["vx"] * dt
            m["y"] += m["vy"] * dt
            if m["x"] < 0 or m["x"] > SCREEN_W or m["y"] < 100 or m["y"] > SCREEN_H - 100:
                m.update(self._new())

    def draw(self, surf):
        for m in self.motes:
            s = pygame.Surface((m["r"]*2, m["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 240, 200, m["alpha"]), (m["r"], m["r"]), m["r"])
            surf.blit(s, (int(m["x"]), int(m["y"])))


# ══════════════════════════════════════════════════════════════════════════════
#  PC FLICKER EFFECT
# ══════════════════════════════════════════════════════════════════════════════

class MonitorFlicker:
    def __init__(self):
        self.timer = 0.0
        self.flicker_state = 0
        self.scroll_y = 0.0
        self.lines = [
            "NET WORTH: $5,000",
            "PORTFOLIO: $0",
            "MARKET: NEUTRAL",
            "G500  $200.00 ↑",
            "TNVA  $142.00 →",
            "XAU  $1920.00 ↑",
            "PRESS [E] TO TRADE",
        ]

    def update(self, dt: float, net_worth: float, market_summary: str):
        self.timer += dt
        self.scroll_y += dt * 8.0
        if self.timer > 0.08:
            self.timer = 0
            self.flicker_state = random.randint(0, 10)
        self.lines[0] = f"NET WORTH: ${net_worth:,.0f}"
        self.lines[2] = f"MARKET: {market_summary}"

    def draw(self, surf: pygame.Surface, rect: pygame.Rect):
        brightness = 1.0 if self.flicker_state > 1 else 0.4
        overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        base_col = (0, int(40 * brightness), int(80 * brightness))
        overlay.fill(base_col)

        try: font = pygame.font.SysFont("Segoe UI", 7)
        except Exception: font = pygame.font.Font(None, 7)

        for i, line in enumerate(self.lines):
            y_pos = int((i * 9 - self.scroll_y % (len(self.lines) * 9)) + 2)
            if 0 <= y_pos < rect.h:
                col = (0, int(200 * brightness), int(255 * brightness))
                txt = font.render(line, False, col)
                overlay.blit(txt, (2, y_pos))

        for sy in range(0, rect.h, 2):
            pygame.draw.line(overlay, (0, 0, 0, 40), (0, sy), (rect.w, sy))

        surf.blit(overlay, rect.topleft)

# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICATION SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

class NotificationSystem:
    def __init__(self):
        self.notes: List[dict] = []

    def add(self, text: str, color=(255, 255, 255), duration=3.5):
        self.notes.append({"text": text, "color": color, "timer": duration, "max": duration})

    def update(self, dt: float):
        self.notes = [n for n in self.notes if n["timer"] > 0]
        for n in self.notes: n["timer"] -= dt

    def draw(self, surf: pygame.Surface):
        try: font = pygame.font.SysFont("Segoe UI", 14, bold=True)
        except Exception: font = pygame.font.Font(None, 14)

        y = 80
        for n in self.notes[-6:]:
            alpha = max(0, min(255, int(255 * (n["timer"] / n["max"]))))
            bg = pygame.Surface((420, 22), pygame.SRCALPHA)
            fill_alpha = max(0, min(255, int(alpha * 0.6)))
            bg.fill((0, 0, 0, fill_alpha))
            
            surf.blit(bg, (SCREEN_W - 430, y - 2))
            
            col = tuple(max(0, min(255, c)) for c in n["color"])
            txt = font.render(n["text"][:80], True, col) # Extended to 80 to fix the +1 bug
            txt.set_alpha(alpha)
            surf.blit(txt, (SCREEN_W - 428, y))
            y += 24

# ══════════════════════════════════════════════════════════════════════════════
#  PLAYER CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class PlayerController:
    SPRITE_W = len(PLAYER_A[0]) * PIXEL_SIZE
    SPRITE_H = len(PLAYER_A)    * PIXEL_SIZE

    def __init__(self, x: int, y: int):
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.on_ground = False; self.facing_right = True
        self.anim_timer = 0.0; self.anim_frame = 0; self.anim_speed = 0.15
        self.idle_bounce_timer = 0.0; self.idle_bounce_offset = 0

    @property
    def feet_y(self) -> float: return self.y + self.SPRITE_H
    @property
    def center_x(self) -> float: return self.x + self.SPRITE_W // 2
    @property
    def center_y(self) -> float: return self.y + self.SPRITE_H // 2

    def update(self, dt: float, floor_y: int, left_wall: int, right_wall: int):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -MOVE_SPEED; self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx =  MOVE_SPEED; self.facing_right = True

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = JUMP_VEL
            self.on_ground = False

        self.vy += GRAVITY * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt

        if self.feet_y >= floor_y:
            self.y = floor_y - self.SPRITE_H
            self.vy = 0
            self.on_ground = True

        self.x = max(left_wall, min(right_wall - self.SPRITE_W, self.x))

        if abs(self.vx) > 1:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_frame = 1 - self.anim_frame
            self.idle_bounce_offset = 0
            self.idle_bounce_timer = 0.0
        else:
            self.anim_frame = 0
            self.idle_bounce_timer += dt
            self.idle_bounce_offset = 1 if (int(self.idle_bounce_timer * 2) % 2 == 0) else 0

    def draw(self, renderer: PixelRenderer):
        sprite = PLAYER_A if self.anim_frame == 0 else PLAYER_B
        renderer.draw_sprite(sprite, int(self.x), int(self.y) + self.idle_bounce_offset, flip_h=not self.facing_right)

# ══════════════════════════════════════════════════════════════════════════════
#  DAY / NIGHT CYCLE
# ══════════════════════════════════════════════════════════════════════════════

class DayNightCycle:
    def __init__(self):
        self.hour = 8.0; self.day = 1

    def advance_hours(self, hours: float):
        self.hour += hours
        while self.hour >= 24.0:
            self.hour -= 24.0
            self.day  += 1

    def overlay_color(self) -> Tuple[int, int, int, int]:
        h = self.hour
        if 6 <= h < 9:
            t = (h - 6) / 3
            return (int(lerp(180,0,t)), int(lerp(80,0,t)), 0, int(lerp(120,0,t)))
        elif 9 <= h < 18:
            return (0, 0, 0, 0)
        elif 18 <= h < 21:
            t = (h - 18) / 3
            return (0, 0, int(lerp(0,20,t)), int(lerp(0,80,t)))
        elif h >= 21 or h < 4:
            return (0, 5, 30, 140)
        else:
            t = (h - 4) / 2
            return (0, 0, int(lerp(30,0,t)), int(lerp(140,120,t)))

    def time_str(self) -> str:
        h = int(self.hour)
        m = int((self.hour - h) * 60)
        return f"{h%12 or 12:02d}:{m:02d} {'AM' if h < 12 else 'PM'}"

def lerp(a, b, t): return a + (b - a) * t

# ══════════════════════════════════════════════════════════════════════════════
#  HUD & UI DRAWING
# ══════════════════════════════════════════════════════════════════════════════

def draw_hud(surf: pygame.Surface, p_ctrl, cycle: DayNightCycle, engine, notes: NotificationSystem, radio: ProceduralRadio):
    try: font_lg = pygame.font.SysFont("Segoe UI", 15, bold=True); font_sm = pygame.font.SysFont("Segoe UI", 12)
    except Exception: font_lg = pygame.font.Font(None, 15); font_sm = pygame.font.Font(None, 12)

    bar = pygame.Surface((SCREEN_W, 48), pygame.SRCALPHA); bar.fill((0, 0, 0, 160)); surf.blit(bar, (0, 0))

    p = engine.player; m = engine.market
    items = [(f"💰 ${p.cash:>10,.0f}", (100, 220, 100)), (f"📈 ${p.net_worth:>10,.0f}", (240, 200, 60)), (f"😊 {p.happiness:>3}/100", (230, 140, 40))]
    x = 12
    for txt, col in items:
        s = font_sm.render(txt, True, col); surf.blit(s, (x, 6)); x += s.get_width() + 20

    career = CAREER_LEVELS[p.career_level]["title"]
    surf.blit(font_sm.render(f"💼 {career}", True, (150, 130, 220)), (x, 6))
    surf.blit(font_sm.render(m.market_summary, True, (200, 200, 200)), (12, 28))

    ds = font_lg.render(f"📅 {engine.date_str()}  🕐 {cycle.time_str()}", True, (200, 210, 240))
    surf.blit(ds, (SCREEN_W // 2 - ds.get_width() // 2, 14))

    notes.draw(surf)

    hint_bar = pygame.Surface((SCREEN_W, 26), pygame.SRCALPHA); hint_bar.fill((0, 0, 0, 120)); surf.blit(hint_bar, (0, SCREEN_H - 26))
    hs = font_sm.render("[←→/A D] Move  [Space] Jump  [E] Interact  [P] Radio  [N] Skip  [Y] 1-Year", True, (100, 110, 140))
    surf.blit(hs, (SCREEN_W // 2 - hs.get_width() // 2, SCREEN_H - 20))

    try: radio_font = pygame.font.SysFont("Segoe UI", 12, bold=True)
    except Exception: radio_font = pygame.font.Font(None, 12)
    track_text = radio_font.render(radio.current_track_name, True, (150, 255, 150))
    surf.blit(track_text, (SCREEN_W - track_text.get_width() - 20, 20))

def draw_interact_prompt(surf: pygame.Surface, label: str, px: int, py: int):
    try: font = pygame.font.SysFont("Segoe UI", 13, bold=True)
    except Exception: font = pygame.font.Font(None, 13)
    txt = font.render(f"[E] {label}", True, (255, 230, 80))
    bg  = pygame.Surface((txt.get_width() + 10, txt.get_height() + 6), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    x = px - bg.get_width() // 2
    y = py - 40
    surf.blit(bg, (x, y)); surf.blit(txt, (x + 5, y + 3))

def draw_sleep_overlay(surf: pygame.Surface, progress: float):
    alpha = int(min(255, progress * 512))
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); ov.fill((5, 5, 20, alpha)); surf.blit(ov, (0, 0))
    if progress > 0.3:
        try: font = pygame.font.SysFont("Segoe UI", 36, bold=True)
        except Exception: font = pygame.font.Font(None, 36)
        txt = font.render("Z" * int(progress * 6 + 1), True, (180, 180, 255, int(alpha)))
        surf.blit(txt, (SCREEN_W // 2 - 40, SCREEN_H // 2 - 20))

def draw_npc_speech_bubble(surf: pygame.Surface, text: str, npc_x: int, npc_y: int):
    try: font = pygame.font.SysFont("segoe ui", 13, bold=True)
    except Exception: font = pygame.font.Font(None, 14)
    txt_surf = font.render(text, True, (20, 20, 40))
    pad_x, pad_y = 10, 7
    w = txt_surf.get_width() + pad_x * 2
    h = txt_surf.get_height() + pad_y * 2
    tail = 8
    bx = npc_x - w // 2
    by = npc_y - h - tail - 4
    bubble = pygame.Surface((w, h + tail), pygame.SRCALPHA)
    pygame.draw.rect(bubble, (255, 255, 255, 230), (0, 0, w, h), border_radius=8)
    pygame.draw.polygon(bubble, (255, 255, 255, 230), [(w//2 - 5, h), (w//2 + 5, h), (w//2, h + tail)])
    surf.blit(bubble, (bx, by))
    surf.blit(txt_surf, (bx + pad_x, by + pad_y))

def draw_npc(surf: pygame.Surface, renderer: PixelRenderer, engine, npc_state: dict, dt: float):
    rel = engine.player.lifestyle.get("relationship")
    if not rel or rel.name not in ("Partner", "Family"):
        return

    npc_state["pacing_timer"] -= dt
    if npc_state["pacing_timer"] <= 0:
        npc_state["is_walking"] = not npc_state["is_walking"]
        npc_state["pacing_timer"] = random.uniform(2.0, 5.0)
        if npc_state["is_walking"]:
            npc_state["facing_right"] = random.choice([True, False])

    if npc_state["is_walking"]:
        speed = 40.0
        if npc_state["facing_right"]:
            npc_state["x"] += speed * dt
            if npc_state["x"] > 350: 
                npc_state["facing_right"] = False
        else:
            npc_state["x"] -= speed * dt
            if npc_state["x"] < 100: 
                npc_state["facing_right"] = True

    npc_y = FLOOR_Y - len(NPC_SPRITE) * PIXEL_SIZE
    renderer.draw_sprite(NPC_SPRITE, int(npc_state["x"]), npc_y, flip_h=not npc_state["facing_right"])

    if rel.name == "Family":
        kid_x = npc_state["x"] - 30
        kid_y = FLOOR_Y - len(KID_SPRITE) * PIXEL_SIZE
        renderer.draw_sprite(KID_SPRITE, int(kid_x), kid_y, flip_h=npc_state["facing_right"])
        kid2_x = npc_state["x"] + 40
        renderer.draw_sprite(KID_SPRITE, int(kid2_x), kid_y, flip_h=not npc_state["facing_right"])

    npc_state["bubble_timer"] -= dt
    npc_state["show_timer"] -= dt

    if npc_state["bubble_timer"] <= 0:
        npc_state["bubble_timer"] = random.uniform(10, 15)
        npc_state["show_timer"] = 3.0
        npc_state["current_text"] = random.choice(NPC_SPEECH)

    if npc_state["show_timer"] > 0 and npc_state.get("current_text"):
        head_x = int(npc_state["x"]) + (len(NPC_SPRITE[0]) * PIXEL_SIZE) // 2
        head_y = npc_y + 2 * PIXEL_SIZE
        draw_npc_speech_bubble(surf, npc_state["current_text"], head_x, head_y)

# ══════════════════════════════════════════════════════════════════════════════
#  TKINTER FINANCIAL DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
#  TASK 5: PROCEDURAL UI BLIP SOUND
# ══════════════════════════════════════════════════════════════════════════════

def _make_ui_blip_sound() -> Optional[pygame.mixer.Sound]:
    """
    Synthesise a short 'blip' UI navigation sound entirely in memory using
    math, struct, io, and wave — no audio files required.
    Returns a pygame.mixer.Sound object ready to .play(), or None on failure.
    """
    try:
        sample_rate = 22050
        duration    = 0.045          # seconds — short, snappy click-blip
        freq_start  = 880.0          # Hz — start pitch (A5)
        freq_end    = 1320.0         # Hz — end pitch (E6), a pleasant rise
        volume      = 0.28           # master amplitude (0.0–1.0)

        num_samples = int(sample_rate * duration)
        packed = bytearray()

        for i in range(num_samples):
            t   = i / sample_rate
            # Linear pitch glide from freq_start to freq_end
            freq = freq_start + (freq_end - freq_start) * (i / num_samples)
            # Amplitude envelope: quick attack, smooth exponential decay
            env  = math.exp(-t * 55.0)
            # Sine wave oscillator
            val  = math.sin(2.0 * math.pi * freq * t) * env * volume
            # Second harmonic for brightness
            val += math.sin(2.0 * math.pi * freq * 2.0 * t) * env * volume * 0.3
            # Clamp and quantise to 16-bit
            sample = max(-32767, min(32767, int(val * 32767)))
            # Write stereo (identical L + R channels)
            packed.extend(struct.pack('<hh', sample, sample))

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(packed)
        wav_io.seek(0)
        return pygame.mixer.Sound(file=wav_io)
    except Exception:
        return None


def launch_investment_terminal(engine):
    import tkinter as tk
    import customtkinter as ctk
    root = ctk.CTk(); root.withdraw()
    blip_sound = _make_ui_blip_sound()
    terminal = InvestmentTerminal(root, engine, blip_sound=blip_sound)
    def on_close():
        try: terminal.destroy()
        except Exception: pass
        try: root.quit()
        except Exception: pass
        try: root.destroy()
        except Exception: pass
    terminal.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

def launch_lifestyle_shop(engine):
    import customtkinter as ctk
    root = ctk.CTk(); root.withdraw()
    shop = LifestyleShop(root, engine, lambda: None)
    def on_close():
        try: shop.destroy()
        except Exception: pass
        try: root.quit()
        except Exception: pass
        try: root.destroy()
        except Exception: pass
    shop.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

# ══════════════════════════════════════════════════════════════════════════════
#  WORLD RENDERER
# ══════════════════════════════════════════════════════════════════════════════

FLOOR_Y    = SCREEN_H - 110
CEILING_Y  = 60
WALL_LEFT  = 0
WALL_RIGHT = SCREEN_W

def draw_room(surf: pygame.Surface, renderer: PixelRenderer, objects: list, flicker: MonitorFlicker, rain: RainSystem, cycle: DayNightCycle, motes: DustMotes, dt: float, engine):
    for ty in range(CEILING_Y, FLOOR_Y, PIXEL_SIZE):
        for tx in range(0, SCREEN_W, PIXEL_SIZE * 2):
            c = WL if (ty // PIXEL_SIZE) % 2 == 0 else WL2
            pygame.draw.rect(surf, c, (tx, ty, PIXEL_SIZE, PIXEL_SIZE))
            pygame.draw.rect(surf, WL2, (tx + PIXEL_SIZE, ty, PIXEL_SIZE, PIXEL_SIZE))

    pygame.draw.rect(surf, (15, 18, 35), (0, CEILING_Y - 10, SCREEN_W, 12))

    for fx in range(0, SCREEN_W, PIXEL_SIZE * 3):
        c = FL if (fx // (PIXEL_SIZE * 3)) % 2 == 0 else FL2
        pygame.draw.rect(surf, c, (fx, FLOOR_Y, PIXEL_SIZE * 3, SCREEN_H - FLOOR_Y))
        pygame.draw.rect(surf, (35, 25, 15), (fx + PIXEL_SIZE * 3 - 1, FLOOR_Y, 1, SCREEN_H))

    pygame.draw.rect(surf, (25, 18, 10), (0, FLOOR_Y, SCREEN_W, 4))

    rug_x, rug_w = 300, 500
    pygame.draw.rect(surf, RP,  (rug_x, FLOOR_Y, rug_w, PIXEL_SIZE * 3))
    pygame.draw.rect(surf, RP3, (rug_x + 8, FLOOR_Y + 4, rug_w - 16, PIXEL_SIZE))
    pygame.draw.rect(surf, RP2, (rug_x + 2, FLOOR_Y + 1, 4, PIXEL_SIZE * 3 - 2))
    pygame.draw.rect(surf, RP2, (rug_x + rug_w - 6, FLOOR_Y + 1, 4, PIXEL_SIZE * 3 - 2))

    for obj in objects: obj.draw(renderer)

    win_obj = next((o for o in objects if o.name == "window"), None)
    if win_obj:
        ws = len(WINDOW_SPRITE[0]) * PIXEL_SIZE; wh = len(WINDOW_SPRITE) * PIXEL_SIZE
        wr = pygame.Rect(win_obj.x + PIXEL_SIZE, win_obj.y + PIXEL_SIZE, ws - PIXEL_SIZE * 2, wh - PIXEL_SIZE * 2)
        rain.update(dt); rain.draw(surf)
        if cycle.hour < 6 or cycle.hour >= 20:
            night_ov = pygame.Surface((wr.w, wr.h), pygame.SRCALPHA); night_ov.fill((0, 5, 20, 160)); surf.blit(night_ov, wr.topleft)

    pc_obj = next((o for o in objects if o.name == "pc"), None)
    if pc_obj:
        mon_rect = pygame.Rect(pc_obj.x + 2 * PIXEL_SIZE, pc_obj.y + 1 * PIXEL_SIZE, 13 * PIXEL_SIZE, 7 * PIXEL_SIZE)
        flicker.update(dt, engine.player.net_worth, engine.market.market_summary); flicker.draw(surf, mon_rect)

    lamp_obj = next((o for o in objects if o.name == "lamp"), None)
    if lamp_obj:
        glow = pygame.Surface((200, 200), pygame.SRCALPHA)
        glow_alpha = 80 if (cycle.hour < 7 or cycle.hour >= 19) else 20
        pygame.draw.circle(glow, (255, 220, 80, glow_alpha), (100, 100), 100)
        surf.blit(glow, (lamp_obj.x - 60, lamp_obj.y - 60))

    motes.update(dt); motes.draw(surf)

    col = cycle.overlay_color()
    if col[3] > 0:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); ov.fill(col); surf.blit(ov, (0, 0))

def build_world() -> list:
    objects = []
    objects.append(WorldObject("window", 80, CEILING_Y + PIXEL_SIZE * 4, WINDOW_SPRITE, "", 0))
    objects.append(WorldObject("door", SCREEN_W - 160, FLOOR_Y - len(DOOR_SPRITE) * PIXEL_SIZE, DOOR_SPRITE, "", 0))
    objects.append(WorldObject("shelf", 60, FLOOR_Y - len(SHELF_SPRITE) * PIXEL_SIZE, SHELF_SPRITE, "", 0))
    objects.append(WorldObject("bed", 250, FLOOR_Y - len(BED_SPRITE) * PIXEL_SIZE + PIXEL_SIZE * 2, BED_SPRITE, "Sleep (advance month)", 90))
    objects.append(WorldObject("tv", 600, FLOOR_Y - len(TV_SPRITE) * PIXEL_SIZE - 80, TV_SPRITE, "Watch TV (Lifestyle Shop)", 100))
    objects.append(WorldObject("pc", 900, FLOOR_Y - len(PC_SPRITE) * PIXEL_SIZE + PIXEL_SIZE * 2, PC_SPRITE, "Use PC (Investment Terminal)", 100))
    objects.append(WorldObject("lamp", 760, FLOOR_Y - len(LAMP_SPRITE) * PIXEL_SIZE, LAMP_SPRITE, "", 0))
    objects.append(WorldObject("plant", 200, FLOOR_Y - len(PLANT_SPRITE) * PIXEL_SIZE, PLANT_SPRITE, "", 0))
    return objects

# ══════════════════════════════════════════════════════════════════════════════
#  FINANCIAL ENGINE & UI CLASSES
# ══════════════════════════════════════════════════════════════════════════════

_ctk_available = False
try:
    import customtkinter as _ctk
    import tkinter as _tk
    from tkinter import messagebox as _mb
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as _FigCanvas
    from matplotlib.figure import Figure as _Figure
    _ctk_available = True
except ImportError: pass

_BG_DEEP  = "#0a0c14"; _BG_MID = "#0f1220"; _BG_CARD = "#141828"; _BG_HOVER = "#1c2235"
_ACCENT   = "#4f9cf9"; _ACCENT2 = "#7c5cbf"; _GREEN   = "#2ecc71"; _RED     = "#e74c3c"
_GOLD     = "#f1c40f"; _AMBER   = "#e67e22"; _WHITE   = "#e8eaf6"; _DIM     = "#5a6480"; _BORDER  = "#1e2540"
_MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

class _AssetType(Enum): STOCK="Stock"; ETF="ETF"; BOND="Bond"; GOLD="Gold"

@dataclass
class _MarketAsset:
    ticker: str; name: str; asset_type: _AssetType
    price: float; base_price: float; volatility: float; trend: float
    dividend: float = 0.0; description: str = ""
    price_history: List[float] = field(default_factory=list)
    crash_prob: float = 0.0; moon_prob: float = 0.0
    def __post_init__(self): self.price_history = [self.price]
    
    def update_price(self, mood: float, recession: bool) -> float:
        # ── TASK 1: BOND DEATH-SPIRAL FIX ─────────────────────────────────────
        # Bonds are isolated entirely from standard drift/recession logic.
        # They mean-revert to base_price with low noise — safe, boring, reliable.
        if self.asset_type == _AssetType.BOND:
            self.price += (self.base_price - self.price) * 0.05
            self.price += random.gauss(0, self.volatility * 0.3) * self.price
            # Bonds pay their coupon but do NOT get an ex-dividend price drop
            self.price = max(0.50, round(self.price, 2))
            self.price_history.append(self.price)
            return self.price

        # ── TASK 2: APOCALYPTIC RECESSION FIX ────────────────────────────────
        # Old value was e.g. -0.08 which produced ~60%+ annual drawdowns.
        # New value is a realistic ~15-18% annualised drag.
        mood_adj = mood * 0.005
        rec_adj  = -0.015 if recession else 0.0
        vol      = self.volatility * (1.6 if recession else 1.0)

        # Gold is a safe-haven: inverse mood, benefits slightly in recessions
        if self.asset_type == _AssetType.GOLD:
            mood_adj *= -0.5
            rec_adj   = 0.02 if recession else 0.0

        drift = self.trend + mood_adj + rec_adj
        shock = random.gauss(0, vol)

        if random.random() < self.crash_prob: shock -= random.uniform(0.15, 0.40)
        if random.random() < self.moon_prob:  shock += random.uniform(0.15, 0.50)

        # ETF bounce: prevent total collapse below 50% of base
        if self.asset_type == _AssetType.ETF and self.price < self.base_price * 0.5:
            drift += 0.02

        # ── TASK 3: STOCK GRAVITY & BOUNCE ───────────────────────────────────
        if self.asset_type == _AssetType.STOCK:
            growth_ratio = self.price / self.base_price
            # Logarithmic gravity: the higher it flies, the more drag applied
            if growth_ratio > 1.0:
                gravity_drag = math.log(growth_ratio) * 0.008
                drift -= gravity_drag
            # Anti-flatline bounce: if stock has crashed to <20% of base, nudge up
            elif growth_ratio < 0.2:
                drift += 0.015

        self.price = max(1.00, self.price * math.exp(drift + shock))

        # ── TASK 4: MAGIC-MONEY DIVIDEND FIX (ex-div price drop) ─────────────
        # Stocks and ETFs drop by the dividend percentage on payout day,
        # preventing shares from accumulating value AND paying out cash.
        if self.dividend > 0 and self.asset_type in (_AssetType.STOCK, _AssetType.ETF):
            self.price = self.price * (1.0 - self.dividend)

        self.price = round(self.price, 2)
        self.price_history.append(self.price)
        return self.price
        
    @property
    def change_1m(self): return 0.0 if len(self.price_history)<2 else (self.price_history[-1]/self.price_history[-2]-1)*100
    @property
    def change_all(self): return 0.0 if len(self.price_history)<2 else (self.price_history[-1]/self.price_history[0]-1)*100

@dataclass
class _Position:
    ticker: str; shares: float; avg_cost: float
    @property
    def total_cost(self): return self.shares * self.avg_cost
    def current_value(self, price): return self.shares * price
    def pnl_pct(self, price): return 0.0 if self.avg_cost==0 else (price/self.avg_cost-1)*100

@dataclass
class _LifestyleOption:
    name: str; category: str; monthly_cost: float; happiness: int
    description: str; icon: str; requires_net_worth: float = 0.0; one_time_cost: float = 0.0

LIFESTYLE_OPTIONS = [
    _LifestyleOption("Studio Apartment","housing",800,5,"Tiny but functional.","🏠"),
    _LifestyleOption("1BR Apartment","housing",1400,15,"More space, better neighborhood.","🏢",10000),
    _LifestyleOption("2BR Apartment","housing",2000,22,"Comfortable city living.","🏙️",30000),
    _LifestyleOption("Own 2BR Condo","housing",200,35,"Fully owned. Just paying HOA & Taxes.","🔑",100000,250000),
    _LifestyleOption("Own Luxury House","housing",600,50,"Fully owned massive estate.","🏰",500000,950000),
    _LifestyleOption("No Car (Bus)","transport",0,0,"Free but slow.","🚌"),
    _LifestyleOption("Used Hatchback","transport",180,10,"Reliable and affordable.","🚗",5000,6000),
    _LifestyleOption("Mid-Range Sedan","transport",350,18,"Comfortable commute.","🚘",20000,18000),
    _LifestyleOption("Luxury SUV","transport",700,25,"Status symbol.","🚙",80000,55000),
    _LifestyleOption("Sports Car","transport",950,30,"Pure driving pleasure.","🏎️",150000,90000),
    _LifestyleOption("Basic Meals","personal",300,0,"Cook at home.","🍜"),
    _LifestyleOption("Dining Out","personal",600,10,"Restaurant meals and cafes.","🍽️"),
    _LifestyleOption("Fine Dining","personal",1200,18,"Best restaurants in town.","🥂",50000),
    _LifestyleOption("Personal Trainer","personal",300,12,"Health is wealth.","💪",15000),
    _LifestyleOption("Therapist","personal",400,15,"Mental health first.","🧠",10000),
    _LifestyleOption("Vacation Fund","personal",400,20,"$400/mo vacation savings.","✈️",20000),
    _LifestyleOption("Single","relationship",0,0,"Flying solo.","👤"),
    _LifestyleOption("Partner","relationship",500,20,"Love costs money, worth every cent.","💑",5000),
    _LifestyleOption("Family","relationship",1500,15,"Kids are expensive but priceless.","👨‍👩‍👧",30000),
]

CAREER_LEVELS = [
    {"title":"Intern","income":2800,"req_net":0}, {"title":"Junior Analyst","income":4200,"req_net":5000},
    {"title":"Analyst","income":5800,"req_net":20000}, {"title":"Senior Analyst","income":8000,"req_net":60000},
    {"title":"Manager","income":11000,"req_net":150000}, {"title":"Director","income":16000,"req_net":400000},
    {"title":"VP","income":24000,"req_net":1000000}, {"title":"C-Suite","income":40000,"req_net":3000000},
]

RANDOM_EVENTS = [
    ("bonus","💰 Performance Bonus!","Your boss recognises your work.",5000,0),
    ("medical","🏥 Medical Emergency!","Unexpected hospital visit.",-3000,-10),
    ("car_broke","🔧 Car Breakdown!","Major repair needed.",-1500,-5),
    ("windfall","🎲 Tax Refund!","Bigger refund than expected.",2500,5),
    ("raise","📈 Salary Increase!","Negotiated a small raise. +$400/mo.",0,8),
    ("friend","🤝 Friend's Tip!","A friend's stock tip pays off.",1500,5),
    ("promotion","🏅 Promoted!","New responsibilities, new title.",3000,15),
]

class MarketEngine:
    def __init__(self):
        self.month=0; self.mood=0.0; self.recession=False
        self.recession_months_left=0; self.bull_streak=0; self.bear_streak=0
        self.assets: Dict[str, _MarketAsset] = {}
        # FIX 5: Crash and Moon probabilities shifted from 1.5% to 0.15% per month. 
        # Bond trends set to 0.0.
        raw = [
            _MarketAsset("TNVA","TechNova Inc.",_AssetType.STOCK,142.0,142.0,0.12,0.015,0.0,"AI-driven cloud platform. The next trillion dollar company?",0.0015,0.0020),
            _MarketAsset("STRM","Stellar Motors",_AssetType.STOCK,78.0,78.0,0.08,0.007,0.0,"EV manufacturer. Volatile but promising.",0.0008,0.0008),
            _MarketAsset("MXPW","MaxPower Energy",_AssetType.STOCK,55.0,55.0,0.07,0.005,0.012,"Renewable energy utility. Pays small dividend.",0.0005,0.0004),
            _MarketAsset("HLTH","VitaHealth Group",_AssetType.STOCK,91.0,91.0,0.06,0.006,0.008,"Healthcare conglomerate. Defensive stock.",0.0004,0.0003),
            _MarketAsset("BNKR","First National Bank",_AssetType.STOCK,63.0,63.0,0.065,0.005,0.015,"Major commercial bank. Dividend payer.",0.0006,0.0003),
            _MarketAsset("G500","Global 500 Index",_AssetType.ETF,200.0,200.0,0.045,0.008,0.004,"Broad market index. The bedrock of any portfolio.",0.0002,0.0001),
            _MarketAsset("TECH","TechBlast ETF",_AssetType.ETF,115.0,115.0,0.065,0.009,0.002,"Tech sector ETF. Higher return, higher vol.",0.0003,0.0002),
            _MarketAsset("DIVD","Dividend Kings ETF",_AssetType.ETF,88.0,88.0,0.030,0.005,0.009,"High-dividend ETF. Monthly income stream.",0.0001,0.0001),
            _MarketAsset("GOV10","Gov Yield 10Y",_AssetType.BOND,100.0,100.0,0.008,0.0,0.004,"10-year government bond. Safe, boring, reliable."),
            _MarketAsset("CORP","Corp Bond Index",_AssetType.BOND,98.0,98.0,0.012,0.0,0.005,"Investment-grade corporate bonds. Slightly better yield."),
            _MarketAsset("XAU","Gold Spot",_AssetType.GOLD,1920.0,1920.0,0.035,0.002,0.0,"Physical gold. Inflation hedge, crisis safe-haven.",0.0003,0.0002),
        ]
        for a in raw: self.assets[a.ticker] = a

    def advance_month(self) -> dict:
        self.month += 1; events = {}
        if self.recession:
            self.recession_months_left -= 1
            if self.recession_months_left <= 0:
                self.recession = False
                events["recession_end"] = True
                self.bear_streak = 0
                self.mood = 0.0
            else:
                self.mood = random.gauss(-0.4, 0.25)
        else:
            self.mood += random.gauss(0, 0.3) - (self.mood * 0.2)
            self.mood  = max(-1.0, min(1.0, self.mood))
            if self.mood > 0.3: self.bull_streak+=1; self.bear_streak=0
            elif self.mood < -0.3: self.bear_streak+=1; self.bull_streak=0
            else: self.bull_streak=max(0,self.bull_streak-1); self.bear_streak=max(0,self.bear_streak-1)
            if self.bear_streak>=4 and random.random()<0.35:
                self.recession=True; self.recession_months_left=random.randint(4,10)
                events["recession_start"]=True

        for asset in self.assets.values(): asset.update_price(self.mood, self.recession)
        events["mood"]=self.mood; events["recession"]=self.recession
        return events

    @property
    def market_summary(self) -> str:
        if self.recession: return "🔴 RECESSION"
        if self.mood > 0.5: return "🟢 BULL MARKET"
        if self.mood > 0.1: return "🟡 BULL TREND"
        if self.mood < -0.5: return "🔴 BEAR MARKET"
        if self.mood < -0.1: return "🟡 BEAR TREND"
        return "⚪ NEUTRAL"

class Player:
    def __init__(self):
        self.name="Player"; self.cash=5000.0; self.happiness=65
        self.month=0; self.year=2025; self.career_level=0
        self.income=CAREER_LEVELS[0]["income"]; self.base_expenses=800.0
        self.lifestyle: Dict[str, _LifestyleOption] = {
            "housing": LIFESTYLE_OPTIONS[0],
            "transport": LIFESTYLE_OPTIONS[5],
            "personal": LIFESTYLE_OPTIONS[10],
            "relationship": LIFESTYLE_OPTIONS[16],
        }
        self.portfolio: Dict[str, _Position] = {}; self.dividend_income=0.0
        self.net_worth_history: List[float]=[self.cash]; self.happiness_history: List[int]=[self.happiness]
        self.cash_history: List[float]=[self.cash]; self.event_log: List[str]=[]
        self.months_low_happiness=0; self._price_cache={}
        self.drip_enabled = False # New DRIP State

    @property
    def monthly_expenses(self): return sum(o.monthly_cost for o in self.lifestyle.values())
    @property
    def monthly_net(self): return self.income - self.monthly_expenses
    @property
    def portfolio_value(self): return sum(p.current_value(self._price_cache.get(t,0.0)) for t,p in self.portfolio.items())
    @property
    def net_worth(self): return self.cash + self.portfolio_value

    def set_price_cache(self, prices): self._price_cache = prices

    def buy(self, ticker, price, amount_dollars):
        shares = amount_dollars / price
        if amount_dollars > self.cash: return False, "Insufficient cash."
        if amount_dollars < 1: return False, "Minimum order: $1."
        cost = shares * price; self.cash -= cost
        if ticker in self.portfolio:
            pos=self.portfolio[ticker]; ts=pos.shares+shares
            pos.avg_cost=(pos.total_cost+cost)/ts; pos.shares=ts
        else: self.portfolio[ticker]=_Position(ticker,shares,price)
        return True, f"Bought {shares:.4f} shares of {ticker} @ ${price:.2f}"

    def sell(self, ticker, price, shares):
        if ticker not in self.portfolio: return False, "You don't own this asset."
        pos=self.portfolio[ticker]
        if shares > pos.shares - 0.0001: shares = pos.shares # Math Fix: Clean clear
        if shares > pos.shares + 1e-9: return False, f"You only own {pos.shares:.4f} shares."
        proceeds=shares*price; self.cash+=proceeds; pos.shares-=shares
        if pos.shares<1e-9: del self.portfolio[ticker]
        return True, f"Sold {shares:.4f} shares of {ticker} @ ${price:.2f} → +${proceeds:,.2f}"

    def advance_month(self, market: MarketEngine) -> List[str]:
        self.month+=1
        if self.month>12: self.month=1; self.year+=1
        self.set_price_cache({tk:a.price for tk,a in market.assets.items()}); messages=[]
        net=self.monthly_net; self.cash+=net
        messages.append(f"💵 Salary: +${self.income:,.0f}  |  Expenses: -${self.monthly_expenses:,.0f}  |  Net: ${net:+,.0f}")
        
        # --- NEW DRIP LOGIC ---
        div_total = 0.0
        for ticker, pos in list(self.portfolio.items()):
            asset = market.assets.get(ticker)
            if asset and asset.dividend > 0:
                div = pos.current_value(asset.price) * asset.dividend
                div_total += div
                if self.drip_enabled:
                    shares_bought = div / asset.price
                    pos.avg_cost = ((pos.shares * pos.avg_cost) + div) / (pos.shares + shares_bought)
                    pos.shares += shares_bought
                    messages.append(f"🔄 DRIP: Reinvested ${div:.2f} into {ticker}")
        
        if div_total > 0 and not self.drip_enabled:
            self.dividend_income = div_total
            self.cash += div_total
            messages.append(f"💸 Dividends: +${div_total:,.2f}")
        # ----------------------
        
        base_hap=min(100,sum(o.happiness for o in self.lifestyle.values()))
        self.happiness=max(0,min(100,int(self.happiness*0.9+base_hap*0.1)))
        if self.cash<0: self.happiness=max(0,self.happiness-8); messages.append("⚠️ Negative cash! Happiness -8")
        if self.happiness<20:
            self.months_low_happiness+=1
            if self.months_low_happiness>=2:
                penalty=random.choice(["job_loss","medical_crisis"])
                if penalty=="job_loss" and self.career_level>0:
                    self.career_level-=1; self.income=CAREER_LEVELS[self.career_level]["income"]
                    messages.append("😞 Burnout! Demoted. Income reduced.")
                else:
                    bill=random.randint(2000,6000); self.cash-=bill
                    messages.append(f"😷 Stress illness! Medical bill: -${bill:,}")
                self.months_low_happiness=0
        else: self.months_low_happiness=0
        nw=self.net_worth
        for i in range(len(CAREER_LEVELS)-1,-1,-1):
            if nw>=CAREER_LEVELS[i]["req_net"] and i>self.career_level:
                self.career_level=i; self.income=CAREER_LEVELS[i]["income"]
                messages.append(f"🏅 Career: {CAREER_LEVELS[i]['title']}! Income: ${self.income:,}/mo"); break
        if random.random()<0.12:
            ev=random.choice(RANDOM_EVENTS); ev_id,title,desc,cash_delta,hap_delta=ev
            if ev_id=="raise": self.income+=400
            else: self.cash+=cash_delta
            self.happiness=max(0,min(100,self.happiness+hap_delta))
            msg=f"{title} {desc}" + (f" ${cash_delta:+,}" if cash_delta!=0 else "")
            messages.append(msg); self.event_log.insert(0,f"[{self.year} {_MONTHS[self.month-1]}] {msg}")
        self.net_worth_history.append(self.net_worth); self.happiness_history.append(self.happiness); self.cash_history.append(self.cash)
        return messages

class GameEngine:
    def __init__(self):
        self.market=MarketEngine(); self.player=Player()
        self.player.set_price_cache({tk:a.price for tk,a in self.market.assets.items()})
        self.game_over=False; self.total_months=0

    def advance(self) -> dict:
        self.total_months+=1
        market_events=self.market.advance_month()
        self.player.set_price_cache({tk:a.price for tk,a in self.market.assets.items()})
        life_messages=self.player.advance_month(self.market)
        
        # Extended Lifespan!
        if self.total_months >= 12 * 75: 
            self.game_over = True
        elif self.player.cash < -50000 and self.player.portfolio_value < 1000: 
            self.game_over = True

        # TASK 6: Auto-export CSV post-mortem the first time game_over is set
        if self.game_over and not getattr(self, "_csv_exported", False):
            self._csv_exported = True
            try:
                csv_path = export_postmortem_csv(self)
                print(f"[Post-Mortem] CSV report saved → {csv_path}")
            except Exception as e:
                print(f"[Post-Mortem] CSV export failed: {e}")
            
        return {"market":market_events,"messages":life_messages,"game_over":self.game_over}

    def date_str(self) -> str:
        m=self.player.month; y=self.player.year
        return f"{_MONTHS[m-1 if m>0 else 0]} {y}"

    def save_game(self, filename="save.json"):
        data = {
            "player": {
                "cash": self.player.cash, "happiness": self.player.happiness,
                "month": self.player.month, "year": self.player.year,
                "career_level": self.player.career_level,
                "portfolio": {k: {"shares": v.shares, "avg_cost": v.avg_cost} for k,v in self.player.portfolio.items()},
                "lifestyle": {k: v.name for k,v in self.player.lifestyle.items()},
                "drip": self.player.drip_enabled
            },
            "market": {
                "month": self.market.month, "mood": self.market.mood, "recession": self.market.recession,
                "assets": {k: {"price": a.price, "history": a.price_history} for k,a in self.market.assets.items()}
            }
        }
        with open(filename, "w") as f: json.dump(data, f)

    def load_game(self, filename="save.json"):
        if not os.path.exists(filename): return False
        with open(filename, "r") as f: data = json.load(f)
        pdata = data["player"]
        self.player.cash = pdata["cash"]; self.player.happiness = pdata["happiness"]
        self.player.month = pdata["month"]; self.player.year = pdata["year"]
        self.player.career_level = pdata["career_level"]
        self.player.drip_enabled = pdata.get("drip", False)
        self.player.portfolio.clear()
        for k,v in pdata["portfolio"].items(): self.player.portfolio[k] = _Position(k, v["shares"], v["avg_cost"])
        for k,vname in pdata["lifestyle"].items():
            opt = next((o for o in LIFESTYLE_OPTIONS if o.category == k and o.name == vname), None)
            if opt: self.player.lifestyle[k] = opt
        mdata = data["market"]
        self.market.month = mdata["month"]; self.market.mood = mdata["mood"]; self.market.recession = mdata["recession"]
        for k,v in mdata["assets"].items():
            if k in self.market.assets:
                self.market.assets[k].price = v["price"]
                self.market.assets[k].price_history = v["history"]
        self.player.set_price_cache({tk:a.price for tk,a in self.market.assets.items()})
        return True

import csv as _csv

# ══════════════════════════════════════════════════════════════════════════════
#  TASK 6: CSV POST-MORTEM EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def export_postmortem_csv(engine: "GameEngine", filename: str = "postmortem.csv") -> str:
    """
    Write a structured post-mortem CSV report when the game ends.

    Sections written to the file:
      1. LIFE SUMMARY       — Final Age, Total Wealth, Career, Peak Happiness
      2. FINAL PORTFOLIO    — per-holding: Shares, Avg Cost, Current Value, P&L
      3. NET WORTH TIMELINE — one row per month so the player can chart growth

    Returns the absolute path of the file written.
    """
    p  = engine.player
    m  = engine.market
    age = 25 + (engine.total_months // 12)
    path = os.path.abspath(filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.writer(f)

        # ── Section 1: Life Summary ─────────────────────────────────────────
        w.writerow(["=== LIFE SUMMARY ==="])
        w.writerow(["Field", "Value"])
        w.writerow(["Final Age",        age])
        w.writerow(["Total Wealth ($)", round(p.net_worth, 2)])
        w.writerow(["Cash ($)",         round(p.cash, 2)])
        w.writerow(["Portfolio Value ($)", round(p.portfolio_value, 2)])
        w.writerow(["Career Title",     CAREER_LEVELS[p.career_level]["title"]])
        w.writerow(["Monthly Income ($)", p.income])
        w.writerow(["Monthly Expenses ($)", round(p.monthly_expenses, 2)])
        w.writerow(["Peak Happiness",   max(p.happiness_history) if p.happiness_history else p.happiness])
        w.writerow(["Final Happiness",  p.happiness])
        w.writerow(["Total Months Played", engine.total_months])
        w.writerow([])

        # ── Section 2: Final Portfolio ──────────────────────────────────────
        w.writerow(["=== FINAL PORTFOLIO ==="])
        w.writerow(["Ticker", "Asset Name", "Type", "Shares", "Avg Cost ($)",
                    "Current Price ($)", "Current Value ($)", "Total Cost ($)",
                    "P&L ($)", "P&L (%)"])
        if p.portfolio:
            for ticker, pos in p.portfolio.items():
                asset        = m.assets.get(ticker)
                cur_price    = asset.price if asset else 0.0
                asset_name   = asset.name  if asset else ticker
                asset_type   = asset.asset_type.value if asset else "—"
                cur_value    = pos.current_value(cur_price)
                total_cost   = pos.total_cost
                pnl_dollars  = cur_value - total_cost
                pnl_pct      = pos.pnl_pct(cur_price)
                w.writerow([
                    ticker,
                    asset_name,
                    asset_type,
                    round(pos.shares, 6),
                    round(pos.avg_cost, 4),
                    round(cur_price, 2),
                    round(cur_value, 2),
                    round(total_cost, 2),
                    round(pnl_dollars, 2),
                    round(pnl_pct, 2),
                ])
        else:
            w.writerow(["(No positions held at game end)"])
        w.writerow([])

        # ── Section 3: Net Worth Timeline ───────────────────────────────────
        w.writerow(["=== NET WORTH TIMELINE ==="])
        w.writerow(["Month #", "Calendar Date", "Net Worth ($)", "Cash ($)",
                    "Happiness"])
        start_year  = 2025
        start_month = 1
        cash_hist    = p.cash_history
        hap_hist     = p.happiness_history
        for i, nw in enumerate(p.net_worth_history):
            # Compute the calendar month for this entry
            abs_month   = start_month + i - 1
            cal_year    = start_year  + abs_month // 12
            cal_month   = (abs_month  % 12) + 1
            date_str    = f"{_MONTHS[cal_month - 1]} {cal_year}"
            cash_val    = cash_hist[i]  if i < len(cash_hist)  else ""
            hap_val     = hap_hist[i]   if i < len(hap_hist)   else ""
            w.writerow([i, date_str, round(nw, 2), round(cash_val, 2) if cash_val != "" else "", hap_val])

    return path
    fig.patch.set_facecolor(_BG_CARD); ax.set_facecolor(_BG_MID)
    ax.tick_params(colors=_DIM,labelsize=8)
    for sp in ["bottom","left"]: ax.spines[sp].set_color(_BORDER)
    for sp in ["top","right"]: ax.spines[sp].set_visible(False)
    ax.yaxis.label.set_color(_DIM); ax.xaxis.label.set_color(_DIM)
    ax.title.set_color(_WHITE); ax.grid(True,color=_BORDER,linewidth=0.5,linestyle="--",alpha=0.6)

def _apply_chart_theme(ax, fig):
    fig.patch.set_facecolor(_BG_CARD)
    ax.set_facecolor(_BG_MID)
    ax.tick_params(colors=_DIM, labelsize=8)
    for sp in ["bottom", "left"]: 
        ax.spines[sp].set_color(_BORDER)
    for sp in ["top", "right"]: 
        ax.spines[sp].set_visible(False)
    ax.yaxis.label.set_color(_DIM)
    ax.xaxis.label.set_color(_DIM)
    ax.title.set_color(_WHITE)
    ax.grid(True, color=_BORDER, linewidth=0.5, linestyle="--", alpha=0.6)
    
class InvestmentTerminal:
    def __init__(self, master, engine: GameEngine, blip_sound: Optional[pygame.mixer.Sound] = None):
        if not _ctk_available: raise RuntimeError("customtkinter not installed.")
        self._root = master
        self.engine = engine; self.market = engine.market; self.player = engine.player
        self._blip_sound = blip_sound          # TASK 5: procedural UI blip
        self.win = _ctk.CTkToplevel(master)
        self.win.title("💹 Investment Terminal")
        self.win.geometry("1200x780")
        self.win.configure(fg_color=_BG_DEEP)
        self.win.resizable(True, True)
        self.selected_ticker = _ctk.StringVar(value="G500")
        self.buy_amount      = _ctk.StringVar(value="500")
        self.sell_shares     = _ctk.StringVar(value="")
        self.filter_type     = _ctk.StringVar(value="All")
        self.chart_timeframe = _ctk.StringVar(value="MAX")
        self.displayed_tickers = []
        self._build_ui()
        self.refresh()
        
        # Keyboard Navigation
        self.win.bind("<Up>", self._nav_up)
        self.win.bind("<Down>", self._nav_down)
        self.win.bind("<Return>", lambda e: self._do_buy())

    def _play_blip(self):
        """Play the procedural navigation blip if available (TASK 5)."""
        if self._blip_sound:
            try:
                # Use a dedicated mixer channel so it never clashes with the radio
                ch = pygame.mixer.Channel(1)
                ch.set_volume(0.4)
                ch.play(self._blip_sound)
            except Exception:
                pass

    def _nav_up(self, event):
        if not self.displayed_tickers: return
        current = self.selected_ticker.get()
        if current in self.displayed_tickers:
            idx = self.displayed_tickers.index(current)
            if idx > 0:
                self._select(self.displayed_tickers[idx - 1])
                self._play_blip()           # TASK 5: sound on navigation

    def _nav_down(self, event):
        if not self.displayed_tickers: return
        current = self.selected_ticker.get()
        if current in self.displayed_tickers:
            idx = self.displayed_tickers.index(current)
            if idx < len(self.displayed_tickers) - 1:
                self._select(self.displayed_tickers[idx + 1])
                self._play_blip()           # TASK 5: sound on navigation

    def winfo_exists(self): return self.win.winfo_exists()
    def protocol(self, *a, **kw): self.win.protocol(*a, **kw)
    def destroy(self): self.win.destroy()
    def focus(self): self.win.focus()

    def _build_ui(self):
        hdr = _ctk.CTkFrame(self.win, fg_color=_BG_MID, height=52)
        hdr.pack(fill="x")
        _ctk.CTkLabel(hdr, text="💹  INVESTMENT TERMINAL", font=_ctk.CTkFont("Segoe UI",18,"bold"), text_color=_ACCENT).pack(side="left",padx=20,pady=14)
        self.market_badge = _ctk.CTkLabel(hdr, text="", font=_ctk.CTkFont("Segoe UI",13,"bold"), text_color=_GREEN)
        self.market_badge.pack(side="right", padx=20)
        body = _ctk.CTkFrame(self.win, fg_color=_BG_DEEP)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)
        left = _ctk.CTkFrame(body, fg_color=_BG_DEEP)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        left.rowconfigure(0, weight=3); left.rowconfigure(1, weight=1); left.columnconfigure(0, weight=1)
        self._build_chart(left); self._build_trade_panel(left)
        right = _ctk.CTkFrame(body, fg_color=_BG_DEEP)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1); right.rowconfigure(1, weight=1); right.columnconfigure(0, weight=1)
        self._build_asset_list(right); self._build_portfolio(right)

    def _build_chart(self, parent):
        card = _ctk.CTkFrame(parent, fg_color=_BG_CARD, corner_radius=8)
        card.grid(row=0, column=0, sticky="nsew", pady=(0,4))
        card.rowconfigure(1, weight=1); card.columnconfigure(0, weight=1)
        tf_row = _ctk.CTkFrame(card, fg_color=_BG_CARD)
        tf_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(6,0))
        _ctk.CTkLabel(tf_row, text="Timeframe:", font=_ctk.CTkFont("Segoe UI", 12), text_color=_DIM).pack(side="left", padx=(4,6))
        for tf in ("1Y", "5Y", "MAX"):
            _ctk.CTkButton(
                tf_row, text=tf, width=42, height=24,
                font=_ctk.CTkFont("Segoe UI", 12, "bold"),
                fg_color=_ACCENT if self.chart_timeframe.get()==tf else _BG_MID,
                hover_color=_ACCENT2,
                command=lambda t=tf: [self.chart_timeframe.set(t), self._update_chart()]
            ).pack(side="left", padx=2)
        self.fig = _Figure(figsize=(7,3.5), dpi=96)
        self.ax  = self.fig.add_subplot(111)
        _apply_chart_theme(self.ax, self.fig)
        self.fig.tight_layout(pad=1.5)
        self.canvas = _FigCanvas(self.fig, master=card)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

    def _update_chart(self):
        ticker = self.selected_ticker.get(); asset = self.market.assets.get(ticker)
        if not asset: return
        self.ax.clear(); _apply_chart_theme(self.ax, self.fig)
        full_hist = asset.price_history
        tf = self.chart_timeframe.get()
        if tf == "1Y":   hist = full_hist[-12:]  if len(full_hist) > 12  else full_hist
        elif tf == "5Y": hist = full_hist[-60:]  if len(full_hist) > 60  else full_hist
        else:            hist = full_hist
        xs = list(range(len(hist)))
        color = _GREEN if hist[-1] >= hist[0] else _RED
        self.ax.plot(xs, hist, color=color, linewidth=1.8, zorder=3)
        self.ax.fill_between(xs, hist, min(hist)*0.98, color=color, alpha=0.12)
        if xs:
            self.ax.set_xlim(0, max(1, xs[-1]))
            y_min = min(hist) * 0.97; y_max = max(hist) * 1.03
            self.ax.set_ylim(y_min, y_max)
        if ticker in self.player.portfolio:
            pos = self.player.portfolio[ticker]
            self.ax.axhline(pos.avg_cost, color=_GOLD, linewidth=1, linestyle="--", alpha=0.7, label=f"Avg Cost ${pos.avg_cost:.2f}")
            self.ax.legend(facecolor=_BG_CARD, edgecolor=_BORDER, labelcolor=_GOLD, fontsize=8)
            
        cp = (hist[-1] / hist[0] - 1) * 100 if len(hist) > 1 and hist[0] > 0 else 0.0
        sign = "+" if cp>=0 else ""
        tf_label = {"1Y":"1 Year","5Y":"5 Years","MAX":"All Time"}[tf]
        self.ax.set_title(f"{asset.name}  ({ticker})   ${asset.price:.2f}   {sign}{cp:.1f}% [{tf_label}]", fontsize=12, color=_WHITE, pad=6)
        self.ax.set_xlabel("Months", fontsize=10); self.ax.set_ylabel("Price ($)", fontsize=10)
        self.fig.tight_layout(pad=1.5); self.canvas.draw_idle()

    def _build_trade_panel(self, parent):
        card = _ctk.CTkFrame(parent, fg_color=_BG_CARD, corner_radius=8)
        card.grid(row=1, column=0, sticky="nsew")
        info_row = _ctk.CTkFrame(card, fg_color=_BG_CARD)
        info_row.pack(fill="x", padx=12, pady=(10,4))
        self.lbl_asset_name  = _ctk.CTkLabel(info_row, text="—", font=_ctk.CTkFont("Segoe UI",15,"bold"), text_color=_ACCENT)
        self.lbl_asset_name.pack(side="left")
        self.lbl_asset_price = _ctk.CTkLabel(info_row, text="", font=_ctk.CTkFont("Segoe UI",14), text_color=_WHITE)
        self.lbl_asset_price.pack(side="left", padx=16)
        self.lbl_asset_desc  = _ctk.CTkLabel(info_row, text="", font=_ctk.CTkFont("Segoe UI",12), text_color=_DIM)
        self.lbl_asset_desc.pack(side="left")
        buy_row = _ctk.CTkFrame(card, fg_color=_BG_CARD)
        buy_row.pack(fill="x", padx=12, pady=4)
        _ctk.CTkLabel(buy_row,text="Buy $:",font=_ctk.CTkFont("Segoe UI",13),text_color=_DIM,width=65).pack(side="left")
        _ctk.CTkEntry(buy_row,textvariable=self.buy_amount,width=100,font=_ctk.CTkFont("Segoe UI",13), fg_color=_BG_MID,border_color=_BORDER).pack(side="left",padx=6)
        for amt in (100,500,1000,5000):
            _ctk.CTkButton(buy_row,text=f"${amt:,}",width=56,height=26,font=_ctk.CTkFont("Segoe UI",11), fg_color=_BG_MID,hover_color=_ACCENT, command=lambda a=amt:self.buy_amount.set(str(a))).pack(side="left",padx=2)
        _ctk.CTkButton(buy_row,text="BUY ▲",width=80,height=28,font=_ctk.CTkFont("Segoe UI",13,"bold"), fg_color=_GREEN,hover_color="#1a9e52",text_color=_BG_DEEP, command=self._do_buy).pack(side="left",padx=8)
        sell_row = _ctk.CTkFrame(card, fg_color=_BG_CARD)
        sell_row.pack(fill="x", padx=12, pady=4)
        _ctk.CTkLabel(sell_row,text="Sell shares:",font=_ctk.CTkFont("Segoe UI",13),text_color=_DIM,width=80).pack(side="left")
        _ctk.CTkEntry(sell_row,textvariable=self.sell_shares,width=100,font=_ctk.CTkFont("Segoe UI",13), fg_color=_BG_MID,border_color=_BORDER).pack(side="left",padx=6)
        for lbl,frac in [("SELL 25%",0.25),("SELL 50%",0.50),("SELL ALL",1.0)]:
            _ctk.CTkButton(sell_row,text=lbl,width=75,height=26,font=_ctk.CTkFont("Segoe UI",11), fg_color=_BG_MID,hover_color=_RED, command=lambda f=frac:self._quick_sell(f)).pack(side="left",padx=2)
        _ctk.CTkButton(sell_row,text="SELL ▼",width=80,height=28,font=_ctk.CTkFont("Segoe UI",13,"bold"), fg_color=_RED,hover_color="#a01020",command=self._do_sell).pack(side="left",padx=8)
        
        # DRIP Toggle
        drip_row = _ctk.CTkFrame(card, fg_color=_BG_CARD)
        drip_row.pack(fill="x", padx=12, pady=(0,4))
        self.drip_switch = _ctk.CTkSwitch(
            drip_row, text="Auto-Reinvest Dividends (DRIP)", 
            font=_ctk.CTkFont("Segoe UI", 12, "bold"),
            progress_color=_GREEN,
            command=self._toggle_drip
        )
        self.drip_switch.pack(side="left")
        if self.player.drip_enabled: self.drip_switch.select()

        self.trade_status = _ctk.CTkLabel(card,text="Select an asset and enter an amount.", font=_ctk.CTkFont("Segoe UI",12),text_color=_DIM)
        self.trade_status.pack(padx=12,pady=(2,8),anchor="w")

    def _toggle_drip(self):
        self.player.drip_enabled = bool(self.drip_switch.get())
        state = "ON" if self.player.drip_enabled else "OFF"
        self.trade_status.configure(text=f"DRIP turned {state}.", text_color=_GOLD)

    def _do_buy(self):
        ticker=self.selected_ticker.get(); asset=self.market.assets.get(ticker)
        if not asset: return
        try: amount=float(self.buy_amount.get().replace(",",""))
        except ValueError: self.trade_status.configure(text="⚠ Enter a valid dollar amount.",text_color=_RED); return
        ok,msg=self.player.buy(ticker,asset.price,amount)
        self.trade_status.configure(text=msg,text_color=_GREEN if ok else _RED); self.refresh()

    def _do_sell(self):
        ticker=self.selected_ticker.get(); asset=self.market.assets.get(ticker)
        if not asset: return
        try: shares=float(self.sell_shares.get().replace(",",""))
        except ValueError: self.trade_status.configure(text="⚠ Enter valid share count.",text_color=_RED); return
        
        pos = self.player.portfolio.get(ticker)
        if not pos: return
        ok,msg=self.player.sell(ticker,asset.price,shares)
        self.trade_status.configure(text=msg,text_color=_GREEN if ok else _RED); self.refresh()

    def _quick_sell(self, fraction):
        ticker=self.selected_ticker.get(); pos=self.player.portfolio.get(ticker)
        if pos: self.sell_shares.set(f"{pos.shares*fraction:.4f}")

    def _build_asset_list(self, parent):
        card=_ctk.CTkFrame(parent,fg_color=_BG_CARD,corner_radius=8)
        card.grid(row=0,column=0,sticky="nsew",pady=(0,4),padx=(4,0))
        card.rowconfigure(1,weight=1); card.columnconfigure(0,weight=1)
        hdr=_ctk.CTkFrame(card,fg_color=_BG_CARD)
        hdr.grid(row=0,column=0,sticky="ew",padx=8,pady=(8,4))
        _ctk.CTkLabel(hdr,text="MARKETS",font=_ctk.CTkFont("Segoe UI",13,"bold"),text_color=_ACCENT).pack(side="left")
        for ft in ("All","Stock","ETF","Bond","Gold"):
            _ctk.CTkButton(hdr,text=ft,width=42,height=22,font=_ctk.CTkFont("Segoe UI",11), fg_color=_BG_MID,hover_color=_ACCENT2, command=lambda f=ft:[self.filter_type.set(f),self._refresh_asset_list()]).pack(side="right",padx=1)
        self.asset_scroll=_ctk.CTkScrollableFrame(card,fg_color=_BG_CARD,scrollbar_button_color=_BORDER)
        self.asset_scroll.grid(row=1,column=0,sticky="nsew",padx=4,pady=4)

    def _refresh_asset_list(self):
        for w in self.asset_scroll.winfo_children(): w.destroy()
        ft=self.filter_type.get()
        self.displayed_tickers.clear()
        hdr_row=_ctk.CTkFrame(self.asset_scroll,fg_color=_BG_CARD)
        hdr_row.pack(fill="x",padx=2,pady=(0,4))
        for txt,w in [("Ticker",52),("Name",130),("Price",72),("1M%",52),("",30)]:
            _ctk.CTkLabel(hdr_row,text=txt,width=w,font=_ctk.CTkFont("Segoe UI",11),text_color=_DIM).pack(side="left")
        for ticker,asset in self.market.assets.items():
            if ft!="All" and asset.asset_type.value!=ft: continue
            self.displayed_tickers.append(ticker)
            is_sel=asset.ticker==self.selected_ticker.get()
            bg=_BG_HOVER if is_sel else _BG_MID
            row=_ctk.CTkFrame(self.asset_scroll,fg_color=bg,corner_radius=4)
            row.pack(fill="x",padx=2,pady=1)
            c1m=asset.change_1m; pc=_GREEN if c1m>=0 else _RED
            held="●" if asset.ticker in self.player.portfolio else ""
            _ctk.CTkLabel(row,text=asset.ticker,width=52,font=_ctk.CTkFont("Segoe UI",12,"bold"), text_color=_ACCENT if is_sel else _WHITE).pack(side="left",padx=2)
            _ctk.CTkLabel(row,text=asset.name[:16],width=130,font=_ctk.CTkFont("Segoe UI",11),text_color=_DIM).pack(side="left")
            _ctk.CTkLabel(row,text=f"${asset.price:,.2f}",width=72,font=_ctk.CTkFont("Segoe UI",12),text_color=_WHITE).pack(side="left")
            _ctk.CTkLabel(row,text=f"{c1m:+.1f}%",width=52,font=_ctk.CTkFont("Segoe UI",11),text_color=pc).pack(side="left")
            _ctk.CTkLabel(row,text=held,width=20,font=_ctk.CTkFont("Segoe UI",11),text_color=_GOLD).pack(side="left")
            row.bind("<Button-1>",lambda e,t=asset.ticker:self._select(t))
            for child in row.winfo_children(): child.bind("<Button-1>",lambda e,t=asset.ticker:self._select(t))

    def _select(self, ticker): self.selected_ticker.set(ticker); self.refresh()

    def _build_portfolio(self, parent):
        card=_ctk.CTkFrame(parent,fg_color=_BG_CARD,corner_radius=8)
        card.grid(row=1,column=0,sticky="nsew",padx=(4,0))
        card.rowconfigure(1,weight=1); card.columnconfigure(0,weight=1)
        _ctk.CTkLabel(card,text="MY PORTFOLIO",font=_ctk.CTkFont("Segoe UI",13,"bold"), text_color=_ACCENT).grid(row=0,column=0,sticky="w",padx=12,pady=(8,4))
        self.portfolio_scroll=_ctk.CTkScrollableFrame(card,fg_color=_BG_CARD,scrollbar_button_color=_BORDER)
        self.portfolio_scroll.grid(row=1,column=0,sticky="nsew",padx=4,pady=4)
        self.lbl_portfolio_summary=_ctk.CTkLabel(card,text="",font=_ctk.CTkFont("Segoe UI",12),text_color=_DIM)
        self.lbl_portfolio_summary.grid(row=2,column=0,sticky="w",padx=12,pady=(0,8))

    def _refresh_portfolio(self):
        for w in self.portfolio_scroll.winfo_children(): w.destroy()
        if not self.player.portfolio:
            _ctk.CTkLabel(self.portfolio_scroll,text="No positions held.", font=_ctk.CTkFont("Segoe UI",12),text_color=_DIM).pack(pady=20)
            self.lbl_portfolio_summary.configure(text=f"Total Assets: 0  |  Cash: ${self.player.cash:,.2f}"); return
        tv=0.0; tc=0.0
        hdr=_ctk.CTkFrame(self.portfolio_scroll,fg_color=_BG_CARD)
        hdr.pack(fill="x",padx=2,pady=(0,4))
        for txt,w in [("Ticker",52),("Shares",72),("Value",80),("P&L%",60)]:
            _ctk.CTkLabel(hdr,text=txt,width=w,font=_ctk.CTkFont("Segoe UI",11),text_color=_DIM).pack(side="left")
        for ticker,pos in self.player.portfolio.items():
            asset=self.market.assets.get(ticker); price=asset.price if asset else 0.0
            val=pos.current_value(price); pnl=pos.pnl_pct(price); pc=_GREEN if pnl>=0 else _RED
            tv+=val; tc+=pos.total_cost
            row=_ctk.CTkFrame(self.portfolio_scroll,fg_color=_BG_MID,corner_radius=4)
            row.pack(fill="x",padx=2,pady=1)
            _ctk.CTkLabel(row,text=ticker,width=52,font=_ctk.CTkFont("Segoe UI",12,"bold"),text_color=_ACCENT).pack(side="left",padx=2)
            _ctk.CTkLabel(row,text=f"{pos.shares:.3f}",width=72,font=_ctk.CTkFont("Segoe UI",11),text_color=_WHITE).pack(side="left")
            _ctk.CTkLabel(row,text=f"${val:,.0f}",width=80,font=_ctk.CTkFont("Segoe UI",11),text_color=_WHITE).pack(side="left")
            _ctk.CTkLabel(row,text=f"{pnl:+.1f}%",width=60,font=_ctk.CTkFont("Segoe UI",11),text_color=pc).pack(side="left")
        tp=(tv/tc-1)*100 if tc>0 else 0; sign="+" if tp>=0 else ""
        num_assets = len(self.player.portfolio)
        self.lbl_portfolio_summary.configure(text=f"Total Assets: {num_assets}  |  Portfolio: ${tv:,.0f}  |  P&L: {sign}{tp:.1f}%  |  Cash: ${self.player.cash:,.0f}")

    def refresh(self):
        self._update_chart(); self._refresh_asset_list(); self._refresh_portfolio()
        ticker=self.selected_ticker.get(); asset=self.market.assets.get(ticker)
        if asset:
            c1m=asset.change_1m
            self.lbl_asset_name.configure(text=f"{asset.ticker}  {asset.asset_type.value}")
            self.lbl_asset_price.configure(text=f"${asset.price:,.2f}  ({c1m:+.1f}%)", text_color=_GREEN if c1m>=0 else _RED)
            self.lbl_asset_desc.configure(text=asset.description)
        self.market_badge.configure(text=self.market.market_summary)

class LifestyleShop:
    def __init__(self, master, engine: GameEngine, refresh_cb):
        if not _ctk_available: raise RuntimeError("customtkinter not installed.")
        self._root = master; self.engine = engine; self.player = engine.player
        self.refresh_cb = refresh_cb
        self.win = _ctk.CTkToplevel(master)
        self.win.title("🏠 Lifestyle Shop")
        self.win.geometry("720x600")
        self.win.configure(fg_color=_BG_DEEP)
        self._build_ui()

    def winfo_exists(self): return self.win.winfo_exists()
    def protocol(self, *a, **kw): self.win.protocol(*a, **kw)
    def destroy(self): self.win.destroy()
    def focus(self): self.win.focus()

    def _build_ui(self):
        _ctk.CTkLabel(self.win,text="🏠  LIFESTYLE UPGRADES",font=_ctk.CTkFont("Segoe UI",18,"bold"), text_color=_GOLD).pack(pady=(18,4))
        self.status_lbl=_ctk.CTkLabel(self.win,text="",font=_ctk.CTkFont("Segoe UI",12),text_color=_GREEN)
        self.status_lbl.pack()
        scroll=_ctk.CTkScrollableFrame(self.win,fg_color=_BG_DEEP)
        scroll.pack(fill="both",expand=True,padx=12,pady=8)
        cats={"housing":"🏠 Housing","transport":"🚗 Transport","personal":"💼 Personal","relationship":"❤️ Relationship"}
        for cat_key,cat_label in cats.items():
            _ctk.CTkLabel(scroll,text=cat_label,font=_ctk.CTkFont("Segoe UI",15,"bold"), text_color=_ACCENT).pack(anchor="w",padx=8,pady=(16,4))
            current=self.player.lifestyle.get(cat_key)
            for opt in LIFESTYLE_OPTIONS:
                if opt.category!=cat_key: continue
                is_active=(current and current.name==opt.name)
                can_nw=self.player.net_worth>=opt.requires_net_worth
                row=_ctk.CTkFrame(scroll,fg_color=_BG_CARD if is_active else _BG_MID,corner_radius=8)
                row.pack(fill="x",padx=4,pady=3)
                left=_ctk.CTkFrame(row,fg_color="transparent")
                left.pack(side="left",fill="both",expand=True,padx=12,pady=8)
                _ctk.CTkLabel(left,text=f"{opt.icon} {opt.name}",font=_ctk.CTkFont("Segoe UI",13,"bold"), text_color=_GOLD if is_active else _WHITE).pack(anchor="w")
                _ctk.CTkLabel(left,text=opt.description,font=_ctk.CTkFont("Segoe UI",12), text_color=_DIM).pack(anchor="w")
                ct=f"+${opt.monthly_cost:,.0f}/mo  |  😊 +{opt.happiness}"
                if opt.one_time_cost>0: ct+=f"  |  One-time: ${opt.one_time_cost:,.0f}"
                if opt.requires_net_worth>0: ct+=f"  |  Required Net Worth: ${opt.requires_net_worth:,.0f}"
                _ctk.CTkLabel(left,text=ct,font=_ctk.CTkFont("Segoe UI",11),text_color=_ACCENT).pack(anchor="w")
                if is_active:
                    _ctk.CTkLabel(row,text="✔ ACTIVE",font=_ctk.CTkFont("Segoe UI",12,"bold"),text_color=_GREEN).pack(side="right",padx=12)
                elif not can_nw:
                    _ctk.CTkLabel(row,text="🔒 LOCKED",font=_ctk.CTkFont("Segoe UI",11),text_color=_DIM).pack(side="right",padx=12)
                else:
                    _ctk.CTkButton(row,text="SELECT",width=80,height=30,font=_ctk.CTkFont("Segoe UI",12,"bold"), fg_color=_ACCENT2,hover_color=_ACCENT, command=lambda o=opt:self._select(o)).pack(side="right",padx=12,pady=8)

    def _select(self, opt):
        if opt.one_time_cost>0:
            if self.player.cash<opt.one_time_cost:
                self.status_lbl.configure(text=f"⚠ Need ${opt.one_time_cost:,.0f} cash.",text_color=_RED); return
            self.player.cash-=opt.one_time_cost
        self.player.lifestyle[opt.category]=opt
        self.player.happiness=min(100,self.player.happiness+opt.happiness//2)
        self.status_lbl.configure(text=f"✔ Switched to '{opt.name}'.  Monthly expenses: ${self.player.monthly_expenses:,.0f}", text_color=_GREEN)
        self.refresh_cb()
        for w in self.win.winfo_children(): w.destroy()
        self._build_ui()

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════

def draw_game_over(surf: pygame.Surface, engine):
    ov = pygame.Surface((SCREEN_W, SCREEN_H)); ov.fill((10, 12, 15)); surf.blit(ov, (0, 0))
    try: font_title = pygame.font.SysFont("Segoe UI", 56, bold=True); font_stats = pygame.font.SysFont("Segoe UI", 26)
    except Exception: font_title = pygame.font.Font(None, 56); font_stats = pygame.font.Font(None, 26)
        
    age = 25 + (engine.total_months // 12)
    title_col = (255, 215, 0) if age >= 80 else (255, 80, 80)
    title_text = "A LIFE WELL LIVED" if age >= 80 else "BANKRUPTCY"
    t_surf = font_title.render(title_text, True, title_col); surf.blit(t_surf, (SCREEN_W // 2 - t_surf.get_width() // 2, 120))
    
    stats = [
        f"Final Age: {age}",
        f"Total Wealth: ${engine.player.net_worth:,.0f}",
        f"Peak Career: {CAREER_LEVELS[engine.player.career_level]['title']}",
        f"Max Happiness Achieved: {max(engine.player.happiness_history)}/100",
        "", "📊 Post-mortem report saved to postmortem.csv",
        "", "Press [ESC] to Exit."
    ]
    y = 250
    for st in stats:
        st_surf = font_stats.render(st, True, (200, 210, 220))
        surf.blit(st_surf, (SCREEN_W // 2 - st_surf.get_width() // 2, y)); y += 40

def main():
    pygame.init(); pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("The 8-Bit Investor")
    clock  = pygame.time.Clock()

    engine        = GameEngine()
    renderer      = PixelRenderer(screen)
    world         = build_world()
    player_ctrl   = PlayerController(x=500, y=FLOOR_Y - PlayerController.SPRITE_H)
    cycle         = DayNightCycle()
    notifications = NotificationSystem()
    flicker       = MonitorFlicker()
    motes         = DustMotes(30)
    radio         = ProceduralRadio()

    win_obj = next(o for o in world if o.name == "window")
    win_rect = pygame.Rect(win_obj.x + PIXEL_SIZE, win_obj.y + PIXEL_SIZE, len(WINDOW_SPRITE[0]) * PIXEL_SIZE - PIXEL_SIZE * 2, len(WINDOW_SPRITE) * PIXEL_SIZE - PIXEL_SIZE * 2)
    rain = RainSystem(win_rect)

    sleeping = False; sleep_progress = 0.0
    npc_state = {"bubble_timer": 5.0, "show_timer": 0.0, "current_text": "", "x": 200.0, "facing_right": True, "pacing_timer": 0.0, "is_walking": False}

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0; dt = min(dt, 0.05) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

                if not engine.game_over:
                    # Radio Controls
                    if event.key == pygame.K_p: radio.toggle()
                    if event.key == pygame.K_n: radio.next_track()
                    if event.key == pygame.K_b: radio.prev_track()
                    if event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS: radio.vol_up()
                    if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS: radio.vol_down()

                    # Save and Load
                    if event.key == pygame.K_F5:
                        engine.save_game()
                        notifications.add("💾 Quick Save Successful.", (100, 255, 100))
                    if event.key == pygame.K_F9:
                        if engine.load_game(): notifications.add("📂 Quick Load Successful.", (100, 200, 255))
                        else: notifications.add("⚠ No save file found.", (255, 100, 100))

                    # Fast Forward 1 Year
                    if event.key == pygame.K_y and not sleeping:
                        for _ in range(12): result = engine.advance()
                        cycle.advance_hours(24 * 30 * 12)
                        notifications.add("⏩ Fast Forwarded 1 Year.", (200, 200, 255))
                        if result["market"].get("recession_start"): notifications.add("🔴 RECESSION ACTIVE!", (255,60,60), 6.0)

                    # Interaction
                    if event.key == pygame.K_e and not sleeping:
                        px, py = int(player_ctrl.center_x), int(player_ctrl.center_y)

                        pc_obj = next(o for o in world if o.name == "pc")
                        if pc_obj.can_interact(px, py):
                            pygame.display.iconify()
                            launch_investment_terminal(engine)
                            pygame.display.set_mode((SCREEN_W, SCREEN_H)); pygame.display.set_caption("The Intelligent Investor")
                            notifications.add("💹 Back from the Investment Terminal.", (100, 200, 255))

                        tv_obj = next(o for o in world if o.name == "tv")
                        if tv_obj.can_interact(px, py):
                            pygame.display.iconify()
                            launch_lifestyle_shop(engine)
                            pygame.display.set_mode((SCREEN_W, SCREEN_H)); pygame.display.set_caption("The Intelligent Investor")
                            notifications.add("🏠 Lifestyle updated.", (255, 220, 80))

                        bed_obj = next(o for o in world if o.name == "bed")
                        if bed_obj.can_interact(px, py) and not sleeping:
                            sleeping = True; sleep_progress = 0.0

        if engine.game_over:
            draw_game_over(screen, engine)
        else:
            if sleeping:
                sleep_progress += dt * 0.6
                if sleep_progress >= 1.0:
                    result = engine.advance()
                    cycle.advance_hours(random.uniform(6, 10))
                    for msg in result["messages"]:
                        col = (100,220,100) if any(x in msg for x in ["+$","Salary","upgrade","Career"]) else (220,80,80) if any(x in msg for x in ["-$","Emergency","Burnout","demoted"]) else (180,180,200)
                        notifications.add(msg, col, duration=5.0)
                    if result["market"].get("recession_start"): notifications.add("🔴 RECESSION STARTED!", (255,60,60), 6.0)
                    if result["market"].get("recession_end"): notifications.add("🟢 Recession over — recovery begins.", (60,220,100), 5.0)
                    sleeping = False; sleep_progress = 0.0
            else:
                player_ctrl.update(dt, FLOOR_Y, WALL_LEFT, WALL_RIGHT)

            cycle.advance_hours(dt * (1.0 / 60.0))
            screen.fill((5, 5, 15))

            draw_room(screen, renderer, world, flicker, rain, cycle, motes, dt, engine)
            draw_npc(screen, renderer, engine, npc_state, dt)
            player_ctrl.draw(renderer)

            px, py = int(player_ctrl.center_x), int(player_ctrl.center_y)
            for obj in world:
                if obj.interact_label and obj.can_interact(px, py):
                    draw_interact_prompt(screen, obj.interact_label, int(obj.x + len(obj.sprite[0]) * PIXEL_SIZE // 2), obj.y)

            draw_hud(screen, player_ctrl, cycle, engine, notifications, radio)

            if sleeping: draw_sleep_overlay(screen, sleep_progress)
            notifications.update(dt)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
