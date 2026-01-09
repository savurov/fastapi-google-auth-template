from fastapi import APIRouter, Request, Response, status
from fastapi.responses import RedirectResponse

from src.auth import google_oauth
from src.auth.google_oauth import OAuthFlowError
from src.core import security
from src.core.config import settings
from src.users.repo import UserRepoDep

router = APIRouter(prefix="/auth", tags=["auth"])


def redirect_oauth_failed() -> RedirectResponse:
    response = RedirectResponse(
        settings.frontend_oauth_error_url, status.HTTP_303_SEE_OTHER
    )
    security.delete_oauth_state_cookie(response)
    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (clear auth cookie)",
)
async def logout(response: Response) -> None:
    security.delete_auth_cookie(response)


@router.get("/google/login", summary="Redirect to Google auth page")
async def start_google_oauth() -> RedirectResponse:
    state = google_oauth.generate_token_state()
    url = google_oauth.build_google_auth_url(state=state)

    response = RedirectResponse(str(url), status_code=status.HTTP_303_SEE_OTHER)
    security.set_oauth_state_cookie(response, state)
    return response


@router.get("/google/callback", summary="Complete Google OAuth (set JWT cookie)")
async def finish_google_oauth(
    request: Request,
    user_repo: UserRepoDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    try:
        if error is not None:
            raise OAuthFlowError(error)
        if code is None:
            raise OAuthFlowError("Code param is missing")

        saved_state = request.cookies.get(security.OAUTH_STATE_COOKIE_NAME)
        if state is None or saved_state != state:
            raise OAuthFlowError("Invalid state")

        id_token = await google_oauth.fetch_id_token_from_code(code)
        google_user = google_oauth.verify_id_token(id_token)

        user = await user_repo.update_or_create_google_user(google_user)
    except OAuthFlowError as exc:
        print("Google OAuth failed: ", exc)
        return redirect_oauth_failed()

    except Exception as exc:  # pragma: no cover
        print("Unexpected OAuth error: ", exc)
        return redirect_oauth_failed()

    response = RedirectResponse(settings.frontend_url, status.HTTP_303_SEE_OTHER)
    security.delete_oauth_state_cookie(response)
    security.set_auth_cookie(response, user.id)
    return response
