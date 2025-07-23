from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from ..models.schemas import AuthStatus
from ..services.auth_service import auth_service
from ..config.settings import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/start")
def auth_start():
    """Start OAuth flow"""
    auth_url = auth_service.get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
def auth_callback(request: Request):
    """Handle OAuth callback"""
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Missing code in callback.")
    
    # Handle the callback and save credentials
    auth_service.handle_callback(code)
    
    # Redirect to frontend with success parameter
    return RedirectResponse(url=f"{settings.frontend_url}/?auth=success")


@router.get("/status", response_model=AuthStatus)
def auth_status():
    """Check if user is authenticated"""
    return AuthStatus(authenticated=auth_service.is_authenticated())


@router.post("/logout")
def auth_logout():
    """Log out user by removing token file"""
    success = auth_service.logout()
    return {"message": "Logged out successfully" if success else "No user was logged in"} 