from app.schemas.auth import (
    StudentRegisterRequest,
    TeacherRegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    MessageResponse
)
from app.schemas.user import (
    UserResponse,
    StudentProfileResponse,
    TeacherProfileResponse,
    UserProfileUpdate
)
from app.schemas.class_schema import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassJoinRequest,
    ClassMemberResponse,
    AssignRepRequest,
    AssignTeacherRequest
)
from app.schemas.poll import (
    PollCreate,
    PollUpdate,
    PollResponse,
    PollOptionResponse
)
from app.schemas.response import (
    SubmitResponseRequest,
    ParticipantDetail,
    PollParticipantsResponse,
    StudentHistoryItem,
    StudentDashboardStats,
    TeacherDashboardStats,
    FacultyDashboardStats
)
