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
python can.py
