from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import models 
import schemas
import database
import auth
from tasks import send_welcome_message_task
from sqlalchemy.exc import IntegrityError
from models import LoginHistory 

app = FastAPI()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Регистрация пользователя
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role, chat_id=user.chat_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Отправляем задачу в очередь на приветственное сообщение
    send_welcome_message_task.delay(new_user.username, new_user.chat_id)
    return new_user



# JWT Авторизация
@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = None):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(data={"sub": user.username})

    # Логируем успешную авторизацию
    client_ip = request.client.host
    login_history = LoginHistory(user_id=user.id, ip_address=client_ip, login_method="JWT")
    db.add(login_history)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

# OAuth маршруты для Yandex и VK
@app.get('/login/yandex')
async def login_yandex(request: Request):
    redirect_uri = request.url_for('auth_yandex')
    return await auth.oauth.yandex.authorize_redirect(request, redirect_uri)

@app.get('/auth/yandex')
async def auth_yandex(request: Request, db: Session = Depends(get_db)):
    token = await auth.oauth_login(request, 'yandex', db)

    # Логируем успешную авторизацию
    username = auth.get_username_from_token(token)
    user = db.query(models.User).filter(models.User.username == username).first()
    client_ip = request.client.host
    login_history = LoginHistory(user_id=user.id, ip_address=client_ip, login_method="OAuth-Yandex")
    db.add(login_history)
    db.commit()

    return {"access_token": token, "token_type": "bearer"}

@app.get('/login/vk')
async def login_vk(request: Request):
    redirect_uri = request.url_for('auth_vk')
    return await auth.oauth.vk.authorize_redirect(request, redirect_uri)

@app.get('/auth/vk')
async def auth_vk(request: Request, db: Session = Depends(get_db)):
    token = await auth.oauth_login(request, 'vk', db)

    # Логируем успешную авторизацию
    username = auth.get_username_from_token(token)
    user = db.query(models.User).filter(models.User.username == username).first()
    client_ip = request.client.host
    login_history = LoginHistory(user_id=user.id, ip_address=client_ip, login_method="OAuth-VK")
    db.add(login_history)
    db.commit()

    return {"access_token": token, "token_type": "bearer"}

# Защищенный маршрут
@app.get("/protected")
def protected_route(user: models.User = Depends(auth.get_current_user)):
    return {"message": f"Hello, {user.username}!"}

# История логинов для текущего пользователя
@app.get("/login-history")
def get_login_history(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    history = db.query(models.LoginHistory).filter(models.LoginHistory.user_id == user.id).all()
    return [{"login_time": h.login_time, "ip_address": h.ip_address, "method": h.login_method} for h in history]
