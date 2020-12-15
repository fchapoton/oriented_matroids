r"""
Signed Subset element
---------------------------------------

This implements a basic signed subet element which is used for oriented
matroids.

AUTHORS:

- Aram Dermenjian (2019-07-12): Initial version
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
from sage.structure.element import Element

import copy


class SignedSubsetElement(Element):
    r"""
    Creates a signed subset.

    INPUT:

    - ``parent`` -- the parent object of the element. Usually is a class
      generated by :class:`OrientedMatroid`.
    - ``data`` -- (default: ``None``) is a tuple with information. Can be
      given in one of the following formats:
        + **as a vector** -- this is a tuple of pluses, minuses, and zeroes.
        + **as three tuples** -- the first tuple is the positives, the second
          the negatives and the third the zeroes.
        + **as a dict** -- the dictionary should have keys *positives*,
          *negatives*, and *zeroes*.
    - ``groundset`` -- (default: ``None``) if not given will construct
      the groundset from the parent, or if none is created in the parent,
      using the elements found in the data.
    - ``positives`` -- (default: ``None``) alternative to ``data``. Should be
      a tuple of elements. Requires ``negatives`` to be set.
    - ``negatives`` -- (default: ``None``) alternative to ``data``. Should be
      a tuple of elements. Requires ``positives`` to be set.
    - ``zeroes`` -- (default: ``None``) alternative to ``data``. Should be a
      tuple of elements. Requires ``positives`` and ``negatives`` to be set.

    EXAMPLES:

    Some examples of element constructions::

        sage: from oriented_matroids.oriented_matroid import OrientedMatroid
        sage: from oriented_matroids.signed_subset_element import SignedSubsetElement
        sage: M = OrientedMatroid([[1],[-1]],key='circuit');
        sage: SignedSubsetElement(M,data = (0,))
        +:
        -:
        0: 0
        sage: SignedSubsetElement(M,data = (1,))
        +: 0
        -:
        0:
        sage: M = OrientedMatroid([[1],[-1]],key='circuit', groundset=['e'])
        sage: SignedSubsetElement(M,data = (1,))
        +: e
        -:
        0:

    Elements are also lazy loaded to return the sign of elements from the grou
ndset::

        sage: M = OrientedMatroid([[1],[-1]],key='circuit', groundset=['e'])
        sage: C = M.elements(); C[0]
        +: e
        -:
        0:
        sage: C[0]('e')
        1

    .. SEEALSO::

        - :class:`oriented_matroids.oriented_Matroid.OrientedMatroid`
        - :class:`oriented_matroids.oriented_matroids_category.OrientedMatroids`

    """

    def __init__(self, parent=None, data=None, groundset=None,
                 positives=None, negatives=None, zeroes=None):
        """
        Initialize ``self``.
        """
        # If our groundset isn't set but our parent has one, use its groundset
        if groundset is None:
            try:
                groundset = parent.groundset()
            except AttributeError:
                groundset = None

        # remove parent if data not present
        if parent is None \
                or (data is None and groundset is None and positives is None):
            from sage.structure.parent import Parent
            data = parent
            parent = Parent()

        # instantiate!
        self._p = set([])
        self._n = set([])
        self._z = set([])

        # If we're setting things one item at a time
        if positives is not None:
            if negatives is None:
                raise ValueError(
                    "If positives is set, negatives must be as well")

            self._p = set(positives)
            self._n = set(negatives)
            if zeroes is None:
                if groundset is None:
                    self._z = set([])
                else:
                    gs = set(groundset)
                    self._z = gs.difference(self._p).difference(self._n)
            else:
                self._z = set(zeroes)

        # If we already have a signed subset element, use it's data
        elif isinstance(data, SignedSubsetElement):
            self._p = data.positives()
            self._n = data.negatives()
            self._z = data.zeroes()

        # If we have a tuple, use its information
        elif isinstance(data, tuple):
            # if we're given vector format
            if data[0] in [-1, 0, 1, '+', '0', '-', '']:
                if groundset is not None and len(data) != len(groundset):
                    raise ValueError(
                        "Length of vector must be same number of elements as ground set")
                for i, j in enumerate(data):
                    label = i
                    if groundset is not None:
                        label = groundset[i]
                    if j == -1 or j == '-':
                        self._n.add(label)
                    elif j == 1 or j == '+':
                        self._p.add(label)
                    elif j == 0 or j == '' or j == '0':
                        self._z.add(label)
                    else:
                        raise ValueError("Must be tuple of -1, 0, 1")

            # If we have a tuple of tuples
            else:
                self._p = set(data[0])
                self._n = set(data[1])
                if len(data) > 2:
                    self._z = set(data[2])
                elif groundset is not None:
                    self._z = set(groundset).difference(
                        self._p).difference(self._n)
        # If we have a dictionary, use the keys to figure it out
        elif isinstance(data, dict):
            if 'p' in data:
                self._p = data['p']
            if 'positives' in data:
                self._p = data['positives']
            if 'n' in data:
                self._n = data['n']
            if 'negatives' in data:
                self._n = data['negatives']
            if 'z' in data:
                self._z = data['z']
            if 'zeroes' in data:
                self._z = data['zeroes']
        else:
            raise ValueError(
                "Either positives and negatives are set or data is a tuple, OrientedMatroidELement or a dict")

        # Type fix
        self._p = set(self._p)
        self._n = set(self._n)
        self._z = set(self._z)

        # Setup the ground set if it's not set yet
        if groundset is None:
            self._g = list(self._p.union(self._n).union(self._z))
        else:
            if not self.support().union(self.zeroes()).issubset(groundset):
                raise ValueError("Elements must appear in groundset")

            # Update the zeroes with everything in the ground set
            if self._z is None:
                self._z = set(groundset).difference(self.support())

            # ground set should be everything
            if not set(groundset).issubset(self.support().union(self.zeroes())):
                raise ValueError(
                    "Every element must be either positive, negative or zero")
            self._g = groundset

        self._g = list(self._g)

        Element.__init__(self, parent)

    def __call__(self, var):
        """
        Return the sign of an element in the groundset.
        """

        if var in self.positives():
            return 1
        if var in self.negatives():
            return -1
        if var in self.zeroes():
            return 0
        raise ValueError("Not in groundset")

    def __hash__(self):
        """
        Return hashed string of signed subset.
        """
        fsp = frozenset(self._p)
        fsn = frozenset(self._n)
        fsz = frozenset(self._z)
        return hash((fsp, fsn, fsz))

    def __neg__(self):
        """
        Return the opposite signed subset.
        """
        N = copy.copy(self)
        N._p = self._n
        N._n = self._p
        return N

    def __eq__(self, other):
        """
        Return whether two elements are equal.
        """
        if isinstance(other, SignedSubsetElement):
            if self._p == other._p \
                    and self._n == other._n \
                    and self._z == other._z:
                return True
        return False

    def __ne__(self, other):
        """
        Return whether two elements are not equal.
        """
        return not (self == other)

    def _cmp_(self, other):
        """
        Arbitrary comparison function so posets work.
        """
        if not isinstance(other, SignedSubsetElement):
            return 0
        return 1
        # x = len(self.support()) - len(other.support())
        # if x == 0:
        #     return x
        # return x / abs(x) * -1

    def __bool__(self):
        r"""
        Returns whether an element is not considered a zero.

        For an oriented matroid, we consider the empty set
        `\emptyset = (\emptyset,\emptyset)` to be a zero as
        it is the same as the all zero vector.
        """
        if len(self.support()) > 0:
            return True
        return False

    def __iter__(self):
        """
        Returns an iter version of self.
        """
        for e in self.groundset():
            yield self(e)

    def _repr_(self):
        """
        Return a string of the signed subset.

        EXAMPLES::

            sage: from oriented_matroids.oriented_matroid import OrientedMatroid
            sage: from oriented_matroids.signed_subset_element import SignedSubsetElement
            sage: C = [ ((1,4),(2,3)) , ((2,3),(1,4)) ]
            sage: M = OrientedMatroid(C,key='circuit')
            sage: SignedSubsetElement(M,data = ((1,4),(2,3)))
            +: 1,4
            -: 2,3
            0:

        """

        p = map(str, self.positives())
        n = map(str, self.negatives())
        z = map(str, self.zeroes())
        return "+: " + ','.join(p) + "\n" + \
            "-: " + ','.join(n) + "\n" +\
            "0: " + ','.join(z)

    def _latex_(self):
        r"""
        Return a latex representation of the signed subset.

        EXAMPLES::

            sage: from oriented_matroids.oriented_matroid import OrientedMatroid
            sage: from oriented_matroids.signed_subset_element import SignedSubsetElement
            sage: C = [ ((1,4),(2,3)) , ((2,3),(1,4)) ]
            sage: M = OrientedMatroid(C,key='circuit')
            sage: latex(SignedSubsetElement(M,data = ((1,4),(2,3))))
            \left( \left{1,4\right},\left{2,3\right} \right)

        """
        p = map(str, self.positives())
        n = map(str, self.negatives())
        return "\\left( \\left{" + ','.join(p) + \
            "\\right},\\left{" + ','.join(n) + "\\right} \\right)"

    def __copy__(self):
        """
        Return a copy of the element
        """
        return SignedSubsetElement(parent=self.parent(), groundset=self.groundset(), positives=self.positives(), negatives=self.negatives(), zeroes=self.zeroes())

    def __deepcopy__(self):
        """
        Return a copy of the element
        """
        return SignedSubsetElement(parent=self.parent(), groundset=self.groundset(), positives=self.positives(), negatives=self.negatives(), zeroes=self.zeroes())

    def to_list(self):
        """
        Convert objcet to a list
        """
        return eval("[" + ','.join([str(self(e)) for e in self.groundset()]) + "]")

    def positives(self):
        """
        Return the set of positives.

        EXAMPLES::

            sage: from oriented_matroids import OrientedMatroid
            sage: M = OrientedMatroid([[1,-1,1],[-1,1,-1]], key='circuit')
            sage: E = M.elements()[0]
            sage: E.positives()
            {0, 2}

        """
        return self._p

    def negatives(self):
        """
        Return the set of negatives.

        EXAMPLES::

            sage: from oriented_matroids import OrientedMatroid
            sage: M = OrientedMatroid([[1,-1,1],[-1,1,-1]], key='circuit')
            sage: E = M.elements()[0]
            sage: E.negatives()
            {1}

        """
        return self._n

    def zeroes(self):
        r"""
        Return the set of zeroes.

        EXAMPLES::

            sage: from oriented_matroids import OrientedMatroid
            sage: M = OrientedMatroid([[1,-1,0],[-1,1,0]], key='circuit')
            sage: E = M.elements()[0]
            sage: E.zeroes()
            {2}

        """
        return self._z

    def support(self):
        r"""
        Return the support set.

        EXAMPLES::

            sage: from oriented_matroids import OrientedMatroid
            sage: M = OrientedMatroid([[1,-1,0],[-1,1,0]], key='circuit')
            sage: E = M.elements()[0]
            sage: E.support()
            {0, 1}

        """
        return self._p.union(self._n)

    def groundset(self):
        r"""
        Return the ground set.

        EXAMPLES::

            sage: from oriented_matroids import OrientedMatroid
            sage: M = OrientedMatroid([[1,-1,0],[-1,1,0]], key='circuit')
            sage: E = M.elements()[0]
            sage: E.groundset()
            [0, 1, 2]

        """
        return self._g

    def composition(self, other):
        r"""
        Return the composition of two elements.

        The composition of two elements `X` and `Y`,
        denoted `X \circ Y` is given componentwise
        where for `e \in E` we have `(X \circ Y)(e) = X(e)`
        if `X(e) \neq 0` else it equals `Y(e)`.

        EXAMPLES::

            sage: from oriented_matroids import OrientedMatroid
            sage: M = OrientedMatroid([[0],[1],[-1]], key='vector')
            sage: E1 = M.elements()[0]; E2 = M.elements()[1]
            sage: E1.composition(E2)
            (1)
            sage: E2.composition(E1)
            (1)
            sage: E1.composition(E2) == E2.composition(E1)
            True

        """
        p = []
        n = []
        z = []
        for e in self.groundset():
            x = self(e)
            # If x is non-zero, keep its value
            if x == 1:
                p.append(e)
            elif x == -1:
                n.append(e)
            else:
                # else grab the value of the other
                x = other(e)
                if x == 1:
                    p.append(e)
                elif x == -1:
                    n.append(e)
                else:
                    z.append(e)
        return type(self)(self.parent(), positives=p, negatives=n, zeroes=z)

    def separation_set(self, other):
        r"""
        Return the separation set between two elements.

        The separation set of two elements `X` and `Y`
        is given by `S(X,Y) = \left\{e \mid X(e) = -Y(e) \neq 0 \right\}`
        """
        return self.positives().intersection(other.negatives()).union(self.negatives().intersection(other.positives()))

    def reorientation(self, change_set):
        r"""
        Return the reorientation by a set.

        The reorientation of `X` by some `A \subseteq E` is
        the signed subset (covector) given by `{}_{-A}X` where
        `{}_{-A}X^+ = (X^+ \backslash A) \cup (X^- \cap A)` and similarly for
        `{}_{-A}X^-`.
        """
        if change_set in self.groundset():
            change_set = set([change_set])
        else:
            change_set = set(change_set)

        # ensure every elt is in the groundset
        for i in change_set:
            if i not in self.groundset():
                raise ValueError("{} is not in the ground set".format(i))

        p = self.positives().difference(change_set).union(
            self.negatives().intersection(change_set))
        n = self.negatives().difference(change_set).union(
            self.positives().intersection(change_set))
        return type(self)(self.parent(), positives=p, negatives=n, groundset=self.groundset())

    def is_conformal_with(self, other):
        r"""
        Return if the two elements are conformal.

        Two elements `X` and `Y` are *conformal* if
        `S(X,Y) = \emptyset`. This is true if and only if `X^+ \subseteq Y^+`
        and `X^- \subseteq Y^-`.
        """
        return len(self.separation_set(other)) == 0

    def is_restriction_of(self, other):
        r"""
        Return if `self` is a restriction of `other`.

        A signed subset `X` is a *restriction* of a signed subset `Y` if
        `X^+ \subsetex Y^+` and `X^- \subseteq Y^-`. If `X` is a restriction of
        `Y` we sometimes say `X` conforms to `Y`. This should not be mistaken
        with *is conformal with*.
        """
        return self.positives().issubset(other.positives()) \
            and self.negatives().issubset(other.negatives())

    def is_tope(self):
        r"""
        Return whether object is a tope.

        A covector is a tope if it is a maximal
        element in the face poset.

        .. WARNING::

            Requires the method `face_lattice` to exist in the oriented
            matroid.
        """
        if getattr(self.parent(), 'face_lattice', None) is not None:
            raise TypeError(
                "Topes are only implemented if .face_lattice() is implemented")

        return self in self.parent().topes()

    def is_simplicial(self):
        r"""
        Return whether or not a tope is simplicial.

        A tope `T` is simplicial if the interval `[0,T]` is boolean
        in the face lattice. We note that the breadth of a lattice
        can characterize this. In particular a lattice of breadth `n`
        contains a sublattice isomorphic to the Boolean lattice of `2^n`
        elements. In other words, if `[0,T]` has `2^n` elements and
        the breadth of `[0,T]` is `n` then the interval is boolean
        and thus `T` is simplicial.
        """
        if not self.is_tope():
            raise TypeError("Only topes can be simplicial")

        P = self.parent().face_lattice()
        I = P.interval(P.bottom(), self)
        PP = P.sublattice(I)
        b = PP.breadth()
        if len(I) == 2**b:
            return True
        return False

    def is_zero(self):
        """
        Return whether or not element is 0
        """
        return len([1 for e in self.groundset() if self(e) != 0]) == 0

