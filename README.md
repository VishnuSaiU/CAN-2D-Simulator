# THE CAN (2D) – Minimal Simulation

A simple 2D Content Addressable Network (CAN) model built for an operating systems homework. The program models a CAN overlay, supports node join/leave, performs content lookups, and provides an ASCII visualization.

## Features (Assignment Checklist)

- **Model CAN that returns the address of the content**
  - `GET` prints the hashed coordinate `(x, y)`, the routing `path`, and the final **owner node** (the address of the content).
- **Starts with a single node** covering `[0,1) × [0,1)`.
- **Add / Delete nodes**
  - **Add**: picks a random point, routes to the current owner, splits that owner’s zone along the longer side at that point, and migrates keys.
  - **Delete**: merges a node with a neighbor when their union is a perfect rectangle; keys move to the survivor.
- **Interactive, intuitive menu** (numbered actions).
- **Visual ASCII display** of the CAN space.
- **Self-report** status & known limits.
- **Text result for lookups** is printed.

## Run

```bash
python can.py
