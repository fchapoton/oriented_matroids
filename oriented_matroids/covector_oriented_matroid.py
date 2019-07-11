r"""
Oriented matroid with covector axioms
---------------------------------------

This implements an oriented matroid using the covector axioms.

AUTHORS:

- Aram Dermenjian (...): Initial version
"""

##############################################################################
#       Copyright (C) 2019 Aram Dermenjian <aram.dermenjian at gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#  The full text of the GPL is available at:
#
#                  http://www.gnu.org/licenses/
##############################################################################

from sage.structure.unique_representation import UniqueRepresentation
from sage.structure.parent import Parent
from sage.categories.oriented_matroids import OrientedMatroids

from sage.matroids.oriented_matroids.signed_vector_element import SignedVectorElement


import copy

class CovectorOrientedMatroid(UniqueRepresentation, Parent):
    r"""
    An oriented matroid implemented using covector axioms.

    This implements an oriented matroid using the covector axioms. For this
    let `\mathcal{C}` be a set of covectors and `E` a ground set. Then
    a pair `M = (E,\mathcal{C})` is an oriented matroid using the covectors
    axioms if (see Theorem 4.1.1 in [BLSWZ1999]_):

        - `0 \in \mathcal{C}`
        - `\mathcal{C} = -\mathcal{C}`
        - For all `X,Y \in \mathcal{C}`, `X \circ Y \in \mathcal{C}`
        - For all `X,Y \in \mathcal{C}` and `e \in S(X,Y)` there exists a `Z \in \mathcal{C}` such that `Z(e) = 0` and `Z(f) = (X \circ Y)(f) = (Y \circ X)(f)` for all `f \notin S(X,Y)`.

    INPUT:

    - ``data`` -- a tuple containing SignedVectorElement elements or data
      that can be used to construct :class:`SignedVectorElement` elements
    - ``goundset`` -- (default: ``None``) is the groundset for the
      data. If not provided, we grab the data from the signed subsets.

    EXAMPLES::

        sage: M = OrientedMatroid([[1],[-1],[0]], groundset=['e'],key='covector'); M
        Covector Oriented Matroid of rank 1
        sage: M.groundset()
        ['e']
        sage: C = [ [1,1,1], [1,1,0],[1,1,-1],[1,0,-1],[1,-1,-1],[0,-1,-1],[-1,-1,-1],
        ....: [0,1,1],[-1,1,1],[-1,0,1],[-1,-1,1],[-1,-1,0],
        ....: [0,0,0]]
        ....: 
        sage: M = OrientedMatroid(C, key='covector'); M
        Covector Oriented Matroid of rank 3
        sage: M.groundset()
        [0, 1, 2]
        sage: M = OrientedMatroid(C, key='covector',groundset=['h1','h2','h3']);
        sage: M.groundset()
        ['h1', 'h2', 'h3']


    .. SEEALSO::

        :class:`OrientedMatroid`
        :class:`OrientedMatroids`
    """
    Element = SignedVectorElement

    @staticmethod
    def __classcall__(cls, data, groundset = None):
        """
        Normalize arguments and set class.
        """
        category = OrientedMatroids()
        return super(CovectorOrientedMatroid, cls).__classcall__(cls, data, groundset = groundset, category=category)

    def __init__(self,data, groundset=None,category=None):
        """
        Initialize ``self``
        """
        Parent.__init__(self,category = category)

        # Set up our covectors
        covectors = []
        for d in data:
            # Ensure we're using the right type.
            covectors.append(self.element_class(self,data=d, groundset=groundset))
        # If our groundset is none, make sure the groundsets are the same for all elements
        if groundset is None:
            groundset = covectors[0].groundset()
            for X in covectors:
                if X.groundset() != groundset:
                    raise ValueError("Groundsets must be the same")

        self._covectors = covectors
        self._groundset = list(groundset)


    def _repr_(self):
        """
        Return a string representation of ``self``.
        """
        rep = "Covector Oriented Matroid of rank {}".format(self.rank())
        return rep

    def is_valid(self):
        """
        Returns whether our covectors satisfy the covector axioms.
        """
        covectors = self.covectors()
        
        zero_fouind = False
        for X in covectors:
            # Axiom 1: Make sure empty is not present
            if X.is_zero():
                zero_found = True
            # Axiom 2: Make sure negative exists
            if -X not in covectors:
                raise ValueError("Every element needs an opposite")
            for Y in covectors:
                # Axiom 3: Closed under composition
                if X.composition(Y) not in covectors:
                    raise ValueError("Composition must be in vectors")
                # Axiom 4: Weak elimination axiom
                E = X.separation_set(Y)
                ze = set(self.groundset()).difference(E)
                xy = X.composition(Y)
                for e in E:
                    found = False
                    for Z in covectors:
                        if found:
                            break
                        if Z(e) == 0:
                            found = True
                            for f in ze:
                                if Z(f) != xy(f):
                                    found = False
                    if not found:
                        raise ValueError("weak elimination failed")

        if not zero_found:
            raise ValueError("Empty set is required")

        return True

    def groundset(self):
        """
        Return the groundset.
        """
        return self._groundset

    def elements(self):
        """
        Return a list of elements.
        """
        return self.covectors()

    def covectors(self):
        """
        Shorthand for :meth:`~sage.categories.oriented_matroids.OrientedMatroids.elements`
        """
        return self._covectors  

    def face_poset(self, facade=False):
        r"""
        Returns the (big) face poset.

        The *(big) face poset* is the poset on covectors such that `X \leq Y`
        if and onlyif `S(X,Y) = \emptyset` and `\underline{Y} \subseteq \underline{X}`.
        """
        from sage.combinat.posets.posets import Poset
        els = self.covectors()
        rels = [ (Y,X) for X in els for Y in els if Y.is_conformal_with(X) and Y.support().issubset(X.support())]
        return Poset((els, rels), cover_relations=False, facade=facade)

    def face_lattice(self, facade=False):
        r"""
        Returns the (big) face lattice.

        The *(big) face lattice* is the (big) face poset with a top element added.
        """
        from sage.combinat.posets.lattices import LatticePoset
        els = copy.deepcopy(self.covectors())
        rels = [ (Y,X) for X in els for Y in els if Y.is_conformal_with(X) and Y.support().issubset(X.support())]

        # Add top element
        for i in els:
            rels.append((i,1))
        els.append(1)
        return LatticePoset((els,rels), cover_relations=False, facade=facade)

