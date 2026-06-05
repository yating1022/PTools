from typing import Annotated

from fastapi import Depends

from app.services.gy_auth_service import GyAuthService, get_gy_auth_service
from app.services.gy_file_service import GyFileService, get_gy_file_service

GyAuthDep = Annotated[GyAuthService, Depends(get_gy_auth_service)]
GyFileDep = Annotated[GyFileService, Depends(get_gy_file_service)]
