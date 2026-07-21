# Authentication Module Feature Mapping

## Objective

This document maps the existing Authentication module features to the planned FastAPI microservices architecture.

| Existing Authentication Feature | Planned Microservice | Remarks |
|---------------------------------|----------------------|---------|
| User Login | Identity and Authentication Service | User authentication and JWT token generation |
| User Logout | Identity and Authentication Service | Token/session invalidation |
| JWT Token Generation | Identity and Authentication Service | Access and refresh token management |
| Password Hashing (Bcrypt/Passlib) | Identity and Authentication Service | Secure password encryption |
| Role-Based Authorization | Identity and Authentication Service | Role and permission validation |
| User Registration | Registration and Verification Service | New user account creation |
| Email Verification | Registration and Verification Service | Verify email using OTP or verification link |
| OTP Verification | Registration and Verification Service | User verification process |
| Password Reset / Forgot Password | Registration and Verification Service | Password recovery workflow |
| Organization Creation | Organization and Tenant Service | Create organizations/tenants |
| Tenant Management | Organization and Tenant Service | Tenant configuration and management |
| Email Notifications | Notification Service | Registration, verification, and password reset emails |
| SMS Notifications (Future) | Notification Service | SMS alerts and OTP delivery |

## Notes

- This task only prepares the microservices architecture.
- No API implementation has been migrated.
- No database connection has been configured.
- Docker containers have not been started.
- Full implementation will be completed in the next development phase.