from .schemas import HuggingFaceEmbeddingModelConfig
from .huggingFace import HuggingFace



class EmbeddingModelFactory:
    
    def get_method(model_type: str , config: dict):
        
        if (model_type == "hugging_face"):
            validated_data = HuggingFaceEmbeddingModelConfig(**config)
            embeddingModel =  HuggingFace()
            
            api_key = config.get("api_key", getattr(validated_data, "api_key", None))
            
            embeddingModel.set_model(model_name=validated_data.model_name, api_key=api_key)
            return embeddingModel.get_model()
            
    