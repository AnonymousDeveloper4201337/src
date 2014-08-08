import DNAGroup
import DNAError
from DNAUtil import *

class DNACornice(DNAGroup.DNAGroup):
    COMPONENT_CODE = 12

    def __init__(self, name):
        DNAGroup.DNAGroup.__init__(self, name)
        self.code = ''
        self.color = (1, 1, 1, 1)

    def setCode(self, code):
        self.code = code

    def getCode(self):
        return self.code

    def setColor(self, color):
        self.color = color

    def getColor(self):
        return self.color

    def makeFromDGI(self, dgi):
        DNAGroup.DNAGroup.makeFromDGI(self, dgi)
        self.code = dgi_extract_string8(dgi)
        self.color = dgi_extract_color(dgi)

    def traverse(self, nodePath, dnaStorage):
        pParentXScale = nodePath.getParent().getScale().getX()
        parentZScale = nodePath.getScale().getZ()
        node = dnaStorage.findNode(self.getCode())
        if node is None:
            raise DNAError.DNAError('DNACornice code {0} not found in '
                           'DNAStorage'.format(self.getCode()))
        nodePathA = nodePath.attachNewNode('cornice-internal')
        node = node.find('**/*_d')
        np = node.copyTo(nodePathA, 0)
        np.setPosHprScale(
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 0),
            LVector3f(1, pParentXScale/parentZScale,
                      pParentXScale/parentZScale))
        np.setEffect(DecalEffect.make())
        node = node.getParent().find('**/*_nd')
        np = node.copyTo(nodePathA, 1)
        np.setPosHprScale(
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 0),
            LVector3f(1, pParentXScale/parentZScale,
                      pParentXScale/parentZScale))
        nodePathA.setPosHprScale(
            LVector3f(0, 0, node.getScale().getZ()),
            LVector3f(0, 0, 0),
            LVector3f(1, 1, 1))
        nodePathA.setColor(self.getColor())