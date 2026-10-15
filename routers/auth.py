from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
import schemas
import crud
from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create first user as admin
    user_count = db.query(crud.models.User).count()
    if user_count == 0:
        # First user becomes admin
        from auth import get_password_hash
        hashed_password = get_password_hash(user.password)
        db_user = crud.models.User(
            full_name=user.full_name,
            email=user.email,
            phone_number=user.phone_number,
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    else:
        db_user = crud.create_user(db, user)
    
    return db_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_admin": user.is_admin,
        "full_name": user.full_name,
        "email": user.email
    }

@router.post("/google-login")
def google_login(email: str, full_name: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        # Create user with random password
        import secrets
        import string
        random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        user_data = schemas.UserCreate(
            full_name=full_name,
            email=email,
            password=random_password,
            confirm_password=random_password
        )
        user = crud.create_user(db, user_data)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_admin": user.is_admin,
        "full_name": user.full_name,
        "email": user.email
    }