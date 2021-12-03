from abc import ABC, abstractmethod

class Blockbuilder(ABC):

    @abstractmethod
    def buildBlockTemplate(self):
        pass

    @abstractmethod
    def outputBlockTemplate(self, blockId=""):
        pass
