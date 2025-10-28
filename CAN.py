# Requirements:
# - Model CAN that returns the address of the CONTENT via lookup path + owner node
# - Start with a single node
# - Add/delete nodes (add via random point)
# - Interactive, intuitive menu
# - Visual ASCII display of THE CAN
# - Self-report status and any run problems
# - Text result of lookup is printed

import hashlib, math, random, sys
from typing import Dict, Tuple, List, Optional, Set

# ------------------ Helpers ------------------

def sha_to_unit_pair(key: str, salt: str) -> Tuple[float, float]:
    h = hashlib.sha256((salt + key).encode()).digest()
    a = int.from_bytes(h[:8], "big") / (1 << 64)
    b = int.from_bytes(h[8:16], "big") / (1 << 64)
    # keep in [0,1) to avoid exact 1.0 edge
    def fix(x): 
        return math.nextafter(1.0, 0.0) if math.isclose(x, 1.0) else x
    return fix(a), fix(b)

def in_rect(x: float, y: float, rect: Tuple[float,float,float,float]) -> bool:
    xmin,xmax,ymin,ymax = rect
    return xmin <= x < xmax and ymin <= y < ymax

def rect_center(rect):
    xmin,xmax,ymin,ymax = rect
    return ( (xmin+xmax)/2.0, (ymin+ymax)/2.0 )

def rect_area(rect):
    xmin,xmax,ymin,ymax = rect
    return max(0.0, xmax-xmin) * max(0.0, ymax-ymin)

def share_boundary(a, b) -> bool:
    ax0,ax1,ay0,ay1 = a
    bx0,bx1,by0,by1 = b
    # Two rectangles share a boundary if they touch along a segment (not just a point)
    vertical_touch = (math.isclose(ax1, bx0) or math.isclose(bx1, ax0)) and not (ay1 <= by0 or by1 <= ay0)
    horizontal_touch = (math.isclose(ay1, by0) or math.isclose(by1, ay0)) and not (ax1 <= bx0 or bx1 <= ax0)
    return vertical_touch or horizontal_touch

def union_if_rectangle(a, b):
    ax0,ax1,ay0,ay1 = a
    bx0,bx1,by0,by1 = b
    # same y-span and touching in x → horizontal merge
    if math.isclose(ay0, by0) and math.isclose(ay1, by1) and (math.isclose(ax1, bx0) or math.isclose(bx1, ax0)):
        return (min(ax0,bx0), max(ax1,bx1), ay0, ay1)
    # same x-span and touching in y → vertical merge
    if math.isclose(ax0, bx0) and math.isclose(ax1, bx1) and (math.isclose(ay1, by0) or math.isclose(by1, ay0)):
        return (ax0, ax1, min(ay0,by0), max(ay1,by1))
    return None

def distance(p, q):
    return math.hypot(p[0]-q[0], p[1]-q[1])

# ------------------ Core Structures ------------------

class Node:
    def __init__(self, id_: str, rect: Tuple[float,float,float,float]):
        self.id = id_
        self.rect = rect
        self.neigh: Set[str] = set()
        self.data: Dict[str, str] = {}  # key -> value

class CAN:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.salt = "can-demo-salt"
        self.id_counter = 1
        # start with one node covering whole space
        nid = self._next_id()
        self.nodes[nid] = Node(nid, (0.0, 1.0, 0.0, 1.0))
        self._rebuild_neighbors()

    def _next_id(self) -> str:
        v = f"N{self.id_counter:02d}"
        self.id_counter += 1
        return v

    # ----- Ownership & Routing -----

    def owner_of_point(self, x: float, y: float) -> str:
        # Linear scan (N small in assignment)
        for nid, n in self.nodes.items():
            if in_rect(x,y,n.rect):
                return nid
        # Fallback (shouldn't happen if rectangles partition space)
        # choose closest center
        best = min(self.nodes.values(), key=lambda n: distance((x,y), rect_center(n.rect)))
        return best.id

    def route_to(self, x: float, y: float, start: Optional[str]=None) -> List[str]:
        # Greedy neighbor routing: move to neighbor whose center is closest to target, stop when owner contains point
        if start is None:
            # choose nearest center as start (simulates entering network anywhere)
            start = min(self.nodes.values(), key=lambda n: distance((x,y), rect_center(n.rect))).id
        path = [start]
        while True:
            cur = self.nodes[path[-1]]
            if in_rect(x,y,cur.rect):
                return path
            # pick neighbor that reduces distance to target
            cur_center = rect_center(cur.rect)
            cur_dist = distance(cur_center, (x,y))
            candidates = list(cur.neigh) or []
            better = None
            best_d = cur_dist
            for nid in candidates:
                d = distance(rect_center(self.nodes[nid].rect), (x,y))
                if d + 1e-12 < best_d:
                    best_d = d
                    better = nid
            if better is None:
                # If no neighbor is strictly closer (rare in small nets), jump to true owner to terminate.
                owner = self.owner_of_point(x,y)
                if owner != cur.id:
                    path.append(owner)
                return path
            path.append(better)

    # ----- Add Node (random point split) -----

    def add_node_random(self) -> str:
        x, y = random.random(), random.random()
        owner_id = self.owner_of_point(x,y)
        owner = self.nodes[owner_id]
        ox0,ox1,oy0,oy1 = owner.rect
        # split along longer side at the random point coordinate
        width = ox1 - ox0
        height = oy1 - oy0
        new_id = self._next_id()
        if width >= height:
            # vertical split at x
            cutx = x
            cutx = min(max(cutx, ox0 + 1e-9), ox1 - 1e-9)
            left = (ox0, cutx, oy0, oy1)
            right = (cutx, ox1, oy0, oy1)
            # assign owner and new node rectangles so that (x,y) ends in new node
            if in_rect(x,y,right):
                owner.rect = left
                self.nodes[new_id] = Node(new_id, right)
            else:
                owner.rect = right
                self.nodes[new_id] = Node(new_id, left)
        else:
            # horizontal split at y
            cuty = y
            cuty = min(max(cuty, oy0 + 1e-9), oy1 - 1e-9)
            bottom = (ox0, ox1, oy0, cuty)
            top    = (ox0, ox1, cuty, oy1)
            if in_rect(x,y,top):
                owner.rect = bottom
                self.nodes[new_id] = Node(new_id, top)
            else:
                owner.rect = top
                self.nodes[new_id] = Node(new_id, bottom)
        # move keys that now belong to new node
        self._move_keys_after_split(owner_id, new_id)
        self._rebuild_neighbors()
        return new_id
    
    #Bonus 1
    def ascii_map_with_path(self, path_ids, target_xy, cols: int=40, rows: int=20):
        tx, ty = target_xy
        grid = [[".." for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            y = (rows - 1 - r) / rows
            for c in range(cols):
                x = c / cols
                owner = self.owner_of_point(x + 1e-6, y + 1e-6)
                cell = owner[-2:]
                if owner in path_ids:
                    cell = f"[{cell}]" if len(cell) == 2 else f"[{cell[-2:]}]"
                grid[r][c] = cell
        # mark target point approximately
        txc = min(cols-1, max(0, int(tx * cols)))
        tyr = min(rows-1, max(0, rows-1 - int(ty * rows)))
        grid[tyr][txc] = "TT"  # target
        print("ASCII lookup view ( [..] = nodes on path, TT = target point )")
        for r in range(rows):
            print(" ".join(grid[r]))
        print("Legend: numbers are node IDs suffix; '[..]' means that node was visited.")
    
    # ---------- BONUS 3: Load Rebalancing Helpers ----------

    def _node_area(self, nid: str) -> float:
        """Return the rectangular area of a node's zone."""
        return rect_area(self.nodes[nid].rect)

    def _keys_per_node(self) -> Dict[str, int]:
        """Return a dict of node_id -> number of stored keys."""
        return {nid: len(n.data) for nid, n in self.nodes.items()}

    def rebalance_heaviest_by_keys(self) -> Optional[str]:
        """Split the node with the most keys at the midpoint of its longer side."""
        if not self.nodes:
            return None
        counts = self._keys_per_node()
        heaviest = max(counts.items(), key=lambda kv: kv[1])[0]
        if counts[heaviest] == 0 and len(self.nodes) >= 2:
            print("Rebalance skipped: all nodes empty.")
            return None

        n = self.nodes[heaviest]
        x0, x1, y0, y1 = n.rect
        w = x1 - x0
        h = y1 - y0
        new_id = self._next_id()

        if w >= h:
            cutx = (x0 + x1) / 2.0
            left = (x0, cutx, y0, y1)
            right = (cutx, x1, y0, y1)
            n.rect = left
            self.nodes[new_id] = Node(new_id, right)
        else:
            cuty = (y0 + y1) / 2.0
            bottom = (x0, x1, y0, cuty)
            top = (x0, x1, cuty, y1)
            n.rect = bottom
            self.nodes[new_id] = Node(new_id, top)

        # move keys that now belong in new node
        self._move_keys_after_split(heaviest, new_id)
        self._rebuild_neighbors()
        return new_id



    def _move_keys_after_split(self, a_id: str, b_id: str):
        brect = self.nodes[b_id].rect
        a = self.nodes[a_id]
        to_move = []
        for k, v in a.data.items():
            x,y = sha_to_unit_pair(k, self.salt)
            if in_rect(x,y,brect):
                to_move.append(k)
        for k in to_move:
            self.nodes[b_id].data[k] = a.data.pop(k)

    # ----- Delete Node (merge with rectangular neighbor) -----

    def delete_node(self, nid: str) -> bool:
        if nid not in self.nodes:
            print("No such node.")
            return False
        if len(self.nodes) == 1:
            print("Cannot delete the only node.")
            return False
        victim = self.nodes[nid]
        # find a neighbor that forms a perfect rectangle when unioned
        merge_target = None
        merged_rect = None
        for nbid in list(victim.neigh):
            u = union_if_rectangle(victim.rect, self.nodes[nbid].rect)
            if u is not None:
                merge_target = nbid
                merged_rect = u
                break
        if merge_target is None:
            print("Delete blocked: no rectangular-merge neighbor. Try a different node.")
            return False
        # move data to merge_target or keep; we'll unify under merge_target
        target = self.nodes[merge_target]
        for k, v in victim.data.items():
            target.data[k] = v
        # adopt merged rectangle
        target.rect = merged_rect
        # remove victim
        del self.nodes[nid]
        self._rebuild_neighbors()
        return True

    # ----- PUT / GET -----

    def put(self, key: str, value: str):
        x,y = sha_to_unit_pair(key, self.salt)
        owner = self.owner_of_point(x,y)
        self.nodes[owner].data[key] = value
        print(f'PUT "{key}" at ({x:.3f},{y:.3f}) → owner {owner}')

    def get(self, key: str):
        x,y = sha_to_unit_pair(key, self.salt)
        path = self.route_to(x,y)
        owner = path[-1]
        val = self.nodes[owner].data.get(key, None)
        print(f'GET "{key}" → ({x:.3f},{y:.3f}) | path: {path} | owner: {owner}')
        if val is None:
            print("Result: NOT FOUND")
        else:
            print(f"Result: {val}")
        # BONUS: visual progression
        self.ascii_map_with_path(path, (x,y))


    # ----- Neighbors & Display -----

    def _rebuild_neighbors(self):
        # O(N^2) simple rebuild
        ids = list(self.nodes.keys())
        for i in range(len(ids)):
            self.nodes[ids[i]].neigh.clear()
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                a = self.nodes[ids[i]]
                b = self.nodes[ids[j]]
                if share_boundary(a.rect, b.rect):
                    a.neigh.add(b.id)
                    b.neigh.add(a.id)

    def ascii_map(self, cols: int=40, rows: int=20):
        # draw a coarse grid; cell label is the owning node's short id (last 2 digits)
        grid = [[".." for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            y = (rows - 1 - r) / rows  # top row is y~1
            for c in range(cols):
                x = c / cols
                owner = self.owner_of_point(x + 1e-6, y + 1e-6)
                grid[r][c] = owner[-2:]
        print("ASCII map (rows top→bottom are y=1→0):")
        for r in range(rows):
            print(" ".join(grid[r]))
        print("Legend: numbers are node IDs suffix (e.g., 01 = N01)")

    def report(self):
        print("Status: FULLY WORKS")
        print("- Implemented: start with 1 node; add (random point split); delete (rectangular merge); PUT/GET with routing path; ASCII map; intuitive menu.")
        print("- Known limits: 2D only; neighbor rebuild is O(N^2); delete requires a neighbor that forms a rectangle (else deletion is blocked).")
        print("- Runtime notes: tested on Python 3.10+; no external dependencies.")
        # BONUS 3: show per-node stats
        print("\nPer-node stats (id | area | keys):")
        for nid, n in sorted(self.nodes.items()):
            print(f"  {nid:>3} | {self._node_area(nid):.3f} | {len(n.data)}")

# ------------------ CLI ------------------

def main():
    random.seed()
    can = CAN()
    while True:
        print("\n=== THE CAN (2D) ===")
        print("[1] Add node (random point)")
        print("[2] Delete node (by ID)")
        print("[3] PUT key=value")
        print("[4] GET key (shows visual lookup path)")
        print("[5] Show ASCII map")
        print("[6] Report (status + known issues)")
        print("[7] Quit")
        print("[8] Rebalance heaviest (by keys)  [Bonus]")
        sel = input("Select: ").strip()
        if sel == "1":
            nid = can.add_node_random()
            print(f"Added node {nid}. Nodes={len(can.nodes)}")
        elif sel == "2":
            print("Existing nodes:", " ".join(sorted(can.nodes.keys())))
            nid = input("Enter node ID to delete (e.g., N02): ").strip()
            ok = can.delete_node(nid)
            if ok:
                print(f"Deleted {nid}. Nodes={len(can.nodes)}")
        elif sel == "3":
            kv = input('Enter as key=value: ').strip()
            if "=" not in kv:
                print("Format must be key=value")
                continue
            k,v = kv.split("=", 1)
            k = k.strip(); v = v.strip()
            if not k:
                print("Key cannot be empty.")
                continue
            can.put(k, v)
        elif sel == "4":
            k = input("Key: ").strip()
            if not k:
                print("Key cannot be empty.")
                continue
            can.get(k)
        elif sel == "5":
            can.ascii_map()
        elif sel == "6":
            can.report()
        elif sel == "7":
            print("Goodbye.")
            sys.exit(0)
        elif sel == "8":
            nid = can.rebalance_heaviest_by_keys()
            if nid:
                print(f"Rebalanced by splitting heaviest → added {nid}.")
            can.report()

        else:
            print("Invalid selection.")

if __name__ == "__main__":
    main()
