from fastapi import HTTPException
from schemas.auth_schemas import SignupRequest, LoginRequest
from lib.jwt import AuthHandler
from models import User
from repositories.user import userRepository
from fastapi.responses import JSONResponse



class AuthController:
    
    
    
    
    ## SignUp Process 
    async def signup(self, payload: SignupRequest):
      existing = await userRepository.getUserByEmail(payload.email)

      if existing:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Your profile already exists. Please log in."
            }
        )

      hashed = AuthHandler.hash_password(payload.password) if payload.password else None

      user : User = User(
        name=payload.name,
        identifier=payload.identifier,
        password_hash=hashed,
        role=payload.role,
        email=payload.email
       )

      userProfile : User = await userRepository.get_or_create(user)

      token = AuthHandler.create_access_token(
        userProfile.id,
        userProfile.role
        )

      return JSONResponse(
        status_code=201,
        content={
            "access_token": token,
            "user_id": userProfile.id,
            "role": userProfile.role
        }
    )
    
    
    ## login process 
    async def login(self, payload: LoginRequest):
        user : User = await userRepository.getUserByEmail(payload.email) 
        
        if user == None: 
            raise HTTPException(status_code=401, detail="Wrong Credentials")
        
        if not AuthHandler.verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Wrong Credntials")
        
        
        ## token creation process 
        token = AuthHandler.create_access_token(user.id, user.role)

        

        return {"access_token": token, "user_id": user.id, "role": user.role}
    


auth = AuthController()     