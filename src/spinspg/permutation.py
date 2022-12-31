from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from spinspg.utils import NDArrayFloat, NDArrayInt


@dataclass
class Permutation:
    permutation: NDArrayInt

    def __call__(self, idx: int) -> int:
        return self.permutation[idx]

    def __mul__(self, rhs: Permutation) -> Permutation:
        # (self * rhs)(i) = self(rhs(i))
        n = len(self.permutation)
        assert len(rhs.permutation) == n
        mul = np.zeros(n, dtype=np.int_)
        for i in range(n):
            mul[i] = self(rhs(i))
        return Permutation(mul)


def get_symmetry_permutations(
    lattice: NDArrayFloat,
    positions: NDArrayFloat,
    numbers: NDArrayInt,
    rotations: NDArrayInt,
    translations: NDArrayFloat,
    symprec: float,
) -> list[Permutation]:
    num_sites = len(positions)

    permutations = []
    for rot, trans in zip(rotations, translations):
        new_positions = positions @ rot.T + trans[None, :]
        perm = [-1 for _ in range(num_sites)]
        found = [False for _ in range(num_sites)]
        for i in range(num_sites):
            for j in range(num_sites):
                if found[j] or (numbers[i] != numbers[j]):
                    continue
                if is_overlap(lattice, new_positions[i] - positions[j], symprec):
                    perm[i] = j
                    found[j] = True
                    break

        if np.all(perm != -1):
            permutations.append(Permutation(perm))

    return permutations


def is_overlap(lattice, frac_coords, symprec) -> bool:
    diff = lattice.T @ (frac_coords - np.rint(frac_coords))
    return np.linalg.norm(diff) < symprec
