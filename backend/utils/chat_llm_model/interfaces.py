from abc import ABC, abstractmethod  


## define the work of the each of the chat models 

class IChatModels(ABC):
 
    @abstractmethod
    def setModel(self, **kwargs):
        pass
    
    @abstractmethod 
    def getModel(self):
        pass  
    