from fastapi.testclient import TestClient
from sqlmodel import Session, select
from decimal import Decimal
from app.core.config import settings
from app.financials.service import FinancialService

def test_generate_remittances_flow(client: TestClient, superuser_token_headers: dict[str, str]):
    response = client.post(
        f"{settings.API_V1_STR}/generate-remittances-for-all-users",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "task_id" in content
    task_id = content["task_id"]
    
    # Poll status
    status_resp = client.get(
        f"{settings.API_V1_STR}/task-status/{task_id}",
        headers=superuser_token_headers,
    )
    assert status_resp.status_code == 200
    assert "status" in status_resp.json()

def test_cancel_remittance_flow(client: TestClient, superuser_token_headers: dict[str, str], db: Session):
    from app.financials.models import Remittance, RemittanceState
    from app.models import User
    admin = db.exec(select(User).where(User.is_superuser)).first()
    
    # Create a pending remittance manually
    remittance = Remittance(worker_id=admin.id, amount=Decimal("50.00"), status=RemittanceState.PENDING)
    db.add(remittance)
    db.commit()
    
    response = client.post(
        f"{settings.API_V1_STR}/remittances/{remittance.id}/cancel",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == RemittanceState.AWAITING_APPROVAL

def test_approve_remittance_flow(client: TestClient, superuser_token_headers: dict[str, str], db: Session):
    from app.financials.models import Remittance, RemittanceState, Wallet
    from app.models import User
    admin = db.exec(select(User).where(User.is_superuser)).first()
    
    # Setup Admin wallet with reserve
    wallet = FinancialService.get_or_create_wallet(db, admin.id)
    wallet.balance = Decimal("1000.00")
    wallet.reserve = Decimal("50.00")
    db.add(wallet)
    db.flush()
    
    # Create a paused remittance manually
    remittance = Remittance(worker_id=admin.id, amount=Decimal("50.00"), status=RemittanceState.AWAITING_APPROVAL)
    db.add(remittance)
    db.commit()
    
    response = client.post(
        f"{settings.API_V1_STR}/remittances/{remittance.id}/approve",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == RemittanceState.COMPLETED
    
    db.refresh(wallet)
    assert wallet.reserve == Decimal("0.00")
    assert wallet.balance == Decimal("1050.00") # Credited to self in this test case