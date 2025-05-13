from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class BaseAPIException(HTTPException):
    def __init__(
            self,
            status_code: int,
            detail: Any = None,
            headers: Optional[Dict[str, str]] = None
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class StationNotFoundException(BaseAPIException):
    def __init__(self, station_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Posto de carregamento {station_id} não encontrado"
        )


class StationAlreadyReservedException(BaseAPIException):
    def __init__(self, station_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Posto de carregamento {station_id} já está reservado"
        )


class ServerCommunicationException(BaseAPIException):
    def __init__(self, server: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro na comunicação com o servidor {server}"
        )


class InvalidReservationDataException(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
