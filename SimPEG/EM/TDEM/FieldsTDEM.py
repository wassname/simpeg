import numpy as np
import scipy.sparse as sp
import SimPEG
from SimPEG import Utils
from SimPEG.EM.Utils import omega
from SimPEG.Utils import Zero, Identity

class Fields(SimPEG.Problem.TimeFields):
    """

    Fancy Field Storage for a TDEM survey. Only one field type is stored for
    each problem, the rest are computed. The fields obejct acts like an array and is indexed by

    .. code-block:: python

        f = problem.fields(m)
        e = f[srcList,'e']
        b = f[srcList,'b']

    If accessing all sources for a given field, use the :code:`:`

    .. code-block:: python

        f = problem.fields(m)
        e = f[:,'e']
        b = f[:,'b']

    The array returned will be size (nE or nF, nSrcs :math:`\\times` nFrequencies)
    """

    knownFields = {}
    dtype = float

    def _eDeriv(self, tInd, src, dun_dm_v, v, adjoint=False):
        if adjoint is True:
            return self._eDeriv_u(tInd, src, v, adjoint), self._eDeriv_m(tInd, src, v, adjoint)
        return self._eDeriv_u(tInd, src, dun_dm_v) + self._eDeriv_m(tInd, src, v)

    def _bDeriv(self, tInd, src, dun_dm_v, v, adjoint=False):
        if adjoint is True:
            return self._bDeriv_u(tInd, src, v, adjoint), self._bDeriv_m(tInd, src, v, adjoint)
        return self._bDeriv_u(tInd, src, dun_dm_v) + self._bDeriv_m(tInd, src, v)

class Fields_Derivs(Fields):
    knownFields = {
                    'bDeriv': 'F',
                    'eDeriv': 'E',
                    'hDeriv': 'E',
                    'jDeriv': 'F'
                  }


class Fields_b(Fields):
    """Fancy Field Storage for a TDEM survey."""
    knownFields = {'bSolution': 'F'}
    aliasFields = {
                    'b': ['bSolution', 'F', '_b'],
                    'e': ['bSolution', 'E', '_e'],
                  }

    def startup(self):
        self.MeSigmaI      = self.survey.prob.MeSigmaI
        self.MeSigmaIDeriv = self.survey.prob.MeSigmaIDeriv
        self.edgeCurl      = self.survey.prob.mesh.edgeCurl
        self.MfMui         = self.survey.prob.MfMui

    def _b(self, bSolution, srcList, tInd):
        return bSolution

    def _bDeriv_u(self, tInd, src, dun_dm_v, adjoint=False):
        return Identity()*dun_dm_v

    def _bDeriv_m(self, tInd, src, v, adjoint=False):
        return Zero()

    # def _bDeriv(self, tInd, src, dun_dm_v, v, adjoint=False):
    #     if adjoint is True:
    #         return self._bDeriv_u(tInd, src, v, adjoint), self._bDeriv_m(tInd, src, v, adjoint)
    #     return self._bDeriv_u(tInd, src, dun_dm_v) + self._bDeriv_m(tInd, src, v)

    def _e(self, bSolution, srcList, tInd):
        e = self.MeSigmaI * ( self.edgeCurl.T * ( self.MfMui * bSolution ) )
        for i, src in enumerate(srcList):
            _, S_e = src.eval(self.survey.prob, self.survey.prob.times[tInd])
            e[:,i] = e[:,i] - self.MeSigmaI * S_e
        return e

    def _eDeriv_u(self, tInd, src, dun_dm_v, adjoint = False):
        if adjoint is True:
            return self.MfMui.T * ( self.edgeCurl * ( self.MeSigmaI.T * dun_dm_v ) )
        return self.MeSigmaI * ( self.edgeCurl.T * ( self.MfMui * dun_dm_v ) )

    def _eDeriv_m(self, tInd, src, v, adjoint = False):
        _, S_e = src.eval(self.survey.prob, self.survey.prob.times[tInd])
        bSolution = self[[src],'bSolution',tInd]

        _, S_eDeriv = src.evalDeriv(self.survey.prob.times[tInd], self, adjoint=adjoint)

        if adjoint is True:
            return self.MeSigmaIDeriv(-S_e + self.edgeCurl.T * ( self.MfMui * bSolution ) ).T * v - S_eDeriv(self.MeSigmaI.T * v)

        return self.MeSigmaIDeriv(-S_e + self.edgeCurl.T * ( self.MfMui * bSolution)) * v - self.MeSigmaI * S_eDeriv(v)



class Fields_e(Fields):
    """Fancy Field Storage for a TDEM survey."""
    knownFields = {'eSolution': 'E'}
    aliasFields = {
                    'e': ['eSolution', 'E', '_e'],
                    'b': ['eSolution', 'F', '_b'],
                  }

    def startup(self):
        self.MeSigmaI      = self.survey.prob.MeSigmaI
        self.MeSigmaIDeriv = self.survey.prob.MeSigmaIDeriv
        self.edgeCurl      = self.survey.prob.mesh.edgeCurl
        self.MfMui         = self.survey.prob.MfMui


    def _e(self, eSolution, srcList, tInd):
        return eSolution

    def _eDeriv_u(self, tInd, src, dun_dm_v, adjoint = False):
        return dun_dm_v

    def _eDeriv_m(self, tInd, src, v, adjoint = False):
        return Zero()

    def _b(self, eSolution, srcList, tInd):
        raise NotImplementedError

    def _bDeriv_u(self, tInd, src, dun_dm_v, adjoint=False):
        raise NotImplementedError

    def _bDeriv_m(self, tInd, src, v, adjoint=False):
        raise NotImplementedError

    # def _bDeriv(self, tInd, src, dun_dm_v, v, adjoint=False):
    #     if adjoint is True:
    #         return self._bDeriv_u(tInd, src, v, adjoint), self._bDeriv_m(tInd, src, v, adjoint)
    #     return self._bDeriv_u(tInd, src, dun_dm_v) + self._bDeriv_m(tInd, src, v)
