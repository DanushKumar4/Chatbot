from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import supabase_admin

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
def signup(req: SignupRequest):
    try:
        response = supabase_admin.auth.sign_up({
            "email": req.email,
            "password": req.password,
        })

        if not response.user:
            raise HTTPException(
                status_code=400,
                detail="Unable to create account",
            )

        customer = (
            supabase_admin
            .table("customer")
            .insert({
                "full_name": req.full_name,
                "email": req.email,
            })
            .execute()
        )

        return {
            "message": "Signup successful",
            "user": response.user,
            "customer": customer.data[0] if customer.data else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post("/login")
def login(req: LoginRequest):
    try:
        response = supabase_admin.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        customer = (
            supabase_admin
            .table("customer")
            .select("*")
            .eq("email", req.email)
            .single()
            .execute()
        )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": response.user,
            "customer": customer.data,
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}