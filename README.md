# CAN-2D: Content Addressable Network Simulator

A minimal 2-dimensional simulation of a **Content Addressable Network (CAN)** written in Python.  
This project models a distributed hash space where nodes own rectangular regions in a Cartesian coordinate grid.  
Users can add or delete nodes, insert key-value pairs, and perform lookups to locate which node stores a given key.

---

## 🧩 Overview

Each node manages a rectangular portion of the `[0,1) × [0,1)` space.  
When a new node joins, the current owner of a random coordinate splits its zone and transfers the relevant data.  
Lookups hash the key to a coordinate, then route greedily through neighboring nodes until reaching the owner.

This simulation focuses on the **administrative structure and routing behavior** of CAN rather than real network transport.

---

## 🚀 Features

- Start with a single node and expand dynamically  
- Randomized node addition with zone splitting  
- Safe node deletion with rectangular merge  
- Greedy routing for key lookup  
- ASCII-based visualization of the CAN grid  
- Textual lookup output showing hashed coordinate, routing path, and owner node  
- Interactive command-line menu for experimentation  
- Self-report function summarizing system state and limitations  

---

## 🖥️ Usage

```bash
python CAN.py

Menu options:
[1] Add node (random point)
[2] Delete node (by ID)
[3] PUT key=value
[4] GET key (lookup)
[5] Show ASCII map
[6] Report status
[7] Quit

Example session:
PUT "alpha" at (0.312,0.528) → owner N03
GET "alpha" → (0.312,0.528) | path: ['N01', 'N03'] | owner: N03
Result: hello

🧠 Technical Notes

Implemented in pure Python 3 (no external libraries)

Neighbor rebuilding: O(N²) — acceptable for small networks

Zone representation: tuples (xmin, xmax, ymin, ymax)

Lookup coordinates derived from SHA-256 hash → normalized to [0,1)

🪪 License

MIT License — free to use and modify for educational or personal research purposes.

Vishnu Sai Uppu
Master’s in Computer Science | University of Memphis
[GitHub Profile](https://github.com/VishnuSaiU)
