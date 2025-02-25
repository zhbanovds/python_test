from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from authlib.integrations.starlette_client import OAuth
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models, database

# JWT настройки
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# OAuth настройка
oauth = OAuth()
oauth.register(
    name='yandex',
    client_id='YOUR_YANDEX_CLIENT_ID',
    client_secret='YOUR_YANDEX_CLIENT_SECRET',
    access_token_url='https://oauth.yandex.com/token',
    authorize_url='https://oauth.yandex.com/authorize',
    api_base_url='https://login.yandex.ru/info',
    client_kwargs={'scope': 'login:email'}
)

oauth.register(
    name='vk',
    client_id='YOUR_VK_CLIENT_ID',
    client_secret='YOUR_VK_CLIENT_SECRET',
    access_token_url='https://oauth.vk.com/access_token',
    authorize_url='https://oauth.vk.com/authorize',
    api_base_url='https://api.vk.com/method',
    client_kwargs={'scope': 'email', 'v': '5.131'}
)

# JWT логика
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Получение текущего пользователя
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = database.SessionLocal()
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Проверка ролей
def require_role(required_roles: list):
    def role_checker(user: models.User = Depends(get_current_user)):
        if user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource"
            )
        return user
    return role_checker

# OAuth логин
async def oauth_login(request: Request, provider_name: str, db: Session):
    provider = oauth.create_client(provider_name)
    token = await provider.authorize_access_token(request)
    
    if provider_name == 'yandex':
        user_info = await provider.get('https://login.yandex.ru/info', token=token)
        profile = user_info.json()
        username = profile.get('login')
    elif provider_name == 'vk':
        user_info = await provider.get('users.get', token=token, params={'fields': 'photo,email'})
        profile = user_info.json()['response'][0]
        username = f"vk_{profile.get('id')}"
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Проверка или создание пользователя
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        user = models.User(username=username, hashed_password="oauth_user")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Генерация JWT
    jwt_token = create_access_token(data={"sub": user.username})
    return jwt_token
